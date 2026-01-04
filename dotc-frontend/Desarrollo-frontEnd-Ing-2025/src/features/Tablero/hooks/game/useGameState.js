import { useState, useEffect, useRef, useCallback } from 'react';
import * as tableroService from '../../tableroService.js';

export function useGameState(gameId, setDeckCount, setDraftCards) {
  const [players, setPlayers] = useState([]);
  const lastPlayersRef = useRef('[]');

  const fetchGameState = useCallback(async () => {
    if (!gameId) return;
    try {
      const response = await tableroService.getGameState(gameId);
      console.log("fetchGameState: ", response);

      const players = response.game.players || [];
      const playersJson = JSON.stringify(players);
      if (playersJson !== lastPlayersRef.current) {
        lastPlayersRef.current = playersJson;
        setPlayers(players);
      }

      // Actualizar deckCount
      if (setDeckCount) {
        const deckSize = await tableroService.getDeckSize(gameId);
        setDeckCount(deckSize);
      }
      console.log("por inicializar draftCards", response);
      // Actualizar draftCards si viene en el estado
      if (setDraftCards && Array.isArray(response.game.draft)) {
        setDraftCards(response.game.draft.map(card => ({
          ...card,
          is_revealed: true
        })));
      }

    } catch {
      // silencioso
    }
  }, [gameId, setDeckCount, setDraftCards]);

  useEffect(() => {
    fetchGameState(); // Solo llamada inicial
  }, [fetchGameState]);

  return { players, forceUpdate: fetchGameState };
}