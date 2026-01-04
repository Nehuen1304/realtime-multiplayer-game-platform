import defaultAvatarImg from '../../../../assets/default_avatar.png';
import SugerenciaAccion from '../../components/SugerenciaAccion.jsx';
import './PlayerHeader.css';

export function PlayerHeader({
  playerName,
  seJugo,
  actionSuggestionVisible,
  actionSuggestionText,
  socialDisgrace = false,
}) {
  return (
    <div className="player-header">
      {socialDisgrace && (
        <span className="desgracia" >Estás en desgracia social...</span>
      )}
      <SugerenciaAccion
        isVisible={actionSuggestionVisible}
        instructionText={actionSuggestionText}
      />
      <div className="jugador-avatar">
        <img src={defaultAvatarImg} alt="Avatar" draggable={false} />
      </div>
      <p className="jugador-nombre">
        {playerName} <span className="jugador-es-tu">(Tú)</span>
      </p>
    </div>
  );
}
