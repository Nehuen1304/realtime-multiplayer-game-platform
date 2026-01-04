from abc import ABC, abstractmethod
from typing import List, Optional

# Importa los modelos Pydantic y Enums que se usan en las firmas de los métodos
from ..domain.models import Game, PlayerInfo, Card, PlayerInGame
from ..api.schemas import GameLobbyInfo
from ..domain.enums import CardLocation, ResponseStatus

# --- INTERFAZ PARA OPERACIONES DE LECTURA (QUERIES) ---

"""
    Idealmente son operaciones que NO escriben la base de datos y solo devuelven el objeto o 
    una lista de objetos Pydantic pedidos.

    Es importante que
    - lo devuelto es un objeto pydantic listo para ser usado y entendido en game_manager. 
      No deberia devolver tablas nunca.
    - Podria quiza en algunos casos devolver errores o status responses, pero me parece que es 
      mas simple pensar en Objeto | None siempre como output. Creo.
"""


class IQueryManager(ABC):
    """
    Define el contrato para todas las operaciones de LECTURA de la base de datos.
    Cualquier clase que implemente esta interfaz debe proveer estos métodos.
    """

    @abstractmethod
    def get_game(self, game_id: int) -> Optional[Game]:
        pass

    @abstractmethod
    def list_games(self) -> List[GameLobbyInfo]:
        pass

    @abstractmethod
    def get_player(self, player_id: int) -> Optional[PlayerInfo]:
        pass

    @abstractmethod
    def list_players(self, game_id: int) -> List[PlayerInGame]:
        pass

    # ... (aca las firmas de TODOS los otros metodos de queries.py) ...
    # Por ejemplo:

    @abstractmethod
    def get_player_cards(self, game_id: int, player_id: int) -> List[Card]:
        pass

    @abstractmethod
    def is_player_in_game(self, game_id: int, player_id: int) -> bool:
        pass


# --- INTERFAZ PARA OPERACIONES DE ESCRITURA (COMMANDS) ---


"""
    Idealmente son operaciones que escriben la base de datos y solo devuelven 
    - Un ID de lo escrito
    - Un status OK/ERROR

    Yo simplificaria los outputs, me parece innecesario devolve run PlayerInfo por ejemplo,
    solo con Player_id bastaria. Eso simplifica la logica aca y da la informacion suficiente 
    para luego hacer algo con ese player.
"""


class ICommandManager(ABC):
    """
    Define el contrato para todas las operaciones de ESCRITURA en la base de datos.
    """

    @abstractmethod
    def create_game(self, game: Game) -> Optional[Game]:
        pass

    @abstractmethod
    def join_player_to_game(
        self, player_id: int, game_id: int
    ) -> ResponseStatus:
        pass

    @abstractmethod
    def save_game(self, game: Game) -> ResponseStatus:
        pass

    @abstractmethod
    def delete_game(self, game_id: int) -> ResponseStatus:
        pass

    # ... (aca las firmas de TODOS los otros metodos de commands.py) ...
    # Por ejemplo:

    @abstractmethod
    def create_new_player(self, player: PlayerInfo) -> Optional[PlayerInfo]:
        pass

    @abstractmethod
    def move_card(
        self,
        game_id: int,
        card_id: int,
        new_location: CardLocation,
        player_id: Optional[int] = None,
    ) -> ResponseStatus:
        pass
