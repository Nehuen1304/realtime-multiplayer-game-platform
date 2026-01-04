import { useCallback, useEffect, useMemo, useState } from 'react';
import { canAddToDetectiveSet, canFormDetectiveSet, canPlayEvent, canShareTextFromDetectiveSet, canShowEventText } from '../../utils/validator.js';
import { getDetectivePrincipal, getDetectiveText, getEventoText } from '../../utils/textoSugerencias.js';

// Maneja la selección de cartas en mano y los derivados (puede formar set, evento, etc.)
// Además calcula el texto de sugerencia de acción cuando corresponde
export function useCardSelection({ playSel, selectedCardIds, setSelectedCardIds, setsPropios, opponentsDetailsById } = {}) {
  const [selectTypesCardIds, setSelectTypesCardIds] = useState([]); // [type, id]
  const [actionSuggestionVisible, setActionSuggestionVisible] = useState(false);
  const [actionSuggestionText, setActionSuggestionText] = useState(null);
  const targetSetInfo = useMemo(() => {
    const setId = playSel?.targetSetId;
    if (!setId) return { type: null, isOwned: false }; // Valor por defecto

    let targetSet = null;
    let isOwned = false;

    // Buscar en sets propios
    if (Array.isArray(setsPropios)) {
      const mySet = setsPropios.find(set => set[0]?.set_id === setId);
      if (mySet) {
        targetSet = mySet;
        isOwned = true; // <-- ¡Lo encontramos! Es nuestro
      }
    }

    // Buscar en sets de oponentes (si no se encontró)
    if (!targetSet && opponentsDetailsById) {
      for (const opp of Object.values(opponentsDetailsById)) {
        const oppSet = (opp.detectiveSets || []).find(set => set[0]?.set_id === setId);
        if (oppSet) {
          targetSet = oppSet;
          isOwned = false; // <-- Es de un oponente
          break;
        }
      }
    }

    if (!targetSet) return { type: null, isOwned: false };

    // Extraer tipo principal
    const setTypesAndIds = targetSet.map(c => [c.card_type, c.card_id]);
    const type = getDetectivePrincipal(setTypesAndIds);

    return { type, isOwned }; // Devolvemos el objeto

  }, [playSel?.targetSetId, setsPropios, opponentsDetailsById]);
  const { type: targetSetType, isOwned: isTargetSetOwnedByMe } = targetSetInfo;
  // Estructura común para validaciones
  const selectionState = useMemo(() => ({
    selectedCardIds,
    selectTypesCardIds,
    targetPlayerId: playSel?.targetPlayerId ?? null,
    targetSecretId: playSel?.targetSecretId ?? null,
    targetCardId: playSel?.targetCardId ?? null,
    targetSetId: playSel?.targetSetId ?? null,
    targetSetType: targetSetType,
    isTargetSetOwnedByMe: isTargetSetOwnedByMe,
    actionType: playSel?.actionType ?? null
  }), [
    selectedCardIds,
    selectTypesCardIds,
    playSel?.targetPlayerId,
    playSel?.targetSecretId,
    playSel?.targetCardId,
    playSel?.targetSetId,
    playSel?.actionType,
    targetSetType,
    isTargetSetOwnedByMe
  ]);

  const puedeFormarSet = useMemo(() => canFormDetectiveSet(selectionState), [selectionState]);
  const puedeJugarEvento = useMemo(() => canPlayEvent(selectionState), [selectionState]);
  const puedeAgregarSet = useMemo(() => canAddToDetectiveSet(selectionState), [selectionState]);
  const puedeCompartirTexto = useMemo(() => canShareTextFromDetectiveSet(selectionState), [selectionState]);
  const puedeMostrarTextoEvento = useMemo(() => canShowEventText(selectionState), [selectionState]);


  // --- FIN DE LÓGICA MODIFICADA ---
  // Sugerencia de acción al detectar un set válido o una carta de evento
  useEffect(() => {
    if (puedeAgregarSet && targetSetType) {
      // Muestra la sugerencia del set al que vas a añadir
      const detectiveText = getDetectiveText(targetSetType);
      setActionSuggestionText(detectiveText);
      setActionSuggestionVisible(true);
    }
    else if (puedeCompartirTexto) {
      const detectiveType = getDetectivePrincipal(selectTypesCardIds);
      const detectiveText = getDetectiveText(detectiveType);
      setActionSuggestionText(`${detectiveType} - ${detectiveText}`);
      setActionSuggestionVisible(true);
    } else if (puedeMostrarTextoEvento) {
      const eventoType = selectTypesCardIds[0][0];
      const eventoText = getEventoText(eventoType);
      setActionSuggestionText(eventoText);
      setActionSuggestionVisible(true);
    } else {
      setActionSuggestionVisible(false);
      setActionSuggestionText(null);
    }
  }, [puedeCompartirTexto, puedeMostrarTextoEvento, selectTypesCardIds, puedeAgregarSet, targetSetType]);

  // Toggle selección de carta: mantiene ids y tuplas [type, id]
  const toggleSelectCard = useCallback((carta) => {
    setSelectedCardIds(prev =>
      prev.includes(carta.card_id)
        ? prev.filter(id => id !== carta.card_id)
        : [...prev, carta.card_id]
    );

    setSelectTypesCardIds(prev => {
      const list = Array.isArray(prev) ? prev : [];
      const typeStr = String(carta.card_type);
      const idNum = Number(carta.card_id);
      const exists = list.some(([t, i]) => String(t) === typeStr && Number(i) === idNum);
      return exists
        ? list.filter(([t, i]) => !(String(t) === typeStr && Number(i) === idNum))
        : [...list, [typeStr, idNum]];
    });
  }, []);

  const resetSelection = useCallback(() => {
    if (typeof setSelectedCardIds === 'function') setSelectedCardIds([]);
    setSelectTypesCardIds([]);
  }, [setSelectedCardIds]);

  return {
    selectedCardIds,
    selectTypesCardIds,
    actionSuggestionVisible,
    actionSuggestionText,
    puedeFormarSet,      // ← Para habilitar botón "Jugar Set"
    puedeJugarEvento,
    puedeAgregarSet,
    selectionState,
    toggleSelectCard,
    resetSelection,
    // setSelectedCardIds is external
  };
}
