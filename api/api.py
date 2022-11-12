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
ASTRA_DB_TABLE = 'albums'

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

    query = {
        'artist_id': {'$in': artist_ids},
        'release_date': {'$gt': '2000-10-01'}
    }
    options = {'page-size': 100}
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