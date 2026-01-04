import { createGameLogicHandlers } from "../logic/gameLogic.js";

// Exportamos la función que crea los handlers, no los handlers directamente.
// Esto permite que quien la llame (ej. LobbyScreen) inyecte callbacks.
export const getWsHandlers = (lobbyCallbacks) => {
  const gameLogic = createGameLogicHandlers(lobbyCallbacks);

  return {
    CARD_DISCARDED: gameLogic.handleCardDiscarded,
    CARD_PLAYED: gameLogic.handleCardPlayed,
    DECK_UPDATED: gameLogic.handleDeckUpdated,
    DRAFT_UPDATED: gameLogic.handleDraftUpdated,
    GAME_REMOVED: gameLogic.handleGameCancelled,
    GAME_CREATED: gameLogic.handleGameCreated,
    GAME_STARTED: gameLogic.handleGameStarted,
    GAME_UPDATED: gameLogic.handleGameUpdated,
    NEW_TURN: gameLogic.handleNewTurn,
    PLAYER_DREW_FROM_DECK: gameLogic.handlePlayerDrewFromDeck,
    PLAYER_JOINED: gameLogic.handlePlayerJoined,
    PLAYER_LEFT: gameLogic.handlePlayerLeft,
    CARDS_PLAYED: gameLogic.handleCardsPlayed,
    CARDS_NSF_DISCARDED: gameLogic.handleCardsNSFDiscarded,
    PROMPT_REVEAL: gameLogic.handlePromptReveal,
    PROMPT_DRAW_FROM_DISCARD: gameLogic.handlePromptDrawFromDiscard,
    SECRET_REVEALED: gameLogic.handleSecretRevealed,
    SECRET_STOLEN: gameLogic.handleSecretStolen,
    SECRET_HIDDEN: gameLogic.handleSecretHidden,
    SET_STOLEN : gameLogic.handleSetStolen,
    GAME_OVER: gameLogic.handleGameOver,
    VOTE_STARTED: gameLogic.handleVoteStarted, 
    SD_APPLIED: gameLogic.handleSocialDisgraceApplied,
    SD_REMOVED: gameLogic.handleSocialDisgraceRemoved,
    GAME_OVER: gameLogic.handleGameOver,
    TRADE_REQUESTED: gameLogic.handleTradeRequested,
    HAND_UPDATED: gameLogic.handleHandUpdated, 
    // nuevos eventos para cierre de cadena NSF
    ACTION_CANCELLED: gameLogic.handleActionCancelled,
    ACTION_RESOLVED: gameLogic.handleActionResolved,
  };
};

