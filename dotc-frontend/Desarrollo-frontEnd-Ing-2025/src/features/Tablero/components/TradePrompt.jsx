import React, {useMemo} from 'react';
import './TradePrompt.css';
import { Button } from '../../../components/Button/Button';

/**
 * Prompt mostrado cuando llega TRADE_REQUESTED.
 * Indica que debes seleccionar una carta del solicitante.
 */
export function TradePrompt({
  requesterPlayerId,
  selectedCard,
  onSendTrade,
  opponentsData,
}) {
  const requesterName = useMemo(() => {
    const found = opponentsData?.find(o => o.player_id === requesterPlayerId);
    return found?.player_name || `Jugador ${requesterPlayerId}`;
  }, [opponentsData, requesterPlayerId]);
  return (
    <div className="trade-prompt-overlay">
      <div className="trade-prompt" role="dialog" aria-modal="true" aria-labelledby="tradePromptTitle">
        <h4 id="tradePromptTitle">Intercambio solicitado</h4>
        <p><strong>{requesterName}</strong> solicitó un Intercambio. Selecciona una carta de su mano para obtenerla.</p>
        <div className="trade-actions">
          <Button
            variant="small"
            disabled={!selectedCard}
            onClick={onSendTrade}
          >
            {selectedCard ? 'Tomar la carta' : 'Selecciona una carta'}
          </Button>
        </div>
      </div>
    </div>
  );
}
export default TradePrompt;