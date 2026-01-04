import { describe, it, expect } from 'vitest';
import { normalizeGameOverEvent } from './gameOverAdapter.js';

describe('normalizeGameOverEvent', () => {
  const players = [
    { player_id: 1, player_name: 'Alice' },
    { player_id: 2, player_name: 'Bob' },
    { player_id: 3, player_name: 'Carol' },
  ];

  it('SECRET_REVEALED MURDERER => INNOCENTS_WIN', () => {
    const res = normalizeGameOverEvent({ event: 'SECRET_REVEALED', role: 'MURDERER', player_id: 2 }, players);
    expect(res.reason).toBe('INNOCENTS_WIN');
    expect(res.murderer).toEqual({ player_id: 2, name: 'Bob' });
    expect(res.innocents.map(p => p.player_id)).toEqual([1, 3]);
  });

  it('GAME_OVER passthrough', () => {
    const payload = {
      event: 'GAME_OVER',
      reason: 'DECK_EMPTY',
      murderer: { player_id: 9, name: 'X' },
      accomplice: { player_id: 10, name: 'Y' },
      innocents: [{ player_id: 11 }],
    };
    const res = normalizeGameOverEvent(payload, players);
    expect(res).toEqual({
      reason: 'DECK_EMPTY',
      murderer: payload.murderer,
      accomplice: payload.accomplice,
      innocents: payload.innocents,
    });
  });

  it('other payload => null', () => {
    expect(normalizeGameOverEvent({ foo: 1 }, players)).toBeNull();
  });
});