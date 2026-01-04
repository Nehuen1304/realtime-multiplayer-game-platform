from typing import List, Optional, TYPE_CHECKING, Callable
from app.api.schemas import (
    DrawCardRequest,
    DiscardCardRequest,
    DrawSource,
    FinishTurnResponse,
    PlayCardRequest,
    RevealSecretRequest,
    PlayerActionRequest,
    SubmitTradeChoiceRequest,
    GeneralActionResponse,
    PlayCardActionType,
    VoteRequest,
)
from app.domain.models import Card, Game, CardLocation
from app.domain.enums import (
    ResponseStatus,
    GameActionState,
    CardType,
    PlayerRole,
    GameFlowStatus,
)
from app.game.effects.interfaces import ICardEffect
from app.game.exceptions import (
    InvalidAction,
    InternalGameError,
    CardNotFound,
    ResourceNotFound,
    ForbiddenAction,
    ActionConflict,
    InvalidSagaState,
)
from app.game.effect_executor import EffectExecutor
from app.game.helpers.turn_utils import TurnUtils
from app.game.helpers.notificators import Notificator
from app.game.helpers.validators import GameValidator
from app.database.interfaces import IQueryManager, ICommandManager
from ..effects.set_effects import RevealChosenSecretEffect

if TYPE_CHECKING:
    from ..services.turn_service import TurnService
# Handlers -------------------------------------------------------------


class DrawCardAction:
    def __init__(
        self,
        queries: IQueryManager,
        commands: ICommandManager,
        validator: GameValidator,
        notifier: Notificator,
    ):
        self.read = queries
        self.write = commands
        self.validator = validator
        self.notifier = notifier

    async def execute(self, request: DrawCardRequest):
        game_id = request.game_id
        player_id = request.player_id
        game = self.validator.validate_game_exists(game_id)
        self.validator.validate_player_in_game(game, player_id)
        self.validator.validate_is_players_turn(game, player_id)

        hand_cards = self.read.get_player_hand(
            game_id=game_id, player_id=player_id
        )
        if len(hand_cards) >= 6:
            raise InvalidAction("No puedes alzar una carta más si ya tienes 6.")

        if request.source == request.source.DISCARD:
            if (
                game.action_state
                is not GameActionState.AWAITING_SELECTION_FOR_CARD
            ):
                raise InvalidAction(
                    "No estás en un estado que te permita robar del descarte."
                )
            if request.card_id is None:
                raise InvalidAction(
                    "Se requiere el ID de la carta para robar del descarte."
                )
            card_in_discard = next(
                (c for c in game.discard_pile if c.card_id == request.card_id),
                None,
            )
            if not card_in_discard:
                raise CardNotFound(
                    f"La carta {request.card_id} no está en la pila de descarte."
                )
            card_to_draw = card_in_discard
            self.write.clear_game_action_state(game_id=game_id)
        elif request.source == request.source.DECK:
            self.validator.validate_deck_has_cards(game)
            card_to_draw = game.deck[0]
        elif request.source == request.source.DRAFT:
            if request.card_id is None:
                raise InvalidAction(
                    "Se requiere el ID de la carta para robar del draft."
                )
            draft_card = next(
                (c for c in game.draft if c.card_id == request.card_id), None
            )
            if not draft_card:
                raise CardNotFound(
                    f"La carta {request.card_id} no está en el draft."
                )
            card_to_draw = draft_card
            await self._refill_draft_slot(game, card_to_draw)
        else:
            raise InvalidAction("Fuente de robo desconocida.")

        status = self.write.update_card_location(
            card_id=card_to_draw.card_id,
            game_id=game_id,
            new_location=CardLocation.IN_HAND,
            owner_id=player_id,
        )
        if status != ResponseStatus.OK:
            raise InternalGameError(
                "La DB no pudo actualizar la ubicación de la carta robada."
            )
        await self.notifier.notify_player_drew(
            game_id, player_id, len(game.deck) - 1
        )
        from app.api.schemas import DrawCardResponse

        # --- Verificaciones fin de partida ---
        murderer_id = self.read.get_murderer_id(game_id)
        accomplice_id = self.read.get_accomplice_id(game_id)
        if not murderer_id:
            raise InternalGameError("No se pudo obtener el ID del asesino.")

        if (
            request.source == DrawSource.DECK
            and not game.draft
            and len(game.deck) == 1
        ) or (
            request.source == DrawSource.DRAFT
            and not game.deck
            and len(game.draft) == 1
        ):
            await self.notifier.notify_murderer_wins(
                game_id=game.id,
                murderer_id=murderer_id,
                accomplice_id=accomplice_id,
            )
            status = self.write.delete_game(game_id=game_id)
            if status != ResponseStatus.OK:
                error_message = "La base de datos no pudo eliminar la partida."
                raise InternalGameError(detail=error_message)
            await self.notifier.notify_game_removed(game_id)

        return DrawCardResponse(drawn_card=card_to_draw)

    async def _refill_draft_slot(self, game: Game, card_taken: Card):
        if not game.deck:
            await self.notifier.notify_draft_updated(
                game.id, card_taken.card_id, None
            )
            return
        new_card = game.deck[0]
        self.write.update_card_location(
            card_id=new_card.card_id,
            game_id=game.id,
            new_location=CardLocation.DRAFT,
        )
        new_card.location = CardLocation.DRAFT
        await self.notifier.notify_draft_updated(
            game.id, card_taken.card_id, new_card
        )

