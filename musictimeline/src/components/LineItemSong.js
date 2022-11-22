import * as React from 'react';
import PropTypes from 'prop-types';
import * as SecureStore from 'expo-secure-store';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { colors, gStyle } from '../constants';

const LineItemSong = ({ active, downloaded, onPress, songData }) => {
  const activeColor = active ? colors.brandPrimary : colors.white;
  const [isLoading, setLoading] = React.useState(true);
  const [track, setTrack] = React.useState({});

  const getPopularityColor = (popularity) => {
    let ceilPopularity = Math.ceil(popularity/10)? Math.ceil(popularity/10) : 1
    let color = [`#9e0142`, `#d53e4f`, `#f46d43`, `#fdae61`, `#fee08b`, `#e6f598`, `#abdda4`, `#66c2a5`, `#3288bd`, `#5e4fa2`]
    return color[ceilPopularity-1]
  }

  const getTrack = async () => {
    try {
      let token = await SecureStore.getItemAsync('accessToken');
      const response = await fetch(`https://api.spotify.com/v1/tracks/${songData.track_id}`, {
      headers: {"Authorization" : `Bearer ${token}`}
     });
     const json = await response.json();

    //  set track 
    setTrack(json);
   } catch (error) {
     console.error(error);
   } finally {
     setLoading(false);
   }
 }

  let dur = String(new Date(songData['duration']).toISOString()).substring(14,19);
  dur = String(parseInt(dur.substring(0,2))).concat(dur.substring(2,5))

  React.useEffect(() => {
    getTrack();
  }, []);
  return (
    <TouchableOpacity
      activeOpacity={gStyle.activeOpacity}
      onPress={() => onPress(songData)}
      style={styles.container}
    >
        <View style={styles.containerLeft}>
          <Text numberOfLines={1} style={[styles.title, { color: activeColor }]}>
            {songData.title}
          </Text>
          <Text style={styles.artist}>
            {songData.artists.map(a => a['name']).join(', ')}
          </Text>
        </View>
        <View style={styles.containerRight}>
          <Text style={styles.dur}>{dur}</Text>
          <View style={styles.popularityContainer}>
            <View style={[styles.popularityView, { backgroundColor: getPopularityColor(track.popularity) }]}>
              <Text style={styles.popularityText}>
                {Math.ceil(track.popularity/10)? Math.ceil(track.popularity/10) : 1}
              </Text>
            </View>
          </View>   
        </View>
    </TouchableOpacity>
  );
};

LineItemSong.defaultProps = {
  active: false,
  downloaded: false
};

LineItemSong.propTypes = {
  // required
  onPress: PropTypes.func.isRequired,
  songData: PropTypes.shape({
    album: PropTypes.string.isRequired,
    artists: PropTypes.array.isRequired,
    images: PropTypes.array.isRequired,
    length: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired
  }).isRequired,

  // optional
  active: PropTypes.bool,
  downloaded: PropTypes.bool
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 5,
    height:70,
    width: '100%'
  },
  title: {
    ...gStyle.textSpotify16,
    marginBottom: 4,
  },
  circleDownloaded: {
    alignItems: 'center',
    backgroundColor: colors.brandPrimary,
    borderRadius: 7,
    height: 14,
    justifyContent: 'center',
    marginRight: 8,
    width: 14
  },
  artist: {
    ...gStyle.textSpotify12,
    color: colors.greyInactive
  },
  containerRight: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    width:'15%'
  },
  containerLeft:{
    alignItems: 'flex-start',
    flexDirection: 'column',
    justifyContent: 'center',
    padding:7,
    minHeight:69,
    width:'85%'
  },
  popularityContainer: {
    justifyContent: 'center',
    height:69
  },
  popularityText: {
    ...gStyle.textSpotify10,
    color: colors.black
  },
  popularityView: {
    alignItems: 'center',
    justifyContent: 'center', 
    padding:1.5, 
    marginBottom:3,
    marginRight:4,
    width:15,
    height:15,
    borderRadius: 10,
    opacity: 0.8
  },
  track:{
  },
  dur: {
    ...gStyle.textSpotify12,
    color: colors.greyInactive,
    padding:12
  }
});

export default LineItemSong;
