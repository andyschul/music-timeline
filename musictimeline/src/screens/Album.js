import * as React from 'react';
import PropTypes from 'prop-types';
import {
  Alert,
  Animated,
  Image,
  StyleSheet,
  Switch,
  Text,
  View,
  ActivityIndicator
} from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { BlurView } from 'expo-blur';
import { colors, device, gStyle, images } from '../constants';

// components
import LinearGradient from '../components/LinearGradient';
import LineItemSong from '../components/LineItemSong';
import TouchIcon from '../components/TouchIcon';
import TouchText from '../components/TouchText';

// mock data
import albums from '../mockdata/albums';
import yourLibrary from '../mockdata/menuYourLibrary.json';

import {
  Feather,
  Entypo,
  MaterialIcons,
  MaterialCommunityIcons,
  FontAwesome
} from '@expo/vector-icons';

// context
import Context from '../context';

import { getUniqueId, getManufacturer } from 'react-native-device-info';

const Album = ({ navigation, route }) => {
  const [isLoading, setLoading] = React.useState(true);
  const [album, setAlbum] = React.useState({});
  const { id } = route.params;

  // get main app state
  const { currentSongData, showMusicBar, updateState } = React.useContext(Context);

  // local state
  // const [downloaded, setDownloaded] = React.useState(false);
  const [song, setSong] = React.useState(currentSongData.title);
  const scrollY = React.useRef(new Animated.Value(0)).current;

  // ui state
  // const album = albums[title] || null;

  const getAlbum = async () => {
    try {
      let token = await SecureStore.getItemAsync('accessToken');
      const response = await fetch(`https://api.spotify.com/v1/albums/${id}`, {
      headers: {"Authorization" : `Bearer ${token}`}
     });
     const json = await response.json();

    //  set album duration
     let albumDuration = json.tracks.items.reduce((accumulator, object) => {
        return accumulator + object.duration_ms;
     }, 0);
     albumDuration = new Date(albumDuration).toISOString().substring(11, 16);
     albumDuration = albumDuration.split(":")

     if (parseInt(albumDuration[0]) === 0) {
      albumDuration = String(parseInt(albumDuration[1])).concat("m ")
     } else {
      albumDuration = String(parseInt(albumDuration[0])).concat("h ").concat(String(parseInt(albumDuration[1])).concat("m "))
     }
     json['duration'] = albumDuration;

     //  set album artists
     let albumArtists = json.artists.map((artist) => (artist.name)).join(', ');
     json['albumArtists'] = albumArtists;

     setAlbum(json);
   } catch (error) {
     console.error(error);
   } finally {
     setLoading(false);
   }
 }

  React.useEffect(() => {
    getAlbum();
  }, []);

  const onToggleDownloaded = (val) => {
    // if web
    if (device.web) {
      setDownloaded(val);

      return;
    }

    // remove downloads alert
    if (val === false) {
      Alert.alert(
        'Remove from Downloads?',
        "You won't be able to play this offline.",
        [
          { text: 'Cancel' },
          {
            onPress: () => {
              setDownloaded(false);
            },
            text: 'Remove'
          }
        ],
        { cancelable: false }
      );
    } else {
      setDownloaded(val);
    }
  };

  playSongSpotify = async (songData) => {
    let token = SecureStore.getItemAsync('accessToken');
      let deviceId = await getUniqueId();
      const response = await fetch(`https://api.spotify.com/v1/me/player/play`, {
      headers: {"Authorization" : `Bearer ${token}`, "Content-Type": "application/json"},
      method: 'post',
      query: {
        "device_id": deviceId
      },
      body: {
          "context_uri": songData.uri,
          "offset": {
            "position": songData.position
          },
          "position_ms": 0
        }
      });
  }

  const onChangeSong = async (songData) => {
    // update local state
    setSong(songData.title);

    // update main state
    updateState('currentSongData', songData);

    await playSongSpotify({
      uri: songData.album_uri,
      position: songData.position
    });
  };

  // album data not set?
  if (album === null) {
    return (
      <View style={[gStyle.container, gStyle.flexCenter]}>
        <Text style={{ color: colors.white }}>{`Album: ${id}`}</Text>
      </View>
    );
  }

  const stickyArray = device.web ? [] : [0];
  const headingRange = device.web ? [140, 200] : [230, 280];
  const shuffleRange = device.web ? [40, 80] : [40, 80];

  const opacityHeading = scrollY.interpolate({
    inputRange: headingRange,
    outputRange: [0, 1],
    extrapolate: 'clamp'
  });

  const opacityShuffle = scrollY.interpolate({
    inputRange: shuffleRange,
    outputRange: [0, 1],
    extrapolate: 'clamp'
  });

  return (
    <React.Fragment>
    {isLoading ? <ActivityIndicator/> : (
      <View style={gStyle.container}>
      {showMusicBar === false && (
        <BlurView intensity={99} style={styles.blurview} tint="dark" />
      )}

      <View style={styles.containerHeader}>
        <Animated.View
          style={[styles.headerLinear, { opacity: opacityHeading }]}
        >
          <LinearGradient fill={album.backgroundColor} height={89} />
        </Animated.View>
        <View style={styles.header}>
          <TouchIcon
            icon={<Feather color={colors.white} name="chevron-left" />}
            onPress={() => navigation.goBack(null)}
          />
          <Text style={styles.albumInfo}>
            {`${album.release_date}`}
          </Text>
          <Animated.View style={{ opacity: opacityShuffle }}>
            <Text style={styles.headerTitle}>{album.name}</Text>
          </Animated.View>
          <TouchIcon
            icon={<Feather color={colors.white} name="more-horizontal" />}
            onPress={() => {
              // update main state
              updateState('showMusicBar', !showMusicBar);

              navigation.navigate('ModalMoreOptions', {
                album
              });
            }}
          />
        </View>
      </View>

      <View style={styles.containerFixed}>
        <View style={styles.containerLinear}>
          <LinearGradient fill={album.backgroundColor} />
        </View>
        <View style={styles.containerImage}>
          <Image source={{uri:album.images[0].url}} style={styles.image} />
        </View>
        <View style={styles.containerTitle}>
          <Text ellipsizeMode="tail" numberOfLines={1} style={styles.title}>
            {album.name}
          </Text>
        </View>
        <View style={styles.containerAlbum}>
          <View style={styles.spaceArtistProducer}>
            <View style={styles.entity}>
              <Feather color={colors.greyInactive} name={"user"} size={17} /> 
              <Text style={styles.albumInfo}>
                {`${album.albumArtists}`}
              </Text>
            </View>
            <View style={styles.entity}>
              <Image
                style={{
                  width: 15,
                  height: 15,
                  borderRadius: 0,
                }}
                source={require('../assets/producer_icon.png')} 
              />
              <Text style={styles.albumInfo}>
                MIN
              </Text>
            </View>
          </View>
        </View>
      </View>

      <Animated.ScrollView
        onScroll={Animated.event(
          [{ nativeEvent: { contentOffset: { y: scrollY } } }],
          { useNativeDriver: true }
        )}
        scrollEventThrottle={16}
        showsVerticalScrollIndicator={false}
        stickyHeaderIndices={stickyArray}
        style={styles.containerScroll}
      >
        <View style={styles.containerSticky}>
          <Animated.View
            style={[styles.containerStickyLinear, { opacity: opacityShuffle }]}
          >
            <LinearGradient fill={colors.black20} height={50} />
          </Animated.View>
          <View style={styles.containerShuffle}>
            <TouchText
              onPress={() => null}
              style={styles.btn}
              styleText={styles.btnText}
              text="Play"
            />
            <Text style={styles.albumInfo}>
              {`${album.duration}`}
            </Text>
          </View>
        </View>
        <View style={styles.containerSongs}>
          {/* <View style={styles.row}>
            <Text style={styles.downloadText}>
              {downloaded ? 'Downloaded' : 'Download'}
            </Text>
            <Switch
              trackColor={colors.greySwitchBorder}
              onValueChange={(val) => onToggleDownloaded(val)}
              value={downloaded}
            />
          </View> */}

          {album.tracks &&
            album.tracks.items.map((track) => (
              <LineItemSong
                active={song === track.name}
                // downloaded={downloaded}
                key={track.name}
                onPress={onChangeSong}
                songData={{
                  album: album.name,
                  artist: track.artists.map((artist) => (artist.name)).join(', '),
                  image: album.images[0].url,
                  duration: track.duration_ms,
                  title: track.name,
                  album_uri: album.uri,
                  position: track.track_number
                }}
              />
            ))}
        </View>
        <View style={gStyle.spacer16} />
      </Animated.ScrollView>
    </View>
    )}
  </React.Fragment>
  );
};

