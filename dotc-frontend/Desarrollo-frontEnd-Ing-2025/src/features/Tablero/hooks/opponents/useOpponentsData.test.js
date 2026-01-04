import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
vi.mock('../../Oponente/oponenteService.js', () => ({
  obtenerManoOponente: vi.fn(async () => ({ cards: [{ card_id: 1 }] })),
  obtenerSecretosOponente: vi.fn(async () => ([{ secret_id: 10 }])),
}));
vi.mock('../../tableroService.js', () => ({
  getSortedPlayers: vi.fn(async () => [
    { player_id: 1, player_name: 'Yo' },
    { player_id: 2, player_name: 'A' },
    { player_id: 3, player_name: 'B' },
  ]),
}));
import { obtenerManoOponente, obtenerSecretosOponente } from '../../Oponente/oponenteService.js';
import { getSortedPlayers } from '../../tableroService.js';
import { useOpponentsData } from './useOpponentsData.js';

describe('useOpponentsData', () => {
  beforeEach(() => vi.clearAllMocks());

  it('ordena y rota oponentes y carga datos', async () => {
    const players = [
      { player_id: 1, player_name: 'Yo' },
      { player_id: 2, player_name: 'A' },
      { player_id: 3, player_name: 'B' },
    ];
    const setOpponentHand = vi.fn();
    const setOpponentSecrets = vi.fn();

    const { result } = renderHook(() =>
      useOpponentsData({
        gameId: 9,
        myPlayerId: 1,
        players,
        currentTurnId: 2,
        opponentsDetailsById: {},
        setOpponentHand,
        setOpponentSecrets,
        sdPlayers: new Set([3]),
      })
    );

    await waitFor(() => {
      expect(getSortedPlayers).toHaveBeenCalled();
    });

    // Esperar a que cargue manos/secretos
    await waitFor(() => {
      expect(setOpponentHand).toHaveBeenCalled();
      expect(setOpponentSecrets).toHaveBeenCalled();
    });

    act(() => { /* trigger memo usage */ });

    const opponentsData = result.current.opponentsData;
    expect(opponentsData.map(o => o.player_id)).toEqual([2, 3]); // rotado después de 1
  });

  it('reloadOpponentSecrets actualiza secretos', async () => {
    const setOpponentSecrets = vi.fn();
    const { result } = renderHook(() =>
      useOpponentsData({
        gameId: 5,
        myPlayerId: 1,
        players: [],
        currentTurnId: null,
        opponentsDetailsById: {},
        setOpponentHand: vi.fn(),
        setOpponentSecrets,
        sdPlayers: null,
      })
    );

    await act(async () => {
      await result.current.reloadOpponentSecrets(2);
    });

    expect(obtenerSecretosOponente).toHaveBeenCalledWith(5, 2);
    expect(setOpponentSecrets).toHaveBeenCalled();
  });
});