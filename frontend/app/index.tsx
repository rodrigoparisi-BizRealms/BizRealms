import { View, StyleSheet, ActivityIndicator, Image } from 'react-native';
import { useEffect } from 'react';
import { useRouter } from 'expo-router';
import { useAuth } from '../context/AuthContext';

export default function Index() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (user) {
        if (user.onboarding_completed) {
          router.replace('/(tabs)/home');
        } else {
          router.replace('/(onboarding)/avatar');
        }
      } else {
        router.replace('/(auth)/login');
      }
    }
  }, [user, loading]);

  return (
    <View style={styles.container}>
      <Image source={require('../assets/images/bizrealms-logo.png')} style={styles.logo} resizeMode="contain" />
      <ActivityIndicator size="large" color="#4CAF50" style={{ marginTop: 24 }} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    width: 180,
    height: 180,
  },
});
