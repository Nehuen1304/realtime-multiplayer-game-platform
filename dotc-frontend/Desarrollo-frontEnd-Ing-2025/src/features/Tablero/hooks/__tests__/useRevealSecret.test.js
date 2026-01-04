import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useRevealSecret } from '../secrets/useRevealSecret.js';

describe('useRevealSecret', () => {
  it('actualiza setSecretP solo cuando el secreto es mío', () => {
    const state = {
      secrets: [
        { secret_id: 1, is_revealed: false },
        { secret_id: 2, is_revealed: false },
      ],
    };
    const setSecretP = vi.fn(updater => {
      const next = typeof updater === 'function' ? updater(state.secrets) : updater;
      state.secrets = next;
    });

    // Estado simulado de oponentes
    let opponentsDetailsById = {
      8: {
        secretCards: [
          { secret_id: 1, is_revealed: false },
          { secret_id: 3, is_revealed: false },
        ],
      },
    };
    // updateOpponentSecrets debe ser una función que recibe playerId y un updater
    const updateOpponentSecrets = vi.fn((pid, updater) => {
      if (!opponentsDetailsById[pid]) return;
      opponentsDetailsById[pid].secretCards = updater(opponentsDetailsById[pid].secretCards);
    });

    const { result } = renderHook(() =>
      useRevealSecret({ playerId: 7, setSecretP, updateOpponentSecrets })
    );

    act(() => {
      result.current.onSecretRevealed({ player_id: 7, secret_id: 2, event: 'SECRET_REVEALED' });
    });

    expect(state.secrets.find(s => s.secret_id === 2)?.is_revealed).toBe(true);

    act(() => {
      result.current.onSecretRevealed({ player_id: 8, secret_id: 1, event: 'SECRET_REVEALED' });
    });
    expect(state.secrets.find(s => s.secret_id === 1)?.is_revealed).toBe(false);

    expect(opponentsDetailsById[8].secretCards.find(s => s.secret_id === 1)?.is_revealed).toBe(true);
    expect(updateOpponentSecrets).toHaveBeenCalled();
  });

  it('no actualiza nada si el payload está vacío o sin secret_id', () => {
    const setSecretP = vi.fn();
    const updateOpponentSecrets = vi.fn();
    const { result } = renderHook(() =>
      useRevealSecret({ playerId: 1, setSecretP, updateOpponentSecrets })
    );

    act(() => {
      result.current.onSecretRevealed({});
    });
    act(() => {
      result.current.onSecretRevealed(null);
    });

    expect(setSecretP).not.toHaveBeenCalled();
    expect(updateOpponentSecrets).not.toHaveBeenCalled();
  });

  it('no actualiza secretos si prev es null', () => {
    const setSecretP = vi.fn(prev => prev);
    const updateOpponentSecrets = vi.fn();
    const { result } = renderHook(() =>
      useRevealSecret({ playerId: 1, setSecretP, updateOpponentSecrets })
    );

    act(() => {
      result.current.onSecretRevealed({ player_id: 1, secret_id: 5 });
    });

    expect(setSecretP).toHaveBeenCalled();
  });

  it('actualiza múltiples secretos correctamente', () => {
    const state = {
      secrets: [
        { secret_id: 10, is_revealed: false },
        { secret_id: 20, is_revealed: false },
        { secret_id: 30, is_revealed: false },
      ],
    };
    const setSecretP = vi.fn(updater => {
      const next = typeof updater === 'function' ? updater(state.secrets) : updater;
      state.secrets = next;
    });

    let opponentsDetailsById = {
      2: {
        secretCards: [
          { secret_id: 10, is_revealed: false },
          { secret_id: 40, is_revealed: false },
        ],
      },
    };
    const updateOpponentSecrets = vi.fn((pid, updater) => {
      if (!opponentsDetailsById[pid]) return;
      opponentsDetailsById[pid].secretCards = updater(opponentsDetailsById[pid].secretCards);
    });

    const { result } = renderHook(() =>
      useRevealSecret({ playerId: 1, setSecretP, updateOpponentSecrets })
    );

    act(() => {
      result.current.onSecretRevealed({ player_id: 1, secret_id: 20 });
    });
    expect(state.secrets.find(s => s.secret_id === 20)?.is_revealed).toBe(true);

    act(() => {
      result.current.onSecretRevealed({ player_id: 2, secret_id: 10 });
    });
    expect(opponentsDetailsById[2].secretCards.find(s => s.secret_id === 10)?.is_revealed).toBe(true);
  });
});
