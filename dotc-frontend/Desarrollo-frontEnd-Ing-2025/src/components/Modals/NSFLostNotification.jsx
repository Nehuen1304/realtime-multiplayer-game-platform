import './NSFLostNotification.css';

export function NSFLostNotification({ 
  isOpen, 
  cardsCount,
  onClose 
}) {
  if (!isOpen) return null;

  return (
    <div className="nsf-notification-backdrop">
      <div className="nsf-notification-modal">
        <div className="nsf-notification-icon">⚠️</div>
        
        <h2 className="nsf-notification-title">CARTAS NOT SO FAST PERDIDAS</h2>
        
        <div className="nsf-notification-message">
          <p>
            Una carta de evento ha provocado que pierdas todas tus cartas
            <br />
            <strong>NOT SO FAST</strong>.
          </p>

          <div className="nsf-notification-stats">
            <span className="nsf-stats-label">Cartas descartadas:</span>
            <span className="nsf-stats-value">{cardsCount}</span>
          </div>
        </div>

        <button 
          className="nsf-notification-button"
          onClick={onClose}
        >
          ✓ ENTENDIDO
        </button>
      </div>
    </div>
  );
}
