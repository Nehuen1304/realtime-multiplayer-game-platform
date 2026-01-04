import { useCallback, useEffect, useState } from 'react';
import * as tableroService from '../../tableroService.js';

// Maneja estado y lógica relacionada a sets: jugados, propios y robados
export function useSetManagement({ gameId, playerId, setMano, upsertOpponentSet, removeOpponentSet, removeOpponentCardsFromHand }) {
  const [setPlayed, setSetPlayed] = useState({});
  const [setsPropios, setSetsPropios] = useState([]);
  const [stolenSet, setStolenSet] = useState({});
  const [cardsPlayed, setCardsPlayed] = useState({});

  const onSetPlayed = useCallback(async (payload) => {
    if (!payload || !Array.isArray(payload.cards_played) || payload.cards_played.length === 0) {
      console.warn('useSetManagement.onSetPlayed: payload inválido', payload);
      return;
    }
    console.log('ACA LLEGA CARDS_PLAYED: ', payload);
    console.log('onSetPlayed. payload: ', payload);

    // Si se jugó un evento especial, refrescar mano
    const special = new Set(['Another Victim', 'Look into the ashes', 'Early train to Paddington', "Delay the murderer's escape!", "Point your suspicions"]);
    setCardsPlayed(payload.cards_played);

    const pid = Number(payload.player_id);
    const idsToRemove = payload.cards_played.map(c => c.card_id);

    // Remover de la mano del oponente que jugó
    if (pid !== Number(playerId) && typeof removeOpponentCardsFromHand === 'function') {
      removeOpponentCardsFromHand(pid, idsToRemove);
    }

    // Si fue un evento especial, refrescar mano SOLO si lo jugué yo
    const hasSpecial = special.has(payload.cards_played[0].card_type);

    if (hasSpecial && pid === Number(playerId)) {
      try {
        const nuevaMano = await tableroService.getManoJugador(gameId, playerId);
        setMano(nuevaMano?.cards || []);
      } catch (err) {
        console.error('useSetManagement.onSetPlayed: fallo al obtener mano', err);
      }
    }

    // Guardar para que el efecto gestione sets (si corresponde)
    setSetPlayed(payload);
  }, [gameId, playerId, setMano, removeOpponentCardsFromHand]);

  const onSetStolen = useCallback((payload) => {
    if (!payload) return;

    const { thief_id, victim_id, set_id, set_cards } = payload || {};
    setStolenSet(payload || {});

    if (Number(thief_id) === Number(playerId)) {
      setSetsPropios(prev => [...prev, set_cards]);
    } else if (Number(victim_id) === Number(playerId)) {
      setSetsPropios(prev => (Array.isArray(prev) ? prev : []).filter(set => Array.isArray(set) && set[0] && Number(set[0].set_id) !== Number(set_id)));
    }

    // oponentes
    if (thief_id != null) upsertOpponentSet(Number(thief_id), set_cards ?? []);
    if (victim_id != null) removeOpponentSet(Number(victim_id), Number(set_id));
  }, [playerId, upsertOpponentSet, removeOpponentSet]);

  // Un set ha sido jugado
  useEffect(() => {
    if (!setPlayed) return;

    const playedSet = setPlayed.cards_played; // Estas son las cartas NUEVAS
    const setId = playedSet?.[0]?.set_id;
    if (!setId) return;

    const numericSetId = Number(setId);

    if (Number(setPlayed.player_id) === Number(playerId)) {
      // Cuando jugamos un set propio
      setSetsPropios(prev => {
        const prevSets = Array.isArray(prev) ? prev : [];

        // 1. Encontrar el set antiguo (si existe)
        const setAntiguo = prevSets.find(set => {
            const firstCard = Array.isArray(set) ? set[0] : null;
            return firstCard && Number(firstCard.set_id) === numericSetId;
        });

        // 2. Filtrar el set antiguo (siempre, para evitar duplicados)
        const otherSets = prevSets.filter(set => {
            const firstCard = Array.isArray(set) ? set[0] : null;
            return !firstCard || Number(firstCard.set_id) !== numericSetId;
        });

        // 3. Crear el set combinado
        // Si encontramos el set antiguo, lo combinamos con las nuevas cartas.
        // Si no (setAntiguo es undefined), 'playedSet' ES el set completo (caso: Formar Set Nuevo)
        const setCombinado = setAntiguo
          ? [...setAntiguo, ...playedSet]
          : playedSet;

        // 4. Añadir el set nuevo/actualizado
        return [...otherSets, setCombinado];
      });
    }
    else {
      // Un oponente ha jugado un set  
      const pid = Number(setPlayed.player_id);
      upsertOpponentSet(pid, playedSet); // Pasamos las cartas nuevas
    }
    setSetPlayed(null);
  }, [setPlayed, playerId, upsertOpponentSet]);

  return {
    cardsPlayed,
    setsPropios,
    onSetPlayed,
    onSetStolen,
  };
}
