import React, { createContext, useContext, useState, ReactNode } from 'react';

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

interface MusicContextType {
  activeTrack: Track | null;
  isPlaying: boolean;
  playTrack: (track: Track) => void;
  togglePlay: () => void;
  stopMusic: () => void;
}

const MusicContext = createContext<MusicContextType>({
  activeTrack: null,
  isPlaying: false,
  playTrack: () => {},
  togglePlay: () => {},
  stopMusic: () => {},
});

export function MusicProvider({ children }: { children: ReactNode }) {
  const [activeTrack, setActiveTrack] = useState<Track | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const playTrack = (track: Track) => {
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
  };

  return (
    <MusicContext.Provider value={{ activeTrack, isPlaying, playTrack, togglePlay, stopMusic }}>
      {children}
    </MusicContext.Provider>
  );
}

export function useMusic() {
  return useContext(MusicContext);
}
