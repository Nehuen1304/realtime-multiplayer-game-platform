import React from 'react';
import { Button } from '../../../components/Button/Button';
import './GameOverScreen.css';

export function GameOverScreen ({ gameOverData }) {
  const { winner, murdererName, reason } = gameOverData || {}

  const handleBackToMenu = () => {
    window.location.reload()
  }

  return (
    <div className='game-over-screen'>
      <div className='game-over-card'>
        <h1 className='game-over-title'>
          {winner === 'INNOCENTS' ? 'Los Inocentes Ganaron' : 'El Asesino Ganó'}
        </h1>

        {reason === 'SECRET_REVEALED' && (
          <p className='game-over-reason'>
            Se reveló el secreto del asesino
          </p>
        )}

        {reason === 'DECK_EMPTY' && (
          <p className='game-over-reason'>
            El mazo de robo se ha quedado sin cartas. El asesino logró escapar.
          </p>
        )}

        <Button onClick={handleBackToMenu}>
          Volver al Menú
        </Button>
      </div>
    </div>
  )
}