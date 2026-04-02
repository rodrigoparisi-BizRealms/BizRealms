import React, { createContext, useContext, useState, useCallback } from 'react';
import i18n, { LANGUAGES } from '../i18n';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CURRENCY_CONFIG: Record<string, { symbol: string; code: string; locale: string; separator: string; decimal: string }> = {
  pt: { symbol: 'R$', code: 'BRL', locale: 'pt-BR', separator: '.', decimal: ',' },
  en: { symbol: '$', code: 'USD', locale: 'en-US', separator: ',', decimal: '.' },
  es: { symbol: '€', code: 'EUR', locale: 'es-ES', separator: '.', decimal: ',' },
  de: { symbol: '€', code: 'EUR', locale: 'de-DE', separator: '.', decimal: ',' },
  fr: { symbol: '€', code: 'EUR', locale: 'fr-FR', separator: ' ', decimal: ',' },
  it: { symbol: '€', code: 'EUR', locale: 'it-IT', separator: '.', decimal: ',' },
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
  formatMoney: (v: number) => `R$ ${v}`,
  currencySymbol: 'R$',
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
