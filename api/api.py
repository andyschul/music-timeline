from flask import Flask
from cassandra.cluster import Cluster
import json

cluster = Cluster()
session = cluster.connect()

app = Flask(__name__)

@app.route("/")
def home():
    select_all = '''
    SELECT id, name, release_date, album_type, artist_id, artist_name, image_url FROM music.albums WHERE release_date >= '2022-10-01' AND artist_id IN ('2WX2uTcsvV5OnS0inACecP','6FBDaR13swtiWwGhX1WQsP','2avRYQUWQpIkzJOEkf0MdY','5f7VJjfbwm532GiveGC0ZK');
    '''
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

    return json.dumps(result)