import { useState, useCallback } from 'react';
import { obtenerManoOponente, obtenerSecretosOponente } from '../../Oponente/oponenteService';

export async function refreshOpponent(
  prevId,
  currentTurnId,
  game_id,
  player_id,
  setMano,
  setOpponentHand,
  setOpponentSecrets 
) {
  if (prevId != null && prevId !== currentTurnId) {
    if (Number(prevId) === Number(player_id)) {
      return;
    }
    try {
      const [manoData, secretosData] = await Promise.all([
        obtenerManoOponente(game_id, prevId),
        obtenerSecretosOponente(game_id, prevId),
      ]);
      const nuevasCartas = manoData?.cards ?? [];
      setOpponentHand(prevId, nuevasCartas);
      setOpponentSecrets(prevId, secretosData ?? []);
    } catch (e) {
      console.error('Error al refrescar datos del jugador que terminó su turno:', e);
    }
  }
}

export function useOpponentsState(initial = {}) {
  const [opponentsDetailsById, setOpponentsDetailsById] = useState(initial);

  const ensure = useCallback((prev, pid) => {
    const key = Number(pid);
    return {
      key,
      current: prev[key] ?? { handCards: [], secretCards: [], detectiveSets: [] },
    };
  }, []);

  const setOpponentHand = useCallback((pid, handCards) => {
    setOpponentsDetailsById(prev => {
      const { key, current } = ensure(prev, pid);
      return { ...prev, [key]: { ...current, handCards: handCards ?? [] } };
    });
  }, [ensure]);

  const setOpponentSecrets = useCallback((pid, secretsOrUpdater) => {
    setOpponentsDetailsById(prev => {
      const { key, current } = ensure(prev, pid);
      const nextSecrets = typeof secretsOrUpdater === 'function'
        ? secretsOrUpdater(current.secretCards ?? [])
        : (secretsOrUpdater ?? []);
      return { ...prev, [key]: { ...current, secretCards: nextSecrets } };
    });
  }, [ensure]);

  const updateOpponentSecrets = useCallback((pid, updater) => {
    setOpponentSecrets(pid, prevSecrets => updater(prevSecrets ?? []));
  }, [setOpponentSecrets]);

  const upsertOpponentSet = useCallback((pid, newCards) => {
   const setId = newCards?.[0]?.set_id;
    if (setId == null) return;
    const numericSetId = Number(setId);

    setOpponentsDetailsById(prev => {
      const { key, current } = ensure(prev, pid);
      const currentSets = current.detectiveSets ?? [];

      // 1. Encontrar el set antiguo
      const setAntiguo = currentSets.find(set => {
          const first = Array.isArray(set) ? set[0] : set;
          return first && Number(first.set_id) === numericSetId;
      });

      // 2. Filtrar el set antiguo
      const otherSets = currentSets.filter(set => {
          const first = Array.isArray(set) ? set[0] : set;
          return !first || Number(first.set_id) !== numericSetId;
      });

      // 3. Crear el set combinado
      const setCombinado = setAntiguo
          ? [...setAntiguo, ...newCards]
          : newCards;
      
      // 4. Añadir el set nuevo/actualizado
      return {
        ...prev,
        [key]: { ...current, detectiveSets: [...otherSets, setCombinado] },
      };
    });
  }, [ensure]);

  const removeOpponentSet = useCallback((pid, setId) => {
    setOpponentsDetailsById(prev => {
      const { key, current } = ensure(prev, pid);
      const filtered = (current.detectiveSets ?? []).filter(set => {
        const first = Array.isArray(set) ? set[0] : set;
        return !first || Number(first.set_id) !== Number(setId);
      });
      return { ...prev, [key]: { ...current, detectiveSets: filtered } };
    });
  }, [ensure]);

  // Nuevo: remover cartas específicas de la mano del oponente
  const removeOpponentCardsFromHand = useCallback((pid, cardIds) => {
    if (!Array.isArray(cardIds) || cardIds.length === 0) return;
    const ids = new Set(cardIds.map(Number));
    setOpponentsDetailsById(prev => {
      const { key, current } = ensure(prev, pid);
      const filtered = (current.handCards ?? []).filter(c => !ids.has(Number(c.card_id)));
      return { ...prev, [key]: { ...current, handCards: filtered } };
    });
  }, [ensure]);

  return {
    opponentsDetailsById,
    setOpponentsDetailsById, // por compatibilidad
    setOpponentHand,
    setOpponentSecrets,
    updateOpponentSecrets,
    upsertOpponentSet,
    removeOpponentSet,
    removeOpponentCardsFromHand, 
  };
}