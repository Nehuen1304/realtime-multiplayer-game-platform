// Encapsula acciones de turno (robar, descartar, pasar)
import { useCallback, useState } from 'react';
import * as apiService from '../../ManoPropia/ManoPropiaService.js';
import * as tableroService from '../../tableroService.js';
import { useGameState } from './useGameState.js';

export function useTurnActions({
	gameId,
	playerId,
	mano,
	setMano,
	esMiTurno,
	setAccionRealizada,
	setSelectedCardIds,
	draftCards,
	setDraftCards,
	discardCard,
	setDiscardCard,
	setAlerta
}) {

	// Generalizado: robar desde draw, discard o draft
	const robarDesdeFuente = useCallback(async (fuente, cartaId = null) => {
		if (!esMiTurno) setAlerta({ 
                titulo: "Acción no válida", 
                mensaje: "No es tu turno", 
                tipo: "warning" 
            });
		// if (mano.length >= 6) return alert("No puedes robar teniendo 6 cartas o más en mano");
		try {
			console.log("Robando")
			let carta = null;
			if (fuente === 'draw') {
				const sendb = {
					player_id: playerId,
					game_id: gameId,
					source: "deck"
				}
				const res = await tableroService.drawCard(gameId, sendb);
				if (res.response_status === 'INVALID_ACTION' || !res.drawn_card) {
					
					setAlerta({ 
                        titulo: "Acción no válida", 
                        mensaje: "No puedes robar una carta ahora.", 
                        tipo: "warning" 
                    });
					return;
				}
				carta = res.drawn_card;
			} else if (fuente === 'draft') {
				// Buscar la carta en el draft usando card_id
				const cartaObj = draftCards.find(c => c.card_id === cartaId);
				if (!cartaObj) {
					setAlerta({ 
                        titulo: "Error", 
                        mensaje: "Carta no encontrada en el draft.", 
                        tipo: "error" 
                    });
					return;
				}
				const res = await tableroService.drawDraftCard(gameId, playerId, cartaObj.card_id); // <-- BIEN: envía el card_id
				if (res.response_status === 'INVALID_ACTION' || !res.drawn_card) {
					setAlerta({ 
                        titulo: "Acción no válida", 
                        mensaje: "No puedes robar una carta del draft ahora.", 
                        tipo: "warning" 
                    });
					return;
				}

				carta = res.drawn_card;
				// setDraftCards(prev => prev.filter((_, idx) => idx !== cardIndex));
			}
			
			console.log(carta);
			if (carta) {
				setAccionRealizada(true);
				// Refresca la mano desde el backend
				const nueva = await tableroService.getManoJugador(gameId, playerId);
				return nueva.cards || []; // Devolver la nueva mano
			}
		} catch (e) {
			console.log("Error al robar:", e.message);
			setAlerta({ 
                titulo: "Error de Red", 
                mensaje: `Error al robar carta: ${e.message}`, 
                tipo: "error" 
            });
		}
		return null; // Devolver null si no hay cambios
	}, [esMiTurno, gameId, playerId, setMano, setAccionRealizada, draftCards, setDraftCards, discardCard, setDiscardCard]);

	const descartarCarta = useCallback(async (selectedCardIds) => {
		if (!esMiTurno || selectedCardIds.length === 0) return;
		try {
			// Descarta en backend
			console.log("cartas_por_descartar: ", selectedCardIds);
			await Promise.all(
				selectedCardIds.map(id => apiService.descartarCarta({ game_id: gameId, player_id: playerId, card_id: id }))
			);
			setSelectedCardIds([]); // Resetear array
			setAccionRealizada(true);
			console.log("mano vieja", mano);
			// refrescar mano (fuente de verdad)
			const nueva = await tableroService.getManoJugador(gameId, playerId);
			console.log("mano nueva", nueva);
			return nueva.cards || [];
		} catch (e) {
			console.log("Error al descartar:", e.message);
			setAlerta({ 
                titulo: "Error de Red", 
                mensaje: `Error al descartar: ${e.message}`, 
                tipo: "error" 
            });
		}
	}, [esMiTurno, gameId, playerId, setAccionRealizada, setSelectedCardIds]);

	const pasarTurno = useCallback(async (currentHandLength) => {
		console.log("pasarTurno");
		if (!esMiTurno) setAlerta({ 
                titulo: "Acción no válida", 
                mensaje: "No es tu turno", 
                tipo: "warning" 
            });
		// console.log("Intentando pasar turno. Cartas en mano:", mano.length);
		// regla original: solo si ya hizo algo y tiene >= 6 cartas
		if (currentHandLength >= 6) {
			try {
				console.log("player_id: ", playerId, "pasando turno");
				await apiService.pasarTurno({ player_id: playerId, game_id: gameId });
				setAccionRealizada(true);
			} catch (e) {
				console.log("Error al pasar turno:", e.message);
				setAlerta({ 
                    titulo: "Error de Red", 
                    mensaje: `Error al pasar turno: ${e.message}`, 
                    tipo: "error" 
                });
			}
		} else {
			setAlerta({ 
                titulo: "Acción no válida", 
                mensaje: "Debes tener al menos 6 cartas para pasar el turno.", 
                tipo: "warning" 
            });
		}
	}, [esMiTurno, gameId, playerId, setAccionRealizada]);

	return { robarDesdeFuente, descartarCarta, pasarTurno };
}