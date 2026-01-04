from pydantic import BaseModel, Field
from typing import Literal, List

from .events import WSEvent
from ...domain.models import Card
from ...domain.enums import PlayerRole
from ...api.schemas import GameLobbyInfo
from typing import Optional

# ---------------------------------------------------------------------------
# --- Modelos de Detalles para cada Evento ---
# ---------------------------------------------------------------------------

"""
Modelos de Detalles para Eventos del Lobby (NotInGame)
Estos eventos son enviados por broadcast a todos los usuarios que no están en una partida.
"""


class GameCreatedDetails(BaseModel):
    """
    Destinatarios: Broadcast a todos en el Lobby.
    Notifica que una nueva partida está disponible para unirse.
    """

    event: Literal[WSEvent.GAME_CREATED] = WSEvent.GAME_CREATED
    game: GameLobbyInfo = Field(
        ...,
        description="Objeto con la información pública de la nueva partida.",
    )


class GameUpdatedDetails(BaseModel):
    """
    Destinatarios: Broadcast a todos en el Lobby.
    Actualiza la información de una partida existente en el Lobby (ej: contador de jugadores, estado).
    """

    event: Literal[WSEvent.GAME_UPDATED] = WSEvent.GAME_UPDATED
    game: GameLobbyInfo = Field(
        ...,
        description="El objeto completo y actualizado de la partida en el lobby.",
    )


class RequestToDonateDetails(BaseModel):
    """
    Destinatarios: Broadcast a todos en el lobby.
    Notifica que "tienes que donar una carta al jugador de {direction = [ left right ]}
    """

    event: Literal[WSEvent.REQUEST_TO_DONATE] = WSEvent.REQUEST_TO_DONATE
    direction: Literal["left", "right"] = Field(
        ..., description="La dirección a la que se debe donar la carta."
    )


class GameRemovedDetails(BaseModel):
    """
    Destinatarios: Broadcast a todos en el Lobby.
    Notifica que una partida fue cancelada y ya no está disponible.
    """

    event: Literal[WSEvent.GAME_REMOVED] = WSEvent.GAME_REMOVED
    game_id: int = Field(..., description="ID de la partida que fue eliminada.")


"""
Modelos de Detalles para Eventos de Partida (InGame)
Estos eventos son enviados por broadcast únicamente a los jugadores dentro de una partida específica.
"""

class GameOverDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que el asesino ha ganado.
    """

    event: Literal[WSEvent.GAME_OVER] = WSEvent.GAME_OVER
    reason: str = Field(..., description="Razón por la cual terminó el juego.")
    murderer_id: int = Field(..., description="ID del jugador asesino.")
    accomplice_id: Optional[int] = Field(..., description="ID del jugador cómplice.")
    game_id: int = Field(..., description="ID de la partida ganada por el asesino.")

class NewTurnDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Anuncia el inicio de un nuevo turno.
    """

    event: Literal[WSEvent.NEW_TURN] = WSEvent.NEW_TURN
    turn_player_id: int = Field(
        ..., description="ID del jugador que ahora tiene el turno."
    )


class CardPlayedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que un jugador ha jugado una carta.
    """

    event: Literal[WSEvent.CARD_PLAYED] = WSEvent.CARD_PLAYED
    player_id: int = Field(..., description="ID del jugador que jugó la carta.")
    card_played: Card = Field(..., description="La carta que fue jugada.")


class CardDiscardedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que un jugador ha descartado una carta.
    """

    event: Literal[WSEvent.CARD_DISCARDED] = WSEvent.CARD_DISCARDED
    player_id: int = Field(
        ..., description="ID del jugador que descartó la carta."
    )
    card: Card = Field(..., description="La carta que fue descartada.")


class PlayerDrewFromDeckDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica públicamente que un jugador ha robado del mazo (sin revelar la carta).
    """

    event: Literal[WSEvent.PLAYER_DREW_FROM_DECK] = (
        WSEvent.PLAYER_DREW_FROM_DECK
    )
    player_id: int = Field(..., description="ID del jugador que robó la carta.")
    deck_size: int = Field(
        ..., description="El nuevo tamaño del mazo de robo tras la acción."
    )


class DeckUpdatedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Evento genérico para forzar una actualización del estado del mazo en los clientes.
    """

    event: Literal[WSEvent.DECK_UPDATED] = WSEvent.DECK_UPDATED
    deck_size: int = Field(
        ..., description="El tamaño actual del mazo de robo."
    )


"""
Modelos de Detalles para Eventos Compuestos
Estos eventos son generados por una acción que requiere notificar a dos audiencias distintas:
1. A los jugadores DENTRO de la partida (con un payload específico).
2. A los usuarios en el LOBBY (generalmente con un 'GAME_UPDATED').
"""


class PlayerJoinedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que un nuevo jugador se ha unido al juego. Este evento va acompañado
    de un 'GAME_UPDATED' al lobby.
    """

    event: Literal[WSEvent.PLAYER_JOINED] = WSEvent.PLAYER_JOINED
    player_id: int = Field(..., description="ID del jugador que se unió.")
    player_name: str = Field(..., description="Nombre del jugador que se unió.")
    game_id: int = Field(..., description="ID de la partida a la que se unió.")


class PlayerLeftDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que un jugador ha abandonado el juego. Este evento va acompañado
    de un 'GAME_UPDATED' al lobby.
    """

    event: Literal[WSEvent.PLAYER_LEFT] = WSEvent.PLAYER_LEFT
    player_id: int = Field(
        ..., description="ID del jugador que abandonó la partida."
    )
    player_name: str = Field(..., description="Nombre del jugador que se fue.")
    game_id: int = Field(..., description="ID de la partida que abandonó.")
    is_host: bool = Field(
        False,
        description="Indica si el jugador que se fue era el anfitrión (host).",
    )


class GameStartedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Anuncia que el juego ha comenzado. Este evento va acompañado
    de un 'GAME_UPDATED' al lobby para cambiar el estado de la partida.
    """

    event: Literal[WSEvent.GAME_STARTED] = WSEvent.GAME_STARTED
    game_id: int = Field(..., description="ID de la partida que ha comenzado.")
    players_in_turn_order: List[int] = Field(
        ..., description="Lista de IDs de los jugadores en su orden de turno."
    )
    first_player_id: int = Field(
        ..., description="ID del jugador que tiene el primer turno."
    )


class HandsUpdatedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que la mano del destinatario ha sido actualizada.
    No da mas informacion.
    """

    event: Literal[WSEvent.HAND_UPDATED] = WSEvent.HAND_UPDATED


class DraftUpdatedDetails(BaseModel):
    """
    Notifica que un slot del Card Draft ha sido actualizado.
    """

    event: Literal[WSEvent.DRAFT_UPDATED] = WSEvent.DRAFT_UPDATED
    card_taken_id: int
    new_card: Optional[Card] = None


class CardsPlayedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que un jugador ha jugado un conjunto de cartas (para formar un set).
    """

    event: Literal[WSEvent.CARDS_PLAYED] = WSEvent.CARDS_PLAYED
    player_id: int = Field(
        ..., description="ID del jugador que jugó las cartas."
    )
    cards_played: List[Card] = Field(
        ..., description="Las cartas que fueron jugadas."
    )
    is_cancellable: bool
    player_name: Optional[str] = None
    action_id: Optional[int] = Field(
        None, description="ID de la acción pendiente (si es cancelable)."
    )


class PlayerToRevealSecretDetails(BaseModel):
    """
    Destinatarios: Mensaje privado a un jugador específico.
    Le ordena al jugador que debe elegir un secreto para revelar.
    """

    event: Literal[WSEvent.PROMPT_REVEAL] = WSEvent.PROMPT_REVEAL
    # Este sobre puede estar vacío, su sola llegada ya es la orden.
    # Opcionalmente, podríamos agregar quién lo pidió, etc.
    # message: str = "Te toca revelar un secreto, ¡mové el culo!"


class SecretRevealedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que el secreto de un jugador ha sido revelado.
    """

    event: Literal[WSEvent.SECRET_REVEALED] = WSEvent.SECRET_REVEALED
    secret_id: int = Field(
        ...,
        description="Secreto a revelar",
    )
    role: PlayerRole = Field(..., description="ROL")
    game_id: int = Field(..., description="ID de la partida a la que se unió.")
    player_id: int = Field(..., description="dueno del secreto")


class SecretStolenDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que un secreto fue robado de un jugador y transferido a otro.
    """

    event: Literal[WSEvent.SECRET_STOLEN] = WSEvent.SECRET_STOLEN
    thief_id: int = Field(
        ..., description="ID del jugador que ahora posee el secreto."
    )
    victim_id: int = Field(
        ..., description="ID del jugador que perdió el secreto."
    )


class SecretHiddenDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que un secreto de un jugador fue ocultado.
    """

    event: Literal[WSEvent.SECRET_HIDDEN] = WSEvent.SECRET_HIDDEN
    secret_id: int = Field(
        ...,
        description="Secreto ocultado",
    )
    player_id: int = Field(..., description="ID del jugador dueño del secreto")
    game_id: int = Field(..., description="ID de la partida a la que se unió.")


