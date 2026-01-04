export const createGameLogicHandlers = (callbacks = {}) => {
  const {
    onGameStartedLobby,
    updateLobbyPlayers,
    onGameCancel,
    onSetCurrentTurnId,
    onSetDeckCount,
    onSetDraftCards,
    onSetDiscardCard,
    onLobbyGameInfoUpdate,
    onSetSetPlayed,
    onStolenSet,
    // callbacks para eventos
    onCardsPlayed,
    onPromptReveal,
    onSecretRevealed,
    onSecretStolen,
    onSecretHidden,
    onPromptDrawFromDiscard,
    onTradeRequested,
    onHandUpdated, 
    onSocialDisgraceApplied,
    onSocialDisgraceRemoved,
    onCardsNSFDiscarded,
    onGameOver,
    onVoteStarted,
    // control de ventana NSF
    onNsfWindowOpen,   // ({ actionId, rootActionId, playedBy, isCancellable, expiresAt, payload })
    onNsfWindowClose,  // ({ actionId, status, payload })
    onOpponentDiscarded,
  } = callbacks;

  return {
    handleCardDiscarded: ({ player_id, card }, context, ws) => {
      onSetDiscardCard?.({ ...card, is_revealed: true });
      console.log(`Jugador ${player_id} descartó la carta:`, card, " // Actualizando pila de descarte");

      // Compat: algunos backends emiten CARD_PLAYED
      // notificar a la UI para que quite la carta de la mano del oponente
      if (typeof onOpponentDiscarded === 'function') {
        console.log('gameLogic. onOpponentDiscarded: ', onOpponentDiscarded);
        onOpponentDiscarded(player_id, card?.card_id);
      }
    },

    handleCardPlayed: (payload, context, ws) => {
      console.log("handleCardPlayed", payload);
      const { player_id, cards_played } = payload || {};
      onSetSetPlayed?.({ player_id, cards_played });
    },

    // Fuente principal: CARDS_PLAYED (incluye NSF)
    handleCardsPlayed: (payload, context, ws) => {
      console.log("CARDS_PLAYED <-", payload);

      // 1) Propagar al feed de jugadas/UI
      onCardsPlayed?.(payload);

      // 2) Actualizar sets mostrados si aplica
      const { player_id, cards_played, cards } = payload || {};
      onSetSetPlayed?.({ player_id, cards_played: cards_played ?? cards });

      // 3) Abrir/renovar ventana NSF cuando es cancelable
      const isCancellable = Boolean(payload?.is_cancellable);
      // 🔍 IMPORTANTE: Verifica cuál es el campo correcto
      const actionId = payload?.action_id; // Puede ser root_action_id según tu backend

      console.log('🔍 DEBUG NSF:', {
        isCancellable,
        actionId,
        root_action_id: payload?.root_action_id,
        payload_keys: Object.keys(payload)
      });

      if (context === "INGAME" && isCancellable && onNsfWindowOpen && actionId) {
        onNsfWindowOpen({
          actionId,
          rootActionId: payload?.root_action_id ?? actionId,
          playedBy: payload?.player_id,
          playedByName: payload?.player_name,
          isCancellable,
          expiresAt: Date.now() + 10000,
          payload,
        });
      }
    },

    handleDeckUpdated: (payload, context, ws) => {
      const size = payload?.size_deck ?? payload?.deck_size ?? null;
      if (context === "INGAME") {
        console.log(`🃏 Deck size actualizado a ${size}`);
        if (typeof size === 'number') onSetDeckCount?.(size);
      }
    },

    handleDraftUpdated: (payload, context, ws) => {
      if (Array.isArray(payload?.cards)) {
        onSetDraftCards?.(payload.cards);
        return;
      }
      const { card_taken_id, new_card } = payload || {};
      if (card_taken_id != null && onSetDraftCards) {
        onSetDraftCards(prevDraft => {
          const idx = prevDraft.findIndex(c => String(c.card_id) === String(card_taken_id));
          if (idx === -1) return prevDraft;
          const updated = [...prevDraft];
          if (new_card) updated[idx] = { ...new_card, is_revealed: true };
          else updated.splice(idx, 1);
          return updated;
        });
      }
    },

    handleGameCancelled: ({ game_id }, context, ws) => {
      console.log(`❌ Partida ${game_id} ha sido CANCELADA.`);
      if (context === "LOBBY") {
        if (onGameCancel) {
          onGameCancel();
        }
        // alert("La partida ha sido cancelada por el host.");
      }
    },

    handleGameCreated: ({ game }, context, ws) => {
      if (context === "LOBBY") {
        console.log(`➕ Nueva partida creada en el lobby: ${game?.name ?? game}`);
      }
    },

    handleGameStarted: (payload, context, ws) => {
      const firstId = payload?.first_player_id ??
        (Array.isArray(payload?.players_in_turn_order) ? payload.players_in_turn_order[0] : null);

      console.log(`🎮 GAME_STARTED recibido. Contexto: ${context}. firstId=${firstId}`);
      if (firstId != null) onSetCurrentTurnId?.(Number(firstId));

      if (context === "LOBBY") {
        if (onGameStartedLobby) onGameStartedLobby();
        else console.warn("⚠️ onGameStartedLobby no está definido...");
      }
    },

    handleGameUpdated: (payload, context, ws) => {
      if (context === "LOBBY") {
        const info = payload?.GameLobbyInfo ?? payload?.lobby ?? payload?.game ?? payload;
        const current_p = info?.player_count ?? info?.current_players ?? info?.players?.length;
        const max_player = info?.max_players ?? info?.max ?? null;
        const name_p = info?.name ?? info?.game_name ?? null;
        const game_id = info?.game_id ?? payload?.game_id ?? null;
        onLobbyGameInfoUpdate?.(current_p, max_player, name_p, game_id);
      }
    },

    handleNewTurn: (payload, context, ws) => {
      const turnId = payload?.turn_player_id ?? null;
      if (turnId != null) onSetCurrentTurnId?.(Number(turnId));
      if (context === "INGAME") console.log(`🔄 Nuevo turno. Es el turno del jugador: ${turnId}`);
    },

    handlePlayerDrewFromDeck: (payload, context, ws) => {
      const size = payload?.size_deck ?? payload?.deck_size;
      if (context === "INGAME") {
        console.log(`🃏 Jugador ${payload?.player_id} robó del mazo. Tamaño del mazo: ${size}`);
        if (typeof size === 'number') onSetDeckCount?.(size);
      }
    },

    handlePlayerJoined: ({ player_name, game_id }, context, ws) => {
      console.log(`👤 Jugador ${player_name} se ha unido a la partida ${game_id}.`);
      if (context === "LOBBY") updateLobbyPlayers?.();
    },

    handlePlayerLeft: ({ player_name, game_id, is_host }, context, ws) => {
      console.log(`👋 Jugador ${player_name} ha abandonado la partida ${game_id}. ¿Era host? ${is_host}`);
      if (context === "LOBBY") {
        if (is_host) {
          console.log("El host abandonó. La partida se cancela para los demás.");


          if (onGameCancel) {
            onGameCancel();
          }


        } else {
          updateLobbyPlayers?.();
        }
      }
    },

    // PROMPTs
    handlePromptReveal: (payload, context, ws) => {
      if (context === "INGAME") {
        console.log('🔓 PROMPT para revelar secreto recibido (privado)', payload);
        // NO cerrar ventana NSF aquí - solo se cierra con ACTION_RESOLVED/ACTION_CANCELLED
      }
      onPromptReveal?.(true);
    },

    handlePromptDrawFromDiscard: (payload, context, ws) => {
      onPromptDrawFromDiscard?.(payload);
      if (context === "INGAME") console.log(`🔓 PROMPT para revelar secreto recibido(privado):`, payload);
    },

    // SECRET_REVEALED (único handler)
    handleSecretRevealed: (payload, context, ws) => {
      const { secret_id, role, game_id, player_id } = payload || {};
      onSecretRevealed?.({ event: "SECRET_REVEALED", secret_id, role, game_id, player_id });
      if (role === "MURDERER") onGameOver?.({ event: "SECRET_REVEALED", role, player_id });
    },

    // SECRET_STOLEN
    handleSecretStolen: (payload, context, ws) => {
      const { thief_id, victim_id } = payload || {};
      console.log("RESPUESTA WS:", payload)
      if (typeof onSecretStolen === "function") {
        console.log("FUNCION", onSecretStolen)
        onSecretStolen(thief_id, victim_id);
      }
      if (context === "INGAME") {
        console.log("FUNCION", onSecretStolen)

      }
    },

    // SECRET_HIDDEN (fix: usar onSecretHidden)
    handleSecretHidden: (payload, context, ws) => {
      const { secret_id, role, game_id, player_id } = payload || {};
      console.log('handleSecretHidden, payload: ', payload);
      onSecretHidden?.({ secret_id, role, game_id, player_id });
      if (context === "INGAME") console.log(`Secreto ${secret_id} ocultado en partida ${game_id}.`);
    },

    handleSetStolen: (payload, context, ws) => {
      onStolenSet?.(payload);
    },

    // Evento: "Cards off the table" descartando NSF
    handleCardsNSFDiscarded: (payload, context, ws) => {
      const { source_player_id, target_player_id, discarded_cards } = payload || {};
      if (context === "INGAME") {
        console.log(
          `🚫 ${discarded_cards?.length || 0} cartas NSF fueron descartadas. ` +
          `Jugador ${source_player_id} jugó "Cards off the table" sobre ${target_player_id}.`
        );
      }
      onCardsNSFDiscarded?.({
        source_player_id,
        target_player_id,
        discarded_cards,
        event: "CARDS_NSF_DISCARDED"
      });
    },

    // Cierre de la cadena NSF
    handleActionCancelled: (payload, context, ws) => {
      console.log("ACTION_CANCELLED <-", payload);
      const actionId = payload?.action_id ?? payload?.root_action_id ?? null;
      console.log(`[GAMELOGIC] handleActionCancelled: actionId=${actionId}, context=${context}`);
      console.log('[GAMELOGIC] Llamando onNsfWindowClose con status CANCELLED');
      onNsfWindowClose?.({ actionId, status: "CANCELLED", payload });
      console.log('[GAMELOGIC] onNsfWindowClose llamado exitosamente');
    },

    handleActionResolved: (payload, context, ws) => {
      console.log("ACTION_RESOLVED <-", payload);
      const actionId = payload?.action_id ?? payload?.root_action_id ?? null;
      console.log(`[GAMELOGIC] handleActionResolved: actionId=${actionId}, context=${context}, player_id=${payload?.player_id}`);

      // Si las cartas tienen set_id, significa que formaron un set - actualizar la visualización
      const cardsResolved = payload?.cards_resolved || [];
      console.log(`[GAMELOGIC] cards_resolved count: ${cardsResolved.length}`);
      const hasSetId = cardsResolved.some(card => card.set_id !== null && card.set_id !== undefined);
      if (hasSetId && payload?.player_id) {
        console.log('📊 Set formado en ACTION_RESOLVED, actualizando...');
        onSetSetPlayed?.({ player_id: payload.player_id, cards_played: cardsResolved });
      }

      console.log('[GAMELOGIC] Llamando onNsfWindowClose con status RESOLVED');
      onNsfWindowClose?.({ actionId, status: "RESOLVED", payload });
      console.log('[GAMELOGIC] onNsfWindowClose llamado exitosamente');
    },

    // Fin de partida
    handleGameOver: (payload, context, ws) => {
      onGameOver?.(payload);
    },

    handleVoteStarted: (payload, context, ws) => {
      if (typeof onVoteStarted === "function") {
        onVoteStarted(payload);
      }
      if (context === "INGAME") {
        console.log("VOTE_STARTED recibido:", payload);
      }
    },
    
    handleSocialDisgraceApplied: (payload, context, ws) => {
      // todavia no esta implementado del back, me imagino que llega el player_id
      const { player_id } = payload || {};
      if (typeof onSocialDisgraceApplied === "function") {
        console.log(`handleSocialDisgraceApplied para ${player_id}.`);
        onSocialDisgraceApplied(player_id);
      }
    },

    handleSocialDisgraceRemoved: (payload, context, ws) => {
      // todavia no esta implementado del back, me imagino que llega el player_id
      const { player_id } = payload || {};
      if (typeof onSocialDisgraceApplied === "function") {
        console.log(`handleSocialDisgraceRemoved para ${player_id}.`);
        onSocialDisgraceRemoved(player_id);
      }
    },

    handleTradeRequested: (payload, context, ws) => {
      // payload esperado: { player_id: <solicitante>, game_id }
      if (context === "INGAME") {
        console.log("🔁 TRADE_REQUESTED recibido:", payload);
      }
      if (typeof onTradeRequested === 'function') {
        onTradeRequested({
          requester_player_id: payload?.initiator_player_id,
        });
      }
    },

    handleHandUpdated: (payload, context, ws) => {
      // payload: { hand: [...] } o directamente {hand:[...]}
      const hand = payload?.hand ?? payload;
      if (Array.isArray(hand)) {
        if (typeof onHandUpdated === 'function') {
          console.log(`🖐️ HAND_UPDATED (${context}) -> ${hand.length} cartas.`);
          onHandUpdated(hand);
        } else {
          console.log("HAND_UPDATED recibido pero sin onHandUpdated definido.");
        }
      } else {
        console.warn("HAND_UPDATED payload inválido:", payload);
      }
    },

  };
}
