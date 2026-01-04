import React, { useEffect, useState, useMemo, useCallback } from 'react';
import './Lobby.css'; // Asumo que el CSS está en el mismo nivel o es una ruta conocida
import { Button } from '../../components/Button/Button'; // Ruta relativa
import { Window } from '../../components/Window/Window'; // Ruta relativa
import * as lobbyService from './lobbyService'; // Asumo un servicio HTTP para el lobby

// Importa el WSManager y la función para obtener los wsHandlers
import { WSManager } from "../../ws/wsManager";
import { getWsHandlers } from "../../ws/wsHandlers";
import { API_CONFIG } from '../../config/api'; // Para la URL base del WebSocket7
import { Alerta } from "../../components/Alerta/Alerta";

export function Lobby({ gameId, playerId, onGameStarted, onGameCancelar }) {
  const [players, setPlayers] = useState([]);
  const [hostId, setHostId] = useState(null);
  const [gameName, setGameName] = useState(null);
  const [alerta, setAlerta] = useState(null);
  const [minPlayers, setMinPlayers] = useState(2); // Valor por defecto
  const fetchAndUpdatePlayers = useCallback(async () => {
    try {
      const data = await lobbyService.getGameState(gameId);
      const gameData = data.game;
      if (gameData) {
        setPlayers(gameData.players || []);
        setMinPlayers(gameData.min_players ?? 2);
        const rawHostId = gameData.host?.player_id;
        setHostId(rawHostId !== null && rawHostId !== undefined ? Number(rawHostId) : null);
      }
    } catch (err) {
      setAlerta({ mensaje: "No se pudo actualizar la lista de jugadores", tipo: "error" });
    }
  }, [gameId]); // Dependencia: solo se recrea si gameId cambia


  const handleCancelar = async () => {
    try {
      await lobbyService.cancelGame(gameId, playerId);
   //   const normalizedPlayerId = Number(playerId);
    
        setAlerta({
          titulo: "Partida Cancelada",
          mensaje: "La partida ha sido cancelada .",
          tipo: "info"
        });

      // } else {
      //   setAlerta({
      //     titulo: "Partida Cancelada",
      //     mensaje: "La partida ha sido cancelada por el host.",
      //     tipo: "info"
      //   });
      // }
      if (onGameCancelar) {
        onGameCancelar();
      }
    } catch (error) {
      console.error("Error al cancelar/Salir la partida:", err);
      setAlerta({ mensaje: "No se pudo cancelar la partida", tipo: "error" });
    }
  }

  useEffect(() => {

    lobbyService.getGameState(gameId)
      .then(data => {
        console.log("📡 Respuesta del backend:", data);

        // La respuesta del backend tiene: {detail, game: {id, name, host, players, ...}}
        const gameData = data.game;

        if (!gameData) {
          setAlerta({ mensaje: "Error al obtener los datos del juego", tipo: "error" });
          return;
        }

        // Extraer hostId del objeto host.player_id
        const rawHostId = gameData.host?.player_id;
        setHostId(rawHostId !== null && rawHostId !== undefined ? Number(rawHostId) : null);
        console.log("🎯 Host ID:", {
          rawHostId,
          normalizado: Number(rawHostId),
          tipo: typeof rawHostId,
          host_completo: gameData.host
        });

        // Actualiza otros estados
        setGameName(gameData.name);
        setPlayers(gameData.players || []);

        console.log("🏠 Players recibidos:", gameData.players);
      }
      )
      .catch(err => {
        console.error("Error al obtener estado de la partida:", err);
        setAlerta({ mensaje: "No se pudo conectar con el servidor del juego", tipo: "error" });

      });
  }, [gameId]);

  const handleStartGame = async () => {
    try {
      const res = await lobbyService.startGame(gameId, playerId);
      // Host will
      console.log("res", res)
    } catch (err) {

      setAlerta({ mensaje: "No se pudo iniciar la partida", tipo: "error" });

    }
  };
  useEffect(() => {
    const wsBase = API_CONFIG.WEBSOCKET_BASE;
    // Asegúrate de que esta URL coincida con lo que tu backend espera para el Lobby.
    const wsUrl = `${wsBase}/ws/game/${gameId}/player/${playerId}`;
    console.log("🔌 Conectando WebSocket desde LobbyScreen a:", wsUrl);

    // Creamos los handlers específicos para el LobbyScreen, inyectando los callbacks
    const lobbySpecificHandlers = getWsHandlers({
      onGameStartedLobby: onGameStarted, // Aquí pasamos el callback prop
      updateLobbyPlayers: fetchAndUpdatePlayers,
      onGameCancel: onGameCancelar// Y el callback para actualizar la lista de jugadores
    });

    // Instanciamos el WSManager con los handlers específicos y el contexto "LOBBY"
    const ws = new WSManager(wsUrl, lobbySpecificHandlers, "LOBBY");

    // Función de limpieza para cerrar el WebSocket cuando el componente se desmonte
    return () => {
      console.log("🔌 Cerrando WebSocket de LobbyScreen.");
      ws.close();
    };
  }, [gameId, playerId, onGameStarted, fetchAndUpdatePlayers, onGameCancelar])
  return (
    <div className="lobby-container">
      <Window>
        <h1>
          {gameName}
        </h1>
        <ul className="lobby-player-list">
          {players.map(p => {
            // PlayerInGame usa player_id y player_name según el modelo del backend
            const pId = p.player_id;
            const pName = p.player_name;
            // Normalizar a número para comparaciones
            const normalizedPId = Number(pId);
            const normalizedPlayerId = Number(playerId);
            return (
              <li key={pId}>
                {pName}
                {normalizedPId === hostId && <span> (Host)</span>}
                {normalizedPId === normalizedPlayerId && <span> (Tú)</span>}
              </li>
            );
          })}
        </ul>
      </Window>
      {(() => {
        const normalizedPlayerId = Number(playerId);
        const isHost = normalizedPlayerId === hostId;
        console.log("🔐 Comparación host:", {
          playerId,
          normalizedPlayerId,
          hostId,
          isHost,
          tipo_playerId: typeof playerId,
          tipo_normalizedPlayerId: typeof normalizedPlayerId,
          tipo_hostId: typeof hostId
        });
        return isHost ? (
          <>
            <Button onClick={handleStartGame} disabled={players.length < minPlayers}>
              INICIAR PARTIDA
            </Button>
            <Button onClick={handleCancelar}>
              CANCELAR PARTIDA
            </Button>
          </>
        )
          : (
            <>
              <div className="lobby-waiting">
                Esperando a que el host inicie la partida...
              </div>

              <Button onClick={handleCancelar}>
                ABANDONAR PARTIDA
              </Button>
            </>
          );
      })()}

      {alerta && (
        <Alerta
          tipo={alerta.tipo}
          mensaje={alerta.mensaje}
          onClose={() => setAlerta(null)}
          duracion={2500}
        />
      )}

    </div>
  );
}

export default Lobby;
