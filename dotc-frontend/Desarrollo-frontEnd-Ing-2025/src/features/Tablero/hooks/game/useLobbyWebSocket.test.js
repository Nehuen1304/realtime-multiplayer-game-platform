import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

vi.mock('../../tableroService.js', () => ({
  getGameState: vi.fn(async () => ({ current_turn_player_id: 42 })),
}));
vi.mock('../../../../config/api.js', () => ({
  API_CONFIG: { WEBSOCKET_BASE: 'ws://test' },
}));
vi.mock('../../../../ws/wsHandlers.js', () => ({
  getWsHandlers: (cbs) => cbs,
}));
const wsClose = vi.fn();
vi.mock('../../../../ws/wsManager.js', () => ({
  WSManager: vi.fn().mockImplementation((_url, handlers) => ({
    handlers,
    close: wsClose,
  })),
}));

import { getGameState } from '../../tableroService.js';
import { WSManager } from '../../../../ws/wsManager.js';
import { useLobbyWebSocket } from './useLobbyWebSocket.js';

describe('useLobbyWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('carga turno inicial y expone esMiTurno', async () => {
    const { result } = renderHook(() =>
      useLobbyWebSocket({ gameId: 1, playerId: 42, onMyTurnGain: vi.fn(), onGameStarted: vi.fn(), setDraftCards: vi.fn(), updeteList: vi.fn() })
    );
    await act(async () => {});
    expect(getGameState).toHaveBeenCalled();
    expect(result.current.currentTurnId).toBe(42);
    expect(result.current.esMiTurno).toBe(true);
  });

  it('invoca updeteList vía onLobbyGameInfoUpdate handler', async () => {
    const updeteList = vi.fn();
    const { result } = renderHook(() =>
      useLobbyWebSocket({ gameId: 2, playerId: 5, updeteList })
    );
    // Simular llamada handler
    act(() => {
      WSManager.mock.calls[0][1].onLobbyGameInfoUpdate(1, 4, 'Alice', 2);
    });
    expect(updeteList).toHaveBeenCalledWith(1, 4, 'Alice', 2);
  });
});