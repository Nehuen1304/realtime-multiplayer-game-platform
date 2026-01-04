import showIcon from '../../../../assets/extras/show.png';
import hiddenIcon from '../../../../assets/extras/hidden.png';
import { Carta_Secreta } from '../../../../components/Carta/Carta_Secreta.jsx';
import './SecretCards.css';

export function SecretCards({
  secretCards,
  targetSecretId,
  toggleTargetSecret,
  revealSecretPrompt,
  showRevealHint,
  revealCountdownMs,
  hasUnrevealedSecrets,
  onReveal,
  revealTotalMs = 10000,
}) {
  return (
    <div className='secretos-propios'>
      {showRevealHint && revealSecretPrompt && hasUnrevealedSecrets && (
        <div className="reveal-hint-box" role="status" aria-live="polite">
          <div className="reveal-hint-text">Debes revelar un secreto</div>
          <div className="reveal-hint-progress" aria-hidden="true">
            <div
              className="reveal-hint-progress__bar"
              style={{ width: `${(revealCountdownMs / revealTotalMs) * 100}%` }}
            />
          </div>
          <div className="reveal-hint-timer">{Math.ceil(revealCountdownMs / 1000)}s</div>
        </div>
      )}

      <div className="mano-secreta-container">
        {secretCards.map((cartaSec) => (
          <div key={cartaSec.secret_id} style={{ display: 'inline-block', textAlign: 'center' }}>
            <Carta_Secreta
              dataSecret={cartaSec}
              isRevealed={cartaSec.is_revealed}
              className="propio small"
              isTargetSecret={cartaSec.secret_id === targetSecretId}
              onClick={() => {
                if (!revealSecretPrompt) {
                  toggleTargetSecret(cartaSec.secret_id, cartaSec.player_id);
                }
                if (!revealSecretPrompt || cartaSec.is_revealed) return;
                onReveal?.(cartaSec.secret_id);
              }}
            />
            <img
              src={cartaSec.is_revealed ? showIcon : hiddenIcon}
              alt={cartaSec.is_revealed ? '🔓' : '🔒'}
              draggable={false}
              style={{ width: '22px', height: '22px', marginTop: '4px' }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
