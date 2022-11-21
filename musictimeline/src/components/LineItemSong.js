import * as React from 'react';
import PropTypes from 'prop-types';
import * as SecureStore from 'expo-secure-store';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import { colors, gStyle } from '../constants';

const LineItemSong = ({ active, downloaded, onPress, songData }) => {
  const activeColor = active ? colors.brandPrimary : colors.white;
  const [isLoading, setLoading] = React.useState(true);
  const [popularity, setPopularity] = React.useState({});

  const getPopularity = async () => {
    try {
      let token = await SecureStore.getItemAsync('accessToken');
      const response = await fetch(`https://api.spotify.com/v1/tracks/${songData.track_id}`, {
      headers: {"Authorization" : `Bearer ${token}`}
     });
     const json = await response.json();

    //  set track popularity
    setPopularity(json);
   } catch (error) {
     console.error(error);
   } finally {
     setLoading(false);
   }
 }

  let dur = String(new Date(songData['duration']).toISOString()).substring(14,19);
  dur = String(parseInt(dur.substring(0,2))).concat(dur.substring(2,5))

  React.useEffect(() => {
    getPopularity();
  }, []);
  return (
    <View style={styles.container}>
      <TouchableOpacity
        activeOpacity={gStyle.activeOpacity}
        onPress={() => onPress(songData)}
        style={styles.track}
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
            <View style={[styles.popularityBar, { color: activeColor }]}></View>   
          </View>
      </TouchableOpacity>
    </View>
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
    alignItems: 'flex-end',
    flex: 1
  },
  containerRight: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    height:69
  },
  containerLeft:{
    alignItems: 'flex-start',
    flexDirection: 'column',
    justifyContent: 'center',
    padding:7,
    minHeight:69,
    width:'85%'
  },
  popularityBar: {
    height: '100%',
    width:3,
    backgroundColor: colors.brandPrimary,
  },
  track:{
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%'
  },
  dur: {
    ...gStyle.textSpotify12,
    color: colors.greyInactive,
    padding:12
  }
});

export default LineItemSong;
