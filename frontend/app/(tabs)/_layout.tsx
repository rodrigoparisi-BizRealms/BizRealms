import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Platform } from 'react-native';
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { WebView } from 'react-native-webview';
import { useLanguage } from '../../context/LanguageContext';
import { useAuth } from '../../context/AuthContext';
import { useMusic } from '../../context/MusicContext';
import { usePushNotifications } from '../../hooks/usePushNotifications';

function MiniPlayer() {
  const { activePlaylist, isPlaying, stopMusic } = useMusic();

  if (!activePlaylist || !isPlaying) return null;

  return (
    <View style={mp.wrapper}>
      {/* Hidden but mounted audio player - keeps playing across tabs */}
      <View style={mp.hiddenPlayer}>
        {Platform.OS === 'web' ? (
          <iframe
            src={`https://www.youtube.com/embed/${activePlaylist.youtubeId}?autoplay=1&loop=1&rel=0&modestbranding=1`}
            style={{ width: 1, height: 1, border: 'none', opacity: 0 }}
            allow="autoplay; encrypted-media"
          />
        ) : (
          <WebView
            source={{ html: `<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>*{margin:0;padding:0}body{background:#000}</style></head><body><iframe src="https://www.youtube.com/embed/${activePlaylist.youtubeId}?autoplay=1&loop=1&rel=0&modestbranding=1&playsinline=1" allow="autoplay; encrypted-media" style="width:1px;height:1px;border:none;opacity:0"></iframe></body></html>` }}
            style={{ width: 1, height: 1, opacity: 0, position: 'absolute' }}
            allowsInlineMediaPlayback
            mediaPlaybackRequiresUserAction={false}
            javaScriptEnabled
          />
        )}
      </View>
      {/* Visible mini bar */}
      <View style={mp.bar}>
        <View style={[mp.dot, { backgroundColor: activePlaylist.color }]} />
        <Ionicons name={activePlaylist.icon as any} size={18} color={activePlaylist.color} />
        <Text style={mp.text} numberOfLines={1}>{activePlaylist.name}</Text>
        <View style={mp.eq}>
          <View style={[mp.eqBar, { height: 8, backgroundColor: activePlaylist.color }]} />
          <View style={[mp.eqBar, { height: 14, backgroundColor: activePlaylist.color }]} />
          <View style={[mp.eqBar, { height: 6, backgroundColor: activePlaylist.color }]} />
          <View style={[mp.eqBar, { height: 12, backgroundColor: activePlaylist.color }]} />
        </View>
        <TouchableOpacity onPress={stopMusic} style={mp.closeBtn}>
          <Ionicons name="close" size={18} color="#888" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const mp = StyleSheet.create({
  wrapper: { position: 'relative' as const },
  hiddenPlayer: { width: 1, height: 1, overflow: 'hidden', position: 'absolute' as const, opacity: 0 },
  bar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1e1e1e',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#2a2a2a',
    gap: 10,
  },
  dot: { width: 8, height: 8, borderRadius: 4 },
  text: { flex: 1, color: '#fff', fontSize: 13, fontWeight: '600' },
  eq: { flexDirection: 'row', alignItems: 'flex-end', gap: 2, height: 16 },
  eqBar: { width: 3, borderRadius: 2, backgroundColor: '#9C27B0' },
  closeBtn: { padding: 4, backgroundColor: '#2a2a2a', borderRadius: 8 },
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
