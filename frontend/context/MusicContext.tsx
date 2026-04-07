import React, { createContext, useContext, useState, useRef, useEffect, useCallback } from 'react';
import { Audio } from 'expo-av';

export interface Track {
  id: string;
  title: string;
  artist: string;
  genre: 'Jazz' | 'Blues';
  icon: string;
  uri: string;
}

// 5 Jazz + 5 Blues royalty-free tracks by Kevin MacLeod (incompetech.com)
// Licensed under Creative Commons: By Attribution 4.0
const TRACKS: Track[] = [
  // === JAZZ ===
  {
    id: 'jazz-1',
    title: 'Backed Vibes',
    artist: 'Kevin MacLeod',
    genre: 'Jazz',
    icon: 'musical-notes',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Backed%20Vibes%20Clean.mp3',
  },
  {
    id: 'jazz-2',
    title: 'Airport Lounge',
    artist: 'Kevin MacLeod',
    genre: 'Jazz',
    icon: 'cafe',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Airport%20Lounge.mp3',
  },
  {
    id: 'jazz-3',
    title: 'Backbay Lounge',
    artist: 'Kevin MacLeod',
    genre: 'Jazz',
    icon: 'wine',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Backbay%20Lounge.mp3',
  },
  {
    id: 'jazz-4',
    title: 'Bossa Antigua',
    artist: 'Kevin MacLeod',
    genre: 'Jazz',
    icon: 'sunny',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Bossa%20Antigua.mp3',
  },
  {
    id: 'jazz-5',
    title: 'Cool Vibes',
    artist: 'Kevin MacLeod',
    genre: 'Jazz',
    icon: 'headset',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Cool%20Vibes.mp3',
  },
  // === BLUES ===
  {
    id: 'blues-1',
    title: 'Cantina Blues',
    artist: 'Kevin MacLeod',
    genre: 'Blues',
    icon: 'flame',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Cantina%20Blues.mp3',
  },
  {
    id: 'blues-2',
    title: 'Whiskey on the Mississippi',
    artist: 'Kevin MacLeod',
    genre: 'Blues',
    icon: 'beer',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Whiskey%20on%20the%20Mississippi.mp3',
  },
  {
    id: 'blues-3',
    title: 'Slow Burn',
    artist: 'Kevin MacLeod',
    genre: 'Blues',
    icon: 'bonfire',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Slow%20Burn.mp3',
  },
  {
    id: 'blues-4',
    title: 'Smoking Gun',
    artist: 'Kevin MacLeod',
    genre: 'Blues',
    icon: 'flash',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Smoking%20Gun.mp3',
  },
  {
    id: 'blues-5',
    title: 'Blue Sizzle',
    artist: 'Kevin MacLeod',
    genre: 'Blues',
    icon: 'water',
    uri: 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Blue%20Sizzle.mp3',
  },
];

interface MusicContextType {
  isPlaying: boolean;
  isLoading: boolean;
  currentTrack: Track | null;
  tracks: Track[];
  play: (track?: Track) => Promise<void>;
  pause: () => Promise<void>;
  toggle: () => Promise<void>;
  nextTrack: () => Promise<void>;
  prevTrack: () => Promise<void>;
  selectTrack: (track: Track) => Promise<void>;
}

const MusicContext = createContext<MusicContextType>({
  isPlaying: false,
  isLoading: false,
  currentTrack: null,
  tracks: TRACKS,
  play: async () => {},
  pause: async () => {},
  toggle: async () => {},
  nextTrack: async () => {},
  prevTrack: async () => {},
  selectTrack: async () => {},
});

export const useMusic = () => useContext(MusicContext);

export function MusicProvider({ children }: { children: React.ReactNode }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTrack, setCurrentTrack] = useState<Track | null>(null);
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

  const loadAndPlay = useCallback(async (track: Track) => {
    try {
      setIsLoading(true);
      if (soundRef.current) {
        await soundRef.current.stopAsync().catch(() => {});
        await soundRef.current.unloadAsync().catch(() => {});
        soundRef.current = null;
      }

      const { sound } = await Audio.Sound.createAsync(
        { uri: track.uri },
        { shouldPlay: true, isLooping: true, volume: 0.5 },
      );
      soundRef.current = sound;
      setCurrentTrack(track);
      setIsPlaying(true);
      setIsLoading(false);

      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded) {
          setIsPlaying(status.isPlaying);
        }
      });
    } catch (e) {
      console.warn('[Music] Error loading track:', e);
      setIsLoading(false);
    }
  }, []);

  const play = useCallback(async (track?: Track) => {
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

  const selectTrack = useCallback(async (track: Track) => {
    await loadAndPlay(track);
  }, [loadAndPlay]);

  return (
    <MusicContext.Provider
      value={{
        isPlaying, isLoading, currentTrack, tracks: TRACKS,
        play, pause, toggle, nextTrack, prevTrack, selectTrack,
      }}
    >
      {children}
    </MusicContext.Provider>
  );
}
