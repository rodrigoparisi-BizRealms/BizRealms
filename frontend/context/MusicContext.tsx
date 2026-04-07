import React, { createContext, useContext, useState, useRef, useEffect, useCallback } from 'react';
import { Audio } from 'expo-av';

// Royalty-free ambient radio streams for background music
const TRACKS = [
  {
    id: '1',
    title: 'Lofi Business',
    artist: 'BizRealms Radio',
    icon: 'cafe',
    uri: 'https://stream.zeno.fm/0r0xa792kwzuv',
  },
  {
    id: '2',
    title: 'Chill Jazz',
    artist: 'BizRealms Radio',
    icon: 'musical-notes',
    uri: 'https://stream.zeno.fm/f3wvbbqmdg8uv',
  },
  {
    id: '3',
    title: 'Focus & Study',
    artist: 'BizRealms Radio',
    icon: 'headset',
    uri: 'https://stream.zeno.fm/4lyg909c28zuv',
  },
  {
    id: '4',
    title: 'Deep House',
    artist: 'BizRealms Radio',
    icon: 'pulse',
    uri: 'https://stream.zeno.fm/k87y77k5c68uv',
  },
  {
    id: '5',
    title: 'Classical Piano',
    artist: 'BizRealms Radio',
    icon: 'heart',
    uri: 'https://stream.zeno.fm/egm2z3sykzzuv',
  },
];

interface MusicContextType {
  isPlaying: boolean;
  currentTrack: typeof TRACKS[0] | null;
  tracks: typeof TRACKS;
  play: (track?: typeof TRACKS[0]) => Promise<void>;
  pause: () => Promise<void>;
  toggle: () => Promise<void>;
  nextTrack: () => Promise<void>;
  prevTrack: () => Promise<void>;
  selectTrack: (track: typeof TRACKS[0]) => Promise<void>;
  showPlayer: boolean;
  setShowPlayer: (show: boolean) => void;
}

const MusicContext = createContext<MusicContextType>({
  isPlaying: false,
  currentTrack: null,
  tracks: TRACKS,
  play: async () => {},
  pause: async () => {},
  toggle: async () => {},
  nextTrack: async () => {},
  prevTrack: async () => {},
  selectTrack: async () => {},
  showPlayer: false,
  setShowPlayer: () => {},
});

export const useMusic = () => useContext(MusicContext);

export function MusicProvider({ children }: { children: React.ReactNode }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTrack, setCurrentTrack] = useState<typeof TRACKS[0] | null>(null);
  const [showPlayer, setShowPlayer] = useState(false);
  const soundRef = useRef<Audio.Sound | null>(null);

  useEffect(() => {
    Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      staysActiveInBackground: true,
      playsInSilentModeIOS: true,
      shouldDuckAndroid: true,
      playThroughEarpieceAndroid: false,
    }).catch(() => {});
    
    return () => {
      if (soundRef.current) {
        soundRef.current.unloadAsync().catch(() => {});
      }
    };
  }, []);

  const loadAndPlay = useCallback(async (track: typeof TRACKS[0]) => {
    try {
      if (soundRef.current) {
        await soundRef.current.stopAsync().catch(() => {});
        await soundRef.current.unloadAsync().catch(() => {});
        soundRef.current = null;
      }

      const { sound } = await Audio.Sound.createAsync(
        { uri: track.uri },
        { shouldPlay: true, isLooping: false, volume: 0.5 },
      );
      soundRef.current = sound;
      setCurrentTrack(track);
      setIsPlaying(true);
      setShowPlayer(true);

      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded) {
          setIsPlaying(status.isPlaying);
        }
      });
    } catch (e) {
      console.warn('[Music] Error loading track:', e);
    }
  }, []);

  const play = useCallback(async (track?: typeof TRACKS[0]) => {
    if (track) {
      await loadAndPlay(track);
    } else if (soundRef.current) {
      await soundRef.current.playAsync().catch(() => {});
      setIsPlaying(true);
    } else {
      await loadAndPlay(TRACKS[0]);
    }
  }, [loadAndPlay]);

  const pause = useCallback(async () => {
    if (soundRef.current) {
      await soundRef.current.pauseAsync().catch(() => {});
      setIsPlaying(false);
    }
  }, []);

  const toggle = useCallback(async () => {
    if (isPlaying) {
      await pause();
    } else {
      await play();
    }
  }, [isPlaying, pause, play]);

  const nextTrack = useCallback(async () => {
    const idx = TRACKS.findIndex(t => t.id === currentTrack?.id);
    const next = TRACKS[(idx + 1) % TRACKS.length];
    await loadAndPlay(next);
  }, [currentTrack, loadAndPlay]);

  const prevTrack = useCallback(async () => {
    const idx = TRACKS.findIndex(t => t.id === currentTrack?.id);
    const prev = TRACKS[(idx - 1 + TRACKS.length) % TRACKS.length];
    await loadAndPlay(prev);
  }, [currentTrack, loadAndPlay]);

  const selectTrack = useCallback(async (track: typeof TRACKS[0]) => {
    await loadAndPlay(track);
  }, [loadAndPlay]);

  return (
    <MusicContext.Provider
      value={{
        isPlaying, currentTrack, tracks: TRACKS,
        play, pause, toggle, nextTrack, prevTrack, selectTrack,
        showPlayer, setShowPlayer,
      }}
    >
      {children}
    </MusicContext.Provider>
  );
}
