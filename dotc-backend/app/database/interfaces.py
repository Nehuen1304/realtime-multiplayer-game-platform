from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date

# Importa los modelos Pydantic y Enums que se usan en las firmas de los métodos
from ..domain.models import (
    Game,
    PlayerInfo,
    Card,
    SecretCard,
    Avatar,
    PlayerRole,
    PlayerInGame,
    PendingAction,
)
from ..domain.enums import GameActionState
from ..api.schemas import GameLobbyInfo, PlayCardRequest
from ..domain.enums import GameStatus, CardLocation, CardType, ResponseStatus


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
    Define el contrato para todas las operaciones de LECTURA (Queries) de la base de datos.
    """

    # ═══════════════════════════════════════════════════════════
    # 🎮 QUERIES DE PARTIDAS (GameTable)
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def get_game(self, game_id: int) -> Optional[Game]:
        """
        Obtiene el objeto de dominio 'Game' completo, con todas sus relaciones
        cargadas (jugadores, mazos, etc.). Es la query más "pesada".
        """
        pass

    @abstractmethod
    def list_games_in_lobby(self) -> List[GameLobbyInfo]:
        """
        Devuelve una lista de DTOs 'GameLobbyInfo' solo para las partidas
        en estado LOBBY, optimizada para mostrar en un listado.
        """
        pass

    @abstractmethod
    def get_game_status(self, game_id: int) -> Optional[GameStatus]:
        """Obtiene únicamente el estado de una partida. Mucho más rápido que get_game()."""
        pass

    @abstractmethod
    def get_current_turn(self, game_id: int) -> Optional[int]:
        """Obtiene únicamente el ID del jugador cuyo turno es actual."""
        pass

    @abstractmethod
    def get_pending_saga(self, game_id: int) -> Optional[dict]:
        """Obtiene el 'pending_saga' de la partida (si existe)."""
        pass

    # ═══════════════════════════════════════════════════════════
    # 👤 QUERIES DE JUGADORES (PlayerTable)
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def get_player(self, player_id: int) -> Optional[PlayerInfo]:
        """Obtiene la información básica de un jugador por su ID."""
        pass

    @abstractmethod
    def get_player_name(self, player_id: int) -> Optional[str]:
        """Obtiene solo el nombre de un jugador."""
        pass

    @abstractmethod
    def get_players_in_game(self, game_id: int) -> List[PlayerInGame]:
        """
        Obtiene la lista de jugadores (como DTOs 'PlayerInGame') de una partida específica.
        Es más eficiente que llamar a get_game() si solo se necesitan los jugadores.
        """
        pass

    @abstractmethod
    def get_player_role(
        self, player_id: int, game_id: int
    ) -> Optional[PlayerRole]:
        """Obtiene el rol de un jugador específico dentro de una partida."""
        pass

    @abstractmethod
    def get_murderer_id(self, game_id: int) -> Optional[int]:
        """Obtiene el ID del jugador con el rol de Asesino en una partida."""
        pass

    @abstractmethod
    def get_accomplice_id(self, game_id: int) -> Optional[int]:
        """Obtiene el ID del jugador con el rol de Cómplice en una partida."""
        pass

    # ═══════════════════════════════════════════════════════════
    # 🃏 QUERIES DE CARTAS (CardTable & SecretCardTable)
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def get_card(self, card_id: int, game_id: int) -> Optional[Card]:
        """Obtiene una carta específica por su ID dentro de una partida."""
        pass

    @abstractmethod
    def get_secret(self, secret_id: int, game_id: int) -> Optional[SecretCard]:
        """Obtiene un secreto específico por su ID y el ID de la partida."""
        pass

    @abstractmethod
    def get_set(self, set_id: int, game_id: int) -> List[Card]:
        """Obtiene una lista de cartas que hayan sido jugadas en un set en
        especifico específicas por su ID dentro de una partida."""
        pass

    @abstractmethod
    def get_player_hand(self, game_id: int, player_id: int) -> List[Card]:
        """Obtiene todas las cartas en la mano de un jugador."""
        pass

    @abstractmethod
    def get_deck(self, game_id: int) -> List[Card]:
        """Obtiene todas las cartas del mazo de robo de una partida."""
        pass

    @abstractmethod
    def get_discard_pile(self, game_id: int) -> List[Card]:
        """Obtiene todas las cartas del mazo de descarte de una partida."""
        pass

    @abstractmethod
    def get_player_secrets(
        self, game_id: int, player_id: int
    ) -> List[SecretCard]:
        """Obtiene las cartas secretas de un jugador en una partida."""
        pass

    # ═══════════════════════════════════════════════════════════
    # ✅ QUERIES DE NUMEROS
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def get_max_set_id(self, game_id: int) -> Optional[int]:
        """
        Obtiene el valor más alto de 'set_id' presente en toda la tabla de cartas.
        """
        pass

    @abstractmethod
    def get_size_deck(self, game_id: int) -> int:
        """
        Obtiene el número de cartas en el mazo de robo (DRAW_PILE) de una partida.
        Devuelve 0 si el mazo está vacío o la partida no existe.
        """
        pass

    # ═══════════════════════════════════════════════════════════
    # ✅ QUERIES DE VALIDACIÓN (Booleanos y Existencia)
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def is_player_in_game(self, game_id: int, player_id: int) -> bool:
        """Verifica si un jugador es parte de una partida. Usa una consulta EXISTS para ser eficiente."""
        pass

    @abstractmethod
    def is_player_host(self, game_id: int, player_id: int) -> bool:
        """Verifica si un jugador es el anfitrión (host) de una partida."""
        pass

    @abstractmethod
    def game_name_exists(self, game_name: str) -> bool:
        """Verifica si ya existe una partida con un nombre determinado."""
        pass

    # ═══════════════════════════════════════════════════════════
    # ⏳ QUERIES DE JUGADAS PENDIENTES (PendingActionTable)
    # ═══════════════════════════════════════════════════════════
    
    @abstractmethod
    def get_pending_action(self, game_id: int) -> Optional[PendingAction]:
        """Obtiene la acción pendiente de una partida, si existe."""
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
    Define el contrato para todas las operaciones de ESCRITURA (Commands)
    en la base de datos. Cada método representa una operación atómica y simple.
    """

    # ═══════════════════════════════════════════════════════════
    # 👤 COMMANDS DE JUGADORES (PlayerTable)
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def create_player(
        self, name: str, birth_date: date, avatar: Avatar
    ) -> Optional[int]:
        """Crea un nuevo jugador. Devuelve el ID del jugador creado o None si falla."""
        pass

    @abstractmethod
    def delete_player(self, player_id: int) -> ResponseStatus:
        """Elimina un jugador por su ID."""
        pass

    @abstractmethod
    def set_player_role(
        self, player_id: int, game_id: int, role: PlayerRole
    ) -> ResponseStatus:
        """Asigna un rol a un jugador dentro de una partida específica."""
        pass

    @abstractmethod
    def set_player_social_disgrace(
        self, player_id: int, game_id: int, is_disgraced: bool
    ) -> ResponseStatus:
        """Marca o desmarca la desgracia social de un jugador en una partida."""
        pass

    # ═══════════════════════════════════════════════════════════
    # 🎮 COMMANDS DE PARTIDAS (GameTable & PlayersGames)
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def create_game(
        self,
        name: str,
        min_players: int,
        max_players: int,
        host_id: int,
        password: Optional[str] = None,
    ) -> Optional[int]:
        """Crea una nueva partida y asocia al host. Devuelve el ID de la partida o None."""
        pass

    @abstractmethod
    def delete_game(self, game_id: int) -> ResponseStatus:
        """Elimina una partida y todas sus relaciones asociadas (cascada)."""
        pass

    @abstractmethod
    def add_player_to_game(
        self, player_id: int, game_id: int
    ) -> ResponseStatus:
        """Añade una fila a la tabla de asociación PlayersGames."""
        pass

    @abstractmethod
    def remove_player_from_game(
        self, player_id: int, game_id: int
    ) -> ResponseStatus:
        """Elimina una fila de la tabla de asociación PlayersGames."""
        pass

    @abstractmethod
    def update_game_status(
        self, game_id: int, new_status: GameStatus
    ) -> ResponseStatus:
        """Actualiza el campo 'game_status' de una partida."""
        pass

    @abstractmethod
    def set_current_turn(self, game_id: int, player_id: int) -> ResponseStatus:
        """Actualiza el campo 'current_player' de una partida."""
        pass

    # ═══════════════════════════════════════════════════════════
    # 🃏 COMMANDS DE CARTAS (CardTable)
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def create_card(
        self,
        card_type: CardType,
        location: CardLocation,
        game_id: int,
        position: Optional[int] = None,
        set_id: Optional[int] = None,
        player_id: Optional[int] = None,
    ) -> Optional[int]:
        """Crea una nueva carta en la base de datos asociada a una partida."""
        pass

    @abstractmethod
    def create_deck_for_game(
        self, game_id: int, cards: List[Card]
    ) -> ResponseStatus:
        """Crea un conjunto de cartas (el mazo inicial) para una partida."""
        # Optimización para evitar N llamadas a create_card.
        pass

    @abstractmethod
    def update_card_location(
        self,
        card_id: int,
        game_id: int,
        new_location: CardLocation,
        owner_id: Optional[int] = None,
        set_id: Optional[int] = None,
    ) -> ResponseStatus:
        """
        Mueve una carta a una nueva ubicación.
        Actualiza 'location' y 'player_id' (si pasa a una mano).
        """
        pass

    @abstractmethod
    def update_cards_to_set(
        self,
        game_id: int,
        card_ids: List[int],
        player_id: int,
        set_id: int,
    ) -> ResponseStatus:
        """Actualiza la ubicación y asigna un set_id a un grupo de cartas."""
        pass

    @abstractmethod
    def setear_set_id(
        self, card_id: int, game_id: int, target_set_id: int
    ) -> ResponseStatus:
        """Actualiza el campo 'set_id' de una carta."""

    @abstractmethod
    def update_card_position(
        self, card_id: int, game_id: int, new_position: int
    ) -> ResponseStatus:
        """Actualiza la posición de una carta (útil para mazos ordenados)."""
        pass

    @abstractmethod
    def create_set(self, card_ids: List[int], game_id: int) -> int:
        """
        Crea un nuevo set asignando un nuevo set_id a un grupo de cartas.
        Devuelve el ID del nuevo set creado.
        """
        pass

    @abstractmethod
    def add_card_to_set(self, card_id: int, set_id: int, game_id: int) -> None:
        """Añade una carta a un set existente."""
        pass

    @abstractmethod
    def steal_set(self, set_id: int, new_owner_id: int, game_id: int) -> None:
        """Cambia el propietario de todas las cartas en un set."""
        pass

    # ═══════════════════════════════════════════════════════════
    # 🤫 COMMANDS DE SECRETOS (SecretCardTable)
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def create_secret_card(
        self, player_id: int, game_id: int, role: PlayerRole, is_revealed: bool
    ) -> Optional[int]:
        """Crea una nueva carta secreta en una partida en la base de datos."""
        pass

    @abstractmethod
    def reveal_secret_card(
        self, secret_id: int, game_id: int, is_revealed: bool
    ) -> ResponseStatus:
        """Actualiza el campo 'is_revealed' de una carta secreta."""
        pass

    @abstractmethod
    def set_game_action_state(
        self,
        game_id: int,
        state: GameActionState,
        prompted_player_id: Optional[int],
        initiator_id: Optional[int],
    ) -> ResponseStatus:
        """
        Actualiza el estado de acción de la partida (action_state, prompted_player_id, action_initiator_id).
        """
        pass

    @abstractmethod
    def clear_game_action_state(
        self,
        game_id: int,
    ) -> ResponseStatus:
        """
        Resetea el estado de acción de la partida (pone action_state en NONE y los otros en None).
        """
        pass

    @abstractmethod
    def change_secret_owner(
        self,
        secret_id: int,
        new_owner_id: int,
        game_id: int,
    ) -> ResponseStatus:
        """
        Cambia el propietario de una carta secreta (SecretCard) en una partida.
        """
        pass

    @abstractmethod
    def update_pending_saga(
        self, game_id: int, saga_data: Optional[dict]
    ) -> ResponseStatus:
        """
        Actualiza o limpia la columna 'pending_saga' para una partida.
        Usado para manejar acciones de múltiples pasos como votaciones o trades.
        """
        pass
    

    # ═══════════════════════════════════════════════════════════
    # ⏳ COMMANDS DE JUGADAS PENDIENTES (PendingActionTable)
    # ═══════════════════════════════════════════════════════════

    @abstractmethod
    def create_pending_action(self, game_id: int,
                              player_id: int,
                              request: 'PlayCardRequest') -> ResponseStatus:
        pass
        
    @abstractmethod
    def increment_nsf_responses(self, game_id: int, player_id: int,
                                add_nsf: bool) -> ResponseStatus:
        pass

    @abstractmethod
    def clear_pending_action(self, game_id: int) -> ResponseStatus:
        pass
