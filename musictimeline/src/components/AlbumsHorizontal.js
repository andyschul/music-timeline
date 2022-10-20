import * as React from 'react';
import PropTypes from 'prop-types';
import {
  FlatList,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { colors, gStyle, images } from '../constants';

const albumList = (data, tagline) => {
  const navigation = useNavigation();
  return (
    <>
    <Text style={styles.tagline}>{tagline}</Text>
    <FlatList
      contentContainerStyle={styles.containerContent}
      data={data}
      horizontal
      keyExtractor={({ id }) => id.toString()}
      renderItem={({ item }) => (
        <TouchableOpacity
          activeOpacity={gStyle.activeOpacity}
          hitSlop={{ top: 10, left: 10, bottom: 10, right: 10 }}
          onPress={() => navigation.navigate('Album', { title: item.title })}
          style={styles.item}
        >
          <View style={styles.image}>
            {item.image_url && (
              <Image source={{uri:item.image_url}} style={styles.image} />
            )}
          </View>
          <Text style={styles.artist}>{item.artist_name}</Text>
          <Text style={styles.title}>{item.name}</Text>
        </TouchableOpacity>
      )}
      showsHorizontalScrollIndicator={false}
    />
  </>
  )
}

const AlbumsHorizontal = ({ data, heading, tagline }) => {
  const navigation = useNavigation();
  return (
    <View style={styles.container}>
      {heading && <Text style={styles.heading}>{heading}</Text>}

      {data.singles.length > 0 && albumList(data.singles, "Singles")}
      {data.albums.length > 0 && albumList(data.albums, "Albums")}
    </View>
  );
};

AlbumsHorizontal.defaultProps = {
  heading: null,
  tagline: null
};

AlbumsHorizontal.propTypes = {
  // required
  data: PropTypes.array.isRequired,

  // optional
  heading: PropTypes.string,
  tagline: PropTypes.string
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 32,
    width: '100%'
  },
  containerContent: {
    paddingLeft: 16
  },
  heading: {
    ...gStyle.textSpotifyBold18,
    color: colors.white,
    paddingBottom: 6,
    textAlign: 'center'
  },
  tagline: {
    ...gStyle.textSpotify12,
    color: colors.greyInactive,
    paddingBottom: 6,
    textAlign: 'center'
  },
  item: {
    marginRight: 16,
    width: 148
  },
  image: {
    backgroundColor: colors.greyLight,
    height: 148,
    width: 148
  },
  artist: {
    ...gStyle.textSpotifyBold12,
    color: colors.white,
    marginTop: 4,
    textAlign: 'center'
  },
  title: {
    ...gStyle.textSpotify12,
    color: colors.white,
    marginTop: 4,
    textAlign: 'center'
  }
});

export default AlbumsHorizontal;
