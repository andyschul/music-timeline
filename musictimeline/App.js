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
import AppState from './src/context/AppState';

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
      let expDate;
      let refreshToken;
      try {
        // Restore token stored in `SecureStore` or any other encrypted storage
        await SplashScreen.preventAutoHideAsync();
        try {
          userToken = await SecureStore.getItemAsync('accessToken');
          expDate = await SecureStore.getItemAsync('accessTokenExpirationDate');
          refreshToken = await SecureStore.getItemAsync('refreshToken');
        } catch (e) {
          alert(e)
        }

        await func.loadAssetsAsync();
      } catch (e) {
        // Restoring token failed
        console.log('Restoring token failed');
      }

      // After restoring token, we may need to validate it in production apps
      if (expDate && expDate < new Date().toISOString()) {
        let result = await authHandler.refreshLogin(refreshToken);
        await SecureStore.setItemAsync('accessToken', result.accessToken);
        await SecureStore.setItemAsync('refreshToken', result.refreshToken);
      }

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
        let result = await authHandler.onLogin();
        await SecureStore.setItemAsync('accessToken', result.accessToken);
        await SecureStore.setItemAsync('accessTokenExpirationDate', result.accessTokenExpirationDate);
        await SecureStore.setItemAsync('refreshToken', result.refreshToken);
        dispatch({ type: 'SIGN_IN', token: result.accessToken });
      },
      refreshToken: async (data) => {
        let refreshToken = await SecureStore.getItemAsync('refreshToken');
        let result = await authHandler.refreshLogin(refreshToken);
        await SecureStore.setItemAsync('accessToken', result.accessToken);
        await SecureStore.setItemAsync('accessTokenExpirationDate', result.accessTokenExpirationDate);
        await SecureStore.setItemAsync('refreshToken', result.refreshToken);
        dispatch({ type: 'RESTORE_TOKEN', token: result.accessToken });
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
        <AppState>
          <RootStack />
        </AppState>
      )}
    </AuthContext.Provider>
  );
}
