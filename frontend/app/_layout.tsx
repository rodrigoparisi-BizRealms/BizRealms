import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { AuthProvider } from '../context/AuthContext';
import { LanguageProvider } from '../context/LanguageContext';
import { NetworkProvider } from '../context/NetworkContext';
import { ThemeProvider } from '../context/ThemeContext';
import { AdProvider } from '../context/AdContext';
import { SoundProvider } from '../context/SoundContext';
import ErrorBoundary from '../components/ErrorBoundary';
import { initSentry, wrapApp } from '../context/sentryService';

// Initialize Sentry as early as possible
initSentry();

function RootLayout() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <SoundProvider>
          <NetworkProvider>
            <LanguageProvider>
              <AuthProvider>
                <AdProvider>
                  <Stack screenOptions={{ headerShown: false }}>
                    <Stack.Screen name="index" />
                    <Stack.Screen name="(auth)" />
                    <Stack.Screen name="(onboarding)" />
                    <Stack.Screen name="(tabs)" />
                    <Stack.Screen name="legal" />
                    <Stack.Screen name="player-profile" />
                  </Stack>
                </AdProvider>
              </AuthProvider>
            </LanguageProvider>
          </NetworkProvider>
        </SoundProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default wrapApp(RootLayout);
