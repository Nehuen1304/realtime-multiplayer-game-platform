import React, { useState, useEffect } from 'react';
import { Carta } from '../../../components/Carta/Carta';
import { Carta_Secreta } from '../../../components/Carta/Carta_Secreta';
import './Oponente.css'
import { obtenerManoOponente, obtenerSecretosOponente } from './oponenteService'
import { SetDetective } from './SetDetective';
import defaultAvatarImg from '../../../assets/default_avatar.png';

export function Oponente({
    playerName,
    playerId,
    isTurn,
    handCards,
    secretCards,
    detectiveSets,
    playSel,
    socialDisgrace = false
}) {

    return (
        <div className={`oponente-container${socialDisgrace ? ' oponente-desgracia' : ''}`}>
            {/* Área de la Mano (6 cartas arriba) y Secretos */}
            <div className="oponente-hand">

                {socialDisgrace && (
                    <span className="sd-badge" title="Desgracia social" data-testid="sd-badge">DS</span>
                )}

                <div className="oponente-hand-cards">
                    {handCards?.map((carta, index) => (
                        <Carta
                            key={`mano-${index}`}
                            cartaData={carta}
                            isRevealed={false} // Siempre boca abajo
                            isExtraSmall={true} // Las cartas de mano suelen ser de tamaño normal
                            onCardClick={() => playSel.toggleTargetCard(carta.card_id, carta.player_id)}
                            dataDiff={carta.card_id}
                            isTargetCard={playSel.targetCardId === carta.card_id}
                        />
                    ))}
                </div>
                {/* Área de Secretos (3 cartas a la izquierda) */}
                <div className="oponente-hand-secrets">
                    {secretCards?.map((cartaSec) => (
                        <Carta_Secreta
                            key={cartaSec.secret_id}
                            dataSecret={cartaSec}
                            isRevealed={cartaSec.is_revealed}
                            isOponente={true}
                            className="extrasmall"
                            onClick={() => playSel.toggleTargetSecret(cartaSec.secret_id, cartaSec.player_id)}
                            isTargetSecret={playSel.targetSecretId === cartaSec.secret_id}
                        />
                    ))}
                </div>
            </div>

            {/* Nombre del Oponente */}
            <div className={`oponente-info ${isTurn ? 'oponente-turn' : ''} ${playSel.targetPlayerId === playerId ? 'oponente-target' : ''}`}
                onClick={() => playSel.toggleTargetPlayer(playerId)}>
                <div className="oponente-avatar">
                    <img src={defaultAvatarImg} alt="Avatar" draggable={false} />
                </div>
                <p className='oponente-nombre'>
                    {playerName}
                </p>
            </div>

            {/* Área de Detectives (Sets a la derecha) */}
            {detectiveSets && (
                <div className="oponente-detective-sets-area">
                    {detectiveSets.map((set, idx) => (
                        <SetDetective
                            key={`set-${idx}`}
                            cartasSet={set}
                            isExtraSmall={true}
                            onCardClick={(setId, player_id) => playSel.toggleTargetSet(setId, player_id)}
                            targetSetId={playSel.targetSetId}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}

export default Oponente;