from flask import Flask, request
from confluent_kafka import Producer, KafkaError
import json
import requests
from astrapy.client import create_astra_client
import os

ASTRA_DB_ID = os.environ['ASTRA_DB_ID']
ASTRA_DB_REGION = os.environ['ASTRA_DB_REGION']
ASTRA_DB_APPLICATION_TOKEN = os.environ['ASTRA_DB_APPLICATION_TOKEN']
ASTRA_DB_KEYSPACE = 'music'
ASTRA_DB_TABLE = 'albums'
SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']

headers = {
  'content-type': 'application/json',
  'x-cassandra-token': ASTRA_DB_APPLICATION_TOKEN
}

astra_client = create_astra_client(astra_database_id=ASTRA_DB_ID,
                                   astra_database_region=ASTRA_DB_REGION,
                                   astra_application_token=ASTRA_DB_APPLICATION_TOKEN)

# TODO: integrate kafka
# topic = 'test1'
# conf = ccloud_lib.read_ccloud_config(Path(__file__).parent / './.kafka.config')
# api_conf = ccloud_lib.read_ccloud_config(Path(__file__).parent / './.api.config')

# # Create Producer instance
# producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
# producer = Producer(producer_conf)

# # Create topic if needed
# ccloud_lib.create_topic(conf, topic)

app = Flask(__name__)

@app.route("/")
def home():
    followers = requests.get('https://api.spotify.com/v1/me/following?type=artist', headers={'Authorization': request.headers['Authorization']})
    artist_ids = [artist['id'] for artist in followers.json()['artists']['items']]
    # producer.produce(topic, key="spotify", value=json.dumps({'artist_ids': artist_ids}))

    query = {
        'artist_id': {'$in': artist_ids},
        'release_date': {'$gt': '2010-10-01'}
    }
    options = {'fields': 'id,name,release_date,album_type,artist_id,artist_name,image_url'}
    res = astra_client.rest.search_table(keyspace=ASTRA_DB_KEYSPACE, table=ASTRA_DB_TABLE, query=query, options=options)

    result = {}
    for row in res['data']:
        date = row['release_date']
        album_data = {
            'id': row['id'],
            'name': row['name'],
            'image_url': row['image_url'],
            'release_date': row['release_date'],
            'album_type': row['album_type'],
            'artist_id': row['artist_id'],
            'artist_name': row['artist_name']
        }
        if date not in result:
            result[date] = {
                'singles': [],
                'albums': []
            }
        if row['album_type'] == 'single':
            result[date]['singles'].append(album_data)
        elif row['album_type'] == 'album':
            result[date]['albums'].append(album_data)

    return json.dumps(dict(sorted(result.items(), reverse=True)))