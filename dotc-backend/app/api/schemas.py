from datetime import date
from pydantic import BaseModel
from typing import List, Optional, Literal
from enum import Enum

from ..domain.enums import GameStatus, Avatar, PlayCardActionType
from ..domain.models import PlayerInfo, Card, SecretCard, Game

# ------------------- MODELO DE RESPUESTA BASE -------------------


class BaseResponse(BaseModel):
    """
    Modelo base para todas las respuestas de acciones de la API.
    - detail: Optional[str]
    """

    detail: Optional[str] = (
        None  # Campo opcional para dar más contexto al frontend
    )


# ------------------- MODELOS DE API (REQUESTS) -------------------


class CreatePlayerRequest(BaseModel):
    """
    Petición para crear un nuevo jugador.
    - name: str
    - birth_date: date
    - avatar: Optional[Avatar] (DEFAULT | ...)
    """

    name: str
    birth_date: date
    avatar: Optional[Avatar] = Avatar.DEFAULT


class CreateGameRequest(BaseModel):
    """
    Petición para crear una nueva partida.
    - host_id: int
    - game_name: str
    - min_players: int
    - max_players: int
    - password: Optional[str]
    """

    host_id: int
    game_name: str
    min_players: int
    max_players: int
    password: Optional[str] = None


class JoinGameRequest(BaseModel):
    """
    Petición para unirse a una partida.
    - player_id: int
    - game_id: Optional[int]
    - password: Optional[str]
    """

    player_id: int
    game_id: Optional[int] = None
    password: Optional[str] = None


class LeaveGameRequest(BaseModel):
    """
    Petición para abandonar una partida.
    - player_id: int
    - game_id: int
    """

    player_id: int
    game_id: int


class PlayerActionRequest(BaseModel):
    """
    Petición genérica para una acción de un jugador dentro de una partida.
    - player_id: int
    - game_id: int
    """

    player_id: int
    game_id: int


class RevealSecretRequest(PlayerActionRequest):
    """
    - player_id: int (heredado)
    - game_id: int (heredado)
    - secret_id: int
    """

    secret_id: int


class DiscardCardRequest(PlayerActionRequest):
    """
    Petición para descartar una carta.
    - player_id: int (heredado)
    - game_id: int (heredado)
    - card_id: int
    """

    card_id: int


class PlayCardRequest(PlayerActionRequest):
    """
    Un jugador al querer jugar una carta me manda esto. Se deriva por los datos si es
    carta individual (detective agregado a set o evento) o grupal (set de detectives desde la mano).
    - player_id: int (heredado)
    - game_id: int (heredado)
    - action_type: PlayCardActionType (EVENT | NEW_SET | ADD EXISTING SET | INSTANT)
    - card_ids: List[int] # IDs de cartas jugadas (1 o varias)
    - target_player_id: Optional[int] # opcional si necesito apuntar
    - target_secret_id: Optional[int] # opcional si necesito robar secreto
    - target_card_id: Optional[int] = None  # opcional si necesito elegir una carta de una mano (trade)
    - target_set_id: Optional[int] = None  # opcional si quiero jugar una carta add set
    """

    action_type: PlayCardActionType
    card_ids: List[int]  # IDs de cartas jugadas (1 o varias)
    target_set_id: Optional[int] = (
        None  # Opcional si la carta se agrega a un set existente
    )
    target_player_id: Optional[int] = None  # opcional si necesito apuntar
    target_secret_id: Optional[int] = None  # opcional si necesito robar secreto
    target_card_id: Optional[int] = (
        None  # opcional si necesito elegir una carta de una mano (trade)
    )
    trade_direction: Optional[Literal["left", "right"]] = None


class GetCurrentTurnRequest(BaseModel):
    """
    Petición para consultar quién tiene el turno actual en una partida.
    - game_id: int
    """

    game_id: int


class ConsultDeckSizeRequest(BaseModel):
    """
    Petición para consultar el número de cartas restantes en el mazo de robo.
    - game_id: int
    """

    game_id: int


class DrawSource(str, Enum):
    """
    Define las fuentes desde las cuales se pueden robar cartas.
    - DECK
    - DRAFT
    - DISCARD
    """

    DECK = "deck"
    DRAFT = "draft"
    DISCARD = "discard"


class SubmitTradeChoiceRequest(PlayerActionRequest):
    """
    Petición para donar una carta a otro jugador.
    - player_id: int (heredado)
    - game_id: int (heredado)
    - card_id: int
    """

    card_id: int


class DrawCardRequest(PlayerActionRequest):
    """
    Petición para robar una carta. Especifica la fuente.
    - source: DrawSource (DECK | DRAFT | DISCARD)
    - card_id: Optional[int]
    """

    source: DrawSource
    card_id: Optional[int] = None


