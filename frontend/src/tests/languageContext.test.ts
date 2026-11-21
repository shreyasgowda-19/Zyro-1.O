import { describe, it, expect } from 'vitest';
import en from '../i18n/en.json';
import hi from '../i18n/hi.json';
import { formatPaise } from '../types';

function translate(dict: Record<string, string>, key: string, params?: Record<string, any>): string {
  let template = dict[key] || key;
  if (params) {
    Object.keys(params).forEach((paramKey) => {
      let val = params[paramKey];
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
}

describe('Bilingual Translation and Parameter Interpolation (§15, D11)', () => {
  it('correctly interpolates R1 parameters in English', () => {
    const text = translate(en, 'risk.reason.R1', {
      multiple_x10: '3.5',
      avg_paise: 100000,
      sample_size: 10,
    });
    expect(text).toBe(
      'Unusual payment amount: 3.5x higher than your recent average of ₹1,000.00 (10 transactions evaluated).'
    );
  });

  it('correctly interpolates R1 parameters in Hindi', () => {
    const text = translate(hi, 'risk.reason.R1', {
      multiple_x10: '3.5',
      avg_paise: 100000,
      sample_size: 10,
    });
    expect(text).toBe(
      'असामान्य भुगतान राशि: आपके हाल के औसत ₹1,000.00 से 3.5 गुना अधिक (10 लेनदेन मूल्यांकित)।'
    );
  });

  it('correctly interpolates R9 balance drain in English and Hindi', () => {
    const enText = translate(en, 'risk.reason.R9', {
      share_pct: 85,
      amount_paise: 4250000,
      available_paise: 5000000,
    });
    expect(enText).toContain('85%');
    expect(enText).toContain('₹42,500.00');
    expect(enText).toContain('₹50,000.00');

    const hiText = translate(hi, 'risk.reason.R9', {
      share_pct: 85,
      amount_paise: 4250000,
      available_paise: 5000000,
    });
    expect(hiText).toContain('85%');
    expect(hiText).toContain('₹42,500.00');
    expect(hiText).toContain('₹50,000.00');
  });

  it('correctly interpolates what-if score breakdown string in English and Hindi', () => {
    const enText = translate(en, 'pay.without_signal', {
      without_score: 55,
      without_band: 'Medium',
    });
    expect(enText).toBe('Without this signal, your score would be 55 (Medium risk)');

    const hiText = translate(hi, 'pay.without_signal', {
      without_score: 55,
      without_band: 'मध्यम',
    });
    expect(hiText).toBe('इस संकेत के बिना, आपका स्कोर 55 (मध्यम जोखिम) होगा');
  });

  it('translates all alert strings cleanly with paise formatting', () => {
    const alertEn = translate(en, 'alert.fraud.held_notice', {
      amount_paise: 1500000,
    });
    expect(alertEn).toBe(
      'Payment of ₹15,000.00 paused for security review due to high risk signals.'
    );

    const alertHi = translate(hi, 'alert.fraud.held_notice', {
      amount_paise: 1500000,
    });
    expect(alertHi).toBe(
      'उच्च जोखिम संकेतों के कारण ₹15,000.00 का भुगतान सुरक्षा समीक्षा के लिए रोक दिया गया है।'
    );
  });
});
