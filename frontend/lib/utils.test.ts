import { describe, it, expect } from 'vitest';
import { formatProb, formatXg, formatKickoff, groupBy } from './utils';

describe('formatProb', () => {
  it('formats a probability as a rounded percent', () => {
    expect(formatProb(0.54)).toBe('54%');
    expect(formatProb(0.5)).toBe('50%');
    expect(formatProb(0)).toBe('0%');
  });
  it('returns em dash for null/undefined', () => {
    expect(formatProb(null)).toBe('—');
    expect(formatProb(undefined)).toBe('—');
  });
});

describe('formatXg', () => {
  it('formats with two decimals', () => {
    expect(formatXg(2.103)).toBe('2.10');
    expect(formatXg(0)).toBe('0.00');
  });
  it('returns em dash for null', () => {
    expect(formatXg(null)).toBe('—');
  });
});

describe('formatKickoff', () => {
  it('parses an ISO timestamp', () => {
    const result = formatKickoff('2026-05-23T12:30:00Z');
    expect(result.weekday).toBeTruthy();
    expect(result.date).toBeTruthy();
    expect(result.time).toBeTruthy();
    expect(result.full).toContain(result.weekday);
  });
});

describe('groupBy', () => {
  it('groups items by key', () => {
    const items = [
      { type: 'a', n: 1 },
      { type: 'a', n: 2 },
      { type: 'b', n: 3 },
    ];
    const grouped = groupBy(items, (i) => i.type);
    expect(grouped.a).toHaveLength(2);
    expect(grouped.b).toHaveLength(1);
  });
});