class DiscardCardAction:
    def __init__(
        self,
        queries: IQueryManager,
        commands: ICommandManager,
        validator: GameValidator,
        notifier: Notificator,
        effect_executor: EffectExecutor,
    ):
        self.read = queries
        self.write = commands
        self.validator = validator
        self.notifier = notifier
        self.effect_executor = effect_executor

    async def execute(self, request: DiscardCardRequest):
        game_id = request.game_id
        player_id = request.player_id
        card_id = request.card_id
        game = self.validator.validate_game_exists(game_id)
        player = self.validator.validate_player_in_game(game, player_id)
        self.validator.validate_is_players_turn(game, player_id)
        self.validator.validate_player_has_cards(player, [card_id])
        status = self.write.update_card_location(
            card_id=card_id,
            game_id=game_id,
            new_location=CardLocation.DISCARD_PILE,
            owner_id=None,
        )
        if status != ResponseStatus.OK:
            raise InternalGameError(
                "La DB no pudo actualizar la ubicación de la carta."
            )
        card_to_discard = next(
            (c for c in player.hand if c.card_id == card_id), None
        )
        if not card_to_discard:
            raise InternalGameError(
                "La carta estaba en la mano para validar pero no para notificar."
            )
        await self.notifier.notify_card_discarded(
            game_id, player_id, card_to_discard
        )
        if card_to_discard.card_type == CardType.EARLY_TRAIN:
            await self.effect_executor.execute_effect(
                game_id=game_id,
                played_cards=[card_to_discard],
                player_id=player_id,
            )
        return GeneralActionResponse(
            detail=f"Carta {card_to_discard.card_id} descartada con éxito."
        )


class FinishTurnAction:
    def __init__(
        self,
        queries: IQueryManager,
        commands: ICommandManager,
        validator: GameValidator,
        notifier: Notificator,
        turn_utils: TurnUtils,
    ):
        self.read = queries
        self.write = commands
        self.validator = validator
        self.notifier = notifier
        self.turn_utils = turn_utils

    async def execute(self, request: PlayerActionRequest):
        game_id = request.game_id
        player_id = request.player_id
        game = self.validator.validate_game_exists(game_id)
        self.validator.validate_player_in_game(game, player_id)
        self.validator.validate_is_players_turn(game, player_id)
        hand_cards = self.read.get_player_hand(
            game_id=game_id, player_id=player_id
        )
        if len(hand_cards) < 6:
            raise InvalidAction(
                "No puedes terminar tu turno con menos de 6 cartas en la mano."
            )
        next_player_id = self._assign_next_turn(game_id)
        await self.notifier.notify_new_turn(game_id, next_player_id)
        return FinishTurnResponse(next_player_id=next_player_id)

    def _assign_next_turn(self, game_id: int) -> int:
        players = self.read.get_players_in_game(game_id)
        if not players:
            raise InternalGameError(
                "No se encontraron jugadores en la partida."
            )
        ordered_players = self.turn_utils.sort_players_by_turn_order(players)
        actual_player_id = self.read.get_current_turn(game_id)
        if actual_player_id is None:
            raise InternalGameError(
                "No se pudo obtener el jugador con turno actual."
            )
        try:
            current_player_index = next(
                i
                for i, p in enumerate(ordered_players)
                if p.player_id == actual_player_id
            )
        except ValueError:
            raise InternalGameError(
                "El jugador del turno actual no está en la lista de jugadores."
            )
        next_player_index = (current_player_index + 1) % len(ordered_players)
        next_player_id = ordered_players[next_player_index].player_id
        response = self.write.set_current_turn(game_id, next_player_id)
        if response != ResponseStatus.OK:
            raise InternalGameError(
                "No se pudo actualizar el turno en la base de datos."
            )
        return next_player_id

