
import { getApiUrl } from '../../config/api.js';

// Get the current game state (includes players)
export async function getGameState(gameId) {
    const res = await fetch(getApiUrl(`/api/games/${gameId}`));
    if (!res.ok) throw new Error("No se pudo obtener el estado de la partida");
    return await res.json();
}

// Start the game (host only)
export async function startGame(gameId, playerId) {
    console.log("Iniciando partida:", { gameId, playerId });
    const res = await fetch(getApiUrl(`/api/games/${gameId}/start`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Enviando el cuerpo como lo requiere tu backend
        body: JSON.stringify({ 
            player_id: Number(playerId), // Aseguramos que sean números
            game_id: Number(gameId)
        })
    });
    
    if (!res.ok) {
        // Si hay un error, intenta leer el detalle del error del backend
        const errorData = await res.json();
        throw new Error(errorData.detail || "No se pudo iniciar la partida");
    }
    return await res.json();

};

export async function cancelGame(gameId, playerId) {
    
    const res = await fetch(getApiUrl(`/api/games/${gameId}/leave`),{

        method:'POST',
         headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            player_id: Number(playerId), // Aseguramos que sean números
            game_id: Number(gameId)
        })
    })

    console.log("CANCELAR", res)
    if (!res.ok) {
  
        const errorData = await res.json().catch(() => ({})); 
        throw new Error(errorData.detail || "No se pudo abandonar la partida");
    }

    return res.json();
}