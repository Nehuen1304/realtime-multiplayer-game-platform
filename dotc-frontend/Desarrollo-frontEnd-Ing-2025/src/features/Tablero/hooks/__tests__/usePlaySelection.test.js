import { renderHook, act } from '@testing-library/react';
import { usePlaySelection } from '../player/usePlaySelection.js';

vi.mock('../../tableroService', () => ({
  playCard: vi.fn(),
}));
const { playCard } = await import('../../tableroService');

describe('usePlaySelection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Suppress console.log output from the hook during tests
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('throws if required params are invalid', () => {
    expect(() =>
      renderHook(() =>
        usePlaySelection({ selectedCardIds: 'x', setSelectedCardIds: () => {} })
      )
    ).toThrow();

    expect(() =>
      renderHook(() =>
        usePlaySelection({ selectedCardIds: [], setSelectedCardIds: 'x' })
      )
    ).toThrow();
  });

  it('computes canPlay correctly', () => {
    const setSelectedCardIds = vi.fn();
    const { result, rerender } = renderHook(
      (props) => usePlaySelection(props),
      { initialProps: { selectedCardIds: [], setSelectedCardIds } }
    );

    expect(result.current.canPlay).toBe(false);

    act(() => {
      result.current.setActionType('PLAY_EVENT');
    });
    expect(result.current.canPlay).toBe(false);

    rerender({ selectedCardIds: [5], setSelectedCardIds });
    expect(result.current.canPlay).toBe(true);
  });

  it('toggleTarget* updates target ids and player selection', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
    );

    act(() => {
      result.current.toggleTargetPlayer(10);
    });
    expect(result.current.targetPlayerId).toBe(10);

    act(() => {
      result.current.toggleTargetPlayer(10);
    });
    expect(result.current.targetPlayerId).toBeNull();

    act(() => {
      result.current.toggleTargetSecret(99, 7);
    });
    expect(result.current.targetSecretId).toBe(99);
    expect(result.current.targetPlayerId).toBe(7);

    act(() => {
      result.current.toggleTargetCard(42, 8);
    });
    expect(result.current.targetCardId).toBe(42);
    expect(result.current.targetPlayerId).toBe(8);

    act(() => {
      result.current.toggleTargetSet(77, 9);
    });
    expect(result.current.targetSetId).toBe(77);
    expect(result.current.targetPlayerId).toBe(9);

    act(() => {
      result.current.toggleTargetSet(77, 9);
    });
    expect(result.current.targetSetId).toBeNull();
  });

  it('selection payload converts ids to numbers and maps fields', () => {
    const setSelectedCardIds = vi.fn();
    const { result, rerender } = renderHook(
      (props) => usePlaySelection(props),
      { initialProps: { selectedCardIds: ['1', '2'], setSelectedCardIds } }
    );

    act(() => {
      result.current.setActionType('PLAY_EVENT');
      result.current.toggleTargetPlayer('3');
      result.current.toggleTargetSecret('4', 3);
      result.current.toggleTargetCard('5', 3);
      result.current.toggleTargetSet('6', 3);
    });

    const payload = result.current.selection(100, 200);
    expect(payload).toEqual({
      player_id: 200,
      game_id: 100,
      action_type: 'PLAY_EVENT',
      card_ids: [1, 2],
      target_set_id: 6,
      target_player_id: 3,
      target_secret_id: 4,
      target_card_id: 5,
    });

    // After rerender with different selectedCardIds
    rerender({ selectedCardIds: ['9'], setSelectedCardIds });
    const payload2 = result.current.selection(100, 200);
    expect(payload2.card_ids).toEqual([9]);
  });

  it('play throws if canPlay is false', async () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
    );

    await expect(result.current.play(1, 2)).rejects.toThrow();
  });

  it('resetSelection resets all state', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [1, 2], setSelectedCardIds })
    );

    act(() => {
      result.current.setActionType('PLAY_EVENT');
      result.current.toggleTargetPlayer(1);
      result.current.toggleTargetSecret(2, 1);
      result.current.toggleTargetCard(3, 1);
      result.current.toggleTargetSet(4, 1);
    });

    expect(result.current.actionType).toBe('PLAY_EVENT');
    expect(result.current.targetPlayerId).toBe(1);
    expect(result.current.targetSecretId).toBe(2);
    expect(result.current.targetCardId).toBe(3);
    expect(result.current.targetSetId).toBe(4);

    act(() => {
      result.current.resetSelection();
    });

    expect(result.current.actionType).toBeNull();
    expect(result.current.targetPlayerId).toBeNull();
    expect(result.current.targetSecretId).toBeNull();
    expect(result.current.targetCardId).toBeNull();
    expect(result.current.targetSetId).toBeNull();
    expect(setSelectedCardIds).toHaveBeenCalledWith([]);
  });

  it('selection returns default values when nothing is set', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
    );
    const payload = result.current.selection(1, 2);
    expect(payload).toEqual({
      player_id: 2,
      game_id: 1,
      action_type: null,
      card_ids: [],
      target_set_id: null,
      target_player_id: null,
      target_secret_id: null,
      target_card_id: null,
    });
  });

  it('initial values are respected', () => {
    const setSelectedCardIds = vi.fn();
    const initial = {
      actionType: 'PLAY_EVENT',
      targetPlayerId: 5,
      targetSecretId: 6,
      targetCardId: 7,
      targetSetId: 8,
    };
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [1], setSelectedCardIds, initial })
    );
    expect(result.current.actionType).toBe('PLAY_EVENT');
    expect(result.current.targetPlayerId).toBe(5);
    expect(result.current.targetSecretId).toBe(6);
    expect(result.current.targetCardId).toBe(7);
    expect(result.current.targetSetId).toBe(8);
  });

  // it('selection always returns numbers for card_ids and targets, even if set as strings', () => {
  //   const setSelectedCardIds = vi.fn();
  //   const { result } = renderHook(() =>
  //     usePlaySelection({ selectedCardIds: ['10', '20'], setSelectedCardIds })
  //   );
  //   act(() => {
  //     result.current.setActionType('PLAY_EVENT');
  //     result.current.toggleTargetPlayer('30');
  //     result.current.toggleTargetSecret('40', '30');
  //     result.current.toggleTargetCard('50', '30');
  //     result.current.toggleTargetSet('60', '30');
  //   });
  //   const payload = result.current.selection(1, 2);
  //   expect(payload.card_ids).toEqual([10, 20]);
  //   expect(payload.target_player_id).toBe(30);
  //   expect(payload.target_secret_id).toBe(40);
  //   expect(payload.target_card_id).toBe(50);
  //   expect(payload.target_set_id).toBe(60);
  //   expect(typeof payload.target_player_id).toBe('number');
  //   expect(typeof payload.target_secret_id).toBe('number');
  //   expect(typeof payload.target_card_id).toBe('number');
  //   expect(typeof payload.target_set_id).toBe('number');
  //   expect(payload.card_ids.every(id => typeof id === 'number')).toBe(true);
  // });

  it('resetSelection resets state even if nothing was set', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
    );
    act(() => {
      result.current.resetSelection();
    });
    expect(result.current.actionType).toBeNull();
    expect(result.current.targetPlayerId).toBeNull();
    expect(result.current.targetSecretId).toBeNull();
    expect(result.current.targetCardId).toBeNull();
    expect(result.current.targetSetId).toBeNull();
    expect(setSelectedCardIds).toHaveBeenCalledWith([]);
  });

  it('play does not reset state if API throws, even with string targets', async () => {
    const setSelectedCardIds = vi.fn();
    playCard.mockRejectedValueOnce(new Error('API error'));
    const { result } = renderHook(
      (props) => usePlaySelection(props),
      { initialProps: { selectedCardIds: ['1'], setSelectedCardIds } }
    );
    act(() => {
      result.current.setActionType('PLAY_EVENT');
      result.current.toggleTargetPlayer('30');
    });
    await expect(result.current.play(1, 2)).rejects.toThrow('API error');
    // State should not be reset
    expect(result.current.actionType).toBe('PLAY_EVENT');
    expect(result.current.targetPlayerId).toBe(30);
  });

  it('selection returns null for targets if not set', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [1], setSelectedCardIds })
    );
    act(() => {
      result.current.setActionType('PLAY_EVENT');
    });
    const payload = result.current.selection(1, 2);
    expect(payload.target_player_id).toBeNull();
    expect(payload.target_secret_id).toBeNull();
    expect(payload.target_card_id).toBeNull();
    expect(payload.target_set_id).toBeNull();
  });

  it('toggleTarget* toggles between number and null', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
    );
    act(() => {
      result.current.toggleTargetPlayer(5);
    });
    expect(result.current.targetPlayerId).toBe(5);
    act(() => {
      result.current.toggleTargetPlayer(5);
    });
    expect(result.current.targetPlayerId).toBeNull();
    act(() => {
      result.current.toggleTargetPlayer('7');
    });
    expect(result.current.targetPlayerId).toBe(7);
    act(() => {
      result.current.toggleTargetPlayer('7');
    });
    expect(result.current.targetPlayerId).toBeNull();
  });

  it('toggleTarget* sets player id if different', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
    );
    act(() => {
      result.current.toggleTargetPlayer(1);
      result.current.toggleTargetSecret(2, 3);
    });
    expect(result.current.targetPlayerId).toBe(3);
    act(() => {
      result.current.toggleTargetCard(4, 5);
    });
    expect(result.current.targetPlayerId).toBe(5);
    act(() => {
      result.current.toggleTargetSet(6, 7);
    });
    expect(result.current.targetPlayerId).toBe(7);
  });

  // it('toggleTarget* sets targetPlayerId to null if player_id is null/undefined', () => {
  //   const setSelectedCardIds = vi.fn();
  //   const { result } = renderHook(() =>
  //     usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
  //   );

  //   // Set to a value first
  //   act(() => {
  //     result.current.toggleTargetPlayer(1);
  //   });
  //   expect(result.current.targetPlayerId).toBe(1);

  //   // Now toggleTargetSecret with undefined player_id
  //   act(() => {
  //     result.current.toggleTargetSecret(2, undefined);
  //   });
  //   expect(result.current.targetSecretId).toBe(2);
  //   expect(result.current.targetPlayerId).toBeNull();

  //   // Now toggleTargetCard with null player_id
  //   act(() => {
  //     result.current.toggleTargetCard(3, null);
  //   });
  //   expect(result.current.targetCardId).toBe(3);
  //   expect(result.current.targetPlayerId).toBeNull();

  //   // Now toggleTargetSet with undefined player_id
  //   act(() => {
  //     result.current.toggleTargetSet(4, undefined);
  //   });
  //   expect(result.current.targetSetId).toBe(4);
  //   expect(result.current.targetPlayerId).toBeNull();
  // });

  it('toggleTarget* does not change targetPlayerId if player_id is same as current', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
    );

    act(() => {
      result.current.toggleTargetPlayer(5);
    });
    expect(result.current.targetPlayerId).toBe(5);

    act(() => {
      result.current.toggleTargetSecret(6, 5);
    });
    expect(result.current.targetPlayerId).toBe(5);

    act(() => {
      result.current.toggleTargetCard(7, 5);
    });
    expect(result.current.targetPlayerId).toBe(5);

    act(() => {
      result.current.toggleTargetSet(8, 5);
    });
    expect(result.current.targetPlayerId).toBe(5);
  });

  it('toggleTarget* toggles target ids between number and null', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
    );

    act(() => {
      result.current.toggleTargetSecret(11, 1);
    });
    expect(result.current.targetSecretId).toBe(11);
    act(() => {
      result.current.toggleTargetSecret(11, 1);
    });
    expect(result.current.targetSecretId).toBeNull();

    act(() => {
      result.current.toggleTargetCard(12, 1);
    });
    expect(result.current.targetCardId).toBe(12);
    act(() => {
      result.current.toggleTargetCard(12, 1);
    });
    expect(result.current.targetCardId).toBeNull();

    act(() => {
      result.current.toggleTargetSet(13, 1);
    });
    expect(result.current.targetSetId).toBe(13);
    act(() => {
      result.current.toggleTargetSet(13, 1);
    });
    expect(result.current.targetSetId).toBeNull();
  });

  it('selection always returns null for targets if state is null or undefined', () => {
    const setSelectedCardIds = vi.fn();
    const { result } = renderHook(() =>
      usePlaySelection({ selectedCardIds: [], setSelectedCardIds })
    );
    const payload = result.current.selection(1, 2);
    expect(payload.target_player_id).toBeNull();
    expect(payload.target_secret_id).toBeNull();
    expect(payload.target_card_id).toBeNull();
    expect(payload.target_set_id).toBeNull();
  });

//   it('selection returns correct types for all fields', () => {
//     const setSelectedCardIds = vi.fn();
//     const { result } = renderHook(() =>
//       usePlaySelection({ selectedCardIds: ['1', '2'], setSelectedCardIds })
//     );
//     act(() => {
//       result.current.setActionType('PLAY_EVENT');
//       result.current.toggleTargetPlayer('3');
//       result.current.toggleTargetSecret('4', '3');
//       result.current.toggleTargetCard('5', '3');
//       result.current.toggleTargetSet('6', '3');
//     });
//     const payload = result.current.selection(100, 200);
//     expect(typeof payload.player_id).toBe('number');
//     expect(typeof payload.game_id).toBe('number');
//     expect(typeof payload.action_type).toBe('string');
//     expect(Array.isArray(payload.card_ids)).toBe(true);
//     expect(typeof payload.target_player_id).toBe('number');
//     expect(typeof payload.target_secret_id).toBe('number');
//     expect(typeof payload.target_card_id).toBe('number');
//     expect(typeof payload.target_set_id).toBe('number');
//   });
});