class RevealSecretAction:
    def __init__(
        self,
        queries: IQueryManager,
        commands: ICommandManager,
        validator: GameValidator,
        notifier: Notificator,
    ):
        self.read = queries
        self.write = commands
        self.validator = validator
        self.notifier = notifier

    async def execute(
        self, request: RevealSecretRequest
    ) -> GeneralActionResponse:
        game_id = request.game_id
        player_id = request.player_id
        secret_id = request.secret_id
        game = self.validator.validate_game_exists(game_id)
        current_action_state = game.action_state
        if current_action_state == GameActionState.AWAITING_REVEAL_FOR_CHOICE:
            status = self.write.reveal_secret_card(
                secret_id=secret_id, game_id=game_id, is_revealed=True
            )
            if status != ResponseStatus.OK:
                raise InternalGameError("Error al revelar el secreto.")
            player_secrets = self.read.get_player_secrets(
                game_id=game_id, player_id=player_id
            )
            try:
                chosen_secret_role = next(
                    c.role for c in player_secrets if c.secret_id == secret_id
                )
            except StopIteration:
                raise ResourceNotFound(
                    f"El secreto {secret_id} no pertenece al jugador {player_id}."
                )
            await self.notifier.notify_secret_revealed(
                game_id=game_id,
                secret_id=secret_id,
                player_role=chosen_secret_role,
                player_id=player_id,
            )
        elif current_action_state == GameActionState.AWAITING_REVEAL_FOR_STEAL:
            status = self.write.reveal_secret_card(
                secret_id=secret_id, game_id=game_id, is_revealed=True
            )
            if status != ResponseStatus.OK:
                raise InternalGameError("Error al revelar el secreto.")
            player_secrets = self.read.get_player_secrets(
                game_id=game_id, player_id=player_id
            )
            try:
                chosen_secret_role = next(
                    c.role for c in player_secrets if c.secret_id == secret_id
                )
            except StopIteration:
                raise ResourceNotFound(
                    f"El secreto {secret_id} no pertenece al jugador {player_id}."
                )
            await self.notifier.notify_secret_revealed(
                game_id=game_id,
                secret_id=secret_id,
                player_role=chosen_secret_role,
                player_id=player_id,
            )
            all_secrets = self.read.get_player_secrets(
                game_id=game_id, player_id=player_id
            )
            all_revealed = all(
                s.is_revealed or s.secret_id == secret_id for s in all_secrets
            )
            if chosen_secret_role == PlayerRole.ACCOMPLICE or all_revealed:
                self.write.set_player_social_disgrace(
                    player_id=player_id, game_id=game_id, is_disgraced=True
                )
                await self.notifier.notify_social_disgrace_applied(
                    game_id=game_id, player_id=player_id
                )
            initiator_id = game.action_initiator_id
            assert initiator_id, (
                "El iniciador de la acción no puede ser nulo en estado de robo"
            )
            self.write.change_secret_owner(
                secret_id=secret_id, new_owner_id=initiator_id, game_id=game_id
            )
            status = self.write.reveal_secret_card(
                secret_id=secret_id, game_id=game_id, is_revealed=False
            )
            if status != ResponseStatus.OK:
                raise InternalGameError(
                    "Error al ocultar el secreto después del robo."
                )
            await self.notifier.notify_secret_stolen(
                game_id, thief_id=initiator_id, victim_id=player_id
            )
        final_secret_state = self.read.get_secret(
            secret_id=secret_id, game_id=game_id
        )
        if final_secret_state and final_secret_state.is_revealed:
            player_role = self.read.get_player_role(
                player_id=player_id, game_id=game_id
            )
            if player_role != PlayerRole.MURDERER:
                all_secrets = self.read.get_player_secrets(
                    game_id=game_id, player_id=player_id
                )
                all_revealed = all(s.is_revealed for s in all_secrets)
                accomplice_revealed = any(
                    s.secret_id == secret_id and s.role == PlayerRole.ACCOMPLICE
                    for s in all_secrets
                )
                if all_revealed or accomplice_revealed:
                    self.write.set_player_social_disgrace(
                        player_id=player_id, game_id=game_id, is_disgraced=True
                    )
                    await self.notifier.notify_social_disgrace_applied(
                        game_id=game_id, player_id=player_id
                    )
                    players = self.read.get_players_in_game(game_id)
                    if not isinstance(players, list):
                        players = []
                    innocents = [
                        p
                        for p in players
                        if getattr(p, "player_role", None)
                        == PlayerRole.INNOCENT
                    ]
                    if innocents and all(
                        getattr(p, "social_disgrace", False) for p in innocents
                    ):
                        await self.notifier.notify_game_over(game_id=game_id)
                        await self.notifier.notify_game_removed(game_id=game_id)
                        self.write.delete_game(game_id)
        self.write.clear_game_action_state(game_id=game_id)
        return GeneralActionResponse(
            detail="Secreto revelado y acción completada."
        )
