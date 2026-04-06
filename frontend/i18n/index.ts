import { I18n } from 'i18n-js';
import * as Localization from 'expo-localization';
import pt from './translations/pt';
import en from './translations/en';
import es from './translations/es';
import de from './translations/de';
import fr from './translations/fr';
import it from './translations/it';
import zh from './translations/zh';

const i18n = new I18n({ pt, en, es, de, fr, it, zh });

// Auto-detect device language
const deviceLang = Localization.getLocales()?.[0]?.languageCode || 'pt';
i18n.locale = ['pt', 'en', 'es', 'de', 'fr', 'it', 'zh'].includes(deviceLang) ? deviceLang : 'pt';
i18n.enableFallback = true;
i18n.defaultLocale = 'pt';

export const LANGUAGES = [
  { code: 'pt', name: 'Português', flag: '🇧🇷' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
];

export default i18n;
