import React, { createContext, useContext, useState, ReactNode } from 'react';

interface Playlist {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  category: string;
  youtubeId: string;
  spotifyUrl?: string;
  youtubeMusicUrl?: string;
}

interface MusicContextType {
  activePlaylist: Playlist | null;
  isPlaying: boolean;
  playPlaylist: (playlist: Playlist) => void;
  stopMusic: () => void;
}

const MusicContext = createContext<MusicContextType>({
  activePlaylist: null,
  isPlaying: false,
  playPlaylist: () => {},
  stopMusic: () => {},
});

export function MusicProvider({ children }: { children: ReactNode }) {
  const [activePlaylist, setActivePlaylist] = useState<Playlist | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const playPlaylist = (playlist: Playlist) => {
    setActivePlaylist(playlist);
    setIsPlaying(true);
  };

  const stopMusic = () => {
    setIsPlaying(false);
    setActivePlaylist(null);
  };

  return (
    <MusicContext.Provider value={{ activePlaylist, isPlaying, playPlaylist, stopMusic }}>
      {children}
    </MusicContext.Provider>
  );
}

export function useMusic() {
  return useContext(MusicContext);
}
