import * as React from 'react';
import * as SplashScreen from 'expo-splash-screen';
import { func } from './src/constants';
import * as SecureStore from 'expo-secure-store';
import { StatusBar } from 'react-native';
import authHandler from "./src/utils/authenticationHandler";
import AuthContext from './src/context/AuthContext';
import authReducer from './src/reducers/authReducer'
import SignInScreen from './src/screens/SignIn'
import RootStack from './src/navigation/RootStack';

export default function App({ navigation }) {
  const [state, dispatch] = React.useReducer(authReducer,
    {
      isLoading: true,
      isSignout: false,
      userToken: null,
    }
  );

  React.useEffect(() => {
    // Fetch the token from storage then navigate to our appropriate place
    const bootstrapAsync = async () => {
      let userToken;

      try {
        // Restore token stored in `SecureStore` or any other encrypted storage
        await SplashScreen.preventAutoHideAsync();
        userToken = await SecureStore.getItemAsync('accessToken');
        await func.loadAssetsAsync();
      } catch (e) {
        // Restoring token failed
      }

      // After restoring token, we may need to validate it in production apps

      // This will switch to the App screen or Auth screen and this loading
      // screen will be unmounted and thrown away.
      dispatch({ type: 'RESTORE_TOKEN', token: userToken });
    };

    bootstrapAsync();
  }, []);

  React.useEffect(() => {
    // when loading is complete
    if (state.isLoading === false) {
      // hide splash function
      const hideSplash = async () => SplashScreen.hideAsync();

      // hide splash screen to show app
      hideSplash();
    }
  }, [state.isLoading]);

  const authContext = React.useMemo(
    () => ({
      signIn: async (data) => {
        let token = await authHandler.onLogin();
        await SecureStore.setItemAsync('accessToken', token);
        dispatch({ type: 'SIGN_IN', token: token });
      },
      signOut: async () => {
        await SecureStore.deleteItemAsync('accessToken');
        dispatch({ type: 'SIGN_OUT' })
      },
    }),
    []
  );

  if (state.isLoading) {
    return null;
  }

  return (
    <AuthContext.Provider value={authContext}>
      <StatusBar barStyle="light-content" />
      {state.userToken == null ? (
        <SignInScreen/>
      ) : (
        <RootStack />
      )}
    </AuthContext.Provider>
  );
}
