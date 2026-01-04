from typing import Optional, List, Annotated, Literal
from .interfaces import ICardEffect
from app.database.interfaces import IQueryManager, ICommandManager
from app.game.helpers.notificators import Notificator

from app.domain.models import SecretCard
from ...domain.enums import (
    PlayerRole,
    ResponseStatus,
    GameActionState,
    PlayerRole,
    GameFlowStatus,
)
from ..exceptions import (
    InvalidAction,
    InternalGameError,
    ResourceNotFound,
    ActionConflict,
)


class BaseCardEffect(ICardEffect):
    """Clase base para inyección de dependencias."""

    def __init__(
        self,
        queries: Annotated[IQueryManager, "Gestor de consultas"],
        commands: Annotated[ICommandManager, "Gestor de comandos"],
        notifier: Annotated[Notificator, "Gestor de notificaciones"],
    ):
        self.read = queries
        self.write = commands
        self.notifier = notifier

    async def execute(
        self,
        game_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        raise NotImplementedError(
            "El método execute debe ser implementado por la subclase."
        )


# =================================================================
# --- CLASES DE EFECTO CONCRETAS ---
# =================================================================


class RevealSpecificSecretEffect(BaseCardEffect):
    """Efecto: Eliges un jugador, que debe revelar un secreto DE TU ELECCIÓN."""

    async def execute(
        self,
        game_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        print(
            f"EJECUTANDO: Revelar secreto específico {target_secret_id} del jugador {target_player_id}"
        )

        if target_player_id is None or target_secret_id is None:
            raise InvalidAction(
                "Este efecto requiere un jugador y un secreto objetivo."
            )

        player_secrets = self.read.get_player_secrets(
            game_id=game_id, player_id=target_player_id
        )
        try:
            chosen_secret = next(
                s for s in player_secrets if s.secret_id == target_secret_id
            )
        except StopIteration:
            raise ResourceNotFound(
                f"El secreto {target_secret_id} no pertenece al jugador {target_player_id}."
            )

        # Actualizar la BD para marcar el secreto como revelado
        status = self.write.reveal_secret_card(
            secret_id=target_secret_id, game_id=game_id, is_revealed=True
        )
        if status != ResponseStatus.OK:
            raise InternalGameError(
                "Fallo al revelar el secreto en la base de datos."
            )

        await self.notifier.notify_secret_revealed(
            game_id=game_id,
            secret_id=target_secret_id,
            player_role=chosen_secret.role,
            player_id=target_player_id,
        )

        murderer_id = player_id
        accomplice_id = self.read.get_accomplice_id(game_id)
        secret = self.read.get_secret(secret_id=target_secret_id, game_id=game_id)
        if not secret:
            raise ResourceNotFound(f"El secreto {target_secret_id} no fue encontrado.")

        if secret.role == PlayerRole.MURDERER:
            await self.notifier.notify_innocents_win(
                game_id=game_id,
                murderer_id=murderer_id,
                accomplice_id=accomplice_id,
            )
            status = self.write.delete_game(game_id=game_id)
            if status != ResponseStatus.OK:
                error_message = "La base de datos no pudo eliminar la partida."
                raise InternalGameError(detail=error_message)
            await self.notifier.notify_game_removed(game_id)

        # Lógica de desgracia social post-revelación
        player_role = self.read.get_player_role(
            player_id=target_player_id, game_id=game_id
        )
        if player_role != PlayerRole.MURDERER:
            all_secrets = self.read.get_player_secrets(
                game_id=game_id, player_id=target_player_id
            )
            all_revealed = all(s.is_revealed for s in all_secrets)
            accomplice_revealed = any(
                s.secret_id == target_secret_id
                and s.role == PlayerRole.ACCOMPLICE
                for s in all_secrets
            )
            if all_revealed or accomplice_revealed:
                self.write.set_player_social_disgrace(
                    player_id=target_player_id,
                    game_id=game_id,
                    is_disgraced=True,
                )
                await self.notifier.notify_social_disgrace_applied(
                    game_id=game_id, player_id=target_player_id
                )
                players = self.read.get_players_in_game(game_id)
                innocent_disgraced = [
                    p
                    for p in players
                    if p.player_role == PlayerRole.INNOCENT
                    and getattr(p, "social_disgrace", False)
                ]
                all_innocents = [
                    p for p in players if p.player_role == PlayerRole.INNOCENT
                ]
                if all_innocents and len(innocent_disgraced) == len(
                    all_innocents
                ):
                    await self.notifier.notify_game_over(game_id=game_id)
                    await self.notifier.notify_game_removed(game_id=game_id)
                    self.write.delete_game(game_id)
        return GameFlowStatus.CONTINUE


class RevealChosenSecretEffect(BaseCardEffect):
    """Efecto: Eliges un jugador, que debe revelar un secreto DE SU ELECCIÓN."""

    async def execute(
        self,
        game_id: int,
        # card_played_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        if target_player_id is None:
            raise InvalidAction("Este efecto requiere un jugador objetivo.")

        # Por congruencia, solo el turn_service se encarga de hacer updates de CardLocation
        # await self._move_cards_to_played_area(game_id, card_ids, player_id)

        print(
            f"EJECUTANDO: Pedir al jugador {target_player_id} que elija un secreto para revelar"
        )
        await self._prompt_for_chosen_secret(
            game_id, target_player_id, player_id
        )

        return GameFlowStatus.PAUSED

    async def _prompt_for_chosen_secret(
        self, game_id: int, target_player_id: int, initiator_id: int
    ):
        """Notifica a un jugador que debe elegir un secreto."""
        self.write.set_game_action_state(
            game_id=game_id,
            state=GameActionState.AWAITING_REVEAL_FOR_CHOICE,
            prompted_player_id=target_player_id,
            initiator_id=initiator_id,
        )
        await self.notifier.notify_player_to_reveal_secret(
            game_id, target_player_id
        )


class HideSecretEffect(BaseCardEffect):
    """Efecto: Oculta un secreto que ya estaba revelado."""

    async def execute(
        self,
        game_id: int,
        # card_played_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        print(f"EJECUTANDO: Ocultar el secreto {target_secret_id}")
        if target_secret_id is None:
            raise InvalidAction(
                "Se requiere un secreto objetivo para este efecto."
            )

        # El efecto es autónomo. Pide el estado del juego que necesita.
        game = self.read.get_game(game_id)
        if not game:
            # Esto es un seguro, aunque el TurnService ya debería haberlo validado.
            raise ResourceNotFound(f"La partida {game_id} no existe.")

        # Ahora busca el secreto dentro del objeto Game que acaba de obtener.
        secret_to_hide: Optional[SecretCard] = self.read.get_secret(
            game_id=game_id, secret_id=target_secret_id
        )

        if not secret_to_hide:
            raise ResourceNotFound(
                f"El secreto {target_secret_id} no existe en esta partida."
            )

        if not secret_to_hide.is_revealed:
            raise ActionConflict(
                "La acción no es válida: el secreto ya está oculto."
            )

        # Si todas las validaciones pasan, ejecutamos.
        status = self.write.reveal_secret_card(
            secret_id=target_secret_id, game_id=game.id, is_revealed=False
        )
        if status != ResponseStatus.OK:
            raise InternalGameError("Error al ocultar el secreto.")

        await self.notifier.notify_secret_hidden(
            game_id=game.id,
            secret_id=target_secret_id,
            player_id=secret_to_hide.player_id,
        )

        # TODO:
        # remover desgracia social solo si ya tenia desgracia social en true
        # target_player_is_in_social_disgrace = all(
        #     s.is_revealed
        #     for s in self.read.get_player_secrets(
        #         player_id=secret_to_hide.player_id,
        #         game_id=game.id,
        #     )
        # )
        # if target_player_is_in_social_disgrace:
        players_in_game = self.read.get_players_in_game(game_id)
        target_player = next(
            (
                p
                for p in players_in_game
                if getattr(p, "player_id", None) == secret_to_hide.player_id
            ),
            None,
        )
        if target_player and getattr(target_player, "social_disgrace", False):
            self.write.set_player_social_disgrace(
                player_id=secret_to_hide.player_id,
                game_id=game_id,
                is_disgraced=False,
            )
            await self.notifier.notify_social_disgrace_removed(
                game_id=game_id, player_id=secret_to_hide.player_id
            )
        return GameFlowStatus.CONTINUE


class StealSecretEffect(BaseCardEffect):
    """Efecto: Roba el secreto revelado por el jugador objetivo."""

    async def execute(
        self,
        game_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        # ... validaciones ...

        # 1. Poner el juego en estado de "espera de robo"
        assert target_player_id
        self.write.set_game_action_state(
            game_id=game_id,
            state=GameActionState.AWAITING_REVEAL_FOR_STEAL,
            prompted_player_id=target_player_id,
            initiator_id=player_id,  # ¡Guardamos quién empezó todo!
        )

        # 2. Notificar al objetivo que elija un secreto (igual que antes)
        await self.notifier.notify_player_to_reveal_secret(
            game_id, target_player_id
        )

        return GameFlowStatus.PAUSED


class BeresfordUncancellableEffect(BaseCardEffect):
    """Efecto: Igual que RevealChosen, pero marcado como incancelable."""

    async def execute(
        self,
        game_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        print(
            "EJECUTANDO: Efecto de los Beresford (incancelable). Pidiendo revelar secreto."
        )
        # La lógica es idéntica a RevealChosenSecretEffect
        # La diferencia se maneja en TurnService, que no lo pone en la pila de reacción.
        assert target_player_id
        await self.notifier.notify_player_to_reveal_secret(
            game_id=game_id, player_id=target_player_id
        )
        return GameFlowStatus.PAUSED
