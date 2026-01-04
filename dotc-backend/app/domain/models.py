from datetime import date
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

from app.domain.enums import PlayCardActionType

from .enums import (
    Avatar,
    GameStatus,
    PlayerRole,
    CardType,
    CardLocation,
    GameActionState,
)

# ------------------- MODELOS DE DOMINIO BASE -------------------


class PlayerInfo(BaseModel):
    """
    Información básica y persistente de un jugador.
    - player_id: int
    - player_name: str
    - player_birth_date: date
    - player_avatar: Avatar
    """

    model_config = ConfigDict(from_attributes=True)

    player_id: int
    player_name: str
    player_birth_date: date
    player_avatar: Avatar


class Card(BaseModel):
    """
    Representa una instancia única de una carta jugable dentro de una partida.
    - player_id: Optional[int]
    - location: CardLocation
    - position: Optional[int]
    - card_id: int
    - game_id: int
    - card_type: CardType
    - set_id: Optional[int]
    """

    model_config = ConfigDict(from_attributes=True)

    player_id: Optional[int] = None
    location: CardLocation
    position: Optional[int] = None
    card_id: int
    game_id: int
    card_type: CardType
    set_id: Optional[int] = None


class SecretCard(BaseModel):
    """
    Representa una carta de rol secreto asignada a un jugador.
    - secret_id: int
    - game_id: int
    - player_id: int
    - role: PlayerRole (MURDERER | INNOCENT | ACCOMPLICE)
    - is_revealed: bool
    """

    model_config = ConfigDict(from_attributes=True)

    secret_id: int
    game_id: int
    player_id: int
    role: PlayerRole
    is_revealed: bool = False


class PlayerInGame(PlayerInfo):
    """
    Representa el estado de un jugador dentro de una partida específica.
    - player_id: int (heredado)
    - player_name: str (heredado)
    - player_birth_date: date (heredado)
    - player_avatar: Avatar (heredado)
    - game_id: Optional[int]
    - player_role: Optional[PlayerRole] (MURDERER | INNOCENT | ACCOMPLICE)
    - turn_order: Optional[int]
    - hand: List[Card]
    - secrets: List[SecretCard]
    - social_disgrace: bool
    """

    model_config = ConfigDict(from_attributes=True)
    game_id: Optional[int] = None
    player_role: Optional[PlayerRole] = None
    turn_order: Optional[int] = None
    hand: List[Card] = []
    secrets: List[SecretCard] = []
    social_disgrace: bool = False


class Game(BaseModel):
    """
    Representa el estado completo de una partida.
    - id: int
    - name: str
    - min_players: int
    - max_players: int
    - password: Optional[str]
    - host: PlayerInfo
    - status: GameStatus
    - players: List[PlayerInGame]
    - deck: List[Card]
    - discard_pile: List[Card]
    - draft: List[Card]
    - current_turn_player_id: Optional[int]
    - action_state: Optional[GameActionState] (NONE | AWAITING_REVEAL_FOR_CHOICE | AWAITING_REVEAL_FOR_STEAL)
    - action_initiator_id: Optional[int]
    - prompted_player_id: Optional[int]
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    min_players: int
    max_players: int
    password: Optional[str] = None
    host: PlayerInfo
    status: GameStatus
    players: List[PlayerInGame] = []
    deck: List[Card] = []
    discard_pile: List[Card] = []
    draft: List[Card] = []
    current_turn_player_id: Optional[int] = None
    action_state: Optional[GameActionState] = None
    action_initiator_id: Optional[int] = None
    prompted_player_id: Optional[int] = None
    pending_saga: Optional[Dict[str, Any]] = None
      
class PendingAction(BaseModel):
    """Representa una acción pendiente de resolución por NSF. Ahora con una lista de cartas real."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int
    player_id: int
    action_type: PlayCardActionType
    
    # ¡Ahora es una lista de objetos Card, no solo IDs!
    cards: List[Card] = []
    
    # Targets
    target_player_id: Optional[int]
    target_secret_id: Optional[int]
    target_card_id: Optional[int]
    target_set_id: Optional[int]
    
    # Contadores
    responses_count: int
    nsf_count: int
    last_action_player_id: int
