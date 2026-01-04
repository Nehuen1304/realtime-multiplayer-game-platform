import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as apiService from '../../ManoPropia/ManoPropiaService.js';
import * as tableroService from '../../tableroService.js';
import { useTurnActions } from '../game/useTurnActions.js';

vi.mock('../../ManoPropia/ManoPropiaService.js', () => ({
  descartarCarta: vi.fn(),
  pasarTurno: vi.fn(),
}));
vi.mock('../../tableroService.js', () => ({
  drawCard: vi.fn(),
  getManoJugador: vi.fn(),
  drawDraftCard: vi.fn(),
}));

describe('useTurnActions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('robarDesdeFuente(draw) devuelve la mano actualizada y marca acción realizada', async () => {
    tableroService.drawCard.mockResolvedValueOnce({ drawn_card: { id: 99 } });
    tableroService.getManoJugador.mockResolvedValueOnce({ cards: [{ id: 99 }] });

    const setMano = vi.fn();
    const setAccionRealizada = vi.fn();

    const { result } = renderHook(() =>
      useTurnActions({
        gameId: 1,
        playerId: 2,
        mano: [],
        setMano,
        esMiTurno: true,
        setAccionRealizada,
        setSelectedCardIds: vi.fn(),
        draftCards: [],
        setDraftCards: vi.fn(),
        discardCard: null,
        setDiscardCard: vi.fn(),
      })
    );

    let nuevaMano;
    await act(async () => {
      nuevaMano = await result.current.robarDesdeFuente('draw');
    });

    expect(nuevaMano).toEqual([{ id: 99 }]);
    expect(setAccionRealizada).toHaveBeenCalledWith(true);
  });

  it('descartarCarta refresca y devuelve la mano, resetea selección y marca acción', async () => {
    apiService.descartarCarta.mockResolvedValueOnce({});
    tableroService.getManoJugador.mockResolvedValueOnce({ cards: [{ id: 2 }] });

    const setMano = vi.fn();
    const setAccionRealizada = vi.fn();
    const setSelectedCardIds = vi.fn();

    const { result } = renderHook(() =>
      useTurnActions({
        gameId: 1,
        playerId: 2,
        mano: [{ id: 1 }, { id: 2 }],
        setMano,
        esMiTurno: true,
        setAccionRealizada,
        setSelectedCardIds,
        draftCards: [],
        setDraftCards: vi.fn(),
        discardCard: null,
        setDiscardCard: vi.fn(),
      })
    );

    let nuevaMano;
    await act(async () => {
      nuevaMano = await result.current.descartarCarta([1]);
    });

    expect(apiService.descartarCarta).toHaveBeenCalled();
    expect(nuevaMano).toEqual([{ id: 2 }]);
    expect(setSelectedCardIds).toHaveBeenCalledWith([]);
    expect(setAccionRealizada).toHaveBeenCalledWith(true);
  });

  it('pasarTurno llama a la API si tiene >= 6 cartas', async () => {
    apiService.pasarTurno.mockResolvedValueOnce({});
    const setAccionRealizada = vi.fn();

    const { result } = renderHook(() =>
      useTurnActions({
        gameId: 1,
        playerId: 2,
        mano: Array(6).fill({}),
        setMano: vi.fn(),
        esMiTurno: true,
        setAccionRealizada,
        setSelectedCardIds: vi.fn(),
        draftCards: [],
        setDraftCards: vi.fn(),
        discardCard: null,
        setDiscardCard: vi.fn(),
      })
    );

    await act(async () => {
      await result.current.pasarTurno(6);
    });

    expect(apiService.pasarTurno).toHaveBeenCalled();
    expect(setAccionRealizada).toHaveBeenCalledWith(true);
  });
});