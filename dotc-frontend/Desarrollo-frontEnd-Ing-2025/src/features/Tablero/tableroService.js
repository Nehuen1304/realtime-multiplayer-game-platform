import { API_CONFIG, getApiUrl } from '../../config/api.js';

const apiRequest = async (url, options = {}) => {
    const response = await fetch(url, options);
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error fetching data' }));
        throw new Error(errorData.detail || 'API request failed');
    }
    return response.json();
};


/**
 * Obtiene el estado completo de una partida.
 * @param {string} gameId - El ID de la partida.
 * @returns {Promise<object>} - Los datos de la partida.
 */
export const getGameState = (gameId) => {
    return apiRequest(getApiUrl(`/api/games/${gameId}`));
};

/**
 * Obtiene la mano de un jugador específico.
 * @param {string} gameId - El ID de la partida.
 * @param {string} playerId - El ID del jugador.
 * @returns {Promise<object>} - La mano del jugador.
 */
export const getManoJugador = (gameId, playerId) => {
    return apiRequest(getApiUrl(`/api/games/${gameId}/players/${playerId}/hand`));
};

/**
 * Consulta el número de cartas en el mazo de robo.
 * @param {string} gameId - El ID de la partida.
 * @returns {Promise<number>} - El número de cartas.
 */
export const getDeckSize = async (gameId) => {
    const data = await apiRequest(getApiUrl(`/api/games/${gameId}/size_deck`));
    const value = Number(data?.size_deck);
    return Number.isFinite(value) ? value : 0;
};

/**
 * Ejecuta la acción de robar una carta.
 * @param {string} gameId - El ID de la partida.
 * @param {string} playerId - El ID del jugador que roba.
 * @returns {Promise<object>} - La respuesta de la acción.
 */
export const drawCard = (gameId, sendb) => {
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sendb)
    };
    return apiRequest(getApiUrl(`/api/games/${gameId}/actions/draw`), options);
};

/**
 * Ejecuta la acción de robar una carta del draft.
 * @param {string} gameId - El ID de la partida.
 * @param {string} playerId - El ID del jugador.
 * @param {number} cardIndex - El índice de la carta en el draft.
 * @returns {Promise<object>} - La respuesta de la acción.
 */
export async function drawDraftCard(gameId, playerId, cardId) {
    const options = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            player_id: playerId,
            game_id: gameId,
            source: "draft",
            card_id: cardId
        })
    };
    return apiRequest(getApiUrl(`/api/games/${gameId}/actions/draw`), options);
};


/**
 * Ejecuta la acción de jugar una carta / set / evento.
 * @param {string|number} gameId - El ID de la partida.
 * @param {object} sendb - El body de la petición con la forma acordada por la API.
 * @returns {Promise<object>} - La respuesta de la API.
 */
export const playCard = async (gameId, sendb = {}) => {
    const payload = {
        ...sendb
    };
    console.log('playCard endpoint. payload: ', payload);
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    };
    console.log('sending playCard. payload: ', payload);
    return apiRequest(getApiUrl(`/api/games/${gameId}/actions/play`), options);
};

export const playCardsOffTheTable = async (gameId, targetPlayerId, cardId, playerId) => {
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            player_id: playerId,
            action_type: 'PLAY_EVENT',
            card_ids: [cardId],
            target_player_id: targetPlayerId
        })
    };
    return apiRequest(getApiUrl(`/api/games/${gameId}/actions/play`), options);
};

export const selectCardLook = async (gameId, sendb) => {
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sendb)
    };
    return apiRequest(getApiUrl(`/api/games/${gameId}/actions/draw`), options);
}

export const exchangeCard = async (gameId, { player_id, game_id: bodyGameId, card_id }) => {
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            player_id,
            game_id: bodyGameId ?? gameId,
            card_id
        })
    };
    return apiRequest(getApiUrl(`/api/games/${gameId}/actions/exchange-card`), options);
};

/**
 * Envía una sospecha (voto) sobre un jugador.
 * @param {string|number} gameId - El ID de la partida.
 * @param {number} suspectId - El ID del jugador sospechoso.
 * @returns {Promise<object>} - La respuesta de la API.
 */
export const sendVote = async (gameId, playerId, votedPlayerId) => {
    const payload = {
        player_id: Number(playerId),
        game_id: Number(gameId),
        voted_player_id: Number(votedPlayerId)
    };
    console.log('sendVote, payload:', payload);
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    };
    return apiRequest(getApiUrl(`/api/games/${gameId}/actions/vote`), options);
};

export const playNSF = async (gameId, body) => {
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    };
    return apiRequest(getApiUrl(`/api/games/${gameId}/actions/play-nsf`), options);
};

/**
 * Obtiene la lista de jugadores de la partida, ordenada por turno.
 * @param {string | number} gameId - El ID de la partida.
 * @returns {Promise<Array<Object>>} - La lista de jugadores ordenada.
 */
export const getSortedPlayers = (gameId) => {
    if (!gameId) {
        // Rechazamos la promesa si no hay gameId
        return Promise.reject(new Error('getSortedPlayers requiere un gameId'));
    }
    
    // Construimos la URL usando el helper
    const url = getApiUrl(`/api/games/${gameId}/players/sorted`);
    
    // Usamos la función base 'apiRequest' para la petición GET
    return apiRequest(url);
};