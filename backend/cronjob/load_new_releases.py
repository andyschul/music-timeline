import spotipy
from cleaner import album_cleaner
import requests
import copy
import json
import os

SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
ASTRA_DB_ID = os.environ['ASTRA_DB_ID']
ASTRA_DB_REGION = os.environ['ASTRA_DB_REGION']
ASTRA_DB_APPLICATION_TOKEN = os.environ['ASTRA_DB_APPLICATION_TOKEN']
ASTRA_DB_KEYSPACE = 'music'
ASTRA_DB_ALBUMS_TABLE = 'albums'

spotify = spotipy.Spotify(client_credentials_manager=spotipy.oauth2.SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

url = f'https://{ASTRA_DB_ID}-{ASTRA_DB_REGION}.apps.astra.datastax.com/api/rest/v2/keyspaces/{ASTRA_DB_KEYSPACE}/{ASTRA_DB_ALBUMS_TABLE}'
headers = {
  'content-type': 'application/json',
  'x-cassandra-token': ASTRA_DB_APPLICATION_TOKEN
}


def build_album(album):
    results = []
    all_album_artists = album['artists']
    album_artist_ids = set([artist['id'] for artist in all_album_artists])
    appears_on_artist_ids = set()
    appears_on_artists = []

    for track in album['tracks']['items']:
        for artist in track['artists']:
            artist_id = artist['id']
            if artist_id not in album_artist_ids and artist_id not in appears_on_artist_ids:
                appears_on_artist_ids.add(artist_id)
                all_album_artists.append(artist)

        new_appears_on_artists = [artist for artist in track['artists'] if artist['id'] not in album_artist_ids and artist['id'] not in appears_on_artist_ids]
        for artist in new_appears_on_artists:
            appears_on_artist_ids.add(artist['id'])
            appears_on_artists.append(artist)

    for artist in all_album_artists:
        album_copy = copy.deepcopy(album)
        if artist['id'] in album_artist_ids:
            album_copy['album_group'] = album['album_type']
        else:
            album_copy['album_group'] = 'appears_on'
        album_copy['artist_id'] = artist['id'],
        album_copy['artist_uri'] = artist['uri'],
        album_copy['artist_name'] = artist['name'],
        album_copy['artist_href'] = artist['href'],
        album_copy['artist_image'] = artist['images'][0]['url'] if artist['images'] else '',
        album_copy['artist_genres'] = artist['genres']
        results.append(album_copy)

    return results

def join_album_ids(albums):
    return ''.join([album['id'] for album in albums if album['album_type'] != 'compilation'])


def handle_results(results):
    res = []
    album_ids = join_album_ids(results['albums']['items'])
    albums = spotify.albums(album_ids)
    for album in albums['albums']:
        if album['album_type'] != 'compilation':
            res.extend(build_album(album))
    return res

def get_artist_albums_from_spotify():
    albums = []
    results = spotify.new_releases(country='US', limit=20)
    albums.extend(handle_results(results))

    while results['albums']['next']:
        results = spotify.next(results['albums'])
        albums.extend(handle_results(results))

    return albums


def load_albums(albums):
    for album in albums:
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
            'artist_id': album['artist_id'],
            'artist_uri': album['artist_uri'],
            'artist_name': album['artist_name'],
            'artist_href': album['artist_href'],
            'artist_image': album['artist_image'],
            'artist_genres': album['artist_genres']
        }
        requests.post(url, data=json.dumps(data), headers=headers)


def main():
    print('starting...')
    albums = get_artist_albums_from_spotify()
    albums = album_cleaner(albums)
    load_albums(albums)
    print(f'Loaded {len(albums)} albums')

if __name__=='__main__':
    main()