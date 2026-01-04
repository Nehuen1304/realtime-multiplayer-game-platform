import { getApiUrl } from '../../../config/api.js';

/**
 * Gestiona la respuesta de la API, lanzando un error si no es exitosa.
 * @param {Response} response - El objeto de respuesta de fetch.
 * @returns {Promise<any>} Una promesa que resuelve al JSON de la respuesta.
 */
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Ocurrió un error en la API');
  }
  return response.json();
};

/**
 * Obtiene las cartas en la mano de un oponente específico.
 * @param {number} gameId - El ID de la partida.
 * @param {number} playerId - El ID del jugador oponente.
 * @returns {Promise<Array<object>>} Una promesa que resuelve a un array de cartas en la mano.
 */
export const obtenerManoOponente = async (gameId, playerId) => {
  const response = await fetch(getApiUrl(`/api/games/${gameId}/players/${playerId}/hand`));
  return handleResponse(response);
};

/**
 * Obtiene las cartas de secreto de un oponente específico.
 * @param {number} gameId - El ID de la partida.
 * @param {number} playerId - El ID del jugador oponente.
 * @returns {Promise<Array<object>>} Una promesa que resuelve a un array de cartas de secreto.
 */
export const obtenerSecretosOponente = async (gameId, playerId) => {
  const response = await fetch(getApiUrl(`/api/games/${gameId}/players/${playerId}/secrets`));
  const data = await handleResponse(response);
  return data.secrets; // Devuelve solo el array de secretos
};
  // return {secrets:[
  //   {
  //     id: 3,
  //     type: 'Innocent',
  //     is_revealed: false
  //   },
  //   {
  //     id: 6,
  //     type: 'Innocent',
  //     is_revealed: true
  //   },
  //   {
  //     id: 5,
  //     type: 'Innocent',
  //     is_revealed: false
  //   }
  // ]};
