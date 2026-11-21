import { describe, it, expect } from 'vitest';
import en from '../i18n/en.json';
import hi from '../i18n/hi.json';

describe('i18n Key and Placeholder Parity (§15, D11)', () => {
  const enKeys = Object.keys(en);
  const hiKeys = Object.keys(hi);

  it('en.json and hi.json must have the identical set of keys', () => {
    const missingInHi = enKeys.filter((k) => !hiKeys.includes(k));
    const extraInHi = hiKeys.filter((k) => !enKeys.includes(k));

    expect(missingInHi, `Keys present in en.json but missing in hi.json: ${missingInHi.join(', ')}`).toEqual([]);
    expect(extraInHi, `Keys present in hi.json but extra: ${extraInHi.join(', ')}`).toEqual([]);
  });

  it('all parameter placeholders {param} must match exactly between en.json and hi.json', () => {
    const placeholderRegex = /\{([a-zA-Z0-9_]+)\}/g;

    const extractPlaceholders = (text: string): string[] => {
      const matches: string[] = [];
      let m;
      while ((m = placeholderRegex.exec(text)) !== null) {
        matches.push(m[1]);
      }
      return matches.sort();
    };

    enKeys.forEach((key) => {
      const enText = (en as Record<string, string>)[key];
      const hiText = (hi as Record<string, string>)[key];

      const enPlaceholders = extractPlaceholders(enText);
      const hiPlaceholders = extractPlaceholders(hiText);

      expect(
        hiPlaceholders,
        `Placeholder mismatch for key '${key}'. Expected [${enPlaceholders.join(', ')}], got [${hiPlaceholders.join(', ')}]`
      ).toEqual(enPlaceholders);
    });
  });
});
