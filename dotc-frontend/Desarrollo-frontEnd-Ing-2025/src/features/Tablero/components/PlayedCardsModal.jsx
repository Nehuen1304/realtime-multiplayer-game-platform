import React, { useState, useEffect } from "react";
import "./PlayedCardsModal.css";
import { Carta } from "../../../components/Carta/Carta";
import { Button } from "../../../components/Button/Button";

export const PlayedCardsModal = ({ cards, onClose }) => {
    const [isClosing, setIsClosing] = useState(false);

    useEffect(() => {
        if (cards && cards.length > 0) {
            const timer = setTimeout(() => {
                setIsClosing(true);
                setTimeout(onClose, 500); // Coincide con la duración de la animación
            }, 4500); // Tiempo antes de que comience a cerrarse

            return () => clearTimeout(timer);
        }
    }, [cards, onClose]);

    if (!cards || cards.length === 0) return null;

    const handleOverlayClick = () => {
        setIsClosing(true);
        setTimeout(onClose, 500);
    };

    return (
        <div className={`played-cards-modal-overlay${isClosing ? " closing" : ""}`} onClick={handleOverlayClick}>
            <div className={`played-cards-modal ${isClosing ? "closing" : ""}`} onClick={e => e.stopPropagation()}>

                <h2>¡Se ha jugado!</h2>
                <div className="played-cards-list">
                    {cards.map(card => (
                        <div className="carta-animada" key={card.card_id}>
                            <Carta cartaData={card} isRevealed={true} />
                        </div>
                    ))}
                </div>

                {/* <Button onClick={onClose} variant="small">
                    CERRAR
                </Button> */}
            </div>
        </div>
    );



};
