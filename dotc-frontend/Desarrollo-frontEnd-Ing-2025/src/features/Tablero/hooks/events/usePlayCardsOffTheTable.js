import { useCallback, useState } from 'react';
import { playCardsOffTheTable } from '../../tableroService.js';

export function usePlayCardsOffTheTable({
  gameId,
  playerId
}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const playCardsEvent = useCallback(async (cardId, targetPlayerId) => {
    if (!targetPlayerId) {
      setError('Debes seleccionar un jugador objetivo');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      await playCardsOffTheTable(gameId, targetPlayerId, cardId, playerId);
      return true;
    } catch (err) {
      const errorMessage = err.message || 'Error al jugar la carta';
      setError(errorMessage);
      console.error('Error al jugar Cards off the Table:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [gameId, playerId]);

  return {
    playCardsEvent,
    isLoading,
    error,
    clearError: () => setError(null)
  };
}
