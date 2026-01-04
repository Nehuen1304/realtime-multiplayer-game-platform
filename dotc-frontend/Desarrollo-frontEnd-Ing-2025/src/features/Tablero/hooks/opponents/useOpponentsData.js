
import { useEffect, useMemo,useCallback, useState } from 'react';

import { obtenerManoOponente, obtenerSecretosOponente } from '../../Oponente/oponenteService.js';
import{getSortedPlayers}from '../../tableroService.js'
export function useOpponentsData({
    gameId,
    myPlayerId,
    players,
    currentTurnId,
    opponentsDetailsById,
    setOpponentHand,
    setOpponentSecrets,
    sdPlayers,
}) {
 // Dentro de useOpponentsData.js
// Dentro de useOpponentsData.js
const [sortedPlayersList, setSortedPlayersList] = useState([]);

    // --- 2. Hook para llamar al endpoint /players/sorted ---
    useEffect(() => {
        if (!gameId) return;
        
        let cancelled = false;
        
        (async () => {
            try {
                // Llama al servicio que implementa GET /api/games/{game_id}/players/sorted
                const sortedList = await getSortedPlayers(gameId); 
                
                if (!cancelled) {
                    setSortedPlayersList(sortedList || []);
                }
                console.log("LISTA DE JUGADORES", sortedList)
            } catch (err) {
                console.error("Error al obtener jugadores ordenados:", err);
            }
        })();

        return () => { cancelled = true; };
    }, [gameId]); // Se ejecuta solo cuando cambia gameId

    // --- 3. Memo para calcular oponentes (con rotación) ---
    // ¡Esta es la versión limpia!
    const opponents = useMemo(() => {
        
        // Si aún no tenemos la lista ordenada, devolvemos array vacío
        if (sortedPlayersList.length === 0) {
            return [];
        }

        // ¡Usamos la lista del estado! Esta es la lista ORDENADA
        const allPlayers = sortedPlayersList; 

        // 1. Encontrar tu índice en la lista ORDENADA
        const myIdNum = Number(myPlayerId);
        const myIndex = allPlayers.findIndex(p => Number(p.player_id) === myIdNum);

        if (myIndex === -1) {
            // Caso de seguridad: si no te encuentras
            console.warn("useOpponentsData: No se encontró al jugador actual en la lista ordenada.");
            // Usamos la prop 'players' (desordenada) como fallback
            return (players || []).filter(p => Number(p.player_id) !== myIdNum);
        }

        // 2. Rotar la lista ORDENADA
        const playersAfterMe = allPlayers.slice(myIndex + 1);
        const playersBeforeMe = allPlayers.slice(0, myIndex);

        // La lista ordenada de oponentes para renderizar
        const sortedOpponents = [...playersAfterMe, ...playersBeforeMe];

        return sortedOpponents;

    }, [sortedPlayersList, myPlayerId, players]); // Depende de la lista ordenada

    
    // --- 4. Hook para cargar datos de oponentes (Mano/Secretos) ---
    // (Esta lógica no cambia)
    useEffect(() => {
        let cancelled = false;
        (async () => {
            if (!gameId || opponents.length === 0) return;

            const results = await Promise.allSettled(
                opponents.map(async (p) => {
                    const [manoData, secretosData] = await Promise.all([
                        obtenerManoOponente(gameId, p.player_id),
                        obtenerSecretosOponente(gameId, p.player_id),
                    ]);
                    return { pid: p.player_id, handCards: manoData?.cards ?? [], secretCards: secretosData ?? [] };
                })
            );

            if (cancelled) return;

            results.forEach(r => {
                if (r.status !== 'fulfilled') return;
                const { pid, handCards, secretCards } = r.value;
                setOpponentHand(pid, handCards);
                setOpponentSecrets(pid, secretCards);
            });
        })();

        return () => { cancelled = true; };
    }, [gameId, opponents, setOpponentHand, setOpponentSecrets]); // 'opponents' ya viene ordenado

    // --- 5. Memo para datos finales de oponentes ---
    // (Esta lógica no cambia)
    const opponentsData = useMemo(() => {
        return opponents.map((p) => ({
            player_id: p.player_id,
            player_name: p.player_name,
            isTurn: p.player_id === currentTurnId,
            handCards: opponentsDetailsById[p.player_id]?.handCards ?? [],
            secretCards: opponentsDetailsById[p.player_id]?.secretCards ?? [],
            detectiveSets: opponentsDetailsById[p.player_id]?.detectiveSets ?? [],
            socialDisgrace: !!sdPlayers?.has(Number(p.player_id)),
        }));
    }, [opponents, currentTurnId, opponentsDetailsById, sdPlayers]);

  const reloadOpponentSecrets = useCallback(async (opponentId) => {
        if (!gameId || !opponentId) return;
        try {
            // Llama al servicio para obtener solo los secretos de ese oponente
            const secretosData = await obtenerSecretosOponente(gameId, opponentId);
            // Actualiza el estado usando la función del padre
            setOpponentSecrets(opponentId, secretosData ?? []);
        } catch (err) {
            console.error("Fallo al recargar secretos para oponente ${opponentId}:, err");
        }
    }, [gameId, setOpponentSecrets]);

    return { opponentsData,reloadOpponentSecrets };
}

 