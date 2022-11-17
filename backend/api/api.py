from flask import Flask, request, jsonify
import json
import requests
from confluent_kafka import Producer
import os
from operator import itemgetter
from itertools import groupby

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

@app.route("/timeline")
def timeline():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    followers = requests.get('https://api.spotify.com/v1/me/following?type=artist', headers={'Authorization': request.headers['Authorization']})
    artist_ids = [artist['id'] for artist in followers.json()['artists']['items']]

    producer.produce(topic, key="spotify", value=json.dumps({'artist_ids': artist_ids}))

    url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/keyspaces/{ASTRA_DB_KEYSPACE}/{ASTRA_DB_ALBUMS_TABLE}'
    params = {
        'where': json.dumps({
            'artist_id': {'$in': artist_ids},
            'release_date': {'$lte': to_date, '$gt': from_date}
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

    result = []
    albums = sorted(albums, key=itemgetter('release_date', 'id'), reverse=True)
    for release_date, date_group in groupby(albums, itemgetter('release_date')):
        date_row = {
            'release_date': release_date,
            'singles': [],
            'albums': []
        }
        for album_id, album_group in groupby(list(date_group), itemgetter('id')):
            album_row = {
                'appearances_by': []
            }
            for album in album_group:
                if 'id' not in album_row:
                    album_row['id'] = album_id
                    album_row['name'] = album['name']
                    album_row['image_url'] = album['image_url']
                    album_row['release_date'] = album['release_date']
                    album_row['album_type'] = album['album_type']
                    album_row['artists'] = album['album_artists']
                if album['album_group'] == 'appears_on':
                    album_row['appearances_by'].append(album['artist_name'])
            if album_row['album_type'] == 'album':
                date_row['albums'].append(album_row)
            else:
                date_row['singles'].append(album_row)
        result.append(date_row)

    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
