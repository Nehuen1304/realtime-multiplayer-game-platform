import React from 'react';
import { Carta } from '../../../components/Carta/Carta';
import './cardsLooks.css';
import { Button } from '../../../components/Button/Button';


export default function CardsLooks({ cards = [], onSelect = () => {}, selectedCard = null, onClickC }) {
    if (!Array.isArray(cards) || cards.length === 0) return null;

    return (
        <div className="cards-looks-wrapper">
            <div className="cards-looks-header">
                <span>Selecciona una carta</span>
            </div>
            <div className="cards-looks-grid">
                {cards.map((c) => (
                    <div key={c.card_id} className="cards-looks-item">
                        <Carta
                            cartaData={c}
                            onCardClick={() => onSelect(c.card_id)}
                            className="look-card"
                            isTargetCard={Number(selectedCard) === Number(c.card_id)}
                            isSmall={true}
                            isExtraSmall={false}
                            isRevealed={true}
                        />
                     
                    </div>
                ))}
                 <Button
                    variant="small" // (Asumiendo que tienes un 'variant' small, como en PanelAcciones)
                    onClick={onClickC} 
                    disabled={!selectedCard}
                          >
                    Seleccionar Carta
                </Button>
            </div>
        </div>
    );
}