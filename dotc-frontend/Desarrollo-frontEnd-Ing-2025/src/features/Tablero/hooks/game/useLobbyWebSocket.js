import { useEffect, useMemo, useRef, useState } from 'react';
import { getGameState } from '../../tableroService.js';
import { API_CONFIG } from '../../../../config/api.js';
import { WSManager } from '../../../../ws/wsManager.js';
import { getWsHandlers } from '../../../../ws/wsHandlers.js';

export function useLobbyWebSocket({ gameId, playerId, onMyTurnGain, onGameStarted, setDraftCards, updeteList }) {
  const [currentTurnId, setCurrentTurnId] = useState(null);
  const prevIsMyTurnRef = useRef(false);
  const wsManagerRef = useRef(null);

  // Carga inicial por HTTP
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const state = await getGameState(gameId);
        const turnId =
          state?.current_turn_player_id ??
          state?.details?.game?.current_turn_player_id ??
          null;
        if (active && turnId != null) setCurrentTurnId(Number(turnId));
      } catch { }
    })();
    return () => { active = false; };
  }, [gameId]);

  // Suscripción WebSocket via gameLogic
  useEffect(() => {
    if (!gameId) return;
    const wsBase = API_CONFIG.WEBSOCKET_BASE;
    const wsUrl = `${wsBase}/ws/game/${gameId}/player/${playerId}`

    const handlers = getWsHandlers({
      onGameStartedLobby: onGameStarted,
      onSetCurrentTurnId: (id) => setCurrentTurnId(Number(id)),
      onSetDraftCards: typeof setDraftCards === 'function' ? (cards) => setDraftCards(cards) : undefined,
      onLobbyGameInfoUpdate: (current_p, max_player, name_p, game_id) => {
        if (typeof updeteList === 'function') {
          updeteList(current_p, max_player, name_p, game_id);
        }
      },
    });

    const ws = new WSManager(wsUrl, handlers, "LOBBY");
    wsManagerRef.current = ws;

    return () => {
      ws.close();
      wsManagerRef.current = null;
    };
  }, [gameId, onGameStarted, setDraftCards, updeteList]);

  const esMiTurno = useMemo(
    () => Number(currentTurnId) === Number(playerId),
    [currentTurnId, playerId]
  );

  // Notificar cuando ganas el turno
  useEffect(() => {
    if (!onMyTurnGain) return;
    const wasMyTurn = prevIsMyTurnRef.current;
    if (!wasMyTurn && esMiTurno) onMyTurnGain();
    prevIsMyTurnRef.current = esMiTurno;
  }, [esMiTurno, onMyTurnGain]);

  return process.env.NODE_ENV === 'test'
    ? { currentTurnId, esMiTurno, wsRef: wsManagerRef }
    : { currentTurnId, esMiTurno };
}
