from confluent_kafka import Consumer
from cassandra.cluster import Cluster
import json
import ccloud_lib
from pathlib import Path
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
cluster = Cluster()
session = cluster.connect()

def check_followed_artist(followed_artists):
    for artist_id in followed_artists:
        select_all = '''
        SELECT artist_id FROM music.albums WHERE artist_id = '%s' LIMIT 1;
        ''' % artist_id
        rows = session.execute(select_all)
        if not rows.current_rows:
            get_artist_from_spotify(artist_id)

def get_artist_from_spotify(artist_id):
    print('getting new artist from spotify '+artist_id)
    results = spotify.artist_albums(artist_id)
    albums = results['items']
    print('start getting results')
    while results['next']:
        results = spotify.next(results)
        albums.extend(results['items'])
    print('end getting results')
    print(albums)
    for album in albums:
        print('inserting album '+album['name'])
        if album['release_date_precision'] != 'day':
            continue
        for artist in album['artists']:
            insert_into = '''
            INSERT INTO music.albums (id, href, image_url, name, release_date, album_type, uri, artist_id, artist_uri, artist_name, artist_href) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');
            '''.format(album['id'], album['href'], album['images'][0]['url'], album['name'].replace("'", "''"), album['release_date'], album['album_type'], album['uri'], artist['id'], artist['uri'], artist['name'].replace("'", "''"), artist['href'])
            session.execute(insert_into)

if __name__ == '__main__':

    # Read arguments and configurations and initialize
    topic = 'test1'
    conf = ccloud_lib.read_ccloud_config(Path(__file__).parent / './.kafka.config')

    # Create Consumer instance
    # 'auto.offset.reset=earliest' to start reading from the beginning of the
    #   topic if no committed offsets exist
    consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
    consumer_conf['group.id'] = 'python_example_group_1'
    consumer_conf['auto.offset.reset'] = 'earliest'
    consumer = Consumer(consumer_conf)

    # Subscribe to topic
    consumer.subscribe([topic])

    # Process messages
    total_count = 0
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                # No message available within timeout.
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                print("Waiting for message or event/error in poll()")
                continue
            elif msg.error():
                print('error: {}'.format(msg.error()))
            else:
                # Check for Kafka message
                record_key = msg.key()
                record_value = msg.value()
                data = json.loads(record_value)
                check_followed_artist(data['artist_ids'])
                
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        consumer.close()
