import * as React from 'react';
import { Animated, StyleSheet, View, ActivityIndicator } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { FontAwesome } from '@expo/vector-icons';
import { colors, device, gStyle } from '../constants';

// components
import AlbumsHorizontal from '../components/AlbumsHorizontal';

// mock data
// import heavyRotation from '../mockdata/heavyRotation.json';
// import jumpBackIn from '../mockdata/jumpBackIn.json';
// import recentlyPlayed from '../mockdata/recentlyPlayed.json';
// import mockData from '../mockdata/apiCall.json';

import AuthContext from '../context/AuthContext';

const DAYS_PER_REQUEST = 90;

const decreaseDate = (d) => {
  d.setDate(d.getDate()-DAYS_PER_REQUEST);
  return d;
}

const Home = () => {
  const [isLoading, setLoading] = React.useState(true);
  const [data, setData] = React.useState([]);
  const [fromDate, setFromDate] = React.useState(() => decreaseDate(new Date()));
  const [toDate, setToDate] = React.useState(() => new Date());
  const { signOut, refreshToken } = React.useContext(AuthContext);
  const scrollY = React.useRef(new Animated.Value(0)).current;

  const renderItem = ({item, index}) => (
    <AlbumsHorizontal key={item['release_date']} data={item} heading={item['release_date']} idx={index} />
  );

  const opacityIn = scrollY.interpolate({
    inputRange: [0, 128],
    outputRange: [0, 1],
    extrapolate: 'clamp'
  });

  const opacityOut = scrollY.interpolate({
    inputRange: [0, 88],
    outputRange: [1, 0],
    extrapolate: 'clamp'
  });

  const getAlbums = async () => {
    try {
      let expDate = await SecureStore.getItemAsync('accessTokenExpirationDate');
      if (expDate < new Date().toISOString()) {
        await refreshToken();
      }

      let token = await SecureStore.getItemAsync('accessToken');
      let params = new URLSearchParams({
        from_date: fromDate.toISOString().substring(0, 10),
        to_date: toDate.toISOString().substring(0, 10),
      })
      const response = await fetch(`https://musictimeline.azurewebsites.net/timeline?${params}`, {
      headers: {"Authorization" : `Bearer ${token}`}
     });
     const json = await response.json();
     setData([...data, ...json]);
     setFromDate(decreaseDate(fromDate));
     setToDate(decreaseDate(toDate));
   } catch (error) {
     console.error(error);
   } finally {
     setLoading(false);
   }
 }

 React.useEffect(() => {
   getAlbums();
 }, []);

  return (
    <React.Fragment>
      {device.iPhoneNotch && (
        <Animated.View style={[styles.iPhoneNotch, { opacity: opacityIn }]} />
      )}

      <Animated.View style={[styles.containerHeader, { opacity: opacityOut }]}>
        <FontAwesome color={colors.white} name="cog" size={28} onPress={signOut}/>
      </Animated.View>

      {isLoading ? <ActivityIndicator/> : (
        <Animated.FlatList
          onScroll={Animated.event(
            [{ nativeEvent: { contentOffset: { y: scrollY } } }],
            { useNativeDriver: true }
          )}
          data={data}
          renderItem={renderItem}
          keyExtractor={item => item.release_date}
          scrollEventThrottle={16}
          style={gStyle.container}
          onEndReached={getAlbums}
        />
      )}

    </React.Fragment>
  );
};

const styles = StyleSheet.create({
  iPhoneNotch: {
    backgroundColor: colors.black70,
    height: 44,
    position: 'absolute',
    top: 0,
    width: '100%',
    zIndex: 20
  },
  containerHeader: {
    alignItems: 'flex-end',
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingHorizontal: 16,
    paddingTop: device.iPhoneNotch ? 60 : 36,
    position: 'absolute',
    top: 0,
    width: '100%',
    zIndex: 10
  }
});

export default Home;
