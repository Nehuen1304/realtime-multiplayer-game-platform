import { useCallback, useMemo, useState } from 'react';
import { playCard } from '../../tableroService'; 

export function usePlaySelection({ selectedCardIds, setSelectedCardIds, initial = {} }) {
  if (!Array.isArray(selectedCardIds) || typeof setSelectedCardIds !== 'function') {
    throw new Error('usePlaySelection requires { selectedCardIds: Array, setSelectedCardIds: Function }');
  }

  const [actionType, setActionType] = useState(initial.actionType || null);
  const [targetPlayerId, setTargetPlayerId] = useState(initial.targetPlayerId ?? null);
  const [targetSecretId, setTargetSecretId] = useState(initial.targetSecretId ?? null);
  const [targetCardId, setTargetCardId] = useState(initial.targetCardId ?? null);
  const [targetSetId, setTargetSetId] = useState(initial.targetSetId ?? null);

 
  const toggleTargetPlayer = useCallback((id) => {
    setTargetPlayerId(prev => {
      const prevNum = prev == null ? null : Number(prev);
      const idNum = id == null ? null : Number(id);
      const newVal = (prevNum !== null && prevNum === idNum) ? null : idNum;
      console.log(newVal);
      return newVal;
    });
  }, []);

  const toggleTargetSecret = useCallback((id, player_id) => {
    setTargetSecretId(prev => {
      const prevNum = prev == null ? null : Number(prev);
      const idNum = id == null ? null : Number(id);
      const newVal = (prevNum !== null && prevNum === idNum) ? null : idNum;
      console.log(newVal);
      return newVal;
    });
    if(targetPlayerId !== player_id){
      setTargetPlayerId(player_id);
    };
  }, []);

  const toggleTargetCard = useCallback((id,player_id) => {
    setTargetCardId(prev => {
      const prevNum = prev == null ? null : Number(prev);
      const idNum = id == null ? null : Number(id);
      const newVal = (prevNum !== null && prevNum === idNum) ? null : idNum;
      console.log(newVal);
      return newVal;
    });
    if(targetPlayerId !== player_id){
      setTargetPlayerId(player_id);
    };

  }, []);

  const toggleTargetSet = useCallback((id,player_id) => {
    setTargetSetId(prev => {
      const prevNum = prev == null ? null : Number(prev);
      const idNum = id == null ? null : Number(id);
      const newVal = (prevNum !== null && prevNum === idNum) ? null : idNum;
      console.log(newVal);
      return newVal;
    });
    if (targetPlayerId !== player_id) {
      setTargetPlayerId(player_id == null ? null : Number(player_id));
    }
  
  }, []);


  const resetSelection = useCallback(() => {
    setActionType(null);
    setSelectedCardIds([]);
    setTargetPlayerId(null);
    setTargetSecretId(null);
    setTargetCardId(null);
    setTargetSetId(null);
  }, []);

  /*
  {
  "player_id": 0,
  "game_id": 0,
  "action_type": "PLAY_EVENT",
  "card_ids": [
    0
  ],
  "target_set_id": 0,
  "target_player_id": 0,
  "target_secret_id": 0,
  "target_card_id": 0
} */


  
 const selection = useCallback((game_id, player_id) => ({
    player_id: player_id,
    game_id: game_id,
    action_type: actionType, // espera "PLAY_EVENT" | "FORM_NEW_SET" | "ADD_TO_EXISTING_SET"
    card_ids: Array.isArray(selectedCardIds) ? selectedCardIds.map(id => Number(id)) : [],
    target_set_id: targetSetId ?? null,
    target_player_id: targetPlayerId ?? null,
    target_secret_id: targetSecretId ?? null,
    target_card_id: targetCardId ?? null
  }), [actionType, selectedCardIds, targetPlayerId, targetSecretId, targetCardId, targetSetId]);


  const canPlay = useMemo(() => {
    if (!actionType) return false;
    if (!Array.isArray(selectedCardIds) || selectedCardIds.length === 0) return false;
    return true;
  }, [actionType, selectedCardIds]);




const play = useCallback(async (gameId, playerId) => {
    if (gameId==null) {
      throw new Error('play requires { gameId }');
    }
    if (playerId==null) {
      throw new Error('play requires { playerId }');
    }

    if (!canPlay) {
      throw new Error('Selección inválida o no puedes jugar ahora');
    }

    // Construir payload siguiendo el contrato de la API
    const payload = selection(gameId, playerId);
    try {
      const response = await playCard(gameId, payload);
      // Se asume que playCard devuelve la respuesta JSON o arroja si status != ok
      // Al retornar éxito, se limpia la selección local
      resetSelection();
      return response;
    } catch (err) {
      throw err;
    }
  }, [canPlay, selection, resetSelection]);


  return {
    selection,
    actionType,
    setActionType,
    targetPlayerId,   
    setTargetPlayerId,
    targetSecretId,   
    targetCardId,     
    targetSetId,  
    toggleTargetPlayer,
    toggleTargetSecret,
    toggleTargetCard,
    toggleTargetSet,
    resetSelection,
    canPlay,
    play
  };
}