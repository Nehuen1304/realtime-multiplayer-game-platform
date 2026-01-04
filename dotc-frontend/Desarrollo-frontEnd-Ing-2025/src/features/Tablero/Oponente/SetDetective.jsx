import React, { useState } from "react";
import { Carta } from '../../../components/Carta/Carta';
import './SetDetective.css';

/**
 * Componente que muestra un set de cartas de Detective jugado.
 * Recibe un array de cartas del set.
 */
export function SetDetective({ cartasSet = [], onCardClick, isSmall = false, isExtraSmall = false, targetSetId }) {
    const [hoveredIndex, setHoveredIndex] = useState(null);

    return (
        <div
            className="detective-set-container"
            data-hovered={hoveredIndex !== null ? 'true' : 'false'}
        >
            {cartasSet.map((carta, i) => {
                const diff = hoveredIndex === null ? undefined : i - hoveredIndex;
                return (
                    <Carta
                        key={`det-set-${carta.card_id || i}`}
                        cartaData={carta}
                        isRevealed={true}
                        isSmall={isSmall}
                        isExtraSmall={isExtraSmall}
                        onCardClick={() => onCardClick(carta.set_id, carta.player_id)}
                        onMouseEnter={() => setHoveredIndex(i)}
                        onMouseLeave={() => setHoveredIndex(null)}
                        dataDiff={diff}
                        isTargetCard={targetSetId===carta.set_id}
                    />
                );
            })}
        </div>
    );
}