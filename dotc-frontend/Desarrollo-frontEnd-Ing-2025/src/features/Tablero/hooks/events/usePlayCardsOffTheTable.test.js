import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
vi.mock('../../tableroService.js', () => ({
  playCardsOffTheTable: vi.fn(async () => ({ ok: true })),
}));
import { playCardsOffTheTable } from '../../tableroService.js';
import { usePlayCardsOffTheTable } from './usePlayCardsOffTheTable.js';

describe('usePlayCardsOffTheTable', () => {
  it('requiere targetPlayerId', async () => {
    const { result } = renderHook(() => usePlayCardsOffTheTable({ gameId: 1, playerId: 2 }));
    let ok;
    await act(async () => {
      ok = await result.current.playCardsEvent(10, null);
    });
    expect(ok).toBe(false);
    expect(result.current.error).toMatch(/Debes seleccionar/);
  });

  it('éxito', async () => {
    const { result } = renderHook(() => usePlayCardsOffTheTable({ gameId: 1, playerId: 2 }));
    let ok;
    await act(async () => {
      ok = await result.current.playCardsEvent(10, 99);
    });
    expect(ok).toBe(true);
    expect(playCardsOffTheTable).toHaveBeenCalledWith(1, 99, 10, 2);
  });

  it('error servicio', async () => {
    playCardsOffTheTable.mockRejectedValueOnce(new Error('fallo'));
    const { result } = renderHook(() => usePlayCardsOffTheTable({ gameId: 7, playerId: 3 }));
    let ok;
    await act(async () => {
      ok = await result.current.playCardsEvent(5, 8);
    });
    expect(ok).toBe(false);
    expect(result.current.error).toBe('fallo');
  });
});