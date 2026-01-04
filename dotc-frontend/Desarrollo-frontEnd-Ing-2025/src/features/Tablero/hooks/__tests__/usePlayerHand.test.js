import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as tableroService from '../../tableroService.js';
import { usePlayerHand } from '../player/usePlayerHand.js';

vi.mock('../../tableroService.js', () => ({
  getManoJugador: vi.fn(),
}));

describe('usePlayerHand', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('carga la mano correctamente', async () => {
    tableroService.getManoJugador.mockResolvedValueOnce({ cards: [{ id: 1 }, { id: 2 }] });

    const { result } = renderHook(() => usePlayerHand(10, 20));

    await waitFor(() => expect(result.current.cargandoMano).toBe(false));

    expect(result.current.mano).toEqual([{ id: 1 }, { id: 2 }]);
    expect(result.current.errorMano).toBeNull();
  });

  it('maneja errores al cargar la mano', async () => {
    tableroService.getManoJugador.mockRejectedValueOnce(new Error('Error de red'));

    const { result } = renderHook(() => usePlayerHand(10, 20));

    await waitFor(() => expect(result.current.cargandoMano).toBe(false));

    expect(result.current.errorMano).toBe('Error de red');
    expect(result.current.mano).toEqual([]);
  });
});