import { describe, it, expect } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useOpponentsState } from './useOpponentsState.js';

describe('useOpponentsState', () => {
  it('setOpponentHand & setOpponentSecrets', () => {
    const { result } = renderHook(() => useOpponentsState());
    act(() => {
      result.current.setOpponentHand(7, [{ card_id: 1 }]);
      result.current.setOpponentSecrets(7, [{ secret_id: 10 }]);
    });
    const d = result.current.opponentsDetailsById[7];
    expect(d.handCards).toEqual([{ card_id: 1 }]);
    expect(d.secretCards).toEqual([{ secret_id: 10 }]);
  });

  it('updateOpponentSecrets function form', () => {
    const { result } = renderHook(() => useOpponentsState());
    act(() => {
      result.current.setOpponentSecrets(8, [{ secret_id: 1, is_revealed: false }]);
      result.current.updateOpponentSecrets(8, prev => prev.map(s => ({ ...s, is_revealed: true })));
    });
    expect(result.current.opponentsDetailsById[8].secretCards[0].is_revealed).toBe(true);
  });

  it('upsertOpponentSet agrega y combina', () => {
    const { result } = renderHook(() => useOpponentsState());
    act(() => {
      result.current.upsertOpponentSet(9, [{ set_id: 100, card_type: 'A' }]);
      result.current.upsertOpponentSet(9, [{ set_id: 100, card_type: 'B' }]);
    });
    const sets = result.current.opponentsDetailsById[9].detectiveSets;
    expect(sets.length).toBe(1);
    expect(sets[0].map(c => c.card_type)).toEqual(['A', 'B']);
  });

  it('removeOpponentSet', () => {
    const { result } = renderHook(() => useOpponentsState());
    act(() => {
      result.current.upsertOpponentSet(5, [{ set_id: 200 }]);
      result.current.removeOpponentSet(5, 200);
    });
    expect(result.current.opponentsDetailsById[5].detectiveSets).toEqual([]);
  });

  it('removeOpponentCardsFromHand', () => {
    const { result } = renderHook(() => useOpponentsState());
    act(() => {
      result.current.setOpponentHand(3, [{ card_id: 1 }, { card_id: 2 }]);
      result.current.removeOpponentCardsFromHand(3, [2]);
    });
    expect(result.current.opponentsDetailsById[3].handCards).toEqual([{ card_id: 1 }]);
  });
});