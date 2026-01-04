import React from 'react';
import { Carta } from '../../../components/Carta/Carta';
import './CentroMesa.css'

export function CentroMesa({ deckCount, onRobarDraw, discardCard, draftCards = [], onRobarDraft, onRobarDiscard, onCardHover, hoveredCard }) {
  
  
  const isTouch = typeof window !== 'undefined' && (
    'ontouchstart' in window || navigator?.maxTouchPoints > 0
  );

  const handleDraftClick = (carta) => {
    if (isTouch) {
      if (!hoveredCard || hoveredCard.card_id !== carta.card_id) {
        onCardHover?.(carta); // primer tap: solo preview
        return;
      }
      onRobarDraft(carta.card_id); // segundo tap: roba
      onCardHover?.(null);
      return;
    }
    onRobarDraft(carta.card_id); // desktop: roba directo
  };

  return (
    <div className="center">
      <div className="center-piles">
        <div className="draw-pile">
          <Carta
            isSmall={true}
            isRevealed={false}
            cartaData={{ card_id: -1, card_type: 'CARD_BACK' }}
            isSelected={false}
            onCardClick={onRobarDraw}
          />
      
          <span className="card-count">{deckCount ?? '-'}</span>
        </div>
        <div className="discard-pile">
          {discardCard && discardCard.card_id
            ? (
              <Carta
                isSmall={true}
                cartaData={discardCard} 
                isSelected={false}
                onCardClick={() => onRobarDiscard(discardCard.card_id)}
                onMouseEnter={() => onCardHover && onCardHover(discardCard)}
                onMouseLeave={() => onCardHover && onCardHover(null)}
              />
            )
            : (
              <Carta
                isSmall={true}
                isRevealed={false}
                cartaData={{ card_id: -2, card_type: 'CARD_BACK' }}
                isSelected={false}
                style={{ filter: 'grayscale(100%) brightness(0.4)', opacity: 0.7 }}
              />
            )
          }
        </div>
      </div>
      <div className="draft">
        {draftCards.map((carta) => (
          <Carta
            key={carta.card_id}
            isSmall={true}
            isRevealed={true}
            cartaData={carta}
            isSelected={false}
            onCardClick={() => handleDraftClick(carta)}
            onMouseEnter={() => onCardHover && onCardHover(carta)}
            onMouseLeave={() => onCardHover && onCardHover(null)}
          />
        ))}
      </div>
    </div>

  );
}