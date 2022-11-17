from confluent_kafka import Consumer
import json
import spotipy
import requests
from spotipy.oauth2 import SpotifyClientCredentials
from cleaner import data_cleaner, album_cleaner
import aiohttp
import asyncio
import os
import time

SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
ASTRA_DB_ID = os.environ['ASTRA_DB_ID']
ASTRA_DB_REGION = os.environ['ASTRA_DB_REGION']
ASTRA_DB_APPLICATION_TOKEN = os.environ['ASTRA_DB_APPLICATION_TOKEN']
ASTRA_DB_KEYSPACE = 'music'
ASTRA_DB_ALBUMS_TABLE = 'albums'
ASTRA_DB_ARTISTS_TABLE = 'artists'

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

headers = {
  'content-type': 'application/json',
  'x-cassandra-token': ASTRA_DB_APPLICATION_TOKEN
}

async def load_album(session, data):
    url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/keyspaces/{ASTRA_DB_KEYSPACE}/{ASTRA_DB_ALBUMS_TABLE}'
    async with session.post(url, data=json.dumps(data), headers=headers) as resp:
        res = await resp.json()
        return res


def get_loaded_artists(artist_ids):
    url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/keyspaces/{ASTRA_DB_KEYSPACE}/{ASTRA_DB_ARTISTS_TABLE}'
    params = {
        'where': json.dumps({
            'id': {'$in': artist_ids}
        })
    }
    res = requests.get(url, headers=headers, params=params)
    res = json.loads(res.text)
    return set([artist['id'] for artist in res['data']])

def get_artist_albums_from_spotify(artist_id):
  start_time = time.time()
  artist = spotify.artist(artist_id)
  results = spotify.artist_albums(artist_id, country='US')
  albums = results['items']

  while results['next']:
      results = spotify.next(results)
      albums.extend(results['items'])
  load_time = "--- %s seconds ---" % (time.time() - start_time)
  print(f'collected {len(albums)} albums from spotify in {load_time}')
  return (artist, albums)

async def load_artist(artist_id):
  artist, albums = get_artist_albums_from_spotify(artist_id)

  # Remove unwanted albums from results
  start_time = time.time()
  filtered_albums = album_cleaner(albums)
  load_time = "--- %s seconds ---" % (time.time() - start_time)
  print(f'filtered to {len(filtered_albums)} albums in {load_time}')

  async with aiohttp.ClientSession() as session:
    tasks = []

    for album in filtered_albums:
        data = {
        'id': album['id'],
        'href': album['href'],
        'image_url': album['images'][0]['url'],
        'name': album['name'],
        'release_date': album['release_date'],
        'album_type': album['album_type'],
        'album_group': album['album_group'],
        'album_artists': [{key : val for key, val in sub.items() if key != 'external_urls'} for sub in album['artists']],
        'uri': album['uri'],
        'total_tracks': album['total_tracks'],
        'artist_id': artist['id'],
        'artist_uri': artist['uri'],
        'artist_name': artist['name'],
        'artist_href': artist['href'],
        'artist_image': artist['images'][0]['url'],
        'artist_genres': artist['genres']
        }
        tasks.append(asyncio.ensure_future(load_album(session, data)))

    await asyncio.gather(*tasks)

    artist_data = {
        'id': artist['id'],
        'uri': artist['uri'],
        'name': artist['name'],
        'href': artist['href'],
        'image': artist['images'][0]['url'],
        'genres': artist['genres']
    }
    url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/keyspaces/{ASTRA_DB_KEYSPACE}/{ASTRA_DB_ARTISTS_TABLE}'
    requests.post(url, headers=headers, data=json.dumps(artist_data))


# TODO: cache with redis
def get_new_artists(followed_artists):
    loaded_artists = get_loaded_artists(followed_artists)
    return [artist_id for artist_id in followed_artists if artist_id not in loaded_artists]


if __name__ == '__main__':
    topic = 'load-new-artists'
    consumer_conf = {
        'bootstrap.servers': os.environ['KAFKA_BOOTSTRAP_SERVERS'],
        'security.protocol': os.environ['KAFKA_SECURITY_PROTOCOL'],
        'sasl.mechanisms': os.environ['KAFKA_SASL_MECHANISMS'],
        'sasl.username': os.environ['KAFKA_SASL_USERNAME'],
        'sasl.password': os.environ['KAFKA_SASL_PASSWORD'],
        'session.timeout.ms': os.environ['KAFKA_SESSION_TIMEOUT'],
        'group.id': 'python_example_group_1',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(consumer_conf)

    # Subscribe to topic
    consumer.subscribe([topic])

    # Process messages
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                print("Waiting for message or event/error in poll()")
                continue
            elif msg.error():
                print('error: {}'.format(msg.error()))
            else:
                # Check for Kafka message
                record_value = msg.value()
                data = json.loads(record_value)
                print(data)
                artist_ids = get_new_artists(tuple(data['artist_ids']))

                for artist_id in artist_ids:
                    print(f'loading new artist: {artist_id}')
                    start_time = time.time()
                    asyncio.run(load_artist(artist_id))
                    load_time = "--- %s seconds ---" % (time.time() - start_time)
                    print(f'finished loading artist: {artist_id} in {load_time}')

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
