import pandas as pd
from ast import literal_eval

def explicit(spotify, album_id):
  tracks = spotify.album(album_id)['tracks']['items']
  for track in tracks:
    if track['explicit']:
      return True
  return False

def data_cleaner(spotify, albums):
    # Clean unwanted album data
    albums = pd.DataFrame(albums)
    albums = albums[~((albums['album_group']=='appears_on') & (albums['album_type']=='compilation'))]
    albums = albums[~((albums['album_group']=='appears_on') & (albums['album_type']=='single') & (albums['name'].str.lower().str.contains('remix')))]
    albums = albums[~((albums['album_group']=='single') & (albums['album_type']=='single') & (albums['name'].str.lower().str.contains('remix')))]
    albums = albums[~albums['name'].str.lower().str.contains('edited version')]
    albums = albums[~albums['name'].str.lower().str.contains('clean version')]
    albums = albums[albums['release_date'].str.contains(pat='^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$')]

    # Remove album duplicates
    #   - Keep explicit version if exists
    dups = albums[albums.duplicated(['name'], keep=False)]
    albums = albums[~albums.duplicated(['name'], keep=False)]
    non_dups = pd.DataFrame(columns=albums.columns)

    dups.sort_values(['name', 'total_tracks'], ascending=False, inplace=True)
    for name in dups['name'].unique():
        temp = dups[dups['name']==name]
        for index, row in temp.iterrows():
            is_explicit = explicit(spotify, row['id'])
            # Return album if explicit
            if is_explicit:
                non_dups = pd.concat([non_dups, pd.DataFrame([row])], ignore_index=True).info()
                break
            if (index==(temp.shape[0]-1)):
                non_dups = pd.concat([non_dups, pd.DataFrame([row])], ignore_index=True).info()

    # Add data to Cassandra
    albums = pd.concat([albums, non_dups], ignore_index=True, sort=False)
    return literal_eval(albums.to_json(orient='records'))