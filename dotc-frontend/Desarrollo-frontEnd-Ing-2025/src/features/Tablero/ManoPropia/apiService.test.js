import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as apiService from './ManoPropiaService';
import { getApiUrl } from '../../../config/api.js';

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal('fetch', vi.fn());
});

describe('descartarCarta', () => {
  it('llama a fetch con método POST y endpoint correcto', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'success' }),
    });

    const data = { game_id: 1, player_id: 1, card_id: 4 };

    await apiService.descartarCarta(data);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      getApiUrl(`/api/games/${data.game_id}/actions/discard`),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(data),
      })
    );
  });

  it('lanza error si la API responde mal', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'No es tu turno' }),
    });

    await expect(apiService.descartarCarta({ game_id: 1 }))
      .rejects
      .toThrow('No es tu turno');
  });
});

describe('pasarTurno', () => {
  it('debería llamar a fetch con el endpoint de finish-turn', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Turno finalizado' }),
    });

    const data = { game_id: 'game-123', player_id: 'player-abc' };

    await apiService.pasarTurno(data);

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      getApiUrl(`/api/games/${data.game_id}/actions/finish-turn`),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(data),
      })
    );
  });

  it('lanza error si la API responde mal', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Error de turno' }),
    });

    await expect(apiService.pasarTurno({ game_id: 1, player_id: 2 }))
      .rejects
      .toThrow('Error de turno');
  });
});

describe('getGame', () => {
  it('debería llamar a fetch con el endpoint correcto y devolver los datos', async () => {
    const mockGame = { id: 1, name: 'Partida 1' };
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => mockGame,
    });

    const result = await apiService.getGame(1);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      getApiUrl('/api/games/1')
    );
    expect(result).toEqual(mockGame);
  });

  it('lanza error si la API responde mal', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'No existe la partida' }),
    });

    await expect(apiService.getGame(999))
      .rejects
      .toThrow('No existe la partida');
  });
});

describe('getManoJugador', () => {
  it('debería realizar una petición GET y devolver los datos de la mano', async () => {
    const mockHand = { cards: [{ id: 'card-1', name: 'Carta de prueba' }] };

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => mockHand,
    });

    const gameId = 1;
    const playerId = 2;

    const result = await apiService.getManoJugador(gameId, playerId);

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      getApiUrl(`/api/games/${gameId}/players/${playerId}/hand`)
    );
    expect(result).toEqual(mockHand);
  });

  it('lanza error si la API responde mal', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'No autorizado' }),
    });

    await expect(apiService.getManoJugador(1, 2))
      .rejects
      .toThrow('No autorizado');
  });
});

describe('getSecretosJugador', () => {
  it('debería realizar una petición GET al endpoint de secretos y devolver los datos', async () => {
    const mockSecrets = { secrets: [{ id: 'secret-1' }] };

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => mockSecrets,
    });

    const gameId = 1;
    const playerId = 2;

    const result = await apiService.getSecretosJugador(gameId, playerId);

    expect(globalThis.fetch).toHaveBeenCalledWith(
      getApiUrl(`/api/games/${gameId}/players/${playerId}/secrets`),
      {} // apiRequest pasa un objeto vacío como segundo argumento
    );
    expect(result).toEqual(mockSecrets);
  });

  it('lanza error si la API responde mal', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'No hay secretos' }),
    });

    await expect(apiService.getSecretosJugador(1, 2))
      .rejects
      .toThrow('No hay secretos');
  });
});