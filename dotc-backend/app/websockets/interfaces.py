from abc import ABC, abstractmethod
from fastapi import WebSocket
from typing import Optional

from .protocol.messages import WSMessage


class IConnectionManager(ABC):
    """
    Define el contrato para cualquier clase que gestione conexiones WebSocket.
    Abstrae los detalles de implementación de la lógica de negocio.
    """

    @abstractmethod
    async def connect(
        self,
        websocket: WebSocket,
        game_id: Optional[int] = None,
        player_id: Optional[int] = None,
    ) -> None:
        """Genera una nueva conexion WebSocket, ya sea al lobby inicial o a una partida."""
        pass

    @abstractmethod
    def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        """Desconecta una conexion WebSocket."""
        pass

    @abstractmethod
    async def broadcast_to_game(self, message: WSMessage, game_id: int) -> None:
        """Envía un mensaje a todos los clientes de una partida específica."""
        pass

    @abstractmethod
    async def broadcast_to_lobby(self, message: WSMessage) -> None:
        """Envía un mensaje a todos los clientes en el lobby general."""
        pass

    @abstractmethod
    async def send_to_player(
        self, message: WSMessage, game_id: int, player_id: int
    ):
        """Envía un mensaje a un jugador específico dentro de una partida."""
        pass
