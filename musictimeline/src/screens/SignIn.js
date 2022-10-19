import * as React from 'react';
import { Button, SafeAreaView } from 'react-native';
import AuthContext from '../context/AuthContext';

export default function SignIn() {
    const { signIn } = React.useContext(AuthContext);
  
    return (
      <SafeAreaView>
        <Button title="Sign in" onPress={() => signIn()} />
      </SafeAreaView>
    );
}
