import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
vi.mock('../../tableroService', () => ({
  selectCardLook: vi.fn(async () => ({ ok: true, choice: 9 })),
}));
import { selectCardLook } from '../../tableroService';
import { useSelectDrawCard } from './useSelectDrawCard.js';

describe('useSelectDrawCard', () => {
  it('no llama servicio si faltan params', async () => {
    const { result } = renderHook(() => useSelectDrawCard(null, 1, 2));
    await act(async () => {
      const r = await result.current.selectCardLookHandler();
      expect(r).toBeUndefined();
    });
    expect(selectCardLook).not.toHaveBeenCalled();
  });

  it('llama servicio correctamente', async () => {
    const { result } = renderHook(() => useSelectDrawCard(3, 4, 55));
    let response;
    await act(async () => {
      response = await result.current.selectCardLookHandler();
    });
    expect(selectCardLook).toHaveBeenCalledWith(3, { player_id: 4, card_id: 55 });
    expect(response).toEqual({ ok: true, choice: 9 });
  });
});