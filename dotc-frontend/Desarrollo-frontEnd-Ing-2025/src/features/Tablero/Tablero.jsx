import { useState, useCallback, useEffect, useRef } from 'react';
import "./Tablero.css";
import { ManoPropia } from './ManoPropia/ManoPropia';
import { usePlayerHand } from './hooks/player/usePlayerHand.js';
import { useGameState } from './hooks/game/useGameState.js';
import { useTurnActions } from './hooks/game/useTurnActions.js';
import { CentroMesa } from './components/CentroMesa.jsx';
import { OpponentsLayout } from './components/OpponentsLayout.jsx';
import { useTurnWebSocket } from './hooks/game/useTurnWebSocket.js';
import { Carta } from '../../components/Carta/Carta.jsx';
import { usePlayerSecret } from './hooks/secrets/useSecretPlayer.js';
import { usePlaySelection } from './hooks/player/usePlaySelection.js';
import { Alerta } from "../../components/Alerta/Alerta.jsx";
import { useCardSelection } from './hooks/player/useCardSelection.js';
import { useSetManagement } from './hooks/sets/useSetManagement.js';
import { useRevealSecret } from './hooks/secrets/useRevealSecret.js';
import { useCardLook } from './hooks/player/useCardLook.js';
import { useNSFDiscarded } from './hooks/events/useNSFDiscarded.js';

import { GameOverScreen } from './components/GameOverScreen.jsx';
import { useOpponentsData } from './hooks/opponents/useOpponentsData.js';
import { useTableroHandlers } from './hooks/game/useTableroHandlers.js';
import { useGameOver } from './hooks/game/useGameOver.js';
import { useOpponentsState } from './hooks/opponents/useOpponentsState.js';
import { VotePrompt } from './components/VotePrompt.jsx';
import { PlayedCardsModal } from './components/PlayedCardsModal.jsx';
import { useSocialDisgrace } from './hooks/player/useSocialDisgrace.js';
import { useStolenSecretHandler } from './hooks/secrets/useSecretStolen.js'

import { NSFLostNotification } from '../../components/Modals/NSFLostNotification.jsx';
import { useNsfWindow } from './useNsfWindow.js';
import { canPlayNSF } from './utils/validator.js';
import { NsfWindow } from './components/NsfWindow.jsx';
import * as tableroService from './tableroService.js';
import { refreshOpponent } from './hooks/opponents/useOpponentsState.js';
import TradePrompt from './components/TradePrompt.jsx';

