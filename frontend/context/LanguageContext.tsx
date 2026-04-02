import React, { createContext, useContext, useState, useCallback } from 'react';
import i18n, { LANGUAGES } from '../i18n';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface LanguageContextType {
  locale: string;
  setLocale: (code: string) => void;
  t: (scope: string, options?: object) => string;
  languages: typeof LANGUAGES;
}

const LanguageContext = createContext<LanguageContextType>({
  locale: 'pt',
  setLocale: () => {},
  t: (scope: string) => scope,
  languages: LANGUAGES,
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState(i18n.locale);

  const setLocale = useCallback(async (code: string) => {
    i18n.locale = code;
    setLocaleState(code);
    try {
      await AsyncStorage.setItem('@app_language', code);
    } catch (e) {
      console.error('Failed to save language:', e);
    }
  }, []);

  // Load saved language on mount
  React.useEffect(() => {
    AsyncStorage.getItem('@app_language').then(saved => {
      if (saved && ['pt', 'en', 'es', 'de', 'fr', 'it'].includes(saved)) {
        i18n.locale = saved;
        setLocaleState(saved);
      }
    }).catch(() => {});
  }, []);

  const t = useCallback((scope: string, options?: object) => {
    return i18n.t(scope, options);
  }, [locale]);

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t, languages: LANGUAGES }}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => useContext(LanguageContext);
