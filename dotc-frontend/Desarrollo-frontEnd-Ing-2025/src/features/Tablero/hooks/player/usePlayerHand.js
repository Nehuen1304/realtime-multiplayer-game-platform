// Hook para cargar y manejar la mano del jugador
import { useState, useEffect, useCallback } from 'react';
import * as tableroService from '../../tableroService.js';

export function usePlayerHand(gameId, playerId) {
  const [mano, setMano] = useState([]);
  const [cargandoMano, setCargandoMano] = useState(false);
  const [errorMano, setErrorMano] = useState(null);

  const cargarMano = useCallback(async () => {
    if (!gameId || !playerId) return;
    setCargandoMano(true);
    setErrorMano(null);
    try {
      const res = await tableroService.getManoJugador(gameId, playerId);
      console.log(res);
      setMano(res.cards || []);
    } catch (e) {
      setErrorMano(e.message);
    } finally {
      setCargandoMano(false);
    }
  }, [gameId, playerId]);

  useEffect(() => { cargarMano(); }, [cargarMano]);

  return { mano, setMano, cargarMano, cargandoMano, errorMano };
}