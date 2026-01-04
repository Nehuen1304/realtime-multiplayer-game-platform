import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCardLook } from '../player/useCardLook.js';

vi.mock('../../tableroService.js', () => ({
  selectCardLook: vi.fn(async () => ({ ok: true })),
  getManoJugador: vi.fn(async () => ({ cards: [{ card_id: 1 }] })),
}));

const { selectCardLook, getManoJugador } = await import('../../tableroService.js');

describe('useCardLook', () => {
  const gameId = 3;
  const playerId = 11;
  const setMano = vi.fn();

  beforeEach(() => {
    setMano.mockClear();
    selectCardLook.mockClear();
    getManoJugador.mockClear();
  });

  it('onCardLook guarda cartas ofrecidas', () => {
    const { result } = renderHook(() => useCardLook({ gameId, playerId, setMano }));
    act(() => {
      result.current.onCardLook({ cards: [{ card_id: 7 }, { card_id: 8 }] });
    });
    expect(result.current.cardsLook).toHaveLength(2);
  });

  it('toggleCardLook activa/desactiva selección', () => {
    const { result } = renderHook(() => useCardLook({ gameId, playerId, setMano }));
    act(() => {
      result.current.toggleCardLook(10);
    });
    expect(result.current.cardLookSelect).toBe(10);
    act(() => {
      result.current.toggleCardLook(10);
    });
    expect(result.current.cardLookSelect).toBeNull();
  });

  it('confirmCardLook postea selección y refresca mano', async () => {
    const { result } = renderHook(() => useCardLook({ gameId, playerId, setMano }));
    act(() => {
      result.current.onCardLook({ cards: [{ card_id: 10 }] });
      result.current.toggleCardLook(10);
    });

    await act(async () => {
      await result.current.confirmCardLook();
    });

    expect(selectCardLook).toHaveBeenCalledWith(gameId, {
      player_id: playerId,
      game_id: gameId,
      source: 'discard',
      card_id: 10,
    });
    expect(getManoJugador).toHaveBeenCalledWith(gameId, playerId);
    expect(setMano).toHaveBeenCalledWith([{ card_id: 1 }]);
    expect(result.current.cardsLook).toEqual([]);
    expect(result.current.cardLookSelect).toBeNull();
  });
});
