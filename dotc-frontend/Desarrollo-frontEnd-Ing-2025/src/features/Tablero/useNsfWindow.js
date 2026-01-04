import { useEffect, useRef, useState, useCallback } from "react";
import { playNSF } from "./tableroService.js";

export function useNsfWindow({ gameId, playerId, setMano }) {
  const [nsfWindow, setNsfWindow] = useState({
    open: false,
    actionId: null,
    playedBy: null,
    playedByName: null, // Añadir para guardar el nombre
    expiresAt: 0,
    remainingMs: 0,
    alreadyResponded: false,
  });

  const timerRef = useRef(null);
  const autoPassSentRef = useRef(false); // ← Prevenir doble envío
  
  const clearTimer = () => { 
    if (timerRef.current) { 
      clearInterval(timerRef.current); 
      timerRef.current = null; 
    }
    autoPassSentRef.current = false; // ← Reset al limpiar
  };

  const openWindow = useCallback(({ actionId, playedBy, playedByName, expiresAt }) => {
    console.log('🔓 Abriendo ventana NSF:', { actionId, playedBy, playedByName, expiresAt, currentPlayerId: playerId });
    clearTimer();
    autoPassSentRef.current = false; // ← Reset al abrir nueva ventana
    setNsfWindow({
      open: true, actionId, playedBy, playedByName, expiresAt,
      remainingMs: Math.max(0, expiresAt - Date.now()),
      alreadyResponded: false,
    });
    
    // 🚫 Verificar si soy el jugador que jugó la carta
    const isMyAction = String(playedBy) === String(playerId);
    if (isMyAction) {
      console.log('⏭️ No inicio auto-pass: es mi propia acción');
    }
    
    // ⏱️ Timer visual (para TODOS): actualiza remainingMs cada 100ms
    timerRef.current = setInterval(() => {
      setNsfWindow(prev => {
        const remaining = Math.max(0, prev.expiresAt - Date.now());
        
        // Solo ejecutar auto-pass si NO es mi acción
        if (remaining === 0 && !isMyAction && !prev.alreadyResponded && !autoPassSentRef.current) {
          console.log('⏰ Auto-pass NSF por timeout');
          autoPassSentRef.current = true; // ← Marcar como enviado
          // Auto-pass: enviar body con card_ids vacío
          playNSF(gameId, { 
            player_id: playerId, 
            game_id: gameId,
            action_type: "PLAY_EVENT",
            card_ids: [],
            action_id: prev.actionId
          }).catch(err => {
            console.error('❌ Error en auto-pass:', err);
            autoPassSentRef.current = false;
            // Si el error es 409 o 404, cerrar la ventana
            if (err.message && (err.message.includes('409') || err.message.includes('404') || 
                err.message.includes('pendiente') || err.message.includes('no existe'))) {
              console.log('🔒 Cerrando ventana NSF por error de acción ya resuelta/inexistente');
              clearTimer();
              setNsfWindow(current => ({ ...current, open: false, remainingMs: 0, alreadyResponded: false }));
            }
          });
          return { ...prev, remainingMs: 0, alreadyResponded: true };
        }
        
        // Actualizar remainingMs para todos
        return { ...prev, remainingMs: remaining };
      });
    }, 100);
  }, [gameId, playerId]);

  const closeWindow = useCallback(() => { 
    console.log('[useNsfWindow] closeWindow llamado');
    console.log('[useNsfWindow] Estado antes de cerrar:', { 
      open: nsfWindow.open, 
      actionId: nsfWindow.actionId,
      alreadyResponded: nsfWindow.alreadyResponded 
    });
    clearTimer(); 
    setNsfWindow(prev => ({ ...prev, open: false, remainingMs: 0, alreadyResponded: false })); 
    console.log('[useNsfWindow] Ventana NSF cerrada');
  }, []);

  const passNSF = useCallback(async () => {
    if (!nsfWindow.open || nsfWindow.alreadyResponded) {
      console.warn('⚠️ passNSF: ventana cerrada o ya respondida');
      return;
    }
    console.log('🚫 Jugador pasa NSF manualmente');
    setNsfWindow(prev => ({ ...prev, alreadyResponded: true }));
    try { 
      await playNSF(gameId, { 
        player_id: playerId, 
        game_id: gameId,
        action_type: "PLAY_EVENT",
        card_ids: [],
        action_id: nsfWindow.actionId
      });
      if (typeof setMano === 'function') {
        setMano(prevMano => 
          prevMano.filter(card => Number(card.card_id) !== Number(cardId))
        );} 
    } catch (err) {
      console.error('❌ Error al pasar NSF:', err);
    }
  }, [nsfWindow.open, nsfWindow.alreadyResponded, nsfWindow.actionId, gameId, playerId]);

  const playNSFCard = useCallback(async (cardId) => {
    if (!nsfWindow.open || nsfWindow.alreadyResponded) {
      console.warn('⚠️ playNSFCard: ventana cerrada o ya respondida');
      return;
    }
    console.log('🃏 Jugando carta NSF:', cardId);
    setNsfWindow(prev => ({ ...prev, alreadyResponded: true }));
    try { 
      await playNSF(gameId, { 
        player_id: playerId, 
        game_id: gameId,
        action_type: "PLAY_EVENT",
        card_ids: [cardId],
        action_id: nsfWindow.actionId
      }); 
      if (typeof setMano === 'function') {
        console.log(`✅ Actualizando mano, quitando card_id: ${cardId}`);
        setMano(prevMano => 
          prevMano.filter(card => Number(card.card_id) !== Number(cardId))
        );
      }
    } catch (err) {
      console.error('❌ Error al jugar NSF:', err);
      setNsfWindow(prev => ({ ...prev, alreadyResponded: false })); // Permitir reintento
    }
  }, [nsfWindow.open, nsfWindow.alreadyResponded, nsfWindow.actionId, gameId, playerId, setMano]);

  const handlePlayNsf = async () => {
    // Verificar si la ventana sigue abierta
    if (!nsfWindow.open) {
      console.warn('⚠️ Ventana NSF ya cerrada');
      return;
    }

    // Verificar si no expiró
    const now = Date.now();
    if (nsfWindow.expiresAt && now >= nsfWindow.expiresAt) {
      console.warn('⚠️ Ventana NSF expirada');
      closeWindow();
      return;
    }

    console.log('🎯 Jugando NSF con:', {
      actionId: nsfWindow.actionId,
      cardId: selectedCard?.card_id,
      timeRemaining: nsfWindow.expiresAt - now
    });

    try {
      await playNSF(gameId, { 
        player_id: playerId, 
        game_id: gameId,
        action_type: "PLAY_EVENT",
        card_ids: [selectedCard?.card_id],
        action_id: nsfWindow.actionId
      });
      closeWindow();
    } catch (error) {
      console.error('❌ Error al jugar NSF:', error);
      // No cerrar la ventana si hay error, dejar que el usuario reintente
    }
  };

  useEffect(() => () => clearTimer(), []);

  return { nsfWindow, openWindow, closeWindow, passNSF, playNSFCard, handlePlayNsf };
}