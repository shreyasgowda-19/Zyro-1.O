import React, { createContext, useContext, useState } from 'react';
import enTranslations from '../i18n/en.json';
import hiTranslations from '../i18n/hi.json';
import { formatPaise } from '../types';

export type Language = 'en' | 'hi';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, params?: Record<string, any>) => string;
}

const dictionaries: Record<Language, Record<string, string>> = {
  en: enTranslations,
  hi: hiTranslations,
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('payguard_lang');
    return saved === 'hi' ? 'hi' : 'en';
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('payguard_lang', lang);
  };

  const t = (key: string, params?: Record<string, any>): string => {
    const dict = dictionaries[language] || dictionaries.en;
    let template = dict[key] || dictionaries.en[key] || key;

    if (params) {
      Object.keys(params).forEach((paramKey) => {
        let val = params[paramKey];
        // Automatically format paise numbers nicely if name ends in _paise
        if (paramKey.endsWith('_paise') && typeof val === 'number') {
          val = formatPaise(val);
        }
        if (Array.isArray(val)) {
          val = val.join(', ');
        }
        template = template.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), String(val));
      });
    }

    return template;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
