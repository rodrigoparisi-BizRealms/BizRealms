import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useMusic } from '../../context/MusicContext';
import { usePushNotifications } from '../../hooks/usePushNotifications';

function MiniPlayer() {
  const { activeTrack, isPlaying, stopMusic } = useMusic();

  if (!activeTrack || !isPlaying) return null;

  return (
    <View style={mp.bar}>
      <View style={[mp.dot, { backgroundColor: activeTrack.color }]} />
      <Ionicons name="musical-notes" size={16} color={activeTrack.color} />
      <Text style={mp.text} numberOfLines={1}>{activeTrack.name}</Text>
      <View style={mp.eq}>
        <View style={[mp.eqBar, { height: 8, backgroundColor: activeTrack.color }]} />
        <View style={[mp.eqBar, { height: 14, backgroundColor: activeTrack.color }]} />
        <View style={[mp.eqBar, { height: 6, backgroundColor: activeTrack.color }]} />
      </View>
      <TouchableOpacity onPress={stopMusic} style={mp.closeBtn}>
        <Ionicons name="close" size={16} color="#888" />
      </TouchableOpacity>
    </View>
  );
}

const mp = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e1e1e',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#2a2a2a',
    gap: 8,
  },
  dot: { width: 6, height: 6, borderRadius: 3 },
  text: { flex: 1, color: '#ccc', fontSize: 12, fontWeight: '600' },
  eq: { flexDirection: 'row', alignItems: 'flex-end', gap: 2, height: 14 },
  eqBar: { width: 3, borderRadius: 2 },
  closeBtn: { padding: 4, backgroundColor: '#2a2a2a', borderRadius: 6 },
});

export default function TabsLayout() {
  const { t } = useLanguage();
  const { token } = useAuth();
  
  // Register for push notifications when user is authenticated
  usePushNotifications(token);
  
  return (
    <View style={{ flex: 1 }}>
      <View style={{ flex: 1 }}>
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
              title: t('nav.home'),
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="home" size={20} color={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="jobs"
            options={{
              title: t('nav.jobs'),
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="briefcase" size={20} color={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="companies"
            options={{
              title: t('nav.companies'),
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="business" size={20} color={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="investments"
            options={{
              title: t('nav.investments'),
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="trending-up" size={20} color={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="store"
            options={{
              title: t('nav.store'),
              tabBarActiveTintColor: '#E91E63',
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="storefront" size={20} color={color} />
              ),
            }}
          />
          <Tabs.Screen
            name="profile"
            options={{
              title: t('nav.profile'),
              tabBarIcon: ({ color, size }) => (
                <Ionicons name="person" size={20} color={color} />
              ),
            }}
          />
          {/* Hidden tabs - accessible via links from other screens */}
          <Tabs.Screen name="patrimonio" options={{ href: null }} />
          <Tabs.Screen name="courses" options={{ href: null }} />
          <Tabs.Screen name="map" options={{ href: null }} />
          <Tabs.Screen name="bank" options={{ href: null }} />
          <Tabs.Screen name="music" options={{ href: null }} />
          <Tabs.Screen name="coaching" options={{ href: null }} />
        </Tabs>
      </View>
      {/* Persistent mini-player - stays mounted across tab switches */}
      <MiniPlayer />
    </View>
  );
}