class VoteRequest(PlayerActionRequest):
    """
    Schema para la solicitud de emisión de un voto durante el efecto
    'Point Your Suspicions'.
    """

    voted_player_id: Optional[int] = (
        None  # El ID del jugador por el que se vota (puede ser null)
    )


class ExchangeCardRequest(PlayerActionRequest):
    """
    Petición para intercambiar una carta durante un Card Trade.
    - player_id: int (heredado)
    - game_id: int (heredado)
    - card_id: int
    """

    card_id: int


# ------------------- MODELOS DE API (RESPONSES) -------------------


class GeneralActionResponse(BaseResponse):
    """
    Respuesta genérica para acciones que solo necesitan reportar un detail opcional.
    - detail: Optional[str] (heredado)
    """

    pass


class CreatePlayerResponse(BaseModel):
    """
    Respuesta al crear un nuevo jugador.
    - player_id: Optional[int]
    """

    player_id: int


class CreateGameResponse(BaseModel):
    """
    Respuesta al crear una nueva partida.
    - game_id: Optional[int]
    """

    game_id: int


class JoinGameResponse(GeneralActionResponse):
    """
    Respuesta al intentar unirse a una partida.
    - detail: Optional[str] (heredado)
    """

    pass


class LeaveGameResponse(GeneralActionResponse):
    """
    Respuesta al abandonar una partida.
    - detail: Optional[str] (heredado)
    """

    pass


class StartGameResponse(GeneralActionResponse):
    """
    Respuesta al iniciar una partida.
    - detail: Optional[str] (heredado)
    - player_id_first_turn: Optional[int]
    """

    player_id_first_turn: Optional[int] = None


class DrawCardResponse(GeneralActionResponse):
    """
    Respuesta al robar una carta del mazo.
    - detail: Optional[str] (heredado)
    - drawn_card: Optional[Card]
    """

    drawn_card: Optional[Card] = None


class FinishTurnResponse(GeneralActionResponse):
    """
    Respuesta al finalizar un turno.
    - detail: Optional[str] (heredado)
    - next_player_id: Optional[int]
    """

    next_player_id: Optional[int] = None


# --- Respuestas de Consulta ---
# Estas respuestas devuelven datos + su ResponseStatus+Details.
# Si el recurso no existe devuelven datos default + su ResponseStatus+Details.


class GameLobbyInfo(BaseModel):  # TODO: deberia ser una response?
    """
    Información resumida de una partida para ser mostrada en el lobby.
    - id: int
    - name: str
    - min_players: int
    - max_players: int
    - host_id: int
    - player_count: int
    - password: Optional[str]
    - game_status: GameStatus (LOBBY | IN_PROGRESS | FINISHED)
    """

    id: int
    name: str
    min_players: int
    max_players: int
    host_id: int
    player_count: int
    password: Optional[str]
    game_status: GameStatus


class ListGamesResponse(GeneralActionResponse):
    """
    Respuesta con el listado de partidas disponibles en el lobby.
    - detail: Optional[str]
    - games: List[GameLobbyInfo]
    """

    games: List[GameLobbyInfo]


class GameStateResponse(GeneralActionResponse):
    """
    Respuesta que contiene el estado completo de una partida.
    - detail: Optional[str]
    - game: Optional[Game]
    """

    game: Optional[Game]


class ConsultDeckSizeResponse(GeneralActionResponse):
    """
    Respuesta con el número de cartas restantes en el mazo de robo.
    - detail: Optional[str]
    - size: int
    """

    size_deck: int


class PlayerHandResponse(GeneralActionResponse):
    """
    Respuesta con el listado de cartas en la mano de un jugador.
    - detail: Optional[str]
    - cards: Optional[List[Card]]
    """

    cards: Optional[List[Card]]


class PlayerSecretsResponse(GeneralActionResponse):
    """
    Respuesta con el listado de cartas de secreto de un jugador.
    - detail: Optional[str]
    - secrets: Optional[List[SecretCard]]
    """

    secrets: Optional[List[SecretCard]]


class GetCurrentTurnResponse(GeneralActionResponse):
    """
    Respuesta que indica el ID del jugador que tiene el turno actual.
    - detail: Optional[str]
    - player_id: Optional[int]
    """

    player_id: Optional[int]


class ListPlayersResponse(GeneralActionResponse):
    """
    Respuesta con el listado de jugadores en una partida.
    - detail: Optional[str]
    - players: Optional[List[PlayerInfo]]
    """

    players: Optional[List[PlayerInfo]]
