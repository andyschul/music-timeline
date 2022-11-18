import {authorize, refresh} from 'react-native-app-auth';
import Config from "react-native-config";

class AuthenticationHandler {
  constructor() {
    this.spotifyAuthConfig = {
      clientId: Config.CLIENT_ID,
      clientSecret: Config.CLIENT_SECRET,
      redirectUrl: Config.REDIRECT_URI,
      scopes: [
        'playlist-read-private',
        'playlist-read-collaborative',
        'playlist-modify-public',
        'playlist-modify-private',
        'user-read-playback-state',
        'user-read-currently-playing',
        'user-read-playback-position',
        'user-read-recently-played',
        'app-remote-control',
        'user-modify-playback-state',
        'user-library-read',
        'user-library-modify',
        'user-top-read',
        'user-follow-read',
        'user-follow-modify',
        'streaming',
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
      return result;
    } catch (error) {
      console.log(JSON.stringify(error));
    }
  }

  async refreshLogin(refreshToken) {
    try {
      const result = await refresh(this.spotifyAuthConfig, {
        refreshToken: refreshToken,
      });
      return result;
    } catch (error) {
      console.log(JSON.stringify(error));
    }
  }

}

const authHandler = new AuthenticationHandler();

export default authHandler;