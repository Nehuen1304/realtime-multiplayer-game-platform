import {useCallback, useEffect, useState} from 'react';
import { selectCardLook } from '../../tableroService';

export function useSelectDrawCard(gameId, playerId, cardLook) {
    
    const selectCardLookHandler = useCallback(async () => {
        if (!gameId || !playerId || cardLook === null) return;
        try {
            const response = await selectCardLook(gameId, {
                player_id: playerId,
                card_id: cardLook
            });
            console.log("selectCardLook response:", response);
            return response;
        }
        catch (e) {
            console.error("Error selecting card look:", e);
            throw e;
        }
}   
    , [gameId, playerId, cardLook]);


    return { selectCardLookHandler };

}