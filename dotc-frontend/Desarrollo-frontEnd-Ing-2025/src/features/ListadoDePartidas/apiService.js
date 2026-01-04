import { getApiUrl } from '../../config/api.js';

export const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Ocurrió un error en la API');
  }
  return response.json();
};

export const obtenerPartidas = async () =>{
   const listPartidas = await fetch(getApiUrl('/api/games'));
    return handleResponse(listPartidas);
}

/**
 * @typedef {object} DatosUnirsePartida
 * @property {int} player_id - El ID o nombre del jugador que intenta unirse.
 * @property {int} game_id - El ID de la partida a la que se quiere unir.
 * @property {string} [password] - (Opcional) La contraseña de la partida si es privada.
 */
/**
 * Permite a un jugador unirse a una partida.
 * Endpoint: POST /join (o /partidas/unirse, asegúrate de que la URL sea correcta)
 * @param {DatosUnirsePartida} datosParaUnirse - El objeto con los datos para unirse.
 * @returns {Promise<object>} Una promesa que resuelve a la respuesta de la API.
 */
export const unirsePartida = async(datosParaUnirse)=>{
    const responseUnirse = await fetch(getApiUrl(`/api/games/${datosParaUnirse.game_id}/join`),
        {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify(datosParaUnirse)
        });
        return handleResponse(responseUnirse);
    }

/**
 * CREAR UNA NUEVA PARTIDA
 * Endpoint: POST /partidas
  * @typedef {object} DatosNuevaPartida
 * @property {string} game_name - El nombre que el host le da a la partida.
 * @property {string} host_name - El nombre del jugador que crea la partida.
 * @property {number} min_players - El número mínimo de jugadores requeridos.
 * @property {number} max_players - El número máximo de jugadores permitidos.
 */
/**
 * CREAR UNA NUEVA PARTIDA
 * Endpoint: POST /partidas
 * @param {DatosNuevaPartida} datosPartida - El objeto con la configuración de la nueva partida.
 * @returns {Promise<object>} Una promesa que resuelve al objeto de la partida recién creada.
 */
export const crearPartida = async (datosDeLaPartida) =>{
        const response = await fetch(getApiUrl('/api/games'),{
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify(datosDeLaPartida)
        });
        return handleResponse(response); 
}