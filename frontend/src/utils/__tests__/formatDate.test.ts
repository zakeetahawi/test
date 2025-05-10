import { describe, it, expect } from 'vitest';
import { formatDate } from '../formatDate';

describe('formatDate', () => {
  it('formats date correctly', () => {
    const date = new Date('2025-05-06');
    expect(formatDate(date)).toBe('2025-05-06');
  });

  it('handles invalid date', () => {
    expect(formatDate(null)).toBe('');
  });
});