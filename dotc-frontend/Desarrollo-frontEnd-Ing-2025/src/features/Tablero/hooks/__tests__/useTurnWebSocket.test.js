import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { useTurnWebSocket } from '../game/useTurnWebSocket.js';

// Mock servicios HTTP usados por el hook
vi.mock('/Users/clementeivetta/Documents/famaf/ingenieria1/lab/dotc-frontend/Desarrollo-frontEnd-Ing-2025/src/features/Tablero/tableroService.js', () => ({
  getGameState: vi.fn().mockResolvedValue({ game: { current_turn_player_id: 42 } }),
  getDeckSize: vi.fn(),
}));

// Mock API config
vi.mock('/Users/clementeivetta/Documents/famaf/ingenieria1/lab/dotc-frontend/Desarrollo-frontEnd-Ing-2025/src/config/api.js', () => ({
  API_CONFIG: { WEBSOCKET_BASE: 'ws://test' },
}));

// Mock handlers del WS: devolvemos los callbacks tal cual
vi.mock('/Users/clementeivetta/Documents/famaf/ingenieria1/lab/dotc-frontend/Desarrollo-frontEnd-Ing-2025/src/ws/wsHandlers.js', () => ({
  getWsHandlers: vi.fn((callbacks) => callbacks),
}));

// Mock WSManager para poder simular eventos fácilmente y exponer la última instancia creada
vi.mock('/Users/clementeivetta/Documents/famaf/ingenieria1/lab/dotc-frontend/Desarrollo-frontEnd-Ing-2025/src/ws/wsManager.js', () => {
  let lastInstance = null;
  return {
    WSManager: vi.fn().mockImplementation((url, handlers) => {
      lastInstance = {
        close: vi.fn(),
        // helper para tests
        triggerNewTurn: (id) => handlers.onSetCurrentTurnId(id),
      };
      return lastInstance;
    }),
    __getLastInstance: () => lastInstance,
  };
});

describe('useTurnWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('inicializa el turno desde getGameState', async () => {
    const { result } = renderHook(() => {
      const [currentTurnId, setCurrentTurnId] = React.useState(null);
      const esMiTurno = currentTurnId === 42;
      useTurnWebSocket({ gameId: 1, playerId: 42, setCurrentTurnId, esMiTurno });
      return { currentTurnId, esMiTurno };
    });

    await waitFor(() => expect(result.current.currentTurnId).toBe(42));
    expect(result.current.esMiTurno).toBe(true);
  });

  it('actualiza el turno al simular evento NEW_TURN', async () => {
    const { __getLastInstance } = await import('/Users/clementeivetta/Documents/famaf/ingenieria1/lab/dotc-frontend/Desarrollo-frontEnd-Ing-2025/src/ws/wsManager.js');

    const { result } = renderHook(() => {
      const [currentTurnId, setCurrentTurnId] = React.useState(null);
      const esMiTurno = currentTurnId === 99;
      useTurnWebSocket({ gameId: 1, playerId: 99, setCurrentTurnId, esMiTurno });
      return { currentTurnId, esMiTurno };
    });

    await waitFor(() => expect(result.current.currentTurnId).toBe(42));
    expect(result.current.esMiTurno).toBe(false);

    act(() => {
      __getLastInstance().triggerNewTurn(99);
    });

    await waitFor(() => expect(result.current.currentTurnId).toBe(99));
    expect(result.current.esMiTurno).toBe(true);
  });

  it('llama a onMyTurnGain cuando el jugador gana el turno', async () => {
    const onMyTurnGain = vi.fn();
    const { __getLastInstance } = await import('/Users/clementeivetta/Documents/famaf/ingenieria1/lab/dotc-frontend/Desarrollo-frontEnd-Ing-2025/src/ws/wsManager.js');

    const { result } = renderHook(() => {
      const [currentTurnId, setCurrentTurnId] = React.useState(null);
      const esMiTurno = currentTurnId === 99;
      useTurnWebSocket({ gameId: 1, playerId: 99, onMyTurnGain, setCurrentTurnId, esMiTurno });
      return { currentTurnId, esMiTurno };
    });

    await waitFor(() => expect(result.current.currentTurnId).toBe(42));
    expect(onMyTurnGain).not.toHaveBeenCalled();

    act(() => {
      __getLastInstance().triggerNewTurn(99);
    });

    await waitFor(() => expect(onMyTurnGain).toHaveBeenCalled());
  });
});