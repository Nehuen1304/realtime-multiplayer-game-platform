import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
vi.useFakeTimers();
vi.mock('../ManoPropiaService.js', () => ({
  revelarSecreto: vi.fn(async () => ({ ok: true })),
}));
import { revelarSecreto } from '../ManoPropiaService.js';
import { useRevealSecretPrompt } from './useRevealSecretPrompt.js';

describe('useRevealSecretPrompt', () => {
  const secrets = [
    { secret_id: 10, is_revealed: false },
    { secret_id: 11, is_revealed: true },
  ];

  it('inicia countdown y auto revela si no selecciona usuario', async () => {
    const { result } = renderHook(() =>
      useRevealSecretPrompt({
        revealSecretPrompt: true,
        secretCards: secrets,
        gameId: 1,
        playerId: 2,
        setRevealSecretPrompt: vi.fn(),
        timeoutMs: 500,
      })
    );
    expect(result.current.showRevealHint).toBe(true);
    act(() => {
      vi.advanceTimersByTime(600);
    });
    expect(revelarSecreto).toHaveBeenCalledWith({ game_id: 1, player_id: 2, secret_id: 10 });
  });
});