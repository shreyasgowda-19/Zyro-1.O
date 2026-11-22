import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import enTranslations from '../i18n/en.json';
import hiTranslations from '../i18n/hi.json';
import knTranslations from '../i18n/kn.json';
import hiInsights from '../i18n/hi_insights.json';
import knInsights from '../i18n/kn_insights.json';
import { formatPaise } from '../types';

export type Language = 'en' | 'hi' | 'kn';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, params?: Record<string, any>) => string;
  translateText: (text: string) => string;
}

const dictionaries: Record<Language, Record<string, string>> = {
  en: enTranslations,
  hi: { ...hiTranslations, ...hiInsights },
  kn: { ...knTranslations, ...knInsights },
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const originalTextNodes = useRef(new WeakMap<Text, { source: string; rendered: string }>());
  const originalAttributes = useRef(new WeakMap<Element, Map<string, { source: string; rendered: string }>>());
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('payguard_lang');
    return saved === 'hi' || saved === 'kn' ? saved : 'en';
  });

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

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

  const englishTextKeys = new Map(Object.entries(enTranslations).map(([key, value]) => [value, key]));
  const translateText = (text: string): string => {
    const normalized = text.replace(/\s+/g, ' ').trim();
    const key = englishTextKeys.get(normalized);
    if (!key) return text;
    const translation = dictionaries[language][key];
    if (!translation || translation === normalized) return text;
    const leading = text.match(/^\s*/)?.[0] || '';
    const trailing = text.match(/\s*$/)?.[0] || '';
    return `${leading}${translation}${trailing}`;
  };

  useEffect(() => {
    const root = document.getElementById('root');
    if (!root) return;

    const translateTextNode = (node: Node) => {
      if (node.nodeType !== Node.TEXT_NODE) return;
      const textNode = node as Text;
      const parent = textNode.parentElement;
      if (!parent || parent.closest('script, style, textarea, input, select, option, code, pre, [contenteditable="true"]')) return;
      let record = originalTextNodes.current.get(textNode);
      if (!record) {
        record = { source: textNode.data, rendered: textNode.data };
        originalTextNodes.current.set(textNode, record);
      } else if (textNode.data !== record.rendered) {
        record.source = textNode.data;
      }
      const translated = translateText(record.source);
      record.rendered = translated;
      if (textNode.data !== translated) textNode.data = translated;
    };

    const translateAttributes = (element: Element) => {
      const names = ['placeholder', 'title', 'aria-label', 'alt'];
      let originals = originalAttributes.current.get(element);
      if (!originals) {
        originals = new Map<string, { source: string; rendered: string }>();
        originalAttributes.current.set(element, originals);
      }
      names.forEach((name) => {
        const current = element.getAttribute(name);
        if (current === null) return;
        let record = originals!.get(name);
        if (!record) {
          record = { source: current, rendered: current };
          originals!.set(name, record);
        } else if (current !== record.rendered) {
          record.source = current;
        }
        const translated = translateText(record.source);
        record.rendered = translated;
        if (current !== translated) element.setAttribute(name, translated);
      });
    };

    const translateSubtree = (node: Node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        translateTextNode(node);
        return;
      }
      if (node.nodeType !== Node.ELEMENT_NODE) return;
      const element = node as Element;
      translateAttributes(element);
      const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
      let textNode: Node | null;
      while ((textNode = walker.nextNode())) translateTextNode(textNode);
      element.querySelectorAll('*').forEach(translateAttributes);
    };

    translateSubtree(root);
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'characterData') translateTextNode(mutation.target);
        mutation.addedNodes.forEach(translateSubtree);
        if (mutation.type === 'attributes') translateAttributes(mutation.target as Element);
      });
    });
    observer.observe(root, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['placeholder', 'title', 'aria-label', 'alt'] });
    return () => observer.disconnect();
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, translateText }}>
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
