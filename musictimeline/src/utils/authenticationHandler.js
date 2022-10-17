import {authorize, refresh} from 'react-native-app-auth';
import Config from "react-native-config";
import * as SecureStore from 'expo-secure-store';

class AuthenticationHandler {
  constructor() {
    this.spotifyAuthConfig = {
      clientId: Config.CLIENT_ID,
      clientSecret: Config.CLIENT_SECRET,
      redirectUrl: Config.REDIRECT_URI,
      scopes: [
        'playlist-read-private',
        'playlist-modify-public',
        'playlist-modify-private',
        'user-library-read',
        'user-library-modify',
        'user-top-read',
        'user-follow-read',
        'user-follow-modify',
      ],
      serviceConfiguration: {
        authorizationEndpoint: Config.AUTH_ENDPOINT,
        tokenEndpoint: Config.TOKEN_ENDPOINT,
      },
    };
  }

  async onLogin() {
    try {
      const result = await authorize(this.spotifyAuthConfig);
      await SecureStore.setItemAsync('accessToken', result.accessToken);
      return result;
    } catch (error) {
      console.log(JSON.stringify(error));
    } 
  }

  async refreshLogin(refreshToken) {
    const result = await refresh(this.spotifyAuthConfig, {
      refreshToken: refreshToken,
    });
    return result;
  }

}

const authHandler = new AuthenticationHandler();

export default authHandler;