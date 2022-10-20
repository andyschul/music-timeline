from cassandra.cluster import Cluster
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

cluster = Cluster()
session = cluster.connect()

create_keyspace = '''
CREATE KEYSPACE IF NOT EXISTS music
  WITH REPLICATION = { 
   'class' : 'SimpleStrategy', 
   'replication_factor' : 1 
  };
'''
session.execute(create_keyspace)

drop_table = '''
DROP TABLE IF EXISTS music.albums
'''
session.execute(drop_table)

create_table = '''
CREATE TABLE IF NOT EXISTS music.albums (
   id text, 
   href text,
   image_url text,
   name text, 
   release_date text, 
   album_type text,
   uri text,
   artist_id text, 
   artist_uri text, 
   artist_name text, 
   artist_href text, 
   PRIMARY KEY (artist_id, release_date, id));
'''
session.execute(create_table)

artist_id = '2WX2uTcsvV5OnS0inACecP'
results = spotify.artist_albums(artist_id)
albums = results['items']
while results['next']:
    results = spotify.next(results)
    albums.extend(results['items'])

for album in albums:
    if album['release_date_precision'] != 'day':
        continue
    for artist in album['artists']:
        insert_into = '''
        INSERT INTO music.albums (id, href, image_url, name, release_date, album_type, uri, artist_id, artist_uri, artist_name, artist_href) VALUES ('{}', '{}', '{}', $${}$$, '{}', '{}', '{}', '{}', '{}', '{}', '{}');
        '''.format(album['id'], album['href'], album['images'][0]['url'], album['name'], album['release_date'], album['album_type'], album['uri'], artist['id'], artist['uri'], artist['name'], artist['href'])
        session.execute(insert_into)


results = spotify.new_releases()
albums = results['albums']['items']
while results['albums']['next']:
    results = spotify.next(results['albums'])
    albums.extend(results['albums']['items'])

for album in albums:
    if album['release_date_precision'] != 'day':
        continue
    for artist in album['artists']:
        insert_into = '''
        INSERT INTO music.albums (id, href, image_url, name, release_date, album_type, uri, artist_id, artist_uri, artist_name, artist_href) VALUES ('{}', '{}', '{}', $${}$$, '{}', '{}', '{}', '{}', '{}', '{}', '{}');
        '''.format(album['id'], album['href'], album['images'][0]['url'], album['name'], album['release_date'], album['album_type'], album['uri'], artist['id'], artist['uri'], artist['name'], artist['href'])
        session.execute(insert_into)


select_all = '''
SELECT id, name, release_date, album_type, artist_id, artist_name, image_url FROM music.albums WHERE release_date >= '2022-10-01' AND artist_id IN ('6FBDaR13swtiWwGhX1WQsP','2avRYQUWQpIkzJOEkf0MdY','5f7VJjfbwm532GiveGC0ZK');
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

print(result)
