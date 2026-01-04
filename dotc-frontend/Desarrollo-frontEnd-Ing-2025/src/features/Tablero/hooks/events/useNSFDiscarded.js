import { useCallback, useState } from 'react';

export function useNSFDiscarded({ 
  playerId,
  setMano,
  onShowNotification
}) {
  const [nsfNotification, setNsfNotification] = useState({
    isOpen: false,
    cardsCount: 0
  });

  const onCardsNSFDiscarded = useCallback((payload) => {
    const { source_player_id, target_player_id, discarded_cards } = payload || {};
    
    if (!target_player_id || !Array.isArray(discarded_cards)) {
      console.warn('useNSFDiscarded: payload inválido', payload);
      return;
    }

    const cardCount = discarded_cards.length;

    if (Number(target_player_id) === Number(playerId)) {
      const discardedCardIds = discarded_cards.map(card => card.card_id);
      
      setMano(prevMano => {
        return prevMano.filter(card => !discardedCardIds.includes(card.card_id));
      });

      setNsfNotification({
        isOpen: true,
        cardsCount: cardCount
      });

      setTimeout(() => {
        setNsfNotification(prev => ({ ...prev, isOpen: false }));
      }, 3000);
    } else {
      if (Number(source_player_id) !== Number(playerId) && onShowNotification) {
        if (cardCount > 0) {
          onShowNotification(
            `Jugador ${target_player_id} descartó ${cardCount} cartas NOT SO FAST`,
            'info'
          );
        } else {
          onShowNotification(
            `Jugador ${target_player_id} no tenía cartas NOT SO FAST`,
            'info'
          );
        }
      }
    }
  }, [playerId, setMano, onShowNotification]);

  const closeNsfNotification = useCallback(() => {
    setNsfNotification(prev => ({ ...prev, isOpen: false }));
  }, []);

  return {
    onCardsNSFDiscarded,
    nsfNotification,
    closeNsfNotification
  };
}