class SocialDisgraceAppliedDetails(BaseModel):
    event: Literal[WSEvent.SD_APPLIED] = WSEvent.SD_APPLIED
    player_id: int = Field(..., description="Jugador afectado")
    game_id: int = Field(..., description="Partida")


class SocialDisgraceRemovedDetails(BaseModel):
    event: Literal[WSEvent.SD_REMOVED] = WSEvent.SD_REMOVED
    player_id: int = Field(..., description="Jugador afectado")
    game_id: int = Field(..., description="Partida")


class GameOverDetails(BaseModel):
    event: Literal[WSEvent.GAME_OVER] = WSEvent.GAME_OVER
    game_id: int = Field(..., description="Partida finalizada")


class SetStolenDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que un set ha sido robado de un jugador y transferido a otro.
    """

    event: Literal[WSEvent.SET_STOLEN] = WSEvent.SET_STOLEN
    thief_id: int = Field(
        ..., description="ID del jugador que ahora posee el set."
    )
    victim_id: int = Field(..., description="ID del jugador que perdió el set.")
    set_id: int = Field(..., description="ID del set que fue robado.")
    set_cards: List[Card] = Field(
        ..., description="Las cartas que componen el set robado."
    )


class PromptDrawFromDiscardDetails(BaseModel):
    """
    Destinatarios: Un jugador en ESPECIFICO pidiendole que seleccione una carta de las mostradas para
    robar a su mano.
    """

    event: Literal[WSEvent.PROMPT_DRAW_FROM_DISCARD] = (
        WSEvent.PROMPT_DRAW_FROM_DISCARD
    )
    cards: List[Card] = Field(
        ...,
        description="Tenes que elegir una carta de las ultimas en la pila de descarte.",
    )


class TradeRequestedDetails(BaseModel):
    """
    Destinatarios: Mensaje privado a un jugador específico.
    Notifica que debe seleccionar una carta para intercambiar.
    """

    event: Literal[WSEvent.TRADE_REQUESTED] = WSEvent.TRADE_REQUESTED
    initiator_player_id: int = Field(
        ..., description="ID del jugador que inició el intercambio."
    )


class HandUpdatedDetails(BaseModel):
    """
    Destinatarios: Mensaje privado a un jugador específico.
    Notifica que su mano ha sido actualizada.
    """

    event: Literal[WSEvent.HAND_UPDATED] = WSEvent.HAND_UPDATED
    hand: List[Card] = Field(
        ..., description="La mano actualizada del jugador."
    )


class CardsNSFDiscardedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que un jugador ha obligado a otro a descartar
    todas sus cartas de tipo 'Not So Fast'.
    """

    event: Literal[WSEvent.CARDS_NSF_DISCARDED] = WSEvent.CARDS_NSF_DISCARDED
    source_player_id: int = Field(
        ..., description="ID del jugador que obligó a descartar cartas."
    )
    target_player_id: int = Field(
        ..., description="ID del jugador que fue obligado a descartar cartas."
    )
    discarded_cards: List[Card] = Field(
        ...,
        description="Las cartas de tipo 'Not So Fast' que fueron descartadas.",
    )

class VoteStartedDetails(BaseModel):
    """
    Payload para cuando se inicia una votación.
    El payload está vacío, la llegada del evento es la señal.
    """

    event: Literal[WSEvent.VOTE_STARTED] = WSEvent.VOTE_STARTED

class VoteEndedDetails(BaseModel):
    """Payload para cuando una votación ha terminado."""

    event: Literal[WSEvent.VOTE_ENDED] = WSEvent.VOTE_ENDED
    most_voted_player_id: Optional[int]
    tie: bool  # Para informar al frontend si hubo empate

class PlayerActionCancelledDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que la acción de un jugador ha sido cancelada.
    """

    event: Literal[WSEvent.ACTION_CANCELLED] = WSEvent.ACTION_CANCELLED
    player_id: int = Field(
        ..., description="ID del jugador cuya acción fue cancelada."
    )
    cards_cancelled: List[Card] = Field(
        ..., description="Las cartas involucradas en la acción cancelada."
    )

class PlayerActionResolvedDetails(BaseModel):
    """
    Destinatarios: Broadcast a los jugadores de la partida.
    Notifica que la acción de un jugador ha sido resuelta.
    """

    event: Literal[WSEvent.ACTION_RESOLVED] = WSEvent.ACTION_RESOLVED
    player_id: int = Field(
        ..., description="ID del jugador cuya acción fue resuelta."
    )
    cards_resolved: List[Card] = Field(
        ..., description="Las cartas involucradas en la acción resuelta."
    )
    action_id: Optional[int] = Field(
        None, description="ID de la acción que fue resuelta."
    )
