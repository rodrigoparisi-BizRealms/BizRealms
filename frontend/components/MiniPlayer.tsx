import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useMusic } from '../context/MusicContext';

export default function MiniPlayer() {
  const { isPlaying, currentTrack, tracks, toggle, nextTrack, prevTrack, selectTrack, showPlayer, setShowPlayer } = useMusic();
  const [showPicker, setShowPicker] = useState(false);

  if (!showPlayer) return null;

  return (
    <>
      {/* Mini Player Bar */}
      <View style={s.container}>
        <TouchableOpacity style={s.trackInfo} onPress={() => setShowPicker(true)}>
          <Ionicons name={(currentTrack?.icon || 'musical-notes') as any} size={18} color="#1DB954" />
          <View style={s.textWrap}>
            <Text style={s.title} numberOfLines={1}>{currentTrack?.title || 'Select a track'}</Text>
            <Text style={s.artist} numberOfLines={1}>{currentTrack?.artist || 'BizRealms Radio'}</Text>
          </View>
        </TouchableOpacity>

        <View style={s.controls}>
          <TouchableOpacity onPress={prevTrack} style={s.btn}>
            <Ionicons name="play-skip-back" size={18} color="#fff" />
          </TouchableOpacity>
          <TouchableOpacity onPress={toggle} style={s.playBtn}>
            <Ionicons name={isPlaying ? 'pause' : 'play'} size={20} color="#000" />
          </TouchableOpacity>
          <TouchableOpacity onPress={nextTrack} style={s.btn}>
            <Ionicons name="play-skip-forward" size={18} color="#fff" />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => setShowPlayer(false)} style={s.btn}>
            <Ionicons name="close" size={16} color="#888" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Track Picker Modal */}
      <Modal visible={showPicker} transparent animationType="slide" onRequestClose={() => setShowPicker(false)}>
        <View style={s.modalOverlay}>
          <View style={s.modal}>
            <View style={s.modalHeader}>
              <Ionicons name="radio" size={22} color="#1DB954" />
              <Text style={s.modalTitle}>BizRealms Radio</Text>
              <TouchableOpacity onPress={() => setShowPicker(false)}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
            </View>
            <Text style={s.modalSubtitle}>Choose your vibe while you play</Text>
            <ScrollView>
              {tracks.map((track) => {
                const isActive = currentTrack?.id === track.id;
                return (
                  <TouchableOpacity
                    key={track.id}
                    style={[s.trackItem, isActive && s.trackItemActive]}
                    onPress={() => { selectTrack(track); setShowPicker(false); }}
                  >
                    <View style={[s.trackIcon, isActive && { backgroundColor: '#1DB954' }]}>
                      <Ionicons name={(track.icon || 'musical-notes') as any} size={22} color={isActive ? '#000' : '#1DB954'} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={[s.trackName, isActive && { color: '#1DB954' }]}>{track.title}</Text>
                      <Text style={s.trackArtist}>{track.artist}</Text>
                    </View>
                    {isActive && isPlaying && (
                      <View style={s.eqBars}>
                        <View style={[s.eqBar, { height: 12 }]} />
                        <View style={[s.eqBar, { height: 18 }]} />
                        <View style={[s.eqBar, { height: 8 }]} />
                        <View style={[s.eqBar, { height: 15 }]} />
                      </View>
                    )}
                    {isActive && !isPlaying && <Ionicons name="pause" size={18} color="#1DB954" />}
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
}

const s = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1a1a2e',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#1DB95433',
  },
  trackInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  textWrap: { flex: 1 },
  title: { color: '#fff', fontSize: 13, fontWeight: '600' },
  artist: { color: '#888', fontSize: 11 },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  btn: { padding: 6 },
  playBtn: {
    backgroundColor: '#1DB954',
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: '#000000aa',
    justifyContent: 'flex-end',
  },
  modal: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '60%',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 4,
  },
  modalTitle: { flex: 1, color: '#fff', fontSize: 18, fontWeight: 'bold' },
  modalSubtitle: { color: '#888', fontSize: 12, marginBottom: 16 },
  trackItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    gap: 12,
    marginBottom: 6,
    backgroundColor: '#2a2a3e',
  },
  trackItemActive: {
    backgroundColor: '#1DB95420',
    borderWidth: 1,
    borderColor: '#1DB95455',
  },
  trackIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#2a2a3e',
    alignItems: 'center',
    justifyContent: 'center',
  },
  trackName: { color: '#fff', fontSize: 15, fontWeight: '600' },
  trackArtist: { color: '#888', fontSize: 12, marginTop: 2 },
  eqBars: { flexDirection: 'row', alignItems: 'flex-end', gap: 2 },
  eqBar: { width: 3, backgroundColor: '#1DB954', borderRadius: 2 },
});
