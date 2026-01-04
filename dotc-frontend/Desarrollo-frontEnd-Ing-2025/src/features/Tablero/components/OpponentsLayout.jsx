// Distribuye oponentes en el tablero
import React, { useMemo } from 'react';
import { Oponente } from '../Oponente/Oponente.jsx';
import './OpponentsLayout.css'

export function OpponentsLayout({
  opponents,
  gameId,
  playSel,
  requesterPlayerId, 
}) {
  const opponentsCount = opponents.length;

  const items = useMemo(() => opponents.map((op, i) => {
    let slotClass = "";
    if (opponentsCount === 1) {
      slotClass = "center-slot";
    } else if (opponentsCount === 2) {
      slotClass = i === 0 ? "center-left" : "center-right";
    } else if (opponentsCount === 3) {
      const threeSlotsMap = ["slot-3", "slot-1", "slot-2"];
      slotClass = threeSlotsMap[i] || "slot-1"; // Usamos el índice para obtener la clase correcta
    
    // 4 Oponentes (Esta es tu lógica original, para 5 jugadores totales)
    } else if (opponentsCount === 4) {
      const fourSlotsMap = ["slot-3", "slot-1", "slot-2", "slot-4"]; 
      // O si es [Arr-Izq, Med-Izq, Med-Der, Arr-Der]
      // const fourSlotsMap = ["slot-3", "slot-5", "slot-4", "slot-2"];
      // Vamos a usar la primera:
      slotClass = fourSlotsMap[i];
    
    // 5 Oponentes (Tu lógica original, para 6 jugadores totales)
    } else if (opponentsCount === 5) {
      const fiveSlotsMap = ["slot-5", "slot-3", "slot-1", "slot-2", "slot-4"];
      slotClass = fiveSlotsMap[i];
    }

    return (
      <div
        key={op.player_id}
        className={`opponent ${slotClass} ${op.player_id === requesterPlayerId ? 'requester' : ''}`}
      >
        <Oponente
          playerName={op.player_name}
          playerId={op.player_id}
          isTurn={op.isTurn}
          handCards={op.handCards}
          secretCards={op.secretCards}
          detectiveSets={op.detectiveSets}
          playSel={playSel}
          socialDisgrace={op.socialDisgrace}
        />
      </div>
    );
  }), [
    opponents,
    gameId,
    playSel
  ]);

  return <>{items}</>;
}