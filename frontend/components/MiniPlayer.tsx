import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, ScrollView, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useMusic, Track } from '../context/MusicContext';

export default function MiniPlayer() {
  const { isPlaying, isLoading, currentTrack, tracks, toggle, nextTrack, prevTrack, selectTrack } = useMusic();
  const [showPicker, setShowPicker] = useState(false);

  const jazzTracks = tracks.filter(t => t.genre === 'Jazz');
  const bluesTracks = tracks.filter(t => t.genre === 'Blues');

  const genreColor = currentTrack?.genre === 'Blues' ? '#4A90D9' : '#E6A817';

  return (
    <>
      {/* Mini Player Bar - Always visible */}
      <View style={s.container}>
        {/* Track Info - toque para abrir lista */}
        <TouchableOpacity style={s.trackInfo} onPress={() => setShowPicker(true)} activeOpacity={0.7}>
          <View style={[s.genreDot, { backgroundColor: currentTrack ? genreColor : '#888' }]} />
          <View style={s.textWrap}>
            <Text style={s.title} numberOfLines={1}>
              {currentTrack ? currentTrack.title : 'Selecione uma música'}
            </Text>
            <Text style={s.subtitle} numberOfLines={1}>
              {currentTrack ? `${currentTrack.genre} • ${currentTrack.artist}` : 'Jazz & Blues'}
            </Text>
          </View>
        </TouchableOpacity>

        {/* Controls */}
        <View style={s.controls}>
          <TouchableOpacity onPress={prevTrack} style={s.btn} activeOpacity={0.6}>
            <Ionicons name="play-skip-back" size={18} color="#ccc" />
          </TouchableOpacity>
          <TouchableOpacity onPress={toggle} style={[s.playBtn, isPlaying && s.playBtnActive]} activeOpacity={0.7}>
            {isLoading ? (
              <ActivityIndicator size="small" color="#000" />
            ) : (
              <Ionicons name={isPlaying ? 'pause' : 'play'} size={20} color="#000" />
            )}
          </TouchableOpacity>
          <TouchableOpacity onPress={nextTrack} style={s.btn} activeOpacity={0.6}>
            <Ionicons name="play-skip-forward" size={18} color="#ccc" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Track Picker Modal */}
      <Modal visible={showPicker} transparent animationType="slide" onRequestClose={() => setShowPicker(false)}>
        <View style={s.modalOverlay}>
          <View style={s.modal}>
            {/* Header */}
            <View style={s.modalHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Ionicons name="musical-notes" size={22} color="#E6A817" />
                <Text style={s.modalTitle}>BizRealms Radio</Text>
              </View>
              <TouchableOpacity onPress={() => setShowPicker(false)} style={{ padding: 4 }}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
            </View>
            <Text style={s.modalSubtitle}>Jazz & Blues • Kevin MacLeod</Text>

            <ScrollView showsVerticalScrollIndicator={false}>
              {/* Jazz Section */}
              <View style={s.sectionHeader}>
                <View style={[s.sectionDot, { backgroundColor: '#E6A817' }]} />
                <Text style={[s.sectionLabel, { color: '#E6A817' }]}>Jazz</Text>
                <View style={s.sectionLine} />
              </View>
              {jazzTracks.map((track) => renderTrackItem(track, currentTrack, isPlaying, selectTrack, setShowPicker))}

              {/* Blues Section */}
              <View style={[s.sectionHeader, { marginTop: 16 }]}>
                <View style={[s.sectionDot, { backgroundColor: '#4A90D9' }]} />
                <Text style={[s.sectionLabel, { color: '#4A90D9' }]}>Blues</Text>
                <View style={s.sectionLine} />
              </View>
              {bluesTracks.map((track) => renderTrackItem(track, currentTrack, isPlaying, selectTrack, setShowPicker))}

              {/* Attribution */}
              <View style={s.attribution}>
                <Ionicons name="information-circle-outline" size={14} color="#555" />
                <Text style={s.attributionText}>
                  Música por Kevin MacLeod (incompetech.com){"\n"}Licença Creative Commons: By Attribution 4.0
                </Text>
              </View>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
}

function renderTrackItem(
  track: Track,
  currentTrack: Track | null,
  isPlaying: boolean,
  selectTrack: (t: Track) => Promise<void>,
  setShowPicker: (v: boolean) => void,
) {
  const isActive = currentTrack?.id === track.id;
  const genreColor = track.genre === 'Blues' ? '#4A90D9' : '#E6A817';

  return (
    <TouchableOpacity
      key={track.id}
      style={[s.trackItem, isActive && { borderColor: genreColor, borderWidth: 1 }]}
      onPress={() => { selectTrack(track); setShowPicker(false); }}
      activeOpacity={0.7}
    >
      <View style={[s.trackIcon, { backgroundColor: isActive ? genreColor : '#2a2a3e' }]}>
        <Ionicons name={(track.icon || 'musical-notes') as any} size={20} color={isActive ? '#000' : genreColor} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[s.trackName, isActive && { color: genreColor }]}>{track.title}</Text>
        <Text style={s.trackArtist}>{track.artist}</Text>
      </View>
      {isActive && isPlaying && (
        <View style={s.eqBars}>
          <View style={[s.eqBar, { height: 10, backgroundColor: genreColor }]} />
          <View style={[s.eqBar, { height: 16, backgroundColor: genreColor }]} />
          <View style={[s.eqBar, { height: 7, backgroundColor: genreColor }]} />
          <View style={[s.eqBar, { height: 13, backgroundColor: genreColor }]} />
        </View>
      )}
      {isActive && !isPlaying && <Ionicons name="pause" size={18} color={genreColor} />}
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111122',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#ffffff10',
  },
  trackInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  genreDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  textWrap: { flex: 1 },
  title: { color: '#fff', fontSize: 13, fontWeight: '700' },
  subtitle: { color: '#888', fontSize: 11, marginTop: 1 },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  btn: { padding: 8 },
  playBtn: {
    backgroundColor: '#E6A817',
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playBtnActive: {
    backgroundColor: '#4A90D9',
  },
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: '#000000cc',
    justifyContent: 'flex-end',
  },
  modal: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    maxHeight: '70%',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  modalTitle: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  modalSubtitle: { color: '#888', fontSize: 12, marginBottom: 16 },
  // Section headers
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
    paddingHorizontal: 4,
  },
  sectionDot: { width: 10, height: 10, borderRadius: 5 },
  sectionLabel: { fontSize: 14, fontWeight: 'bold' },
  sectionLine: { flex: 1, height: 1, backgroundColor: '#ffffff15' },
  // Track items
  trackItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    gap: 12,
    marginBottom: 6,
    backgroundColor: '#222238',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  trackIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  trackName: { color: '#fff', fontSize: 15, fontWeight: '600' },
  trackArtist: { color: '#888', fontSize: 12, marginTop: 2 },
  eqBars: { flexDirection: 'row', alignItems: 'flex-end', gap: 2 },
  eqBar: { width: 3, borderRadius: 2 },
  // Attribution
  attribution: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#ffffff10',
    paddingHorizontal: 4,
  },
  attributionText: { color: '#555', fontSize: 10, flex: 1, lineHeight: 15 },
});
