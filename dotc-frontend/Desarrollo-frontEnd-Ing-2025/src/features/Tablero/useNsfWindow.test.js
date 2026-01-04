import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

vi.useFakeTimers();

// Mock the service used by the hook
vi.mock('./tableroService.js', () => ({
  playNSF: vi.fn(async () => ({ ok: true }))
}));

import { playNSF } from './tableroService.js';
import { useNsfWindow } from './useNsfWindow.js';

const gameId = 1;
const playerId = 10;

describe('useNsfWindow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    // ensure timers are cleared between tests
    vi.runOnlyPendingTimers();
    vi.clearAllTimers();
  });

  it('abre ventana, inicia conteo y hace auto-pass al llegar a 0', async () => {
    const { result } = renderHook(() => useNsfWindow({ gameId, playerId }));

    // Abrir ventana NSF por 5s
    act(() => {
      result.current.openWindow({ actionId: 'a1', playedBy: 99, expiresAt: Date.now() + 5000 });
    });

    // Debe estar abierta y remainingMs > 0
    expect(result.current.nsfWindow.open).toBe(true);
    expect(result.current.nsfWindow.remainingMs).toBeGreaterThan(0);

    // Avanzar 5s de timer
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    // Auto-pass debe haberse enviado una vez
    expect(playNSF).toHaveBeenCalledTimes(1);
    const [calledGameId, body] = playNSF.mock.calls[0];
    expect(calledGameId).toBe(gameId);
    expect(body).toMatchObject({
      player_id: playerId,
      game_id: gameId,
      action_type: 'PLAY_EVENT',
      card_ids: []
    });
    expect(typeof body.action_id).toBe('string');
    // alreadyResponded true después del auto-pass
    expect(result.current.nsfWindow.alreadyResponded).toBe(true);
  });

  it('reinicia el timer y alreadyResponded al recibir una nueva ventana', () => {
    const { result } = renderHook(() => useNsfWindow({ gameId, playerId }));

    // Abrir y dejar correr 2s
    act(() => {
      result.current.openWindow({ actionId: 'a1', playedBy: 2, expiresAt: Date.now() + 5000 });
    });
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    const remainingAfter2s = result.current.nsfWindow.remainingMs;
    expect(remainingAfter2s).toBeLessThan(5000);

    // Nueva NSF (reinicia a 5s)
    act(() => {
      result.current.openWindow({ actionId: 'a2', playedBy: 3, expiresAt: Date.now() + 5000 });
    });

    // Debe volver a ~5s
    expect(result.current.nsfWindow.remainingMs).toBeGreaterThan(4500);
    // Y alreadyResponded debe resetearse a false
    expect(result.current.nsfWindow.alreadyResponded).toBe(false);
  });
});
