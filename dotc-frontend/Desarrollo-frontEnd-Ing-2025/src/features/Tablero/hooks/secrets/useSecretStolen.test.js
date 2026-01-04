import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useStolenSecretHandler } from './useSecretStolen.js';

describe('useStolenSecretHandler', () => {
  it('recarga secretos para thief y victim según corresponda', () => {
    const secretPlayer = vi.fn();
    const reloadOpponentSecrets = vi.fn();
    const { result } = renderHook(() =>
      useStolenSecretHandler({ playerId: 5, secretPlayer, reloadOpponentSecrets })
    );
    act(() => {
      result.current.onSecretStolen(5, 7); // soy ladrón
    });
    expect(secretPlayer).toHaveBeenCalled();

    act(() => {
      result.current.onSecretStolen(8, 5); // soy víctima
    });
    expect(secretPlayer).toHaveBeenCalledTimes(2);

    act(() => {
      result.current.onSecretStolen(8, 9); // observador
    });
    expect(reloadOpponentSecrets).toHaveBeenCalledWith(8);
    expect(reloadOpponentSecrets).toHaveBeenCalledWith(9);
  });

  it('no actúa si faltan dependencias', () => {
    const { result } = renderHook(() =>
      useStolenSecretHandler({ playerId: null, secretPlayer: null, reloadOpponentSecrets: null })
    );
    act(() => {
      result.current.onSecretStolen(1, 2);
    });
    // simplemente no lanza errores
    expect(true).toBe(true);
  });
});