const Tablero = ({ playerName, game_id, player_id }) => {
    // Mano
    const { mano, setMano, cargandoMano, errorMano } = usePlayerHand(game_id, player_id);
    const [deckCount, setDeckCount] = useState(999);
    const [hoveredCard, setHoveredCard] = useState(null);
    const [currentTurnId, setCurrentTurnId] = useState(null);
    const esMiTurno = currentTurnId === player_id;
    const prevTurnIdRef = useRef(null);
    // Estado local para draft y discard pile
    const [draftCards, setDraftCards] = useState([]);
    const [discardCard, setDiscardCard] = useState(null);
    // Estado auxiliar (turnos y polling)
    const [accionRealizada, setAccionRealizada] = useState(false);
    const [actionSuggestionVisible, setActionSuggestionVisible] = useState(false);
    const [actionSuggestionText, setActionSuggestionText] = useState(null);
    const [selectedCardIds, setSelectedCardIds] = useState([]);
    const [alerta, setAlerta] = useState(null);
    const [revealSecretPrompt, setRevealSecretPrompt] = useState(false);
    const [tradeRequest, setTradeRequest] = useState(null);

    // voto (point your suspicions)
    const [votePrompt, setVotePrompt] = useState(null);
    const [sendingVote, setSendingVote] = useState(false);
    // Estado centralizado de datos extra por oponente
    const {
        opponentsDetailsById,
        setOpponentsDetailsById, // si algo externo aún lo necesita
        setOpponentHand,
        setOpponentSecrets,
        updateOpponentSecrets,
        upsertOpponentSet,
        removeOpponentSet,
        removeOpponentCardsFromHand,
    } = useOpponentsState({});

    // Acciones de turno
    const { robarDesdeFuente, descartarCarta, pasarTurno } = useTurnActions({
        gameId: game_id,
        playerId: player_id,
        esMiTurno,
        setAccionRealizada,
        setSelectedCardIds,
        draftCards,
        setDraftCards,
        discardCard,
        setDiscardCard,
        setDeckCount,
        setAlerta
    });

    useEffect(() => {
        if (currentTurnId == null) {
            prevTurnIdRef.current = currentTurnId;
            return;
        }
        const prevId = prevTurnIdRef.current;
        // Si el turno cambió y había un jugador previo, refrescar su mano
        refreshOpponent(prevId, currentTurnId, game_id, player_id, setMano, setOpponentHand, setOpponentSecrets);
        prevTurnIdRef.current = currentTurnId;
    }, [currentTurnId, game_id, player_id, setMano, setOpponentHand]);
        const { cardsPlayed, setsPropios, onSetPlayed, onSetStolen } =
        useSetManagement({
            gameId: game_id,
            playerId: player_id,
            setMano,
            upsertOpponentSet,
            removeOpponentSet,
            removeOpponentCardsFromHand,
        });
    // Selección y acciones de juego
    const playSel = usePlaySelection({ selectedCardIds, setSelectedCardIds });

    const { actionSuggestionVisible: selSuggestionVisible, actionSuggestionText: selSuggestionText, puedeFormarSet, puedeJugarEvento, puedeAgregarSet, toggleSelectCard, resetSelection, selectTypesCardIds  } = useCardSelection({ playSel, selectedCardIds, setSelectedCardIds,setsPropios,        
        opponentsDetailsById });

  
    const handleMyTurnGain = useCallback(() => {
        setAccionRealizada(false);
        resetSelection();
    }, [resetSelection]);
    // Sugerencias visibles en ManoPropia
    useEffect(() => {
        setActionSuggestionVisible(selSuggestionVisible);
        setActionSuggestionText(selSuggestionText);
    }, [selSuggestionVisible, selSuggestionText]);

    const {
        handleRobarDraw,
        handleRobarDraft,
        handleRobarDiscard,
        handleSelectCard,
        handleDiscard,
        handlePassTurn,
        handlePlayAction,
        handleSendVote,
        handleOpponentDiscard,
        handleSendTradeCard,
    } = useTableroHandlers({
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
        setVotePrompt,
        setActionSuggestionVisible,
        removeOpponentCardsFromHand,
        tradeRequest,
        setTradeRequest,
    });

    const { players, forceUpdate } = useGameState(
        game_id,
        setDeckCount,
        setDraftCards
    );

    // NSF window state and actions
    const { nsfWindow, openWindow: openNsfWindow, closeWindow: closeNsfWindow, passNSF, playNSFCard } = useNsfWindow({ gameId: game_id, playerId: player_id, setMano });

    const { secretP, setSecretP, cargandoSecreto, errorSecreto, secretPlayer } = usePlayerSecret({ playerId: player_id, gameId: game_id });

    const { gameOverData, handleGameOverEvent } = useGameOver({
        players,
        onGameOver: (data) => {
            // Callback opcional cuando se detecta fin de partida
        }
    });
    const { onSecretRevealed, onSecretHidden } = useRevealSecret({
        playerId: player_id,
        setSecretP,
        updateOpponentSecrets,
    });

    const handleGameStarted = useCallback(() => {
        forceUpdate();
    }, [forceUpdate]);

    // Sets jugados/robados y prompt de look


    const { onCardsNSFDiscarded, nsfNotification, closeNsfNotification } = useNSFDiscarded({
        playerId: player_id,
        setMano,
        onShowNotification: (message, type) => {
            setAlerta({ mensaje: message, tipo: type });
        }
    });

    const { cardsLook, cardLookSelect, onCardLook, toggleCardLook: toogleTargetSelect, confirmCardLook: handleButtonLook } =
        useCardLook({ gameId: game_id, playerId: player_id, setMano });

    const { sdPlayers, markSD, clearSD, hasSocialDisgrace } = useSocialDisgrace(player_id);

    const { opponentsData, reloadOpponentSecrets } = useOpponentsData({
        gameId: game_id,
        myPlayerId: player_id,
        players,
        currentTurnId,
        opponentsDetailsById,
        setOpponentHand,
        setOpponentSecrets,
        sdPlayers,
        onSocialDisgraceApplied: markSD,
        onSocialDisgraceRemoved: clearSD,
        onGameOver: handleGameOverEvent,
        setCurrentTurnId,
        esMiTurno,
        robarDesdeFuente,
        setAlerta,
        selectedCardIds,
        descartarCarta,
        accionRealizada,
        toggleSelectCard,
        pasarTurno,
        playSel,
        nsfWindowOpen: nsfWindow.open,
        removeOpponentCardsFromHand: handleOpponentDiscard,
        onCardsNSFDiscarded: onCardsNSFDiscarded,
    });

    const { onSecretStolen } = useStolenSecretHandler({
        playerId: player_id,
        secretPlayer, // de usePlayerSecret
        reloadOpponentSecrets
    })



    useTurnWebSocket({
        gameId: game_id,
        playerId: player_id,
        onMyTurnGain: handleMyTurnGain,
        onGameStarted: handleGameStarted,
        setDeckCount,
        setDraftCards,
        setDiscardCard,
        setRevealedSecret: onSecretRevealed,
        setHiddenSecret: onSecretHidden,
        setSetPlayed: onSetPlayed,
        setRevealSecretPrompt,
        stolenSet: onSetStolen,
        stolenSecret: onSecretStolen,
        setCardLook: onCardLook,
        onSocialDisgraceApplied: markSD,
        onSocialDisgraceRemoved: clearSD,
        onGameOver: handleGameOverEvent,
        currentTurnId,
        setCurrentTurnId,
        esMiTurno,
        removeOpponentCardsFromHand: handleOpponentDiscard,
        onCardsNSFDiscarded: onCardsNSFDiscarded,
        onTradeRequested: (payload) => {
            playSel.resetSelection;
            setTradeRequest(payload);
        },
        setPlayerHand: setMano, // para actualizar mano con HAND_UPDATED
        onVoteStarted: (payload) => {
            if (playSel?.setTargetPlayerId) playSel.setTargetPlayerId(null);
            setVotePrompt(payload || {});
        },

        // NSF window callbacks from gameLogic WS events
        onNsfWindowOpen: ({ actionId, playedBy, playedByName, expiresAt }) => openNsfWindow({ actionId, playedBy, playedByName, expiresAt }),
        onNsfWindowClose: async ({ status, payload } = {}) => {
            console.log(`[TABLERO] onNsfWindowClose llamado: status=${status}, payload=`, payload);
            closeNsfWindow();
            console.log(`[TABLERO] closeNsfWindow() ejecutado`);

            // Siempre refrescar la mano cuando la ventana NSF se cierra (CANCELLED o RESOLVED)
            // porque cualquier jugador pudo haber jugado cartas NSF que deben desaparecer de su mano
            if (status === 'CANCELLED' || status === 'RESOLVED') {
                const actionLabel = status === 'CANCELLED' ? 'cancelada' : 'resuelta';
                console.log(`[TABLERO] Acción ${actionLabel}, refrescando mano (pude haber jugado NSF)...`);
                try {
                    const response = await tableroService.getManoJugador(game_id, player_id);
                    if (response?.cards) {
                        console.log(`[TABLERO] Mano actualizada después de ${actionLabel}, ${response.cards.length} cartas`);
                        setMano(response.cards);
                    }
                } catch (error) {
                    console.error(`[TABLERO] Error al actualizar mano después de ${actionLabel}:`, error);
                }
            }
        },

        onCardsPlayed: async (payload) => {
            // Si soy el jugador que jugó las cartas, solo limpiar la selección
            if (payload?.player_id === player_id) {
                console.log('🧹 Limpiando selección: jugué mis cartas');
                setSelectedCardIds([]);
                resetSelection(); // Limpia también selectTypesCardIds

                // NO actualizar mano aquí - las cartas aún están en IN_HAND en el backend
                // Se actualizará cuando llegue ACTION_RESOLVED o ACTION_CANCELLED
            }
        }
    });

    // Habilitación del botón NSF según selección actual
    const puedeJugarNSF = canPlayNSF({
        selectedCardIds,
        selectTypesCardIds: selectTypesCardIds,
        targetPlayerId: playSel?.targetPlayerId ?? null,
        targetSecretId: playSel?.targetSecretId ?? null,
        targetCardId: playSel?.targetCardId ?? null,
        targetSetId: playSel?.targetSetId ?? null,
        actionType: playSel?.actionType ?? null
    }, {
        nsfWindowOpen: nsfWindow.open,
        alreadyResponded: nsfWindow.alreadyResponded,
        currentPlayerId: player_id,
        windowPlayedBy: nsfWindow.playedBy
    });

    // Log de diagnóstico NSF
    useEffect(() => {
        if (nsfWindow.open) {
            console.log('🔍 DEBUG canPlayNSF:', {
                puedeJugarNSF,
                selectedCardIds,
                selectTypesCardIds,
                cardType: selectTypesCardIds?.[0]?.[0],
                nsfWindowOpen: nsfWindow.open,
                alreadyResponded: nsfWindow.alreadyResponded,
                currentPlayerId: player_id,
                windowPlayedBy: nsfWindow.playedBy
            });
        }
    }, [puedeJugarNSF, selectedCardIds, selectTypesCardIds, nsfWindow.open, nsfWindow.alreadyResponded, player_id, nsfWindow.playedBy]);

    // después de definir playSel y handlePlayAction
    useEffect(() => {
        const at = playSel?.actionType;
        if (!at) return; // ignorar cuando es null (reset)
        let mounted = true;

        (async () => {
            try {
                playSel.setActionType(null);
                // Ejecuta la acción; playSel.play usa el actionType del hook
                await handlePlayAction();
                // marcar que se realizó acción y forzar refresh si corresponde
                setAccionRealizada(true);
            } catch (err) {
                setAlerta({
                    titulo: "Acción Inválida",
                    mensaje: err.message, // Muestra el mensaje de error de la API
                    tipo: "error"
                });
                console.error('Error auto-play desde useEffect en Tablero:', err);
            }
        })();
        return () => { mounted = false; };
    }, [playSel.actionType]);

    const [showPlayedCardsModal, setShowPlayedCardsModal] = useState(false);
    const [lastPlayedCards, setLastPlayedCards] = useState([]);

    useEffect(() => {
        console.log('se actualizo cardsPlayed: ', cardsPlayed);
        if (cardsPlayed && cardsPlayed.length > 0) {
            setLastPlayedCards(cardsPlayed);
            setShowPlayedCardsModal(true);
            // Ocultar automaticamente despues de 5 segundos
            const timer = setTimeout(() => setShowPlayedCardsModal(false), 5000);
            return () => clearTimeout(timer);
        }
    }, [cardsPlayed]);

    // useEffect para detectar fin del juego
    useEffect(() => {
        if (deckCount === 0 && !gameOverData) {
            handleGameOverEvent({ event: 'DECK_EMPTY' });
        }
    }, [deckCount, handleGameOverEvent, gameOverData]);

    //  helpers touch y ver si la preview es del draft
    const isTouch = typeof window !== 'undefined' && ('ontouchstart' in window || navigator?.maxTouchPoints > 0);
    const hoveredIsDraft = !!hoveredCard && draftCards.some(c => c.card_id === hoveredCard.card_id);

    if (gameOverData) {
        return <GameOverScreen gameOverData={gameOverData} />;
    }

    return (
        <div className="game-board">

            {/* Point your suspicions  */}
            {votePrompt && (<VotePrompt
                votePrompt={votePrompt}
                playSel={playSel}
                onSendVote={handleSendVote}
                opponents={opponentsData}
                timeoutMs={20000}
            />)}

            {/* Modal de cartas jugadas */}
            {showPlayedCardsModal && (
                <PlayedCardsModal
                    cards={lastPlayedCards}
                    onClose={() => setShowPlayedCardsModal(false)}
                />
            )}

            {/* Zoom preview */}
            {hoveredCard && (
                <div className="card-zoom-preview">
                    <Carta
                        cartaData={hoveredCard}
                        isRevealed={hoveredCard.is_revealed ?? true}
                        isSmall={false}
                        isExtraSmall={false}
                        onCardClick={isTouch && hoveredIsDraft ? () => { handleRobarDraft(hoveredCard.card_id); setHoveredCard(null); } : undefined}
                    />
                </div>
            )}

            {tradeRequest && (
                <TradePrompt
                    requesterPlayerId={tradeRequest.requester_player_id}
                    selectedCard={playSel.targetCardId}
                    onSendTrade={handleSendTradeCard}
                    opponentsData={opponentsData}
                />
            )}

            <div className="board-area">
                <OpponentsLayout
                    opponents={opponentsData}
                    gameId={game_id}
                    playSel={playSel}
                    requesterPlayerId={tradeRequest?.requester_player_id}
                />
                <CentroMesa
                    deckCount={deckCount}
                    onRobarDraw={handleRobarDraw}
                    discardCard={discardCard}
                    draftCards={draftCards}
                    onRobarDraft={handleRobarDraft}
                    onRobarDiscard={handleRobarDiscard}
                    onCardHover={setHoveredCard}
                    hoveredCard={hoveredCard}
                    canDraw={mano.length < 6 && esMiTurno}
                />
            </div>

            <ManoPropia
                playerId={player_id}
                gameId={game_id}
                playerName={playerName}
                puedoJugar={esMiTurno}
                mano={mano}
                selectedCardsIds={selectedCardIds} // compatibilidad con prop vieja
                onSelectCard={handleSelectCard}
                setPlayType={playSel.setActionType}
                onDiscard={handleDiscard}
                onPassTurn={handlePassTurn}
                cargando={cargandoMano}
                error={errorMano}
                seJugo={accionRealizada}
                secretCards={secretP}
                cargandoSecreto={cargandoSecreto}
                errorSecreto={errorSecreto}
                puedeFormarSet={puedeFormarSet}
                puedeJugarEvento={puedeJugarEvento}
                puedeAgregarSet={puedeAgregarSet}
                setsPropios={setsPropios}
                actionSuggestionVisible={actionSuggestionVisible}
                actionSuggestionText={actionSuggestionText}
                revealSecretPrompt={revealSecretPrompt}
                setRevealSecretPrompt={setRevealSecretPrompt}
                cardsLook={cardsLook}
                cardLookSelect={cardLookSelect}
                toogleCardLook={toogleTargetSelect}
                handleButtonLook={handleButtonLook}
                playSel={playSel}
                // NSF props hacia PanelAcciones
                nsfWindowOpen={nsfWindow.open}
                nsfRemainingMs={nsfWindow.remainingMs}
                nsfAlreadyResponded={nsfWindow.alreadyResponded}
                puedeJugarNSF={puedeJugarNSF}
                onPlayNSF={() => {
                    const cardId = selectedCardIds?.[0];
                    if (cardId != null) playNSFCard(cardId);
                }}
                socialDisgrace={hasSocialDisgrace}
            />
            {alerta && (
                <Alerta
                    tipo={alerta.tipo}
                    mensaje={alerta.mensaje}
                    onClose={() => setAlerta(null)}
                    duracion={4000}
                />
            )}

            <NSFLostNotification
                isOpen={nsfNotification.isOpen}
                sourceName={nsfNotification.sourceName}
                cardsCount={nsfNotification.cardsCount}
                onClose={closeNsfNotification}
            />
            

            {/* Overlay NSF: solo renderizar cuando la ventana está abierta */}
            {nsfWindow.open && (
                <NsfWindow
                    nsfWindow={nsfWindow}
                    currentPlayerId={player_id}
                    canPlayNSF={puedeJugarNSF}
                    onPass={passNSF}
                    onPlayClick={() => {
                        const cardId = selectedCardIds?.[0];
                        if (cardId != null) playNSFCard(cardId);
                    }}
                />
            )}

        </div>
    );
};

export default Tablero;

