import { useCallback, useRef } from 'react';
import { Platform } from 'react-native';

// Sound types for the game
type SoundType = 'click' | 'success' | 'error' | 'coin' | 'purchase' | 'levelup' | 'notification' | 'sell';

// Web Audio API based sound generator - works on web and modern platforms
const createWebAudioContext = () => {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    const AudioCtx = (window as any).AudioContext || (window as any).webkitAudioContext;
    if (AudioCtx) return new AudioCtx();
  }
  return null;
};

// Sound configurations: frequency, duration, waveform, volume
const SOUND_CONFIGS: Record<SoundType, { notes: { freq: number; dur: number; delay: number }[]; wave: OscillatorType; vol: number }> = {
  click: {
    notes: [{ freq: 800, dur: 0.05, delay: 0 }],
    wave: 'sine',
    vol: 0.15,
  },
  success: {
    notes: [
      { freq: 523, dur: 0.12, delay: 0 },
      { freq: 659, dur: 0.12, delay: 0.12 },
      { freq: 784, dur: 0.2, delay: 0.24 },
    ],
    wave: 'sine',
    vol: 0.2,
  },
  error: {
    notes: [
      { freq: 300, dur: 0.15, delay: 0 },
      { freq: 200, dur: 0.25, delay: 0.15 },
    ],
    wave: 'sawtooth',
    vol: 0.12,
  },
  coin: {
    notes: [
      { freq: 987, dur: 0.08, delay: 0 },
      { freq: 1318, dur: 0.15, delay: 0.08 },
    ],
    wave: 'sine',
    vol: 0.18,
  },
  purchase: {
    notes: [
      { freq: 440, dur: 0.1, delay: 0 },
      { freq: 554, dur: 0.1, delay: 0.1 },
      { freq: 659, dur: 0.1, delay: 0.2 },
      { freq: 880, dur: 0.25, delay: 0.3 },
    ],
    wave: 'sine',
    vol: 0.2,
  },
  levelup: {
    notes: [
      { freq: 523, dur: 0.1, delay: 0 },
      { freq: 659, dur: 0.1, delay: 0.1 },
      { freq: 784, dur: 0.1, delay: 0.2 },
      { freq: 1047, dur: 0.3, delay: 0.3 },
    ],
    wave: 'triangle',
    vol: 0.25,
  },
  notification: {
    notes: [
      { freq: 880, dur: 0.1, delay: 0 },
      { freq: 1100, dur: 0.15, delay: 0.12 },
    ],
    wave: 'sine',
    vol: 0.15,
  },
  sell: {
    notes: [
      { freq: 880, dur: 0.08, delay: 0 },
      { freq: 1100, dur: 0.08, delay: 0.08 },
      { freq: 1320, dur: 0.08, delay: 0.16 },
      { freq: 1760, dur: 0.2, delay: 0.24 },
    ],
    wave: 'sine',
    vol: 0.2,
  },
};

export function useSounds() {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const enabledRef = useRef(true);

  const getCtx = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = createWebAudioContext();
    }
    // Resume if suspended (browser autoplay policy)
    if (audioCtxRef.current?.state === 'suspended') {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  }, []);

  const play = useCallback((type: SoundType) => {
    if (!enabledRef.current) return;

    try {
      const ctx = getCtx();
      if (!ctx) return;

      const config = SOUND_CONFIGS[type];
      if (!config) return;

      config.notes.forEach(note => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = config.wave;
        osc.frequency.value = note.freq;

        gain.gain.setValueAtTime(0, ctx.currentTime + note.delay);
        gain.gain.linearRampToValueAtTime(config.vol, ctx.currentTime + note.delay + 0.01);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + note.delay + note.dur);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(ctx.currentTime + note.delay);
        osc.stop(ctx.currentTime + note.delay + note.dur + 0.05);
      });
    } catch (e) {
      // Silently fail - sound is not critical
    }
  }, [getCtx]);

  const setEnabled = useCallback((enabled: boolean) => {
    enabledRef.current = enabled;
  }, []);

  return { play, setEnabled, enabled: enabledRef.current };
}
