import { describe, it, expect } from 'vitest';
import { formatPaise } from '../types';

describe('formatPaise', () => {
  it('formats 100 paise as ₹1.00', () => {
    expect(formatPaise(100)).toBe('₹1.00');
  });

  it('formats zero paise as ₹0.00', () => {
    expect(formatPaise(0)).toBe('₹0.00');
  });

  it('formats Indian grouping correctly: ₹50,000.00 (5000000 paise)', () => {
    expect(formatPaise(5000000)).toBe('₹50,000.00');
  });

  it('formats Indian grouping correctly: ₹2,00,000.00 (20000000 paise)', () => {
    expect(formatPaise(20000000)).toBe('₹2,00,000.00');
  });

  it('formats Indian grouping correctly: ₹10,00,000.00 (100000000 paise)', () => {
    expect(formatPaise(100000000)).toBe('₹10,00,000.00');
  });

  it('formats single rupee amounts without decimals when requested', () => {
    expect(formatPaise(350000, false)).toBe('₹3,500');
  });

  it('formats fractional paise amounts: 95 paise as ₹0.95', () => {
    expect(formatPaise(95)).toBe('₹0.95');
  });

  it('formats negative balances cleanly with -₹', () => {
    expect(formatPaise(-25000)).toBe('-₹250.00');
  });
});
