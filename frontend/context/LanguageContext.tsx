import React, { createContext, useContext, useState, useCallback } from 'react';
import i18n, { LANGUAGES } from '../i18n';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getLocales } from 'expo-localization';

const CURRENCY_CONFIG: Record<string, { symbol: string; code: string; locale: string; separator: string; decimal: string }> = {
  pt: { symbol: '$', code: 'USD', locale: 'en-US', separator: ',', decimal: '.' },
  en: { symbol: '$', code: 'USD', locale: 'en-US', separator: ',', decimal: '.' },
  es: { symbol: '$', code: 'USD', locale: 'en-US', separator: ',', decimal: '.' },
  de: { symbol: '$', code: 'USD', locale: 'en-US', separator: ',', decimal: '.' },
  fr: { symbol: '$', code: 'USD', locale: 'en-US', separator: ',', decimal: '.' },
  it: { symbol: '$', code: 'USD', locale: 'en-US', separator: ',', decimal: '.' },
  zh: { symbol: '$', code: 'USD', locale: 'en-US', separator: ',', decimal: '.' },
};

interface LanguageContextType {
  locale: string;
  setLocale: (code: string) => void;
  t: (scope: string, options?: object) => string;
  languages: typeof LANGUAGES;
  formatMoney: (value: number, compact?: boolean) => string;
  currencySymbol: string;
}

const LanguageContext = createContext<LanguageContextType>({
  locale: 'pt',
  setLocale: () => {},
  t: (scope: string) => scope,
  languages: LANGUAGES,
  formatMoney: (v: number) => `$ ${v}`,
  currencySymbol: '$',
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

  const SUPPORTED_LOCALES = ['pt', 'en', 'es', 'de', 'fr', 'it'];

  // Detect device locale
  const getDeviceLocale = (): string => {
    try {
      const locales = getLocales();
      if (locales && locales.length > 0) {
        const deviceLang = locales[0].languageCode || '';
        if (SUPPORTED_LOCALES.includes(deviceLang)) return deviceLang;
      }
    } catch (e) {
      console.log('Could not detect device locale:', e);
    }
    return 'en'; // default fallback
  };

  // Load saved language on mount, or auto-detect from device
  React.useEffect(() => {
    AsyncStorage.getItem('@app_language').then(saved => {
      if (saved && SUPPORTED_LOCALES.includes(saved)) {
        i18n.locale = saved;
        setLocaleState(saved);
      } else {
        // First time: auto-detect from device
        const detected = getDeviceLocale();
        i18n.locale = detected;
        setLocaleState(detected);
        AsyncStorage.setItem('@app_language', detected);
      }
    }).catch(() => {});
  }, []);

  const t = useCallback((scope: string, options?: object) => {
    return i18n.t(scope, options);
  }, [locale]);

  const currencySymbol = CURRENCY_CONFIG[locale]?.symbol || 'R$';

  const formatMoney = useCallback((value: number, compact?: boolean) => {
    const cfg = CURRENCY_CONFIG[locale] || CURRENCY_CONFIG.pt;
    if (compact) {
      if (value >= 1_000_000) return `${cfg.symbol} ${(value / 1_000_000).toFixed(1)}M`;
      if (value >= 1_000) return `${cfg.symbol} ${(value / 1_000).toFixed(1)}K`;
    }
    try {
      const formatted = value.toLocaleString(cfg.locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      return `${cfg.symbol} ${formatted}`;
    } catch {
      return `${cfg.symbol} ${value.toFixed(2)}`;
    }
  }, [locale]);

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t, languages: LANGUAGES, formatMoney, currencySymbol }}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => useContext(LanguageContext);
