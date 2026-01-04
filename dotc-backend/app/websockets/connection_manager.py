from fastapi import WebSocket
from typing import Dict, Set, Optional
from .protocol.messages import WSMessage
from .interfaces import IConnectionManager


class ConnectionManager(IConnectionManager):
    def __init__(self):
        # La nueva estructura: game_id -> { player_id -> WebSocket }
        self.connections_by_game: Dict[int, Dict[int, WebSocket]] = {}
        self.lobby_connections: Set[WebSocket] = set()

    async def connect(
        self,
        websocket: WebSocket,
        game_id: Optional[int] = None,
        player_id: Optional[int] = None,
    ):
        """Registra una conexión. Si tiene game_id y player_id, la asocia. Si no, va al lobby."""
        await websocket.accept()
        if game_id is not None and player_id is not None:
            if game_id not in self.connections_by_game:
                self.connections_by_game[game_id] = {}
            self.connections_by_game[game_id][player_id] = websocket
        else:
            self.lobby_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Desconecta un websocket, ya sea este de lobby o de partida.
        Este método no depende de argumentos externos.
        """
        # Si el websocket está en el lobby.
        self.lobby_connections.discard(websocket)

        # Si el websocket está en alguna partida.
        game_to_delete_from = None
        player_to_delete = None

        for g_id, players in self.connections_by_game.items():
            for p_id, ws in players.items():
                if ws is websocket:
                    game_to_delete_from = g_id
                    player_to_delete = p_id
                    break
            if game_to_delete_from:
                break

        # Se elimina solo si encuentra una coincidencia
        if game_to_delete_from is not None and player_to_delete is not None:
            del self.connections_by_game[game_to_delete_from][player_to_delete]
            # Si la partida queda sin jugadores, la elimina del diccionario de Websockets.
            if not self.connections_by_game[game_to_delete_from]:
                del self.connections_by_game[game_to_delete_from]

    async def broadcast_to_game(self, message: WSMessage, game_id: int):
        """Envía un mensaje a TODOS los jugadores de una partida."""
        if game_id in self.connections_by_game:
            json_message = message.model_dump_json()
            # Iteramos sobre los sockets del diccionario interno
            for connection in self.connections_by_game[game_id].values():
                await connection.send_text(json_message)

    async def broadcast_to_lobby(self, message: WSMessage):
        json_message = message.model_dump_json()
        for connection in self.lobby_connections:
            await connection.send_text(json_message)

    async def send_to_player(
        self, message: WSMessage, game_id: int, player_id: int
    ):
        """Envía un mensaje a un jugador específico dentro de una partida."""
        if (
            game_id in self.connections_by_game
            and player_id in self.connections_by_game[game_id]
        ):
            connection = self.connections_by_game[game_id][player_id]
            json_message = message.model_dump_json()
            await connection.send_text(json_message)
        else:
            # Podrías loggear un warning acá. Significa que intentaste mandarle
            # un mensaje a un jugador que no está conectado.
            print(
                f"WARN: Intento de enviar mensaje a jugador {player_id} en partida {game_id}, pero no se encontró conexión."
            )
