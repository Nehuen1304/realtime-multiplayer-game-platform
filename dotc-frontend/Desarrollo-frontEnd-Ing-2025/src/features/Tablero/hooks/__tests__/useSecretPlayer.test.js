import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { usePlayerSecret } from '../secrets/useSecretPlayer.js';

vi.mock('../../ManoPropia/ManoPropiaService.js', () => ({
  getSecretosJugador: vi.fn(),
}));

const { getSecretosJugador } = await import('../../ManoPropia/ManoPropiaService.js');

describe('usePlayerSecret', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches secrets and updates state when gameId and playerId are provided', async () => {
    const mockSecrets = [{ id: 1, name: 'S1' }, { id: 2, name: 'S2' }];
    getSecretosJugador.mockResolvedValueOnce({ secrets: mockSecrets });

    const { result } = renderHook(() =>
      usePlayerSecret({ gameId: 123, playerId: 456 })
    );

    await waitFor(() => {
      expect(result.current.secretP).toEqual(mockSecrets);
    });

    expect(result.current.cargando).toBe(false);
    expect(result.current.errorSecreto).toBeNull();
    expect(getSecretosJugador).toHaveBeenCalledWith(123, 456);
  });

  it('does not fetch when gameId or playerId is missing', async () => {
    const { result: res1 } = renderHook(() =>
      usePlayerSecret({ gameId: null, playerId: 1 })
    );
    const { result: res2 } = renderHook(() =>
      usePlayerSecret({ gameId: 1, playerId: null })
    );

    expect(getSecretosJugador).not.toHaveBeenCalled();
    expect(res1.current.secretP).toEqual([]);
    expect(res1.current.cargando).toBe(false);
    expect(res1.current.errorSecreto).toBeNull();

    expect(res2.current.secretP).toEqual([]);
    expect(res2.current.cargando).toBe(false);
    expect(res2.current.errorSecreto).toBeNull();
  });

  it('handles errors from service and sets errorSecreto', async () => {
    getSecretosJugador.mockRejectedValueOnce(new Error('Boom'));

    const { result } = renderHook(() =>
      usePlayerSecret({ gameId: 1, playerId: 2 })
    );

    await waitFor(() => {
      expect(result.current.errorSecreto).toBe('Boom');
    });

    expect(result.current.cargando).toBe(false);
    expect(result.current.secretP).toEqual([]);
  });

  it('sets empty list if service returns no secrets field', async () => {
    getSecretosJugador.mockResolvedValueOnce({});

    const { result } = renderHook(() =>
      usePlayerSecret({ gameId: 1, playerId: 2 })
    );

    await waitFor(() => {
      expect(result.current.secretP).toEqual([]);
    });

    expect(result.current.errorSecreto).toBeNull();
  });
});


