import './Carta.css'
// import { getCardImage } from '../../../../assets/cards';
import { getCardImage } from '../../assets/cards';
import { useState } from 'react';
import React from 'react';

const Carta = React.memo(
    function Carta({
        cartaData,
        isSelected,
        onCardClick,
        isSmall = false,
        isExtraSmall = false,
        isRevealed = true,
        onMouseEnter,
        onMouseLeave,
        style,
        dataDiff,
        isTargetCard = false
    }) {

        // Añadimos una clase condicional si la carta está seleccionada
        const className = `carta-visual 
        ${isSelected ? 'selected' : ''} 
        ${isSmall ? 'small' : ''}
        ${isExtraSmall ? 'extrasmall' : ''}
        ${isTargetCard ? 'target' : ''}`.trim();

        let imageSrc;

        const isSecret = cartaData.role === 'Innocent' ||
            cartaData.role === 'Murderer' ||
            cartaData.role === 'Accomplice';

        if (isRevealed) {
            imageSrc = getCardImage(cartaData.card_type);
        }
        else if (!isRevealed && isSecret) {
            imageSrc = getCardImage('SECRET_BACK');
        }
        else {
            imageSrc = getCardImage('CARD_BACK');
        }

       

        return (
            // Usamos la función onCardClick que nos pasa el componente padre
            <div
                className={className}
                onClick={onCardClick}
                onMouseEnter={onMouseEnter}
                onMouseLeave={onMouseLeave}
                style={style}
                data-diff={dataDiff}
                onContextMenu={e => e.preventDefault()}
                draggable={false}
                onDragStart={e => e.preventDefault()}
            >
                <div className="carta-inner">
                    <img
                        src={imageSrc}
                        className="carta-image"
                        draggable={false}
                        onTouchStart={e => e.preventDefault()}
                        onContextMenu={e => e.preventDefault()}
                    />
                </div>
            </div>
        )
    }

)


export { Carta };