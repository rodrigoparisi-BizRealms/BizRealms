/**
 * BizRealms - Sound Context
 * Provides UI click sound effects for buttons throughout the app.
 * Replaces the removed background music with lightweight interaction sounds.
 */
import React, { createContext, useContext, useRef, useEffect, useState, useCallback } from 'react';
import { Audio } from 'expo-av';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface SoundContextType {
  playClick: () => void;
  playSuccess: () => void;
  playError: () => void;
  playCoin: () => void;
  soundEnabled: boolean;
  toggleSound: () => void;
}

const SoundContext = createContext<SoundContextType>({
  playClick: () => {},
  playSuccess: () => {},
  playError: () => {},
  playCoin: () => {},
  soundEnabled: true,
  toggleSound: () => {},
});

/**
 * Generate a short beep/click sound programmatically using expo-av.
 * We create Audio buffers inline so no external sound files are needed.
 */
function generateWav(
  frequency: number,
  duration: number,
  volume: number = 0.3,
  sampleRate: number = 22050
): string {
  const numSamples = Math.floor(sampleRate * duration);
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = sampleRate * numChannels * (bitsPerSample / 8);
  const blockAlign = numChannels * (bitsPerSample / 8);
  const dataSize = numSamples * blockAlign;
  const headerSize = 44;
  const totalSize = headerSize + dataSize;

  const buffer = new ArrayBuffer(totalSize);
  const view = new DataView(buffer);

  // RIFF header
  writeString(view, 0, 'RIFF');
  view.setUint32(4, totalSize - 8, true);
  writeString(view, 8, 'WAVE');

  // fmt chunk
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true); // chunk size
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);

  // data chunk
  writeString(view, 36, 'data');
  view.setUint32(40, dataSize, true);

  // Generate samples
  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    // Envelope: quick attack, fast decay
    const envelope = Math.exp(-t * 20) * volume;
    const sample = Math.sin(2 * Math.PI * frequency * t) * envelope;
    const intSample = Math.max(-32768, Math.min(32767, Math.floor(sample * 32767)));
    view.setInt16(headerSize + i * 2, intSample, true);
  }

  // Convert to base64
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return 'data:audio/wav;base64,' + btoa(binary);
}

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

// Pre-defined sound parameters
const SOUNDS = {
  click: { frequency: 1200, duration: 0.06, volume: 0.15 },
  success: { frequency: 880, duration: 0.12, volume: 0.2 },
  error: { frequency: 300, duration: 0.15, volume: 0.15 },
  coin: { frequency: 1500, duration: 0.08, volume: 0.2 },
};

export function SoundProvider({ children }: { children: React.ReactNode }) {
  const [soundEnabled, setSoundEnabled] = useState(true);
  const soundsRef = useRef<Record<string, Audio.Sound | null>>({
    click: null,
    success: null,
    error: null,
    coin: null,
  });
  const loadedRef = useRef(false);

  useEffect(() => {
    loadPreference();
    if (Platform.OS !== 'web') {
      Audio.setAudioModeAsync({
        playsInSilentModeIOS: false,
        staysActiveInBackground: false,
        shouldDuckAndroid: true,
      }).catch(() => {});
    }
    loadSounds();

    return () => {
      Object.values(soundsRef.current).forEach(sound => {
        if (sound) sound.unloadAsync().catch(() => {});
      });
    };
  }, []);

  const loadPreference = async () => {
    try {
      const val = await AsyncStorage.getItem('sound_enabled');
      if (val !== null) setSoundEnabled(val === 'true');
    } catch {}
  };

  const loadSounds = async () => {
    if (loadedRef.current) return;
    loadedRef.current = true;

    try {
      for (const [key, params] of Object.entries(SOUNDS)) {
        const uri = generateWav(params.frequency, params.duration, params.volume);
        const { sound } = await Audio.Sound.createAsync(
          { uri },
          { shouldPlay: false, volume: params.volume }
        );
        soundsRef.current[key] = sound;
      }
    } catch (e) {
      console.log('Sound loading skipped:', e);
    }
  };

  const playSound = useCallback(async (key: string) => {
    if (!soundEnabled) return;
    try {
      const sound = soundsRef.current[key];
      if (sound) {
        await sound.setPositionAsync(0);
        await sound.playAsync();
      }
    } catch {
      // Silently fail - sounds are non-critical
    }
  }, [soundEnabled]);

  const playClick = useCallback(() => playSound('click'), [playSound]);
  const playSuccess = useCallback(() => playSound('success'), [playSound]);
  const playError = useCallback(() => playSound('error'), [playSound]);
  const playCoin = useCallback(() => playSound('coin'), [playSound]);

  const toggleSound = useCallback(async () => {
    const newState = !soundEnabled;
    setSoundEnabled(newState);
    await AsyncStorage.setItem('sound_enabled', newState ? 'true' : 'false');
  }, [soundEnabled]);

  return (
    <SoundContext.Provider value={{ playClick, playSuccess, playError, playCoin, soundEnabled, toggleSound }}>
      {children}
    </SoundContext.Provider>
  );
}

export const useSound = () => useContext(SoundContext);
