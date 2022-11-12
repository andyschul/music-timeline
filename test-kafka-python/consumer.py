from confluent_kafka import Consumer
from cassandra.cluster import Cluster
import json
from astrapy.client import create_astra_client
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from functools import lru_cache
cluster = Cluster()
session = cluster.connect()
import os

SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
ASTRA_DB_ID = os.environ['ASTRA_DB_ID']
ASTRA_DB_REGION = os.environ['ASTRA_DB_REGION']
ASTRA_DB_APPLICATION_TOKEN = os.environ['ASTRA_DB_APPLICATION_TOKEN']
ASTRA_DB_KEYSPACE = 'music'
ASTRA_DB_ALBUMS_TABLE = 'albums'
ASTRA_DB_ARTISTS_TABLE = 'artists'
LOAD_LIMIT = 20

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))
astra_client = create_astra_client(astra_database_id=ASTRA_DB_ID,
                                   astra_database_region=ASTRA_DB_REGION,
                                   astra_application_token=ASTRA_DB_APPLICATION_TOKEN)

def artist_is_loaded(artist_id):
  query = {
    'id': {'$eq': artist_id}
  }
  res = astra_client.rest.search_table(keyspace=ASTRA_DB_KEYSPACE, table=ASTRA_DB_ARTISTS_TABLE, query=query)
  if 'count' in res and res['count'] == 1:
    return True
  return False

def load_artist(artist_id):
  artist = spotify.artist(artist_id)
  results = spotify.artist_albums(artist_id, country='US')
  albums = results['items']

  while results['next']:
      results = spotify.next(results)
      albums.extend(results['items'])

  # TODO: Remove clean albums from results

  count = 0
  for album in albums:
    if count > LOAD_LIMIT:
      break
    count += 1
    if album['release_date_precision'] != 'day' or album['album_type'] == 'compilation':
        continue
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
    # load each album into cassandra
    row = astra_client.rest.add_row(keyspace=ASTRA_DB_KEYSPACE, table=ASTRA_DB_ALBUMS_TABLE, row=data)
    print(row)

  print('loading artist')
  artist_data = {
    'id': artist['id'],
    'uri': artist['uri'],
    'name': artist['name'],
    'href': artist['href'],
    'image': artist['images'][0]['url'],
    'genres': artist['genres']
  }
  row = astra_client.rest.add_row(keyspace=ASTRA_DB_KEYSPACE, table=ASTRA_DB_ARTISTS_TABLE, row=artist_data)
  print(row)

@lru_cache(maxsize=None)
def check_followed_artists(followed_artists):
    print('checking artists')
    for artist_id in followed_artists:
        if not artist_is_loaded(artist_id):
            print(f'loading artist: {artist_id}')
            load_artist(artist_id)

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
                record_key = msg.key()
                record_value = msg.value()
                data = json.loads(record_value)
                print(data)
                check_followed_artists(tuple(data['artist_ids']))
                
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
