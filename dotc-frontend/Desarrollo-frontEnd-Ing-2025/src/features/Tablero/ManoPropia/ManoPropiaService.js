import { getApiUrl } from '../../../config/api.js';
import { handleResponse } from '../../ListadoDePartidas/apiService.js';

const apiRequest = async (url, options = {}) => {
    console.log('API request to:', url, options && options.method);
    const res = await fetch(url, options);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(err.detail || 'API error');
    }
    return res.json();
};


/**
 * Realiza la acción de descartar una carta.
 * POST /api/games/{game_id}/actions/discard
 * @param {int} gameId - El ID de la partida.
 * @param {object} data - El cuerpo de la petición, ej: { player_id: string, card_id: string }.
 * @returns {Promise<object>} La respuesta de la API.
 */


export const descartarCarta = async (data) => {
    const response = await fetch(getApiUrl(`/api/games/${data.game_id}/actions/discard`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return handleResponse(response);
};
/**
 * Realiza la acción de pasar/finalizar el turno.
 * POST /api/games/{game_id}/actions/finish-turn
 * @param {int} gameId - El ID de la partida.
 * @param {object} data - El cuerpo de la petición, ej: { player_id: string }.
 * @returns {Promise<object>} La respuesta de la API.
 */
export const pasarTurno = async (data) => {
    const response = await fetch(getApiUrl(`/api/games/${data.game_id}/actions/finish-turn`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    console.log(response);
    return handleResponse(response);
};


export const getGame= async(gameId)=>{
    const response = await fetch(getApiUrl(`/api/games/${gameId}`));
    return handleResponse(response);

}
/**
 * Obtiene las cartas en la mano de un jugador.
 * GET /api/games/{game_id}/players/{player_id}/hand
 * @param {number} gameId - El ID de la partida.
 * @param {number} playerId - El ID del jugador.
 * @returns {Promise<object>} La respuesta de la API con la lista de cartas.
 */
export const getManoJugador = async (gameId, playerId) => {
    const response = await fetch(getApiUrl(`/api/games/${gameId}/players/${playerId}/hand`));
    return handleResponse(response);
};

/**
 * Obtiene las cartas de secretos de un jugador.
 * GET /api/games/{game_id}/players/{player_id}/secrets
 * @param {int} gameId - El ID de la partida.
 * @param {int} playerId - El ID del jugador.
 * @returns {Promise<object>} La respuesta de la API con la lista de secretos.
 */
export const getSecretosJugador = (gameId, playerId) => {
    return apiRequest(getApiUrl(`/api/games/${gameId}/players/${playerId}/secrets`));
};

/**
 * Revela un secreto del jugador.
 * POST /api/games/{game_id}/actions/reveal-secret
 * body: { player_id, game_id, secret_id }
 */
export const revelarSecreto = async (data) => {
  const response = await fetch(getApiUrl(`/api/games/${data.game_id}/actions/reveal-secret`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return handleResponse(response);
};