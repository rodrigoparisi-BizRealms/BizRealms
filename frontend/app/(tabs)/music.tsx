import React from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useLanguage } from '../../context/LanguageContext';
import { useMusic, Track } from '../../context/MusicContext';
import { useTheme } from '../../context/ThemeContext';

export default function Music() {
  const router = useRouter();
  const { t } = useLanguage();
  const { currentTrack, isPlaying, selectTrack, toggle, tracks } = useMusic();
  const { colors } = useTheme();

  const jazzTracks = tracks.filter(t => t.genre === 'Jazz');
  const bluesTracks = tracks.filter(t => t.genre === 'Blues');

  const handleTrackPress = (track: Track) => {
    if (currentTrack?.id === track.id) {
      toggle();
    } else {
      selectTrack(track);
    }
  };

  return (
    <SafeAreaView style={[s.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={s.title}>BizRealms Radio</Text>
        <Ionicons name="radio" size={28} color="#E6A817" />
      </View>

      <Text style={s.desc}>Jazz & Blues para acompanhar sua jornada empresarial</Text>

      <ScrollView contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>
        {/* Jazz Section */}
        <View style={s.sectionHeader}>
          <View style={[s.sectionDot, { backgroundColor: '#E6A817' }]} />
          <Text style={[s.sectionLabel, { color: '#E6A817' }]}>Jazz</Text>
          <View style={s.sectionLine} />
          <Text style={s.sectionCount}>{jazzTracks.length} faixas</Text>
        </View>
        {jazzTracks.map((track) => {
          const isActive = currentTrack?.id === track.id;
          return (
            <TouchableOpacity
              key={track.id}
              style={[s.trackCard, isActive && { borderColor: '#E6A817', borderWidth: 2 }]}
              onPress={() => handleTrackPress(track)}
              activeOpacity={0.7}
            >
              <View style={[s.trackIcon, { backgroundColor: isActive ? '#E6A817' : '#E6A81720' }]}>
                <Ionicons name={(track.icon || 'musical-notes') as any} size={24} color={isActive ? '#000' : '#E6A817'} />
              </View>
              <View style={s.trackInfo}>
                <Text style={[s.trackName, isActive && { color: '#E6A817' }]}>{track.title}</Text>
                <Text style={s.trackArtist}>{track.artist}</Text>
              </View>
              <View style={s.playBtn}>
                {isActive && isPlaying ? (
                  <View style={[s.playingCircle, { backgroundColor: '#E6A817' }]}>
                    <Ionicons name="pause" size={18} color="#000" />
                  </View>
                ) : (
                  <View style={[s.playCircle, isActive && { backgroundColor: '#E6A817' }]}>
                    <Ionicons name="play" size={18} color={isActive ? '#000' : '#fff'} />
                  </View>
                )}
              </View>
            </TouchableOpacity>
          );
        })}

        {/* Blues Section */}
        <View style={[s.sectionHeader, { marginTop: 24 }]}>
          <View style={[s.sectionDot, { backgroundColor: '#4A90D9' }]} />
          <Text style={[s.sectionLabel, { color: '#4A90D9' }]}>Blues</Text>
          <View style={s.sectionLine} />
          <Text style={s.sectionCount}>{bluesTracks.length} faixas</Text>
        </View>
        {bluesTracks.map((track) => {
          const isActive = currentTrack?.id === track.id;
          return (
            <TouchableOpacity
              key={track.id}
              style={[s.trackCard, isActive && { borderColor: '#4A90D9', borderWidth: 2 }]}
              onPress={() => handleTrackPress(track)}
              activeOpacity={0.7}
            >
              <View style={[s.trackIcon, { backgroundColor: isActive ? '#4A90D9' : '#4A90D920' }]}>
                <Ionicons name={(track.icon || 'musical-notes') as any} size={24} color={isActive ? '#000' : '#4A90D9'} />
              </View>
              <View style={s.trackInfo}>
                <Text style={[s.trackName, isActive && { color: '#4A90D9' }]}>{track.title}</Text>
                <Text style={s.trackArtist}>{track.artist}</Text>
              </View>
              <View style={s.playBtn}>
                {isActive && isPlaying ? (
                  <View style={[s.playingCircle, { backgroundColor: '#4A90D9' }]}>
                    <Ionicons name="pause" size={18} color="#000" />
                  </View>
                ) : (
                  <View style={[s.playCircle, isActive && { backgroundColor: '#4A90D9' }]}>
                    <Ionicons name="play" size={18} color={isActive ? '#000' : '#fff'} />
                  </View>
                )}
              </View>
            </TouchableOpacity>
          );
        })}

        {/* Attribution */}
        <View style={s.attribution}>
          <Ionicons name="information-circle-outline" size={16} color="#555" />
          <Text style={s.attributionText}>
            Música por Kevin MacLeod (incompetech.com){"\n"}
            Licença Creative Commons: By Attribution 4.0
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  backBtn: { padding: 4 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#fff', flex: 1, textAlign: 'center' },
  desc: { color: '#888', fontSize: 13, textAlign: 'center', paddingHorizontal: 20, paddingTop: 12 },
  content: { padding: 16, paddingBottom: 40 },
  // Section
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  sectionDot: { width: 12, height: 12, borderRadius: 6 },
  sectionLabel: { fontSize: 16, fontWeight: 'bold' },
  sectionLine: { flex: 1, height: 1, backgroundColor: '#ffffff15' },
  sectionCount: { color: '#666', fontSize: 12 },
  // Track Card
  trackCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#222238',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    gap: 12,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  trackIcon: {
    width: 52,
    height: 52,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  trackInfo: { flex: 1 },
  trackName: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
  trackArtist: { color: '#888', fontSize: 12, marginTop: 2 },
  playBtn: { padding: 4 },
  playCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#3a3a4a',
    justifyContent: 'center',
    alignItems: 'center',
  },
  playingCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  // Attribution
  attribution: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginTop: 24,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#ffffff10',
    paddingHorizontal: 4,
  },
  attributionText: { color: '#555', fontSize: 11, flex: 1, lineHeight: 16 },
});
