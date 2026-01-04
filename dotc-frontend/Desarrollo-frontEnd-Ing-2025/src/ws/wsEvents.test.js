import { describe, it, expect } from 'vitest';
import { WSEVENTS } from './wsEvents.js';

describe('WSEVENTS', () => {
  it('is an array of strings', () => {
    expect(Array.isArray(WSEVENTS)).toBe(true);
    expect(WSEVENTS.length).toBeGreaterThan(0);
    for (const e of WSEVENTS) expect(typeof e).toBe('string');
  });

  it('contains representative event names', () => {
    const expected = [
      'CARD_PLAYED',
      'CARDS_PLAYED',
      'GAME_CREATED',
      'GAME_STARTED',
      'SECRET_REVEALED',
    ];
    for (const name of expected) {
      expect(WSEVENTS).toContain(name);
    }
  });

  it('has no duplicate entries', () => {
    const set = new Set(WSEVENTS);
    expect(set.size).toBe(WSEVENTS.length);
  });
});
