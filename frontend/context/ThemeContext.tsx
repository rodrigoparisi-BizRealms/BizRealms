/**
 * BizRealms - Theme Context
 * Provides dark/light theme toggle with persistence.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const THEME_KEY = '@bizrealms_theme';

export interface ThemeColors {
  background: string;
  surface: string;
  card: string;
  cardBorder: string;
  text: string;
  textSecondary: string;
  textMuted: string;
  accent: string;
  accentLight: string;
  divider: string;
  inputBg: string;
  inputBorder: string;
  tabBar: string;
  tabBarBorder: string;
  headerBg: string;
  modalOverlay: string;
  modalBg: string;
  success: string;
  warning: string;
  danger: string;
  gold: string;
}

const darkColors: ThemeColors = {
  background: '#121212',
  surface: '#1a1a1a',
  card: '#1e1e1e',
  cardBorder: '#2a2a2a',
  text: '#ffffff',
  textSecondary: '#aaaaaa',
  textMuted: '#666666',
  accent: '#4CAF50',
  accentLight: '#1a3a1a',
  divider: '#2a2a2a',
  inputBg: '#2a2a2a',
  inputBorder: '#3a3a3a',
  tabBar: '#1a1a1a',
  tabBarBorder: '#2a2a2a',
  headerBg: '#1a1a1a',
  modalOverlay: 'rgba(0,0,0,0.85)',
  modalBg: '#1e1e1e',
  success: '#4CAF50',
  warning: '#FF9800',
  danger: '#F44336',
  gold: '#FFD700',
};

const lightColors: ThemeColors = {
  background: '#F2F3F5',
  surface: '#FFFFFF',
  card: '#FFFFFF',
  cardBorder: '#E0E0E0',
  text: '#1A1A2E',
  textSecondary: '#555555',
  textMuted: '#999999',
  accent: '#2E7D32',
  accentLight: '#E8F5E9',
  divider: '#E0E0E0',
  inputBg: '#F5F5F5',
  inputBorder: '#D0D0D0',
  tabBar: '#FFFFFF',
  tabBarBorder: '#E0E0E0',
  headerBg: '#FFFFFF',
  modalOverlay: 'rgba(0,0,0,0.5)',
  modalBg: '#FFFFFF',
  success: '#2E7D32',
  warning: '#E65100',
  danger: '#C62828',
  gold: '#F9A825',
};

interface ThemeContextType {
  isDark: boolean;
  colors: ThemeColors;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType>({
  isDark: true,
  colors: darkColors,
  toggleTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    AsyncStorage.getItem(THEME_KEY).then(val => {
      if (val !== null) setIsDark(val === 'dark');
    }).catch(() => {});
  }, []);

  const toggleTheme = useCallback(() => {
    setIsDark(prev => {
      const next = !prev;
      AsyncStorage.setItem(THEME_KEY, next ? 'dark' : 'light');
      return next;
    });
  }, []);

  const colors = isDark ? darkColors : lightColors;

  return (
    <ThemeContext.Provider value={{ isDark, colors, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
