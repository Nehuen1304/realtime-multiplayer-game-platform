import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSetManagement } from '../sets/useSetManagement.js';

vi.mock('../../tableroService.js', () => ({
  getManoJugador: vi.fn(async () => ({ cards: [{ card_id: 9 }] })),
}));

const { getManoJugador } = await import('../../tableroService.js');

describe('useSetManagement', () => {
  const setMano = vi.fn();
  const gameId = 1;
  const playerId = 7;
  let opponentsDetailsById = {};
  const setOpponentsDetailsById = vi.fn(updater => {
    const next = typeof updater === 'function' ? updater(opponentsDetailsById) : updater;
    opponentsDetailsById = next;
  });

  // Mocks for upsertOpponentSet and removeOpponentSet
  const upsertOpponentSet = vi.fn();
  const removeOpponentSet = vi.fn();

  beforeEach(() => {
    setMano.mockClear();
    getManoJugador.mockClear();
    opponentsDetailsById = {};
    setOpponentsDetailsById.mockClear();
    upsertOpponentSet.mockClear();
    removeOpponentSet.mockClear();
  });

  it('refresca mano si se juega un evento especial', async () => {
    const { result } = renderHook(() => useSetManagement({ gameId, playerId, setMano, upsertOpponentSet, removeOpponentSet }));
    const specialPayload = {
      player_id: playerId,
      cards_played: [{ card_type: 'Another Victim' }],
    };

    await act(async () => {
      await result.current.onSetPlayed(specialPayload);
    });

    expect(getManoJugador).toHaveBeenCalledWith(gameId, playerId);
    expect(setMano).toHaveBeenCalledWith([{ card_id: 9 }]);
    expect(result.current.setsPropios).toEqual([]);
  });

  it('agrega a setsPropios cuando yo juego un set no especial', async () => {
    const { result } = renderHook(() => useSetManagement({ gameId, playerId, setMano, upsertOpponentSet, removeOpponentSet }));
    const payload = {
      player_id: playerId,
      cards_played: [{ card_type: 'Ariadne Oliver', set_id: 123 }],
    };

    await act(async () => {
      await result.current.onSetPlayed(payload);
    });

    expect(result.current.setsPropios.length).toBe(1);
    expect(result.current.setsPropios[0][0].set_id).toBe(123);
  });

  it('maneja onSetStolen agregando si soy ladrón y quitando si soy víctima', async () => {
    const { result } = renderHook(() => useSetManagement({ gameId, playerId, setMano, upsertOpponentSet, removeOpponentSet }));
    await act(async () => {
      await result.current.onSetPlayed({ player_id: playerId, cards_played: [{ set_id: 99, card_type: 'Ariadne Oliver' }] });
    });
    expect(result.current.setsPropios.length).toBe(1);

    act(() => {
      result.current.onSetStolen({ thief_id: 3, victim_id: playerId, set_id: 99 });
    });
    expect(result.current.setsPropios.length).toBe(0);

    act(() => {
      result.current.onSetStolen({ thief_id: playerId, victim_id: 4, set_id: 77, set_cards: [{ set_id: 77 }] });
    });
    expect(result.current.setsPropios.length).toBe(1);
    expect(result.current.setsPropios[0][0].set_id).toBe(77);
  });

  it('llama upsertOpponentSet cuando un oponente juega un set', async () => {
    const opponentId = 99;
    const playedSet = [{ set_id: 555, card_type: 'Poirot' }];
    const { result } = renderHook(() => useSetManagement({ gameId, playerId, setMano, upsertOpponentSet, removeOpponentSet }));

    await act(async () => {
      await result.current.onSetPlayed({ player_id: opponentId, cards_played: playedSet });
    });

    expect(upsertOpponentSet).toHaveBeenCalledWith(opponentId, playedSet);
  });

  it('no agrega set propio si payload.cards_played está vacío', async () => {
    const { result } = renderHook(() => useSetManagement({ gameId, playerId, setMano, upsertOpponentSet, removeOpponentSet }));

    await act(async () => {
      await result.current.onSetPlayed({ player_id: playerId, cards_played: [] });
    });

    expect(result.current.setsPropios).toEqual([]);
  });

  it('llama removeOpponentSet y upsertOpponentSet correctamente en onSetStolen', () => {
    const { result } = renderHook(() => useSetManagement({ gameId, playerId, setMano, upsertOpponentSet, removeOpponentSet }));

    act(() => {
      result.current.onSetStolen({ thief_id: 2, victim_id: 3, set_id: 44, set_cards: [{ set_id: 44 }] });
    });

    expect(upsertOpponentSet).toHaveBeenCalledWith(2, [{ set_id: 44 }]);
    expect(removeOpponentSet).toHaveBeenCalledWith(3, 44);
  });

  it('no llama nada si onSetStolen recibe payload vacío', () => {
    const { result } = renderHook(() => useSetManagement({ gameId, playerId, setMano, upsertOpponentSet, removeOpponentSet }));

    act(() => {
      result.current.onSetStolen(null);
    });

    expect(upsertOpponentSet).not.toHaveBeenCalled();
    expect(removeOpponentSet).not.toHaveBeenCalled();
    expect(result.current.setsPropios).toEqual([]);
  });
});
