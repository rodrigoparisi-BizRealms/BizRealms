import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface Track {
  id: string;
  name: string;
  artist: string;
  youtubeId: string;
  color: string;
}

export const JAZZ_BLUES_TRACKS: Track[] = [
  {
    id: '1',
    name: 'Smooth Jazz Vibes',
    artist: 'Jazz Instrumental',
    youtubeId: 'neV3EPgvZ3g',
    color: '#9C27B0',
  },
  {
    id: '2',
    name: 'Late Night Blues',
    artist: 'Blues Instrumental',
    youtubeId: 'JjPVQsdFSKA',
    color: '#3F51B5',
  },
  {
    id: '3',
    name: 'Relaxing Jazz Cafe',
    artist: 'Cafe Jazz',
    youtubeId: 'Dx5qFachd3A',
    color: '#FF9800',
  },
  {
    id: '4',
    name: 'Blues Guitar Session',
    artist: 'Blues Guitar',
    youtubeId: 'gIpMz5PtVDg',
    color: '#F44336',
  },
  {
    id: '5',
    name: 'Midnight Jazz Lounge',
    artist: 'Jazz Lounge',
    youtubeId: 'fEvM-OUbaKs',
    color: '#4CAF50',
  },
];

// Build a YouTube playlist string with all IDs for auto-advance
export const ALL_YOUTUBE_IDS = JAZZ_BLUES_TRACKS.map(t => t.youtubeId).join(',');

interface MusicContextType {
  activeTrack: Track | null;
  isPlaying: boolean;
  musicEnabled: boolean;
  playTrack: (track: Track) => void;
  togglePlay: () => void;
  stopMusic: () => void;
  setMusicEnabled: (enabled: boolean) => void;
  nextTrack: () => void;
}

const MusicContext = createContext<MusicContextType>({
  activeTrack: null,
  isPlaying: false,
  musicEnabled: true,
  playTrack: () => {},
  togglePlay: () => {},
  stopMusic: () => {},
  setMusicEnabled: () => {},
  nextTrack: () => {},
});

const MUSIC_ENABLED_KEY = '@bizrealms_music_enabled';

export function MusicProvider({ children }: { children: ReactNode }) {
  const [activeTrack, setActiveTrack] = useState<Track | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [musicEnabled, _setMusicEnabled] = useState(true);
  const autoAdvanceTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load music enabled preference and auto-start
  useEffect(() => {
    AsyncStorage.getItem(MUSIC_ENABLED_KEY).then(val => {
      const enabled = val === null ? true : val === 'true';
      _setMusicEnabled(enabled);
      // Auto-start music if enabled
      if (enabled && !activeTrack) {
        const randomIndex = Math.floor(Math.random() * JAZZ_BLUES_TRACKS.length);
        setActiveTrack(JAZZ_BLUES_TRACKS[randomIndex]);
        setIsPlaying(true);
      }
    });
  }, []);

  const setMusicEnabled = (enabled: boolean) => {
    _setMusicEnabled(enabled);
    AsyncStorage.setItem(MUSIC_ENABLED_KEY, String(enabled));
    if (!enabled) {
      setIsPlaying(false);
      setActiveTrack(null);
      if (autoAdvanceTimer.current) clearInterval(autoAdvanceTimer.current);
    }
  };

  const nextTrack = () => {
    if (!activeTrack) {
      playTrack(JAZZ_BLUES_TRACKS[0]);
      return;
    }
    const idx = JAZZ_BLUES_TRACKS.findIndex(t => t.id === activeTrack.id);
    const next = JAZZ_BLUES_TRACKS[(idx + 1) % JAZZ_BLUES_TRACKS.length];
    setActiveTrack(next);
    setIsPlaying(true);
  };

  const playTrack = (track: Track) => {
    if (!musicEnabled) return;
    setActiveTrack(track);
    setIsPlaying(true);
  };

  const togglePlay = () => {
    if (!activeTrack) return;
    setIsPlaying(prev => !prev);
  };

  const stopMusic = () => {
    setIsPlaying(false);
    setActiveTrack(null);
    if (autoAdvanceTimer.current) clearInterval(autoAdvanceTimer.current);
  };

  return (
    <MusicContext.Provider value={{
      activeTrack, isPlaying, musicEnabled,
      playTrack, togglePlay, stopMusic, setMusicEnabled, nextTrack,
    }}>
      {children}
    </MusicContext.Provider>
  );
}

export function useMusic() {
  return useContext(MusicContext);
}
