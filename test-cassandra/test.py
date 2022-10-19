from cassandra.cluster import Cluster
import uuid
from collections import OrderedDict

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

# session.execute('USE music')

drop_table = '''
DROP TABLE IF EXISTS music.albums
'''
session.execute(drop_table)

create_table = '''
CREATE TABLE IF NOT EXISTS music.albums (
   id text, 
   href text,
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


birdy_uri = '2WX2uTcsvV5OnS0inACecP'
results = spotify.artist_albums(birdy_uri, album_type='album')
albums = results['items']
while results['next']:
    results = spotify.next(results)
    albums.extend(results['items'])

for album in albums:
    for artist in album['artists']:
        insert_into = '''
        INSERT INTO music.albums (id, href, name, release_date, album_type, uri, artist_id, artist_uri, artist_name, artist_href) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');
        '''.format(album['id'], album['href'], album['name'], album['release_date'], album['album_type'], album['uri'], artist['id'], artist['uri'], artist['name'], artist['href'])
        session.execute(insert_into)


select_all = '''
SELECT release_date, name, artist_name, name FROM music.albums WHERE release_date >= '2008-02-01' AND release_date < '2015-02-01' AND artist_id IN ('2WX2uTcsvV5OnS0inACecP');
'''
rows = session.execute(select_all)

for row in rows:
    print(row)