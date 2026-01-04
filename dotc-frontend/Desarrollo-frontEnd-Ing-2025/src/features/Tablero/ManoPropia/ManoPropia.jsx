import { PanelAcciones } from "./PanelAcciones/PanelAcciones.jsx";
import { useMemo } from 'react';
import './ManoPropia.layout.css';
import './ManoPropia.cartas.css';
import './ManoPropia.status.css';
import { SetDetective } from '../Oponente/SetDetective.jsx';
import CardsLooks from './cardsLooks.jsx';
import { useRevealSecretPrompt } from './hooks/useRevealSecretPrompt.js';
import { PlayerHeader } from './components/PlayerHeader.jsx';
import { SecretCards } from './components/SecretCards.jsx';
import { HandCards } from './components/HandCards.jsx';

// Renderiza la mano del jugador y el panel de acciones
export function ManoPropia({
    playerId,
    gameId,
    playerName,
    mano = [],
    puedoJugar,
    onDiscard,
    onSelectCard,
    onPassTurn,
    cargando,
    error,
    seJugo,
    selectedCardsIds = [],
    secretCards = [],
    setPlayType,
    puedeFormarSet,
    puedeJugarEvento,
    puedeAgregarSet,
    setsPropios,
    actionSuggestionVisible,
    actionSuggestionText,
    revealSecretPrompt = false,
    setRevealSecretPrompt,
    cardsLook,
    handleButtonLook,
    cardLookSelect,
    toogleCardLook,
    playSel,
    // NSF integration (opcionales)
    nsfWindowOpen = false,
    nsfRemainingMs = 0,
    nsfAlreadyResponded = false,
    puedeJugarNSF = false,
    onPlayNSF,
    socialDisgrace = false
}) {

    // Limita seleccion a una carta si socialDisgrace
    const handleSelectCard = (card) => {
        if (!puedoJugar) return;
        if (socialDisgrace) {
            if (selectedCardsIds.length === 0) {
                onSelectCard(card); // Selecciona si no hay ninguna seleccionada
            } else if (selectedCardsIds.length === 1 && selectedCardsIds[0] === card.card_id) {
                onSelectCard(card); // Deselecciona si se toca la misma
            }
        } else {
            onSelectCard(card);
        }
    };

    const {
        showRevealHint,
        revealCountdownMs,
        hasUnrevealedSecrets,
        handleReveal,
        timeoutMs: REVEAL_TIMEOUT_MS,
    } = useRevealSecretPrompt({
        revealSecretPrompt,
        secretCards,
        gameId,
        playerId,
        setRevealSecretPrompt,
        timeoutMs: 20000,
    });


    if (cargando) {
        // Muestra spinner mientras se carga la mano
        return (
            <div className="status-overlay">
                <div className="status-box">
                    <div className="spinner"></div>
                    <span>Cargando mano...</span>
                </div>
            </div>
        );
    }

    if (error) {
        // Muestra mensaje de error si falla la carga
        return (
            <div className="status-overlay">
                <div className="status-box error">
                    <div className="error-icon">!</div>
                    <span>Error: {error}</span>
                </div>
            </div>
        );
    }

    return (
        <div className={`mano-propia-hud${socialDisgrace ? ' hud-desgracia' : ''}`}>
            {/* Identidad del jugador */}
            <div className="jugador">
            
                <PlayerHeader
                    playerName={playerName}
                    seJugo={seJugo}
                    actionSuggestionVisible={actionSuggestionVisible}
                    actionSuggestionText={actionSuggestionText}
                    socialDisgrace={socialDisgrace}
                />

                <SecretCards
                    secretCards={secretCards}
                    targetSecretId={playSel.targetSecretId}
                    toggleTargetSecret={playSel.toggleTargetSecret}
                    revealSecretPrompt={revealSecretPrompt}
                    showRevealHint={showRevealHint}
                    revealCountdownMs={revealCountdownMs}
                    hasUnrevealedSecrets={hasUnrevealedSecrets}
                    onReveal={handleReveal}
                    revealTotalMs={REVEAL_TIMEOUT_MS}
                />
            </div>

            <div className="mano-propia-container">
                {/* Sets de detectives jugados */}
                {setsPropios.length > 0 && (
                    <div className="mano-detective-sets-area-wrapper">
                        <div className="mano-detective-sets-area">
                            {setsPropios.map((set, idx) => (
                                <SetDetective
                                    key={`set-propio-${idx}`}
                                    cartasSet={set}
                                    isSmall={true}
                                    onCardClick={(id, player_id) => playSel.toggleTargetSet(id, player_id)}
                                    targetSetId={playSel.targetSetId}
                                />
                            ))}
                        </div>
                    </div>
                )}
                {/*CardsLooks renderiza solo si esta en el evento */}
                {Array.isArray(cardsLook) && cardsLook.length > 0 && (
                    <>
                        {/* Botón condicional: sólo aparece si hay cardsLook */}
                        <div className="cards-looks-control">
                        </div>
                        <CardsLooks
                            cards={cardsLook}
                            onSelect={toogleCardLook}
                            selectedCard={cardLookSelect}
                            onClickC={handleButtonLook}
                        />
                    </>
                )}

                <HandCards
                    mano={mano}
                    puedoJugar={puedoJugar}
                    seJugo={seJugo}
                    selectedCardsIds={selectedCardsIds}
                    onSelectCard={onSelectCard}
                    nsfWindowOpen={nsfWindowOpen}
                />

                {/* Panel de acciones solo si es tu turno */}
                {puedoJugar && (
                    <PanelAcciones 
                        setPlayType={setPlayType}
                        puedeFormarSet={puedeFormarSet} 
                        puedeAgregarSet={puedeAgregarSet}
                        puedeJugarEvento={puedeJugarEvento}
                        // NSF props
                        puedeJugarNSF={puedeJugarNSF}
                        nsfWindowOpen={nsfWindowOpen}
                        nsfAlreadyResponded={nsfAlreadyResponded}
                        nsfRemainingMs={nsfRemainingMs}
                        onPlayNSF={onPlayNSF}
                        socialDisgrace={socialDisgrace}
                        onPassTurn={onPassTurn} 
                        onDiscard={onDiscard} 
                        seJugo={seJugo} 
                        manoLength={mano.length}
                        selectedCardsLength={selectedCardsIds.length}
                    />
                )}


            </div>
        </div>
    );
}



