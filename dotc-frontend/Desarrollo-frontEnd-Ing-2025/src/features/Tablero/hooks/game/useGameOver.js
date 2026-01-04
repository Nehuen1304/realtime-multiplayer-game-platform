import { useState, useCallback } from 'react';

export function useGameOver({ players, onGameOver }) {
  const [gameOverData, setGameOverData] = useState(null);

  const handleGameOverEvent = useCallback((payload) => {
    let data = null;
    // Caso 1: Se reveló el asesino -> Ganan los Inocentes
    if (payload?.event === 'SECRET_REVEALED' && payload?.role === 'MURDERER') {
      const murdererPlayer = players.find(p => p.player_id === payload.player_id);
      data = {
        winner: 'INNOCENTS',
        murdererName: murdererPlayer?.player_name || 'Desconocido',
        reason: 'SECRET_REVEALED'
      };
    }
    // Caso 2: Mazo vacío -> Gana el Asesino
    else if (payload?.event === 'DECK_EMPTY') {
      data = {
        winner: 'MURDERER',
        murdererName: 'Desconocido',
        reason: 'DECK_EMPTY'
      };
    }

    if (data) {
      setGameOverData(data);
      if (typeof onGameOver === 'function') {
        onGameOver(payload);
      }
    }
  }, [players, onGameOver]);

  return { gameOverData, handleGameOverEvent };
}
