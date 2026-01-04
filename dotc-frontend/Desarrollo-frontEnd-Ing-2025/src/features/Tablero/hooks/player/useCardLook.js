import { useCallback, useState } from 'react';
import * as tableroService from '../../tableroService.js';

// Maneja el flujo de "look" desde descarte: cartas ofrecidas, selección y confirmación
export function useCardLook({ gameId, playerId, setMano }) {
  const [cardsLook, setCardsLook] = useState([]);
  const [cardLookSelect, setCardLookSelect] = useState(null);

  const onCardLook = useCallback((payload) => {
    setCardsLook(payload?.cards || []);
  }, []);

  const toggleCardLook = useCallback((id) => {
    setCardLookSelect(prev => {
      const prevNum = prev == null ? null : Number(prev);
      const idNum = id == null ? null : Number(id);
      return prevNum !== null && prevNum === idNum ? null : idNum;
    });
  }, []);

  const confirmCardLook = useCallback(async () => {
    try {
      if (cardLookSelect == null) return;
      const response = await tableroService.selectCardLook(gameId, {
        player_id: playerId,
        game_id: gameId,
        source: 'discard',
        card_id: cardLookSelect,
      });
      // limpiar estado local del prompt
      setCardsLook([]);
      setCardLookSelect(null);
      // refrescar mano
      if (response) {
        const nuevaMano = await tableroService.getManoJugador(gameId, playerId);
        setMano(nuevaMano?.cards || []);
      }
    } catch (err) {
      console.error('useCardLook.confirmCardLook error:', err);
    }
  }, [cardLookSelect, gameId, playerId, setMano]);

  return {
    cardsLook,
    cardLookSelect,
    onCardLook,
    toggleCardLook,
    confirmCardLook,
  };
}
