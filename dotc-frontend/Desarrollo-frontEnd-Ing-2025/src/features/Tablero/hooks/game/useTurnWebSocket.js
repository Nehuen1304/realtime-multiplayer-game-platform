// Hook para manejar la conexion WebSocket y el estado de turnos en el tablero
// Centraliza la logica de suscripcion y actualizacion de estado por eventos del server
// Lo hice para que el componente principal no tenga que preocuparse por los detalles del WS
// Tambien inicializa el estado por HTTP para evitar flickers hasta que llega el primer evento WS

import { useEffect, useMemo, useRef, useState } from 'react';
import { getGameState, getDeckSize } from '../../tableroService.js';
import { WSManager } from '../../../../ws/wsManager.js';
import { API_CONFIG } from '../../../../config/api.js';
import { getWsHandlers } from '../../../../ws/wsHandlers.js';
import { getManoJugador } from '../../tableroService.js';

// Recibe varios callbacks y setters para actualizar el estado global del tablero
// gameId: id de la partida actual
// playerId: id del jugador local (para saber si es su turno)
// onMyTurnGain: callback cuando el jugador gana el turno
// onGameStarted: callback cuando arranca la partida
// setDraftCards: setter para las cartas del draft
// setDeckCount: setter para el tamaño del mazo
export function useTurnWebSocket({
  gameId,
  playerId,
  onMyTurnGain,
  onGameStarted,
  setDraftCards,
  setDeckCount,
  setDiscardCard,
  setRevealedSecret,
  setHiddenSecret,
  setSetPlayed,
  setRevealSecretPrompt,
  stolenSet,
  setCardLook, 
  onGameOver,
  onVoteStarted,
  stolenSecret,
  onCardsNSFDiscarded,
  // NSF feature callbacks
  onNsfWindowOpen,
  onNsfWindowClose,
  onCardsPlayed,
  onSocialDisgraceApplied,
  onSocialDisgraceRemoved, 
  currentTurnId,
  setCurrentTurnId,
  removeOpponentCardsFromHand,
  esMiTurno,
  onTradeRequested,
  setPlayerHand,
}) {
  const prevIsMyTurnRef = useRef(false);
  const wsManagerRef = useRef(null);

  // Primer efecto: carga el estado inicial por HTTP (por si el WS tarda en conectar)
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        // Pido el estado del juego, y saco el id del jugador con el turno actual
        const state = await getGameState(gameId);
        const turnId = state?.game?.current_turn_player_id ?? null;
        if (active && turnId != null) {
          setCurrentTurnId(Number(turnId));
        }
      } catch { }
      // Si el caller pidio el tamaño del mazo, lo pido por HTTP tambien
      try {
        if (typeof setDeckCount === 'function') {
          const deck = await getDeckSize(gameId);
          const size =
            deck?.size_deck ?? null;
          if (active && typeof size === 'number') setDeckCount(size);
        }
      } catch { }
    })();
    // Cleanup: si el componente se desmonta, no actualizo el estado
    return () => { active = false; };
  }, [gameId]);

  // Segundo efecto: conecta el WebSocket y setea los handlers de eventos
  useEffect(() => {
    if (!gameId) return;

    // Armo la URL del WS usando la config global
    const wsBase = API_CONFIG.WEBSOCKET_BASE;
    const wsUrl = `${wsBase}/ws/game/${gameId}/player/${playerId}`

    // Inyectar callbacks a gameLogic
    const handlers = getWsHandlers({
      // Paso el callback de inicio de juego, por compatibilidad con el lobby
      onGameStartedLobby: onGameStarted,
      onSetCurrentTurnId: (id) => setCurrentTurnId(Number(id)),
      onSetDeckCount: typeof setDeckCount === 'function' ? (n) => setDeckCount(n) : undefined,
      onSetDraftCards: typeof setDraftCards === 'function' ? (cards) => setDraftCards(cards) : undefined,
      onSetDiscardCard: setDiscardCard,
      onSecretRevealed: setRevealedSecret,
      onSecretHidden: setHiddenSecret,
      onSetSetPlayed: setSetPlayed,
      onPromptReveal: setRevealSecretPrompt,
      onStolenSet: stolenSet,
      onSecretStolen: stolenSecret,
      onPromptDrawFromDiscard: setCardLook,
      onGameOver: onGameOver,
      onVoteStarted: onVoteStarted,
      onSocialDisgraceApplied,
      onSocialDisgraceRemoved,
      onCardsNSFDiscarded: onCardsNSFDiscarded,
      // NSF integration
      onNsfWindowOpen,
      onNsfWindowClose,
      onCardsPlayed,
      onOpponentDiscarded: removeOpponentCardsFromHand,
      onTradeRequested,
      onHandUpdated: async () => {
        try {
          const res = await getManoJugador(gameId, playerId);
          console.log('nueva mano: ',res);
          if (Array.isArray(res?.cards)) {
            setPlayerHand(res.cards);
          }
        } catch (e) {
          console.warn('HAND_UPDATED: fallo al recargar mano', e);
        }
      },
    });

    const ws = new WSManager(wsUrl, handlers, "INGAME");
    wsManagerRef.current = ws;
    return () => { ws.close(); wsManagerRef.current = null; };
  }, [gameId, playerId]);

  // Efecto para disparar el callback cuando el jugador gana el turno
  useEffect(() => {
    if (!onMyTurnGain) return;
    const wasMyTurn = prevIsMyTurnRef.current;
    // Solo disparo si antes no era mi turno y ahora si
    if (!wasMyTurn && esMiTurno) onMyTurnGain();
    prevIsMyTurnRef.current = esMiTurno;
  }, [esMiTurno, onMyTurnGain]);

  return;
}
