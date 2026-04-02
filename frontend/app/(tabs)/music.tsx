import React, { useState, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, Platform, Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { WebView } from 'react-native-webview';
import { useSounds } from '../../hooks/useSounds';

type PlaylistCategory = 'lofi' | 'motivation' | 'focus' | 'jazz' | 'gaming';

interface Playlist {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  category: PlaylistCategory;
  youtubeId: string; // YouTube video/playlist ID for embed
  spotifyUrl?: string;
  youtubeMusicUrl?: string;
}

const PLAYLISTS: Playlist[] = [
  {
    id: 'lofi-chill',
    name: 'Lo-fi Chill Beats',
    description: 'Beats relaxantes para jogar e focar',
    icon: 'headset',
    color: '#9C27B0',
    category: 'lofi',
    youtubeId: 'jfKfPfyJRdk',
    spotifyUrl: 'https://open.spotify.com/playlist/0vvXsWCC9xrXsKd4FyS8kM',
    youtubeMusicUrl: 'https://music.youtube.com/playlist?list=PLDIoUOhQQPlXr63I_vwF9GD8sAKh77dWU',
  },
  {
    id: 'motivation-business',
    name: 'Motivação Empresarial',
    description: 'Músicas para inspirar seu lado empreendedor',
    icon: 'rocket',
    color: '#FF9800',
    category: 'motivation',
    youtubeId: 'Dx5qFachd3A',
    spotifyUrl: 'https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M',
    youtubeMusicUrl: 'https://music.youtube.com/playlist?list=PLgzTt0k8mXzEk586Rw3VKhIgUMjMkoRLE',
  },
  {
    id: 'focus-deep',
    name: 'Deep Focus',
    description: 'Concentração máxima com sons ambientes',
    icon: 'eye',
    color: '#2196F3',
    category: 'focus',
    youtubeId: 'yIQd2Ya0Ziw',
    spotifyUrl: 'https://open.spotify.com/playlist/37i9dQZF1DWZeKCadgRdKQ',
    youtubeMusicUrl: 'https://music.youtube.com/playlist?list=PLDIoUOhQQPlXr63I_vwF9GD8sAKh77dWU',
  },
  {
    id: 'jazz-smooth',
    name: 'Jazz & Bossa Nova',
    description: 'Clássicos do jazz e bossa nova brasileira',
    icon: 'musical-notes',
    color: '#E91E63',
    category: 'jazz',
    youtubeId: 'DSGyEsJ17cI',
    spotifyUrl: 'https://open.spotify.com/playlist/37i9dQZF1DX4wta20PHgwo',
    youtubeMusicUrl: 'https://music.youtube.com/playlist?list=PLgzTt0k8mXzEk586Rw3VKhIgUMjMkoRLE',
  },
  {
    id: 'gaming-epic',
    name: 'Epic Gaming',
    description: 'Trilhas sonoras épicas de jogos e filmes',
    icon: 'game-controller',
    color: '#F44336',
    category: 'gaming',
    youtubeId: 'GDnQ3GRkjJc',
    spotifyUrl: 'https://open.spotify.com/playlist/37i9dQZF1DX8GjsySWIS1x',
    youtubeMusicUrl: 'https://music.youtube.com/playlist?list=PLDIoUOhQQPlXr63I_vwF9GD8sAKh77dWU',
  },
  {
    id: 'classical-piano',
    name: 'Piano Clássico',
    description: 'Chopin, Debussy e outras obras-primas',
    icon: 'albums',
    color: '#4CAF50',
    category: 'focus',
    youtubeId: 'lbblMwMGD5o',
    spotifyUrl: 'https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO',
  },
];

const CATEGORY_LABELS: Record<PlaylistCategory, string> = {
  lofi: 'Lo-fi',
  motivation: 'Motivação',
  focus: 'Foco',
  jazz: 'Jazz & Bossa',
  gaming: 'Gaming',
};

export default function Music() {
  const router = useRouter();
  const { play } = useSounds();
  const [activePlaylist, setActivePlaylist] = useState<Playlist | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeCategory, setActiveCategory] = useState<PlaylistCategory | 'all'>('all');
  const webviewRef = useRef<WebView>(null);

  const filteredPlaylists = activeCategory === 'all'
    ? PLAYLISTS
    : PLAYLISTS.filter(p => p.category === activeCategory);

  const handlePlayPlaylist = (playlist: Playlist) => {
    play('click');
    setActivePlaylist(playlist);
    setIsPlaying(true);
  };

  const handleOpenExternal = async (url: string, appName: string) => {
    play('click');
    try {
      const supported = await Linking.canOpenURL(url);
      if (supported) {
        await Linking.openURL(url);
      } else {
        // Fallback to web URL
        await Linking.openURL(url);
      }
    } catch (e) {
      console.error(`Failed to open ${appName}:`, e);
    }
  };

  const getYouTubeEmbedHTML = (videoId: string) => `
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #1a1a1a; display: flex; align-items: center; justify-content: center; height: 100vh; }
        iframe { border-radius: 12px; width: 100%; height: 100%; border: none; }
      </style>
    </head>
    <body>
      <iframe
        src="https://www.youtube.com/embed/${videoId}?autoplay=1&loop=1&rel=0&modestbranding=1&playsinline=1"
        allow="autoplay; encrypted-media"
        allowfullscreen
      ></iframe>
    </body>
    </html>
  `;

  return (
    <SafeAreaView style={s.container}>
      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={s.title}>Música</Text>
        <Ionicons name="musical-notes" size={28} color="#9C27B0" />
      </View>

      {/* Active Player */}
      {activePlaylist && isPlaying && (
        <View style={s.playerContainer}>
          <View style={s.playerWebview}>
            {Platform.OS === 'web' ? (
              <iframe
                src={`https://www.youtube.com/embed/${activePlaylist.youtubeId}?autoplay=1&loop=1&rel=0&modestbranding=1`}
                style={{ width: '100%', height: '100%', border: 'none', borderRadius: 12 }}
                allow="autoplay; encrypted-media"
                allowFullScreen
              />
            ) : (
              <WebView
                ref={webviewRef}
                source={{ html: getYouTubeEmbedHTML(activePlaylist.youtubeId) }}
                style={s.webview}
                allowsInlineMediaPlayback
                mediaPlaybackRequiresUserAction={false}
                javaScriptEnabled
              />
            )}
          </View>
          <View style={s.playerInfo}>
            <View style={s.playerTextRow}>
              <View style={[s.playerDot, { backgroundColor: activePlaylist.color }]} />
              <View style={{ flex: 1 }}>
                <Text style={s.playerTitle} numberOfLines={1}>{activePlaylist.name}</Text>
                <Text style={s.playerSub} numberOfLines={1}>{activePlaylist.description}</Text>
              </View>
            </View>
            <View style={s.playerActions}>
              {activePlaylist.spotifyUrl && (
                <TouchableOpacity
                  style={[s.externalBtn, { backgroundColor: '#1DB95420' }]}
                  onPress={() => handleOpenExternal(activePlaylist.spotifyUrl!, 'Spotify')}
                >
                  <Ionicons name="logo-apple" size={16} color="#1DB954" />
                  <Text style={[s.externalBtnText, { color: '#1DB954' }]}>Spotify</Text>
                </TouchableOpacity>
              )}
              {activePlaylist.youtubeMusicUrl && (
                <TouchableOpacity
                  style={[s.externalBtn, { backgroundColor: '#FF000020' }]}
                  onPress={() => handleOpenExternal(activePlaylist.youtubeMusicUrl!, 'YouTube Music')}
                >
                  <Ionicons name="logo-youtube" size={16} color="#FF0000" />
                  <Text style={[s.externalBtnText, { color: '#FF0000' }]}>YT Music</Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity
                style={s.closePlayerBtn}
                onPress={() => { setIsPlaying(false); setActivePlaylist(null); }}
              >
                <Ionicons name="close" size={20} color="#888" />
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}

      {/* Category Filter */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.categoryScroll} contentContainerStyle={s.categoryContent}>
        <TouchableOpacity
          style={[s.categoryChip, activeCategory === 'all' && s.categoryChipActive]}
          onPress={() => setActiveCategory('all')}
        >
          <Text style={[s.categoryChipText, activeCategory === 'all' && s.categoryChipTextActive]}>Todas</Text>
        </TouchableOpacity>
        {(Object.keys(CATEGORY_LABELS) as PlaylistCategory[]).map(cat => (
          <TouchableOpacity
            key={cat}
            style={[s.categoryChip, activeCategory === cat && s.categoryChipActive]}
            onPress={() => setActiveCategory(cat)}
          >
            <Text style={[s.categoryChipText, activeCategory === cat && s.categoryChipTextActive]}>
              {CATEGORY_LABELS[cat]}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Playlist Grid */}
      <ScrollView contentContainerStyle={s.content}>
        {filteredPlaylists.map(playlist => {
          const isActive = activePlaylist?.id === playlist.id && isPlaying;
          return (
            <TouchableOpacity
              key={playlist.id}
              style={[s.playlistCard, isActive && { borderColor: playlist.color, borderWidth: 2 }]}
              onPress={() => handlePlayPlaylist(playlist)}
              activeOpacity={0.7}
            >
              <View style={[s.playlistIcon, { backgroundColor: `${playlist.color}20` }]}>
                <Ionicons name={playlist.icon as any} size={28} color={playlist.color} />
              </View>
              <View style={s.playlistInfo}>
                <Text style={s.playlistName}>{playlist.name}</Text>
                <Text style={s.playlistDesc}>{playlist.description}</Text>
                <View style={s.playlistMeta}>
                  <View style={[s.categoryBadge, { backgroundColor: `${playlist.color}20` }]}>
                    <Text style={[s.categoryBadgeText, { color: playlist.color }]}>
                      {CATEGORY_LABELS[playlist.category]}
                    </Text>
                  </View>
                </View>
              </View>
              <View style={s.playBtn}>
                {isActive ? (
                  <View style={[s.playingIndicator, { backgroundColor: playlist.color }]}>
                    <Ionicons name="pause" size={18} color="#fff" />
                  </View>
                ) : (
                  <View style={s.playCircle}>
                    <Ionicons name="play" size={20} color="#fff" />
                  </View>
                )}
              </View>
            </TouchableOpacity>
          );
        })}

        {/* External App Links */}
        <View style={s.externalSection}>
          <Text style={s.externalTitle}>Abrir em App Externo</Text>
          <View style={s.externalRow}>
            <TouchableOpacity
              style={[s.externalCard, { borderColor: '#1DB954' }]}
              onPress={() => handleOpenExternal('https://open.spotify.com', 'Spotify')}
            >
              <View style={[s.externalCardIcon, { backgroundColor: '#1DB95420' }]}>
                <Ionicons name="musical-note" size={24} color="#1DB954" />
              </View>
              <Text style={s.externalCardName}>Spotify</Text>
              <Text style={s.externalCardSub}>Abrir app</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[s.externalCard, { borderColor: '#FF0000' }]}
              onPress={() => handleOpenExternal('https://music.youtube.com', 'YouTube Music')}
            >
              <View style={[s.externalCardIcon, { backgroundColor: '#FF000020' }]}>
                <Ionicons name="logo-youtube" size={24} color="#FF0000" />
              </View>
              <Text style={s.externalCardName}>YouTube Music</Text>
              <Text style={s.externalCardSub}>Abrir app</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a1a' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: '#2a2a2a' },
  backBtn: { padding: 4 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', flex: 1, textAlign: 'center' },
  content: { padding: 16, paddingBottom: 40 },
  // Player
  playerContainer: { backgroundColor: '#2a2a2a', margin: 12, borderRadius: 16, overflow: 'hidden', borderWidth: 1, borderColor: '#3a3a3a' },
  playerWebview: { height: 200, backgroundColor: '#1a1a1a' },
  webview: { flex: 1, backgroundColor: '#1a1a1a' },
  playerInfo: { padding: 14 },
  playerTextRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 10 },
  playerDot: { width: 10, height: 10, borderRadius: 5 },
  playerTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  playerSub: { color: '#888', fontSize: 12, marginTop: 2 },
  playerActions: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  externalBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  externalBtnText: { fontSize: 12, fontWeight: 'bold' },
  closePlayerBtn: { marginLeft: 'auto', padding: 6, backgroundColor: '#3a3a3a', borderRadius: 8 },
  // Categories
  categoryScroll: { maxHeight: 50 },
  categoryContent: { paddingHorizontal: 16, paddingVertical: 10, gap: 8 },
  categoryChip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: '#2a2a2a' },
  categoryChipActive: { backgroundColor: '#9C27B0' },
  categoryChipText: { color: '#888', fontSize: 13, fontWeight: '600' },
  categoryChipTextActive: { color: '#fff' },
  // Playlist Cards
  playlistCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#2a2a2a', borderRadius: 14, padding: 14, marginBottom: 10, gap: 12, borderWidth: 1, borderColor: 'transparent' },
  playlistIcon: { width: 56, height: 56, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
  playlistInfo: { flex: 1 },
  playlistName: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
  playlistDesc: { color: '#888', fontSize: 12, marginTop: 2 },
  playlistMeta: { flexDirection: 'row', marginTop: 6, gap: 6 },
  categoryBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  categoryBadgeText: { fontSize: 10, fontWeight: 'bold' },
  playBtn: { padding: 4 },
  playCircle: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#9C27B0', justifyContent: 'center', alignItems: 'center' },
  playingIndicator: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center' },
  // External section
  externalSection: { marginTop: 20, paddingTop: 20, borderTopWidth: 1, borderTopColor: '#2a2a2a' },
  externalTitle: { color: '#888', fontSize: 14, fontWeight: '600', marginBottom: 12 },
  externalRow: { flexDirection: 'row', gap: 12 },
  externalCard: { flex: 1, backgroundColor: '#2a2a2a', borderRadius: 14, padding: 16, alignItems: 'center', gap: 8, borderWidth: 1 },
  externalCardIcon: { width: 48, height: 48, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  externalCardName: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  externalCardSub: { color: '#888', fontSize: 12 },
});
