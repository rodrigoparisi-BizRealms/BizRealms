import { Stack } from 'expo-router';
import { AuthProvider } from '../context/AuthContext';

export default function RootLayout() {
  return (
    <AuthProvider>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="(auth)/login" />
        <Stack.Screen name="(auth)/register" />
        <Stack.Screen name="(onboarding)/avatar" />
        <Stack.Screen name="(onboarding)/background" />
        <Stack.Screen name="(onboarding)/dream" />
        <Stack.Screen name="(onboarding)/personality" />
        <Stack.Screen name="(tabs)" />
      </Stack>
    </AuthProvider>
  );
}
