import { useCallback, useEffect, useRef } from 'react';
import * as tableroService from '../../tableroService.js';

export function useTableroHandlers({
    mano,
    setMano,
    esMiTurno,
    robarDesdeFuente,
    setAlerta,
    selectedCardIds,
    descartarCarta,
    accionRealizada,
    toggleSelectCard,
    pasarTurno,
    game_id,
    player_id,
    playSel,
    nsfWindowOpen,
    removeOpponentCardsFromHand,
    setActionSuggestionVisible,
    tradeRequest,
    setTradeRequest,
    setVotePrompt,
}) {
    // Refs para evitar closures obsoletos
    const nsfWindowOpenRef = useRef(nsfWindowOpen);
    const accionRealizadaRef = useRef(accionRealizada);

    useEffect(() => { nsfWindowOpenRef.current = nsfWindowOpen; }, [nsfWindowOpen]);
    useEffect(() => { accionRealizadaRef.current = accionRealizada; }, [accionRealizada]);

    const handleRobarDraw = useCallback(async () => {
        if (mano.length >= 6) {
            setAlerta({ mensaje: "No puedes robar teniendo 6 cartas o más en mano ⚠️", tipo: "warning" });
            return;
        }
        const nuevaMano = await robarDesdeFuente('draw');
        if (nuevaMano) {
            setMano(nuevaMano);
        }
    }, [robarDesdeFuente, setMano, mano.length, setAlerta]);

    const handleRobarDraft = useCallback(async (id) => {
        if (!esMiTurno) {
            setAlerta({ mensaje: "No puedes robar porque no es tu turno ⚠️", tipo: "warning" });
        }
        if (mano.length >= 6) {
            setAlerta({ mensaje: "No puedes robar teniendo 6 cartas o más en mano ⚠️", tipo: "warning" });
            return;
        }
        const nuevaMano = await robarDesdeFuente('draft', id);
        if (nuevaMano) {
            setMano(nuevaMano);
        }
    }, [robarDesdeFuente, setMano, mano.length, esMiTurno, setAlerta]);

    const handleRobarDiscard = useCallback(async () => {
        // Implementar si es necesario
    }, []);

    const handleSelectCard = useCallback((carta) => {
        const isNSF = String(carta?.card_type) === 'Not So Fast';
        const nsfOpen = nsfWindowOpenRef.current;
        const accionDone = accionRealizadaRef.current;

        // Permitir selección si la ventana NSF está abierta o si la carta es NSF (preselección)
        if (!nsfOpen && accionDone && !isNSF) {
            console.log('⚠️ handleSelectCard bloqueado: acción ya realizada', { nsfOpen, accionDone, carta: carta?.card_id });
            return;
        }
        console.log('✅ handleSelectCard: seleccionando carta', carta?.card_id, { nsfOpen, accionDone, isNSF });
        toggleSelectCard(carta);
    }, [toggleSelectCard]);

    const handleDiscard = useCallback(async () => {
        if (selectedCardIds.length === 0) return;
        setActionSuggestionVisible(false);
        const nuevaMano = await descartarCarta(selectedCardIds);
        if (nuevaMano) {
            setMano(nuevaMano);
        }
    }, [selectedCardIds, descartarCarta, setMano, setActionSuggestionVisible]);

    const handlePassTurn = useCallback(() => {
        if (!accionRealizada) {
            setAlerta({ mensaje: "Debes realizar una acción antes de pasar turno ⚠️", tipo: "warning" });
            return;
        }
        setActionSuggestionVisible(false);
        pasarTurno(mano.length);
    }, [accionRealizada, pasarTurno, mano.length, setAlerta, setActionSuggestionVisible]);

    const handlePlayAction = useCallback(async () => {
        try {
            setActionSuggestionVisible(false);
            const response = await playSel.play(game_id, player_id);
            const nuevaMano = await tableroService.getManoJugador(game_id, player_id);
            setMano(nuevaMano.cards || []);
            return response;
        } catch (err) {
            console.error("No se pudo ejecutar la acción de juego:", err);
            throw err;
        }
    }, [playSel, game_id, player_id, setMano, setActionSuggestionVisible]);

    const handleOpponentDiscard = useCallback((pid, cardId) => {
        if (Number(pid) === Number(player_id)) return;          // ignorar mi propio discard
        if (cardId == null) return;
        const ids = Array.isArray(cardId) ? cardId.map(Number) : [Number(cardId)];
        removeOpponentCardsFromHand?.(Number(pid), ids);
    }, [player_id, removeOpponentCardsFromHand]);

    // FIX intercambio
    const handleSendTradeCard = useCallback(async () => {
        if (!tradeRequest) return;
        const cardId = playSel?.targetCardId;
        if (!cardId) {
            setAlerta({ mensaje: "Selecciona una carta primero.", tipo: "warning" });
            return;
        }
        try {
            const payload = {
                player_id: player_id,
                game_id: game_id,
                card_id: Number(cardId),
            };
            const res = await tableroService.exchangeCard(game_id, payload);
            setTradeRequest(null);
            return res;
        } catch (e) {
            console.warn(e);
            setAlerta({ mensaje: "Error al enviar la carta ❌", tipo: "error" });
        }
    }, [tradeRequest, playSel?.targetCardId, game_id, player_id, setTradeRequest, setAlerta]);

    const handleSendVote = useCallback(async () => {
        const selectedSuspectId = playSel.targetPlayerId;

        if (!selectedSuspectId) {
            return;
        }
        try {
            await tableroService.sendVote(game_id, player_id, selectedSuspectId);
            setVotePrompt(null);
        } catch (e) {
            console.error(e);
        } 
    }, [game_id, player_id, playSel, setVotePrompt]);

    return {
        handleRobarDraw,
        handleRobarDraft,
        handleRobarDiscard,
        handleSelectCard,
        handleDiscard,
        handlePassTurn,
        handlePlayAction,
        handleOpponentDiscard,
        handleSendTradeCard,
        handleSendVote,
    };
}