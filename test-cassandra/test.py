import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import json
from astrapy.client import create_astra_client
import os

SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
ASTRA_DB_ID = os.environ['ASTRA_DB_ID']
ASTRA_DB_REGION = os.environ['ASTRA_DB_REGION']
ASTRA_DB_APPLICATION_TOKEN = os.environ['ASTRA_DB_APPLICATION_TOKEN']
ASTRA_DB_KEYSPACE = 'music'
ASTRA_DB_TABLE = 'albums'

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

astra_client = create_astra_client(astra_database_id=ASTRA_DB_ID,
                                   astra_database_region=ASTRA_DB_REGION,
                                   astra_application_token=ASTRA_DB_APPLICATION_TOKEN)

headers = {
  'content-type': 'application/json',
  'x-cassandra-token': ASTRA_DB_APPLICATION_TOKEN
}

def delete_table():
  url = 'https://{}-{}.apps.astra.datastax.com/api/rest/v2/schemas/keyspaces/{}/tables/albums'.format(ASTRA_DB_ID, ASTRA_DB_REGION, ASTRA_DB_KEYSPACE)
  res = requests.delete(url, headers=headers)

def create_table():
  url = 'https://{}-{}.apps.astra.datastax.com/api/rest/v2/schemas/keyspaces/{}/tables'.format(ASTRA_DB_ID, ASTRA_DB_REGION, ASTRA_DB_KEYSPACE)
  data = {
    "name": "albums",
    "ifNotExists": True,
    "columnDefinitions": [
      {"name": "id", "typeDefinition": "text"},
      {"name": "href", "typeDefinition": "text"},
      {"name": "image_url", "typeDefinition": "text"},
      {"name": "name", "typeDefinition": "text"},
      {"name": "release_date", "typeDefinition": "text"},
      {"name": "album_type", "typeDefinition": "text"},
      {"name": "uri", "typeDefinition": "text"},
      {"name": "artist_id", "typeDefinition": "text"},
      {"name": "artist_uri", "typeDefinition": "text"},
      {"name": "artist_name", "typeDefinition": "text"},
      {"name": "artist_href", "typeDefinition": "text"}
    ],
    "primaryKey":
      {
        "partitionKey": ["artist_id"],
        "clusteringKey": ["release_date", "id"]
      },
    "tableOptions": {"defaultTimeToLive":0}}
  res = requests.post(url, headers=headers, data=json.dumps(data))

def load_birdy():
  url = 'https://{}-{}.apps.astra.datastax.com/api/rest/v2/keyspaces/music/albums'.format(ASTRA_DB_ID, ASTRA_DB_REGION)
  artist_id = '2WX2uTcsvV5OnS0inACecP'
  results = spotify.artist_albums(artist_id)
  albums = results['items']

  while results['next']:
      results = spotify.next(results)
      albums.extend(results['items'])

  count = 0
  for album in albums:
    if count > 30:
      break
    count += 1
    if album['release_date_precision'] != 'day':
        continue
    for artist in album['artists']:
        data = {
          'id': album['id'],
          'href': album['href'],
          'image_url': album['images'][0]['url'],
          'name': album['name'],
          'release_date': album['release_date'],
          'album_type': album['album_type'],
          'uri': album['uri'],
          'artist_id': artist['id'],
          'artist_uri': artist['uri'],
          'artist_name': artist['name'],
          'artist_href': artist['href']
        }
        row = astra_client.rest.add_row(keyspace=ASTRA_DB_KEYSPACE, table=ASTRA_DB_TABLE, row=data)

def get_birdy():
  query = {
    'artist_id': {'$in': ['2WX2uTcsvV5OnS0inACecP']},
    'release_date': {'$gt': '2010-10-01'}
  }
  options = {'fields': 'id,name,release_date,album_type,artist_id,artist_name,image_url'}
  res = astra_client.rest.search_table(keyspace=ASTRA_DB_KEYSPACE, table=ASTRA_DB_TABLE, query=query, options=options)
  print(res)

# get_birdy()
load_birdy()

# cluster = Cluster()
# session = cluster.connect()

# create_keyspace = '''
# CREATE KEYSPACE IF NOT EXISTS music
#   WITH REPLICATION = {
#    'class' : 'SimpleStrategy',
#    'replication_factor' : 1
#   };
# '''
# session.execute(create_keyspace)

# drop_table = '''
# DROP TABLE IF EXISTS music.albums
# '''
# session.execute(drop_table)

# create_table = '''
# CREATE TABLE IF NOT EXISTS music.albums (
#    id text,
#    href text,
#    image_url text,
#    name text,
#    release_date text,
#    album_type text,
#    uri text,
#    artist_id text,
#    artist_uri text,
#    artist_name text,
#    artist_href text,
#    PRIMARY KEY (artist_id, release_date, id));
# '''
# session.execute(create_table)

# results = spotify.new_releases()
# albums = results['albums']['items']
# while results['albums']['next']:
#     results = spotify.next(results['albums'])
#     albums.extend(results['albums']['items'])

# for album in albums:
#     if album['release_date_precision'] != 'day':
#         continue
#     for artist in album['artists']:
#         insert_into = '''
#         INSERT INTO music.albums (id, href, image_url, name, release_date, album_type, uri, artist_id, artist_uri, artist_name, artist_href) VALUES ('{}', '{}', '{}', $${}$$, '{}', '{}', '{}', '{}', '{}', '{}', '{}');
#         '''.format(album['id'], album['href'], album['images'][0]['url'], album['name'], album['release_date'], album['album_type'], album['uri'], artist['id'], artist['uri'], artist['name'], artist['href'])
#         session.execute(insert_into)


# select_all = '''
# SELECT id, name, release_date, album_type, artist_id, artist_name, image_url FROM music.albums WHERE release_date >= '2022-10-01' AND artist_id IN ('6FBDaR13swtiWwGhX1WQsP','2avRYQUWQpIkzJOEkf0MdY','5f7VJjfbwm532GiveGC0ZK');
# '''
# rows = session.execute(select_all)

# result = {}
# for row in rows:
#     date = row.release_date
#     album_data = {
#         'id': row.id,
#         'name': row.name,
#         'image_url': row.image_url,
#         'release_date': row.release_date,
#         'album_type': row.album_type,
#         'artist_id': row.artist_id,
#         'artist_name': row.artist_name
#     }
#     if date not in result:
#         result[date] = {
#             'singles': [],
#             'albums': []
#         }
#     if row.album_type == 'single':
#         result[date]['singles'].append(album_data)
#     elif row.album_type == 'album':
#         result[date]['albums'].append(album_data)

# print(result)
