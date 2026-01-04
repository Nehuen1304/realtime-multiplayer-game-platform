from typing import List, Optional, Literal
from .interfaces import ICardEffect
from ...database.interfaces import IQueryManager, ICommandManager
from ...game.helpers.notificators import Notificator
from ...domain.enums import (
    GameFlowStatus,
    ResponseStatus,
    GameActionState,
    CardLocation,
)
from ...domain.enums import ResponseStatus, GameActionState, CardLocation
from ...game.exceptions import InternalGameError


class BaseCardEffect(ICardEffect):
    """Clase base para inyección de dependencias."""

    def __init__(
        self,
        queries: IQueryManager,
        commands: ICommandManager,
        notifier: Notificator,
    ):
        self.queries = queries
        self.commands = commands
        self.notifier = notifier

    async def execute(
        self,
        # --- Parámetros del efecto ---
        game_id: int,
        player_id: int,
        card_ids: List[int],
        # --- Parámetros opcionales ---
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        raise NotImplementedError(
            "El método execute debe ser implementado por la subclase."
        )


class SocialFauxPasEffect(BaseCardEffect):
    """
    Efecto de la carta Devious 'Social Faux Pas'.
    El jugador que recibe esta carta (la víctima) debe descartarla
    y luego revelar un secreto de su propia elección.
    """

    async def execute(
        self,
        game_id: int,
        player_id: int,  # ¡IMPORTANTE: Este es el ID de la VÍCTIMA que recibió la carta!
        card_ids: List[int],  # Contendrá el ID de la carta 'Social Faux Pas'
        # --- Parámetros opcionales ---
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        # --- PASO 1: Descartar la carta Devious ---
        card_to_discard_id = card_ids[0]
        status = self.commands.update_card_location(
            card_id=card_to_discard_id,
            game_id=game_id,
            new_location=CardLocation.DISCARD_PILE,
            owner_id=None,
        )
        if status != ResponseStatus.OK:
            raise InternalGameError(
                "No se pudo descartar la carta Social Faux Pas."
            )
        card = self.queries.get_card(
            game_id=game_id, card_id=card_to_discard_id
        )
        assert card
        # Notificamos que la carta fue descartada por su efecto.
        # Es importante para el log y para que la UI la elimine visualmente.
        await self.notifier.notify_card_discarded(
            game_id=game_id, player_id=player_id, card_discarded=card
        )

        # --- PASO 2: Forzar a la víctima a revelar un secreto de su elección ---
        # ¡LÓGICA REUTILIZADA de RevealChosenSecretEffect! ¡Elegancia pura!
        self.commands.set_game_action_state(
            game_id=game_id,
            state=GameActionState.AWAITING_REVEAL_FOR_CHOICE,
            prompted_player_id=player_id,  # La víctima es la que debe actuar
            initiator_id=player_id,  # El iniciador es la propia víctima forzada
        )

        # Notificamos a la víctima que debe elegir un secreto.
        await self.notifier.notify_player_to_reveal_secret(game_id, player_id)

        return GameFlowStatus.PAUSED
