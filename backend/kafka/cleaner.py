import spotipy
import os
from operator import itemgetter

SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']

spotify = spotipy.Spotify(client_credentials_manager=spotipy.oauth2.SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

def is_explicit(album_id):
  tracks = spotify.album(album_id)['tracks']['items']
  for track in tracks:
    if track['explicit']:
      return True
  return False


def filter_same_name(albums):
  albums = sorted(albums, key=itemgetter('total_tracks'), reverse=True)
  for album in albums:
    if is_explicit(album['id']):
      return album
  return albums[0]


def album_filter(album):
  album_name_lower = album['name'].lower()
  if album['release_date_precision'] != 'day':
    return False
  if album['album_group'] == 'appears_on' and album['album_type'] == 'compilation':
    return False
  if album['album_group'] in ['appears_on', 'single'] and album['album_type'] == 'single' and 'remix' in album_name_lower:
    return False
  if 'edited version' in album_name_lower or 'clean version' in album_name_lower:
    return False
  return True


def album_cleaner(albums):
  result = []
  albums_by_name = {}
  for album in albums:
    if album_filter(album):
      album_name = album['name']
      if album_name not in albums_by_name:
        albums_by_name[album_name] = [album]
      else:
        albums_by_name[album_name].append(album)

  for _, albums in albums_by_name.items():
    if len(albums) == 1:
      result.append(albums[0])
    else:
      result.append(filter_same_name(albums))

  return result