Album.propTypes = {
  // required
  navigation: PropTypes.object.isRequired,
  route: PropTypes.object.isRequired
};

const styles = StyleSheet.create({
  blurview: {
    ...StyleSheet.absoluteFill,
    zIndex: 101
  },
  containerHeader: {
    height: 89,
    position: 'absolute',
    top: 0,
    width: '100%',
    zIndex: 100
  },
  headerLinear: {
    height: 89,
    width: '100%'
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingTop: device.iPhoneNotch ? 48 : 24,
    position: 'absolute',
    top: 0,
    width: '100%'
  },
  headerTitle: {
    ...gStyle.textSpotifyBold16,
    color: colors.white,
    marginTop: 2,
    paddingHorizontal: 8,
    textAlign: 'center',
    width: device.width - 100
  },
  containerFixed: {
    alignItems: 'center',
    paddingTop: device.iPhoneNotch ? 94 : 60,
    position: 'absolute',
    width: '100%'
  },
  containerLinear: {
    position: 'absolute',
    top: 0,
    width: '100%',
    height:'100%',
    zIndex: device.web ? 5 : 0
  },
  containerImage: {
    shadowColor: colors.black,
    shadowOffset: { height: 8, width: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
    zIndex: device.web ? 20 : 0
  },
  image: {
    height: 150,
    marginBottom: device.web ? 0 : 16,
    width: 150
  },
  containerTitle: {
    marginTop: device.web ? 8 : 0,
    zIndex: device.web ? 20 : 0
  },
  title: {
    ...gStyle.textSpotifyBold20,
    color: colors.white,
    marginBottom: 8,
    paddingHorizontal: 24,
    textAlign: 'center'
  },
  containerAlbum: {
    zIndex: device.web ? 20 : 0
  },
  albumInfo: {
    ...gStyle.textSpotify12,
    color: colors.greyInactive,
    marginTop: 7,
    marginBottom: 3,
    textAlign: 'center'
  },
  containerScroll: {
    paddingTop: 89
  },
  containerSticky: {
    marginTop: device.iPhoneNotch ? 320 : 194
  },
  containerShuffle: {
    alignItems: 'center',
    height: 50,
    shadowColor: colors.blackBg,
    shadowOffset: { height: -10, width: 0 },
    shadowOpacity: 0.2,
    shadowRadius: 20
  },
  containerStickyLinear: {
    position: 'absolute',
    top: 0,
    width: '100%'
  },
  btn: {
    backgroundColor: colors.brandPrimary,
    borderRadius: 25,
    height: 35,
    width: 110
  },
  btnText: {
    ...gStyle.textSpotifyBold16,
    color: colors.white,
    letterSpacing: 1,
    textTransform: 'uppercase'
  },
  containerSongs: {
    alignItems: 'center',
    backgroundColor: colors.blackBg,
    minHeight: 540
  },
  row: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 16,
    width: '100%'
  },
  entity: {
    alignItems: 'center',
    justifyContent: 'space-between',
    flexDirection: 'column',
    padding: 5
  },
  spaceArtistProducer: {
    justifyContent: 'space-between',
    flexDirection: 'column'
  },
  downloadText: {
    ...gStyle.textSpotifyBold18,
    color: colors.white
  }
});

export default Album;
