from flask import Flask, request
from cassandra.cluster import Cluster
from confluent_kafka import Producer, KafkaError
import json
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
cluster = Cluster()
session = cluster.connect()
import ccloud_lib
from pathlib import Path


topic = 'test1'
conf = ccloud_lib.read_ccloud_config(Path(__file__).parent / './.kafka.config')
api_conf = ccloud_lib.read_ccloud_config(Path(__file__).parent / './.api.config')
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=api_conf['spotify.client_id'], client_secret=api_conf['spotify.client_secret']))

# Create Producer instance
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
producer = Producer(producer_conf)

# Create topic if needed
ccloud_lib.create_topic(conf, topic)


app = Flask(__name__)

@app.route("/")
def home():
    followers = requests.get('https://api.spotify.com/v1/me/following?type=artist', headers={'Authorization': request.headers['Authorization']})
    artist_ids = [artist['id'] for artist in followers.json()['artists']['items']]
    producer.produce(topic, key="spotify", value=json.dumps({'artist_ids': artist_ids}))

    artist_ids = ', '.join(["'{}'".format(artist['id']) for artist in followers.json()['artists']['items']])
    select_all = '''
    SELECT id, name, release_date, album_type, artist_id, artist_name, image_url FROM music.albums WHERE release_date >= '2022-10-01' AND artist_id IN ({});
    '''.format(artist_ids)
    rows = session.execute(select_all)

    result = {}
    for row in rows:
        date = row.release_date
        album_data = {
            'id': row.id,
            'name': row.name,
            'image_url': row.image_url,
            'release_date': row.release_date,
            'album_type': row.album_type,
            'artist_id': row.artist_id,
            'artist_name': row.artist_name
        }
        if date not in result:
            result[date] = {
                'singles': [],
                'albums': []
            }
        if row.album_type == 'single':
            result[date]['singles'].append(album_data)
        elif row.album_type == 'album':
            result[date]['albums'].append(album_data)

    return json.dumps(dict(sorted(result.items(), reverse=True)))