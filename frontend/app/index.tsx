import { View, StyleSheet, ActivityIndicator, Image, Dimensions, Text } from 'react-native';
import { useEffect, useRef } from 'react';
import { useRouter } from 'expo-router';
import { useAuth } from '../context/AuthContext';
import { Animated } from 'react-native';

const { width, height } = Dimensions.get('window');

export default function Index() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Fade in animation
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 800,
      useNativeDriver: true,
    }).start();

    // Pulse animation for loading indicator
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.1, duration: 1000, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1000, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  useEffect(() => {
    if (!loading) {
      // Small delay to show the splash
      const timer = setTimeout(() => {
        if (user) {
          if (user.onboarding_completed) {
            router.replace('/(tabs)/home');
          } else {
            router.replace('/(onboarding)/avatar');
          }
        } else {
          router.replace('/(auth)/login');
        }
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [user, loading]);

  return (
    <View style={styles.container}>
      {/* Full-screen banner image */}
      <Image
        source={require('../assets/images/splash-banner.png')}
        style={styles.bannerImage}
        resizeMode="cover"
      />

      {/* Gradient overlay at bottom for loading text */}
      <Animated.View style={[styles.overlay, { opacity: fadeAnim }]}>
        <View style={styles.bottomSection}>
          <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
            <ActivityIndicator size="large" color="#FFD700" />
          </Animated.View>
          <Text style={styles.loadingText}>Carregando seu império...</Text>
          <Text style={styles.versionText}>v1.0.0</Text>
        </View>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a3d7a',
  },
  bannerImage: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: width,
    height: height,
  },
  overlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  bottomSection: {
    alignItems: 'center',
    paddingBottom: 60,
    paddingTop: 30,
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  loadingText: {
    color: '#FFD700',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 12,
    letterSpacing: 0.5,
  },
  versionText: {
    color: 'rgba(255,255,255,0.4)',
    fontSize: 11,
    marginTop: 8,
  },
});
