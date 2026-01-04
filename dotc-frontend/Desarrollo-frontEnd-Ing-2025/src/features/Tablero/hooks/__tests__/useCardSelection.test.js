import { renderHook, act } from '@testing-library/react';
import { useState } from 'react';
import { describe, it, expect } from 'vitest';
import { useCardSelection } from '../player/useCardSelection.js';

describe('useCardSelection', () => {
  const setup = () =>
    renderHook(() => {
      const [ids, setIds] = useState([]);
      const playSel = {};
      return useCardSelection({ playSel, selectedCardIds: ids, setSelectedCardIds: setIds });
    });

  it('toggleSelectCard agrega y remueve ids y tipos', () => {
    const { result } = setup();
    const c1 = { card_id: 1, card_type: 'Ariadne Oliver' };

    act(() => result.current.toggleSelectCard(c1));
    expect(result.current.selectionState.selectedCardIds).toEqual([1]);
    expect(result.current.selectionState.selectTypesCardIds).toEqual([['Ariadne Oliver', 1]]);

    act(() => result.current.toggleSelectCard(c1));
    expect(result.current.selectionState.selectedCardIds).toEqual([]);
    expect(result.current.selectionState.selectTypesCardIds).toEqual([]);
  });

  it('muestra sugerencia con una sola Ariadne Oliver (compartir texto) sin formar set', () => {
    const { result } = setup();
    const c1 = { card_id: 1, card_type: 'Ariadne Oliver' };

    act(() => {
      result.current.toggleSelectCard(c1);
    });

    // No forma set (validator lo rechaza) pero muestra sugerencia por canShareTextFromDetectiveSet
    expect(result.current.puedeFormarSet).toBe(false);
    expect(result.current.actionSuggestionVisible).toBe(true);
    expect(result.current.actionSuggestionText).toContain('Ariadne Oliver');
  });

  it('muestra sugerencia cuando se puede formar un set válido con Parker Pyne (2 cartas)', () => {
    const { result } = setup();
    const c1 = { card_id: 1, card_type: 'Parker Pyne' };
    const c2 = { card_id: 2, card_type: 'Parker Pyne' };

    act(() => {
      result.current.toggleSelectCard(c1);
      result.current.toggleSelectCard(c2);
    });

    expect(result.current.actionSuggestionVisible).toBe(true);
    expect(result.current.actionSuggestionText).toContain('Parker Pyne');
  });

  it('dos Ariadne Oliver no forman set pero siguen mostrando sugerencia', () => {
    const { result } = setup();
    const c1 = { card_id: 1, card_type: 'Ariadne Oliver' };
    const c2 = { card_id: 2, card_type: 'Ariadne Oliver' };

    act(() => {
      result.current.toggleSelectCard(c1);
      result.current.toggleSelectCard(c2);
    });

    expect(result.current.puedeFormarSet).toBe(false);
    expect(result.current.actionSuggestionVisible).toBe(true);
    expect(result.current.actionSuggestionText).toContain('Ariadne Oliver');
  });

  it('muestra sugerencia con Tommy Beresford y Tuppence Beresford (set hermanos)', () => {
    const { result } = setup();
    const c1 = { card_id: 1, card_type: 'Tommy Beresford' };
    const c2 = { card_id: 2, card_type: 'Tuppence Beresford' };

    act(() => {
      result.current.toggleSelectCard(c1);
      result.current.toggleSelectCard(c2);
    });

    expect(result.current.actionSuggestionVisible).toBe(true);
    expect(result.current.actionSuggestionText).toMatch(/Tommy Beresford|Tuppence Beresford/);
  });

  it('resetSelection limpia selección y sugerencias', () => {
    const { result } = setup();
    const c1 = { card_id: 1, card_type: 'Ariadne Oliver' };
    const c2 = { card_id: 2, card_type: 'Ariadne Oliver' };

    act(() => {
      result.current.toggleSelectCard(c1);
      result.current.toggleSelectCard(c2);
    });
    expect(result.current.selectionState.selectedCardIds).toHaveLength(2);
    expect(result.current.actionSuggestionVisible).toBe(true);

    act(() => {
      result.current.resetSelection();
    });

    expect(result.current.selectionState.selectedCardIds).toHaveLength(0);
    expect(result.current.actionSuggestionVisible).toBe(false);
    expect(result.current.actionSuggestionText).toBeNull();
  });
});
