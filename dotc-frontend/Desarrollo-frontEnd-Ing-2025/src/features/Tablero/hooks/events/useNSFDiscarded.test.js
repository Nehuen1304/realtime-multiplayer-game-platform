import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useNSFDiscarded } from './useNSFDiscarded.js';

describe('useNSFDiscarded', () => {
  vi.useFakeTimers();

  it('filtra mano y muestra notificación si soy target', () => {
    let mano = [{ card_id: 1 }, { card_id: 2 }];
    const setMano = vi.fn(fn => { mano = fn(mano); });
    const { result } = renderHook(() => useNSFDiscarded({ playerId: 5, setMano, onShowNotification: vi.fn() }));
    act(() => {
      result.current.onCardsNSFDiscarded({
        source_player_id: 3,
        target_player_id: 5,
        discarded_cards: [{ card_id: 2 }],
      });
    });
    expect(mano).toEqual([{ card_id: 1 }]);
    expect(result.current.nsfNotification.isOpen).toBe(true);
    act(() => {
      vi.advanceTimersByTime(3100);
    });
    expect(result.current.nsfNotification.isOpen).toBe(false);
  });

  it('notifica vía callback si soy observador', () => {
    const notify = vi.fn();
    const { result } = renderHook(() => useNSFDiscarded({ playerId: 1, setMano: vi.fn(), onShowNotification: notify }));
    act(() => {
      result.current.onCardsNSFDiscarded({
        source_player_id: 2,
        target_player_id: 3,
        discarded_cards: [{ card_id: 9 }],
      });
    });
    expect(notify).toHaveBeenCalled();
  });
});