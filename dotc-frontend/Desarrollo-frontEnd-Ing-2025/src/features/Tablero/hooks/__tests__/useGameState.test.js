import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useGameState } from '../game/useGameState.js';

vi.mock('../../tableroService.js', () => ({
  getGameState: vi.fn(),
  getDeckSize: vi.fn(),
}));
const { getGameState, getDeckSize } = await import('../../tableroService.js');

describe('useGameState', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches game state on mount and updates players, deck count, and draft cards', async () => {
    const mockPlayers = [{ id: 1, name: 'A' }];
    const mockDraft = [{ id: 10, type: 'X' }, { id: 11, type: 'Y' }];
    getGameState.mockResolvedValueOnce({
      game: { players: mockPlayers, draft: mockDraft },
    });
    getDeckSize.mockResolvedValueOnce(42);

    const setDeckCount = vi.fn();
    const setDraftCards = vi.fn();

    const { result } = renderHook(() =>
      useGameState(123, setDeckCount, setDraftCards)
    );

    await waitFor(() => {
      expect(result.current.players).toEqual(mockPlayers);
    });

    expect(setDeckCount).toHaveBeenCalledWith(42);
    expect(setDraftCards).toHaveBeenCalledWith([
      { id: 10, type: 'X', is_revealed: true },
      { id: 11, type: 'Y', is_revealed: true },
    ]);
  });

  it('does nothing when gameId is falsy', async () => {
    const setDeckCount = vi.fn();
    const setDraftCards = vi.fn();

    const { result } = renderHook(() =>
      useGameState(undefined, setDeckCount, setDraftCards)
    );

    // small wait to ensure no calls happened
    await new Promise((r) => setTimeout(r, 0));

    expect(result.current.players).toEqual([]);
    expect(getGameState).not.toHaveBeenCalled();
    expect(getDeckSize).not.toHaveBeenCalled();
    expect(setDeckCount).not.toHaveBeenCalled();
    expect(setDraftCards).not.toHaveBeenCalled();
  });

  it('handles errors silently when fetching game state', async () => {
    getGameState.mockRejectedValueOnce(new Error('fail'));
    const setDeckCount = vi.fn();
    const setDraftCards = vi.fn();

    const { result } = renderHook(() =>
      useGameState(999, setDeckCount, setDraftCards)
    );

    await new Promise((r) => setTimeout(r, 0));

    expect(result.current.players).toEqual([]);
  });

  it('does not update players state if players are unchanged between fetches', async () => {
    const playersA1 = [{ id: 1, name: 'A' }];
    getGameState.mockResolvedValueOnce({ game: { players: playersA1, draft: [] } });
    getDeckSize.mockResolvedValueOnce(10);

    const setDeckCount = vi.fn();
    const setDraftCards = vi.fn();

    const { result } = renderHook(() =>
      useGameState(1, setDeckCount, setDraftCards)
    );

    await waitFor(() => {
      expect(result.current.players).toEqual(playersA1);
    });

    const firstRef = result.current.players;

    // Next fetch with a new array instance but same JSON content
    const playersA2 = [{ id: 1, name: 'A' }];
    getGameState.mockResolvedValueOnce({ game: { players: playersA2, draft: [] } });
    getDeckSize.mockResolvedValueOnce(10);

    await act(async () => {
      await result.current.forceUpdate();
    });

    expect(result.current.players).toBe(firstRef); // no state update because same content
  });

  it('updates players when content changes on subsequent forceUpdate', async () => {
    const playersV1 = [{ id: 1, name: 'A' }];
    getGameState.mockResolvedValueOnce({ game: { players: playersV1, draft: [] } });
    getDeckSize.mockResolvedValueOnce(10);

    const setDeckCount = vi.fn();
    const setDraftCards = vi.fn();

    const { result } = renderHook(() =>
      useGameState(5, setDeckCount, setDraftCards)
    );

    await waitFor(() => {
      expect(result.current.players).toEqual(playersV1);
    });

    const playersV2 = [{ id: 2, name: 'B' }];
    getGameState.mockResolvedValueOnce({ game: { players: playersV2, draft: [] } });
    getDeckSize.mockResolvedValueOnce(9);

    await act(async () => {
      await result.current.forceUpdate();
    });

    expect(result.current.players).toEqual(playersV2);
  });
});