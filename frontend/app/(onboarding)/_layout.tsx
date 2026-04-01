import { Stack } from 'expo-router';

export default function OnboardingLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="avatar" />
      <Stack.Screen name="background" />
      <Stack.Screen name="dream" />
      <Stack.Screen name="personality" />
    </Stack>
  );
}
