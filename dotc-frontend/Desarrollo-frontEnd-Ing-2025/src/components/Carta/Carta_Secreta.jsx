import './Carta_Secreta.css';
import './Carta.css';
import { getCardImage } from '../../assets/cards';
import { useState } from 'react';
import React from 'react';

const Carta_Secreta = React.memo(
  function Carta_Secreta({
    dataSecret,
    isRevealed,
    isOponente = false,
    className = "",
    onClick,
    isTargetSecret = false
  }) {

    // Si es carta secreta de oponente y no está revelada, mostrar reverso
    const imageSrc = isOponente && !isRevealed
      ? getCardImage("SECRET_BACK")
      : getCardImage(dataSecret?.role);

    const combinedClassName = [
      "secreta",
      className,
      isTargetSecret ? "target" : ""
    ].filter(Boolean).join(" ");

    return (
      <div className={`carta-visual ${combinedClassName}`} onClick={onClick}>
        <img
          src={imageSrc}
          alt={dataSecret?.role || 'Carta secreta'}
          className="carta-image"
          draggable={false}
        />
      </div>
    );
  }
) 

export { Carta_Secreta };