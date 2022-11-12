import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import json
from astrapy.client import create_astra_client
import os

DISCOGS_CONSUMER_ID = os.environ['DISCOGS_CONSUMER_ID']
DISCOGS_CONSUMER_SECRET = os.environ['DISCOGS_CONSUMER_SECRET']
SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
ASTRA_DB_ID = os.environ['ASTRA_DB_ID']
ASTRA_DB_REGION = os.environ['ASTRA_DB_REGION']
ASTRA_DB_APPLICATION_TOKEN = os.environ['ASTRA_DB_APPLICATION_TOKEN']
ASTRA_DB_KEYSPACE = 'music'
ASTRA_DB_ALBUMS_TABLE = 'albums'
ASTRA_DB_ARTISTS_TABLE = 'artists'

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

astra_client = create_astra_client(astra_database_id=ASTRA_DB_ID,
                                   astra_database_region=ASTRA_DB_REGION,
                                   astra_application_token=ASTRA_DB_APPLICATION_TOKEN)

headers = {
  'content-type': 'application/json',
  'x-cassandra-token': ASTRA_DB_APPLICATION_TOKEN
}

def delete_albums_table():
  url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/schemas/keyspaces/{ASTRA_DB_KEYSPACE}/tables/{ASTRA_DB_ALBUMS_TABLE}'
  res = requests.delete(url, headers=headers)
  print(res)

def delete_artists_table():
  url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/schemas/keyspaces/{ASTRA_DB_KEYSPACE}/tables/{ASTRA_DB_ARTISTS_TABLE}'
  res = requests.delete(url, headers=headers)
  print(res)

def create_albums_table():
  udt_url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/schemas/keyspaces/{ASTRA_DB_KEYSPACE}/types'
  udt_data = {
  "name": "artist",
  "ifNotExists": True,
  "fields":[
      {
        "name": "id",
        "typeDefinition": "text"
      },
      {
        "name": "name",
        "typeDefinition": "text"
      },
      {
        "name": "type",
        "typeDefinition": "text"
      },
      {
        "name": "href",
        "typeDefinition": "text"
      },
      {
        "name": "uri",
        "typeDefinition": "text"
      }
    ]
  }
  res = requests.post(udt_url, headers=headers, data=json.dumps(udt_data))
  print(res)

  url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/schemas/keyspaces/{ASTRA_DB_KEYSPACE}/tables'
  data = {
    "name": ASTRA_DB_ALBUMS_TABLE,
    "ifNotExists": True,
    "columnDefinitions": [
      {"name": "id", "typeDefinition": "text"},
      {"name": "href", "typeDefinition": "text"},
      {"name": "image_url", "typeDefinition": "text"},
      {"name": "name", "typeDefinition": "text"},
      {"name": "release_date", "typeDefinition": "text"},
      {"name": "album_type", "typeDefinition": "text"},
      {"name": "album_group", "typeDefinition": "text"},
      {"name": "album_artists", "typeDefinition": "list<artist>"},
      {"name": "uri", "typeDefinition": "text"},
      {"name": "total_tracks", "typeDefinition": "int"},
      {"name": "artist_id", "typeDefinition": "text"},
      {"name": "artist_uri", "typeDefinition": "text"},
      {"name": "artist_name", "typeDefinition": "text"},
      {"name": "artist_href", "typeDefinition": "text"},
      {"name": "artist_image", "typeDefinition": "text"},
      {"name": "artist_genres", "typeDefinition": "set<text>"}
    ],
    "primaryKey":
      {
        "partitionKey": ["artist_id"],
        "clusteringKey": ["release_date", "id"]
      },
    "tableOptions": {"defaultTimeToLive":0}}
  res = requests.post(url, headers=headers, data=json.dumps(data))
  print(res)


def create_artists_table():
  url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/schemas/keyspaces/{ASTRA_DB_KEYSPACE}/tables'
  data = {
    "name": ASTRA_DB_ARTISTS_TABLE,
    "ifNotExists": True,
    "columnDefinitions": [
      {"name": "id", "typeDefinition": "text"},
      {"name": "uri", "typeDefinition": "text"},
      {"name": "name", "typeDefinition": "text"},
      {"name": "href", "typeDefinition": "text"},
      {"name": "image", "typeDefinition": "text"},
      {"name": "genres", "typeDefinition": "set<text>"}
    ],
    "primaryKey":
      {
        "partitionKey": ["id"]
      },
    "tableOptions": {"defaultTimeToLive":0}}
  res = requests.post(url, headers=headers, data=json.dumps(data))
  print(res)


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
    if count > 2:
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

def get_artist(artist_id):
  query = {
    'artist_id': {'$in': [artist_id]},
    'release_date': {'$gt': '2010-10-01'}
  }
  options = {'fields': 'id,name,release_date,album_type,artist_id,artist_name,image_url'}
  res = astra_client.rest.search_table(keyspace=ASTRA_DB_KEYSPACE, table=ASTRA_DB_ALBUMS_TABLE, query=query, options=options)
  print(res)

def artist_is_loaded(artist_id):
  query = {
    'id': {'$eq': artist_id}
  }
  res = astra_client.rest.search_table(keyspace=ASTRA_DB_KEYSPACE, table=ASTRA_DB_ARTISTS_TABLE, query=query)
  if 'count' in res and res['count'] == 1:
    return True
  return False

# eminem_id = '7dGJo4pcD2V6oG8kP0tJRR'
# big_sean_id = '0c173mlxpT3dSFRgMO8XPh'

# delete_albums_table()
# create_albums_table()
# delete_artists_table()
# create_artists_table()
# load_artist(big_sean_id)
# get_artist(eminem_id)
# print(artist_is_loaded(big_sean_id))
