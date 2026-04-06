import { Stack } from 'expo-router';
import { AuthProvider } from '../context/AuthContext';
import { LanguageProvider } from '../context/LanguageContext';
import { MusicProvider } from '../context/MusicContext';
import { NetworkProvider } from '../context/NetworkContext';
import { ThemeProvider } from '../context/ThemeContext';
import ErrorBoundary from '../components/ErrorBoundary';

export default function RootLayout() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <NetworkProvider>
          <LanguageProvider>
            <AuthProvider>
              <MusicProvider>
                <Stack screenOptions={{ headerShown: false }}>
                  <Stack.Screen name="index" />
                  <Stack.Screen name="(auth)" />
                  <Stack.Screen name="(onboarding)" />
                  <Stack.Screen name="(tabs)" />
                  <Stack.Screen name="legal" />
                  <Stack.Screen name="player-profile" />
                </Stack>
              </MusicProvider>
            </AuthProvider>
          </LanguageProvider>
        </NetworkProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
