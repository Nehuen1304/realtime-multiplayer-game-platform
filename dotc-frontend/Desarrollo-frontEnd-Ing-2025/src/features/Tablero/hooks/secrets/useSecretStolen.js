// En: hooks/game/useStolenSecretHandler.js

import { useCallback } from 'react';

/**
 * Este hook encapsula la lógica para manejar el evento de WebSocket 'SECRET_STOLEN'.
 * Recibe las dependencias (ID del jugador y funciones de recarga)
 * y devuelve el manejador 'onSecretStolen' memoizado.
 */
export function useStolenSecretHandler({
  playerId,
  secretPlayer, // de usePlayerSecret
  reloadOpponentSecrets, // de useOpponentsData
}) {
  const onSecretStolen = useCallback(
    (thief_id, victim_id) => {
      // Comprobación de seguridad
      console.log("Playe", playerId)
      console.log("SECRET", secretPlayer)
      console.log("RELOAD", reloadOpponentSecrets)
      if (!playerId || !secretPlayer || !reloadOpponentSecrets) {
        console.warn('useStolenSecretHandler no está listo, faltan dependencias.');
        return;
      }

      console.log(
     "Recibido SECRET_STOLEN: Ladrón: ${thief_id}, Víctima: ${victim_id}"
      );

      // --- Recargar al Ladrón ---
      if (Number(thief_id) === Number(playerId)) {
        console.log('Soy el ladrón, recargando mis secretos...');
        secretPlayer(); //
      } else {
        console.log('Recargando secretos del ladrón oponente ${thief_id}...');
        reloadOpponentSecrets(thief_id); //
      }

      // --- Recargar a la Víctima ---
      if (Number(victim_id) === Number(playerId)) {
        console.log('Soy la víctima, recargando mis secretos...');
        secretPlayer(); //
      } else {
        console.log("Recargando secretos de la víctima oponente ${victim_id}...");
        reloadOpponentSecrets(victim_id); //
      }
    },
    [playerId, secretPlayer, reloadOpponentSecrets] // Dependencias del useCallback
  );

  // Devuelve el manejador
  return { onSecretStolen };
}