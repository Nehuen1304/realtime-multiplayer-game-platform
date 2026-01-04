// import { ManoPropia } from './features/ManoPropia/ManoPropia';
import { useState, useCallback } from 'react'
import { CrearUnirse } from "./features/ListadoDePartidas/CrearUnirse";
import PantallaInicio from './features/PantallaInicio'
import Lobby from './features/Lobby/Lobby'
import './App.css'
import Tablero from './features/Tablero/Tablero';

const SCREENS = {
  INICIO: 'inicio',
  CREAR_UNIRSE: 'crearUnirse',
  LOBBY: 'lobby',
  IN_GAME: 'inGame'
};

export function App() {
	const [playerName, setPlayerName] = useState(null);
	const [screen, setScreen] = useState(SCREENS.INICIO); // 'inicio', 'crearUnirse', 'lobby'
	const [playerId, setPlayerId] = useState(null);
	const [gameId, setGameId] = useState(null);

	// const playerId = 1; // SACAR. SOLO PARA TESTING
	// const gameId = 1; // SACAR. SOLO PARA TESTING
	// funciones envueltas useCallback
	// memorizar la función para que React entienda que es la misma en todos los renders
    const handlePlayerCreated = useCallback((name, id) => {
        setPlayerName(name);
        setPlayerId(id);
        setScreen(SCREENS.CREAR_UNIRSE);
    }, []); // El array vacío significa que esta función nunca cambiará
    const handleLeft = useCallback(()=>{
        setGameId(null); 
        setScreen(SCREENS.CREAR_UNIRSE);
    },[])
    const handleGameJoined = useCallback(gameId => {
        setGameId(gameId);
        setScreen(SCREENS.LOBBY);
    }, []);

    const handleGameStarted = useCallback(() => {
        setScreen(SCREENS.IN_GAME);
    }, []);

	switch (screen) {
    case SCREENS.INICIO:
      return <div className="App"><PantallaInicio onPlayerCreated={handlePlayerCreated} /></div>;
    case SCREENS.CREAR_UNIRSE:
      return <div className="App">
        <CrearUnirse playerName={playerName} playerId={playerId} onGameJoined={handleGameJoined} />
      </div>;
    case SCREENS.LOBBY:
      return <div className="App">
        <Lobby gameId={gameId} playerId={playerId} onGameStarted={handleGameStarted} onGameCancelar={handleLeft} />
      </div>;
    case SCREENS.IN_GAME:
      if (!gameId || !playerId) return <div className="App">Faltan datos de partida.</div>;
      return <div className="App">
        <Tablero playerName={playerName} game_id={gameId} player_id={playerId} />
      </div>;
    default:
      return <div className="App">Pantalla desconocida.</div>;
  }
}

export default App

