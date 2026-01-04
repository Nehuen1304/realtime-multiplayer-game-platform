import React, { useMemo } from 'react';
import './NsfWindow.css';
import { Button } from '../../../components/Button/Button';

export function NsfWindow({ nsfWindow, currentPlayerId, canPlayNSF, onPass, onPlayClick }) {
  const seconds = useMemo(
    () => (nsfWindow.open ? nsfWindow.remainingMs / 1000 : 0),
    [nsfWindow.open, nsfWindow.remainingMs]
  );
  const pct = useMemo(
    () => Math.max(0, Math.min(100, (nsfWindow.remainingMs / 10000) * 100)),
    [nsfWindow.remainingMs]
  );
  const isMyAction = String(nsfWindow.playedBy) === String(currentPlayerId);

  return (
    <div className={`nsf-overlay ${nsfWindow.open ? 'visible' : 'hidden'}`}>
      <div className="nsf-panel" role="status" aria-live="polite">
        <div className="nsf-header">
          <strong>Acción cancelable</strong>
        </div>
        <div className="nsf-body">
          <p className="nsf-text">
            Jugada por: <b>{nsfWindow.playedByName ?? nsfWindow.playedBy ?? '-'}</b><br/>
            {isMyAction
              ? "Esperando posibles 'Not So Fast...' de otros jugadores."
              : "Puedes responder con 'Not So Fast...' o pasar."}
          </p>
          <div className="nsf-timer">
            <div className="nsf-timer-bar" aria-hidden>
              <div className="fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="nsf-timer-number" aria-label={`Tiempo restante ${seconds.toFixed(1)} segundos`}>
              {seconds.toFixed(1)}s
            </span>
          </div>
        </div>

        {!isMyAction && (
          <div className="nsf-actions">
            <Button
              variant="small"
              disabled={!(canPlayNSF && !nsfWindow.alreadyResponded)}
              onClick={() => {
                console.log('🔴 Click en botón NSF:', { canPlayNSF, alreadyResponded: nsfWindow.alreadyResponded });
                if (canPlayNSF && !nsfWindow.alreadyResponded) onPlayClick?.();
              }}
            >
              Not So Fast
            </Button>
            <Button
              variant="small"
              disabled={nsfWindow.alreadyResponded}
              onClick={() => {
                if (!nsfWindow.alreadyResponded) onPass?.();
              }}
            >
              Pasar
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
