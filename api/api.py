from flask import Flask, request
from confluent_kafka import Producer, KafkaError
import json
import requests
from confluent_kafka import Producer, KafkaError
from astrapy.client import create_astra_client
import os

ASTRA_DB_ID = os.environ['ASTRA_DB_ID']
ASTRA_DB_REGION = os.environ['ASTRA_DB_REGION']
ASTRA_DB_APPLICATION_TOKEN = os.environ['ASTRA_DB_APPLICATION_TOKEN']
ASTRA_DB_KEYSPACE = 'music'
ASTRA_DB_ALBUMS_TABLE = 'albums'
ASTRA_DB_ARTISTS_TABLE = 'artists'

headers = {
  'content-type': 'application/json',
  'x-cassandra-token': ASTRA_DB_APPLICATION_TOKEN
}

astra_client = create_astra_client(astra_database_id=ASTRA_DB_ID,
                                   astra_database_region=ASTRA_DB_REGION,
                                   astra_application_token=ASTRA_DB_APPLICATION_TOKEN)

producer_conf = {
    'bootstrap.servers': os.environ['KAFKA_BOOTSTRAP_SERVERS'],
    'security.protocol': os.environ['KAFKA_SECURITY_PROTOCOL'],
    'sasl.mechanisms': os.environ['KAFKA_SASL_MECHANISMS'],
    'sasl.username': os.environ['KAFKA_SASL_USERNAME'],
    'sasl.password': os.environ['KAFKA_SASL_PASSWORD'],
    'session.timeout.ms': os.environ['KAFKA_SESSION_TIMEOUT']
}
producer = Producer(producer_conf)
topic = 'load-new-artists'

app = Flask(__name__)

@app.route("/")
def home():
    followers = requests.get('https://api.spotify.com/v1/me/following?type=artist', headers={'Authorization': request.headers['Authorization']})
    artist_ids = [artist['id'] for artist in followers.json()['artists']['items']]

    producer.produce(topic, key="spotify", value=json.dumps({'artist_ids': artist_ids}))

    url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/keyspaces/{ASTRA_DB_KEYSPACE}/{ASTRA_DB_ALBUMS_TABLE}'
    params = {
        'where': json.dumps({
            'artist_id': {'$in': artist_ids},
            'release_date': {'$gt': '2000-10-01'}
        })
    }
    res = requests.get(url, headers=headers, params=params)

    j_res = json.loads(res.text)
    albums = j_res['data']
    while 'pageState' in j_res:
        params.update({'page-state': j_res['pageState']})
        res = requests.get(url, headers=headers, params=params)
        j_res = json.loads(res.text)
        albums.extend(j_res['data'])

    grouped_albums = {}
    for row in albums:
        album_id = row['id']
        album_group = row['album_group']
        if album_id not in grouped_albums:
            grouped_albums[album_id] = {
                'id': row['id'],
                'name': row['name'],
                'image_url': row['image_url'],
                'release_date': row['release_date'],
                'album_type': row['album_type'],
                'artists': row['album_artists'],
                'appearances_by': []
            }
        if album_group == 'appears_on':
            grouped_albums[album_id]['appearances_by'].append(row['artist_name'])

    results = {}
    for _, row in grouped_albums.items():
        date = row['release_date']
        album_type = row['album_type']
        if date not in results:
            results[date] = {
                'singles': [],
                'albums': []
            }
        if album_type == 'single':
            results[date]['singles'].append(row)
        elif album_type == 'album':
            results[date]['albums'].append(row)

    return json.dumps(dict(sorted(results.items(), reverse=True)))