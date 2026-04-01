import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#2a2a2a',
          borderTopColor: '#3a3a3a',
          height: 58,
          paddingBottom: 6,
          paddingTop: 4,
        },
        tabBarActiveTintColor: '#4CAF50',
        tabBarInactiveTintColor: '#666',
        tabBarLabelStyle: {
          fontSize: 9,
          fontWeight: '600',
        },
        tabBarIconStyle: {
          marginBottom: -2,
        },
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: 'Início',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={20} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="jobs"
        options={{
          title: 'Empregos',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="briefcase" size={20} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="companies"
        options={{
          title: 'Empresas',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="business" size={20} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="investments"
        options={{
          title: 'Investir',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="trending-up" size={20} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="store"
        options={{
          title: 'Loja',
          tabBarActiveTintColor: '#E91E63',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="storefront" size={20} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Perfil',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" size={20} color={color} />
          ),
        }}
      />
      {/* Hidden tabs - accessible via links from other screens */}
      <Tabs.Screen name="patrimonio" options={{ href: null }} />
      <Tabs.Screen name="courses" options={{ href: null }} />
      <Tabs.Screen name="map" options={{ href: null }} />
    </Tabs>
  );
}
