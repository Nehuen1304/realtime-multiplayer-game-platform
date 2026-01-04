from app.game.effects.interfaces import ICardEffect
from ...database.interfaces import IQueryManager, ICommandManager
from ...api.schemas import (
    DiscardCardRequest,
    PlayerActionRequest,
    GeneralActionResponse,
    SubmitTradeChoiceRequest,
    FinishTurnResponse,
    DrawCardResponse,
    PlayCardRequest,
    RevealSecretRequest,
    DrawCardRequest,
    DrawSource,
    PlayCardActionType,
    VoteRequest,
    ExchangeCardRequest,
)

from ...domain.enums import (
    CardType,
    GameFlowStatus,
    ResponseStatus,
    GameActionState,
    PlayerRole,
)
from ...domain.models import Card, CardLocation, Game
from typing import Callable, List, Optional
from ..helpers.validators import GameValidator
from ..helpers.notificators import Notificator
from app.game.helpers.turn_utils import TurnUtils
from ..exceptions import (
    ActionConflict,
    InternalGameError,
    InvalidAction,
    ResourceNotFound,
    CardNotFound,
    ActionConflict,
    InvalidSagaState,
    ForbiddenAction,
    NotYourTurn,
)
from ..effects.set_effects import RevealChosenSecretEffect
from ..effect_executor import EffectExecutor


class TurnService:
    """
    Servicio que gestiona la lógica de las acciones realizadas durante el turno de un jugador.
    """

    def __init__(
        self,
        queries: IQueryManager,
        commands: ICommandManager,
        validator: GameValidator,
        notifier: Notificator,
        effect_executor: EffectExecutor,
        turn_utils: TurnUtils,
    ):
        self.read = queries
        self.write = commands
        self.validator = validator
        self.notifier = notifier
        self.effect_executor = effect_executor
        self.turn_utils = turn_utils

    async def draw_card(self, request: DrawCardRequest) -> DrawCardResponse:
        from app.game.turn_actions.actions import DrawCardAction

        return await DrawCardAction(
            self.read, self.write, self.validator, self.notifier
        ).execute(request)

    async def discard_card(
        self, request: DiscardCardRequest
    ) -> GeneralActionResponse:
        from app.game.turn_actions.actions import DiscardCardAction

        return await DiscardCardAction(
            self.read,
            self.write,
            self.validator,
            self.notifier,
            self.effect_executor,
        ).execute(request)

    async def finish_turn(
        self, request: PlayerActionRequest
    ) -> FinishTurnResponse:
        from app.game.turn_actions.actions import FinishTurnAction

        return await FinishTurnAction(
            self.read,
            self.write,
            self.validator,
            self.notifier,
            self.turn_utils,
        ).execute(request)

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

    async def play_card(
        self,
        request: PlayCardRequest,
    ) -> GeneralActionResponse:
        """
        Gestiona la jugada de una carta.
        Si la acción es cancelable, pone el juego en estado PENDING_NSF.
        Si no, la ejecuta inmediatamente.
        """
        game_id = request.game_id
        player_id = request.player_id
        action_type = request.action_type

        # --- PASO 1: VALIDACIONES DE ESTADO Y POSESIÓN ---
        game = self.validator.validate_game_exists(game_id)
        player = self.validator.validate_player_in_game(game, player_id)

        if request.target_player_id:
            self.validator.validate_player_in_game(game,
                                                    request.target_player_id)

        if request.target_secret_id:
            if not self.read.get_secret(request.target_secret_id, game_id):
                raise ResourceNotFound("El secreto objetivo no existe.")

        if request.target_card_id:
            if not self.read.get_card(request.target_card_id, game_id):
                raise ResourceNotFound("La carta objetivo no existe.")
        
        if request.target_set_id:
            if not self.read.get_set(request.target_set_id, game_id):
                raise ResourceNotFound("El set objetivo no existe.")
            
        if not request.card_ids:
            raise InvalidAction("Se requiere al menos una carta para jugar.")

        card_obj = self.read.get_card(request.card_ids[0], game_id)
        if not card_obj:
            raise CardNotFound(
                f"La carta {request.card_ids[0]} no existe en la partida."
            )

        is_devious_trigger = card_obj.card_type in {
            CardType.BLACKMAILED,
            CardType.SOCIAL_FAUX_PAS,
        }

        if not is_devious_trigger:
            # --- FLUJO NORMAL: NO ES UN VIP ---
            # Se aplican todas las validaciones de seguridad.
            print(
                f"Jugada normal detectada para carta tipo: {card_obj.card_type.value}. Aplicando validaciones completas."
            )
            self.validator.validate_is_players_turn(game, player_id)
            played_cards = self.validator.validate_player_has_cards(
                player, request.card_ids
            )
        else:
            # --- FLUJO ESPECIAL: ¡ES UN VIP! ---
            # Se asume que la llamada es interna y legítima. Nos saltamos las
            # validaciones de turno y posesión, confiando en el frontend/sistema.
            print(
                f"Trigger 'Devious' detectado para carta tipo: {card_obj.card_type.value}. Saltando validaciones de turno y posesión."
            )
            # La lista de cartas es simplemente la que ya leímos.
            played_cards = [card_obj]

        # --- PASO 2: PREPARACIÓN Y VALIDACIÓN DE LÓGICA DE JUGADA ---

        cards_for_effect_check: List[Card] = []

        if action_type == PlayCardActionType.INSTANT:
            raise InvalidAction(
                "Las cartas instantáneas no se juegan con este endpoint."
            )

        # Restricción por Desgracia Social usando el estado ya cargado del juego
        iterable_players = []
        if hasattr(game, "players") and isinstance(
            getattr(game, "players"), list
        ):
            iterable_players = game.players
        me = next(
            (
                p
                for p in iterable_players
                if getattr(p, "player_id", None) == player_id
            ),
            None,
        )
        if me and getattr(me, "social_disgrace", False):
            if action_type != PlayCardActionType.PLAY_EVENT:
                raise ForbiddenAction(
                    "Jugador en desgracia social: acción no permitida."
                )
            allowed_events = {
                CardType.NOT_SO_FAST,
                CardType.POINT_YOUR_SUSPICIONS,
                CardType.CARD_TRADE,
            }
            if (
                len(played_cards) != 1
                or played_cards[0].card_type not in allowed_events
            ):
                raise ForbiddenAction(
                    "Jugador en desgracia social: evento no permitido."
                )

        if action_type == PlayCardActionType.FORM_NEW_SET:
            if any(
                c.card_type == CardType.ARIADNE_OLIVER for c in played_cards
            ):
                raise InvalidAction(
                    "Ariadne Oliver no puede usarse para formar un set nuevo."
                )

            cards_for_effect_check = played_cards

        elif action_type == PlayCardActionType.ADD_TO_EXISTING_SET:
            if not request.target_set_id or len(played_cards) != 1:
                raise InvalidAction(
                    "Añadir a un set requiere 1 carta y un target_set_id."
                )

            target_set_id: int = request.target_set_id
            card_to_add: Card = played_cards[0]
            cards_in_set_orm = self.read.get_set(target_set_id, game_id)
            if not cards_in_set_orm:
                raise ResourceNotFound(f"El set {target_set_id} no existe.")

            cards_for_effect_check = cards_in_set_orm + [card_to_add]

            if card_to_add.card_type == CardType.ARIADNE_OLIVER:
                cards_for_effect_check = [card_to_add]

        elif action_type == PlayCardActionType.PLAY_EVENT:
            if len(played_cards) != 1:
                raise InvalidAction("Las cartas de evento se juegan de a una.")
            cards_for_effect_check = played_cards

        else:
            raise InvalidAction("Tipo de acción de juego desconocida.")

        # Verifico que sea un set valido antes de guardar en BD / notificar
        effect_class: Optional[Callable[..., ICardEffect]] = (
            self.effect_executor.classify_effect(cards_for_effect_check)
        )
        if not effect_class:
            raise InvalidAction(
                "La combinación de cartas jugadas no es válida o no tiene efecto."
            )

        # Determinar si es cancelable
        is_cancellable = True
        card_types_in_play = {c.card_type for c in cards_for_effect_check}
        if CardType.CARDS_OFF_THE_TABLE in card_types_in_play:
            is_cancellable = False
        if CardType.BLACKMAILED in card_types_in_play:
            is_cancellable = False
        if (
            CardType.TOMMY_BERESFORD in card_types_in_play
            and CardType.TUPPENCE_BERESFORD in card_types_in_play
        ):
            is_cancellable = False

        # --- PASO 3: EJECUCIÓN DEL EFECTO ---
        if is_cancellable:
            status = self.write.create_pending_action(
                game_id=request.game_id,
                player_id=request.player_id,
                request=request,
            )
            if status != ResponseStatus.OK:
                raise InternalGameError(
                    "No se pudo registrar la acción pendiente."
                )

            response = self.write.set_game_action_state(
                game_id=game_id,
                state=GameActionState.PENDING_NSF,
                prompted_player_id=None,
                initiator_id=player_id,
            )
            if response != ResponseStatus.OK:
                raise InternalGameError(
                    "No se pudo actualizar el estado de acción en la DB."
                )

            # Obtener el action_id de la pending_action recién creada
            pending_action = self.read.get_pending_action(game_id)
            action_id = pending_action.id if pending_action else None

            await self.notifier.notify_cards_played(
                game_id, player_id, cards_for_effect_check, is_cancellable=True,
                player_name=player.player_name, action_id=action_id
            )
            return GeneralActionResponse(
                detail="Jugada pendiente de confirmación por cartas NSF."
            )

        else:
            # Modularizacion de la escritura en DB y notificacion
            await self._execute_play_card_logic(request, cards_for_effect_check)

        return GeneralActionResponse(detail="La jugada fue procesada.")

    async def reveal_secret(self, request: RevealSecretRequest):
        game_id = request.game_id
        player_id = request.player_id
        secret_id = request.secret_id
        game = self.validator.validate_game_exists(game_id)
        player = self.validator.validate_player_in_game(game, player_id)

        current_action_state = game.action_state

        # --- Lógica de la Máquina de Estados ---

        if current_action_state == GameActionState.AWAITING_REVEAL_FOR_CHOICE:
            # --- CASO REVELAR POR ELECCIÓN (Tommy, Ariadne, etc.) ---

            # Validamos que el jugador que revela es a quien se le pidió.
            # if game.prompted_player_id != player_id:
            #    raise NotYourTurn("No es tu turno para revelar un secreto.")

            status = self.write.reveal_secret_card(
                secret_id=secret_id, game_id=game_id, is_revealed=True
            )
            if status != ResponseStatus.OK:
                raise InternalGameError("Error al revelar el secreto.")

            # ¡TU LÓGICA MEJORADA!
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

            # Aplicar desgracia social si corresponde por revelación
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

        # --- Verificaciones fin de partida ---
        murderer_id = player_id
        accomplice_id = self.read.get_accomplice_id(game_id)
        secret = self.read.get_secret(secret_id=secret_id, game_id=game_id)
        if not secret:
            raise ResourceNotFound(f"El secreto {secret_id} no fue encontrado.")

        if secret.role == PlayerRole.MURDERER:
            await self.notifier.notify_innocents_win(
                game_id=game.id,
                murderer_id=murderer_id,
                accomplice_id=accomplice_id,
            )
            status = self.write.delete_game(game_id=game_id)
            if status != ResponseStatus.OK:
                error_message = "La base de datos no pudo eliminar la partida."
                raise InternalGameError(detail=error_message)
            await self.notifier.notify_game_removed(game_id)
            return GeneralActionResponse(
                detail="La partida ha finalizado. Los inocentes han ganado."
            )
        # --- Después de revelar (solo si quedó revelado) aplicar lógica de desgracia ---
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

        # --- Limpieza Final ---
        # Si hay una pending_action activa (cadena NSF), restauramos el estado PENDING_NSF
        # Si no, limpiamos el estado completamente
        pending_action = self.read.get_pending_action(game_id)
        if pending_action:
            # Hay una acción pendiente, restauramos el estado PENDING_NSF
            self.write.set_game_action_state(
                game_id=game_id,
                state=GameActionState.PENDING_NSF,
                prompted_player_id=None,
                initiator_id=pending_action.player_id
            )
        else:
            # No hay pending_action, limpiamos completamente
            self.write.clear_game_action_state(game_id=game_id)

        return GeneralActionResponse(
            detail="Secreto revelado y acción completada."
        )

    async def submit_vote(self, request: VoteRequest) -> GeneralActionResponse:
        """Nuevo método central para registrar votos del evento 'Point Your Suspicions'."""
        game_id = request.game_id
        voter_id = request.player_id
        game = self.validator.validate_game_exists(game_id)
        if game.action_state != GameActionState.AWAITING_VOTES:
            raise ActionConflict("No es momento de votar.")
        saga = self.read.get_pending_saga(game_id)
        if not saga or saga.get("type") != "point_your_suspicions":
            raise InvalidSagaState("Saga de votación no encontrada.")
        if str(voter_id) in saga.get("votes", {}):
            raise ActionConflict("Ya has emitido tu voto.")
        saga["votes"][str(voter_id)] = request.voted_player_id
        self.write.update_pending_saga(game_id, saga)
        eligible_voters = saga.get("eligible_voters", [])
        all_votes_in = len(saga["votes"]) >= len(eligible_voters)
        print(
            f"[SUBMIT_VOTE] Voto de {voter_id} recibido. {len(saga['votes'])} de {len(eligible_voters)}. Todos? {all_votes_in}"
        )
        if all_votes_in and eligible_voters:
            print("[SUBMIT_VOTE] Todos los votos recibidos. Resolviendo...")
            from collections import Counter

            votes = saga.get("votes", {})
            initiator_id = saga.get("initiator_id") or saga.get(
                "tie_breaker_player_id"
            )
            valid_votes = [v for v in votes.values() if v is not None]
            most_voted_id = None
            is_tie = False
            if valid_votes:
                vote_counts = Counter(valid_votes)
                most_common = vote_counts.most_common()
                is_tie = (
                    len(most_common) > 1
                    and most_common[0][1] == most_common[1][1]
                )
                if not is_tie:
                    most_voted_id = most_common[0][0]
                else:
                    tie_breaker_vote = votes.get(str(initiator_id))
                    top_voted_ids = {
                        item[0]
                        for item in most_common
                        if item[1] == most_common[0][1]
                    }
                    most_voted_id = (
                        tie_breaker_vote
                        if tie_breaker_vote in top_voted_ids
                        else sorted(list(top_voted_ids))[0]
                    )
            await self.notifier.notify_vote_result(
                game_id, most_voted_id, is_tie
            )
            if most_voted_id:
                reveal_effect = RevealChosenSecretEffect(
                    self.read, self.write, self.notifier
                )
                await reveal_effect.execute(
                    game_id=game_id,
                    player_id=initiator_id,
                    card_ids=[],
                    target_player_id=most_voted_id,
                )
            else:
                self.write.clear_game_action_state(game_id)
            source_card_id = saga.get("source_card_id")
            if source_card_id:
                self.write.update_card_location(
                    source_card_id, game_id, CardLocation.DISCARD_PILE
                )
                card_obj = self.read.get_card(source_card_id, game_id)
                if card_obj:
                    await self.notifier.notify_cards_played(
                        game_id, initiator_id, [card_obj]
                    )
            self.write.update_pending_saga(game_id, None)
        return GeneralActionResponse(detail="Voto registrado con éxito.")

    async def submit_trade_choice(
        self, request: SubmitTradeChoiceRequest
    ) -> GeneralActionResponse:
        """
        Recibe la carta que un jugador elige para un intercambio (Dead Card Folly o Card Trade).
        Si es la última elección, resuelve la saga de intercambio.
        """
        game_id = request.game_id
        player_id = request.player_id
        card_id = request.card_id

        game = self.validator.validate_game_exists(game_id)
        if game.action_state != GameActionState.AWAITING_CARD_DONATIONS:
            raise ActionConflict(
                "No es momento de elegir una carta para intercambiar."
            )

        saga = self.read.get_pending_saga(game_id)
        if (
            not saga or saga.get("type") != "dead_card_folly"
        ):  # Ampliaremos esto para Card Trade
            raise InvalidSagaState(
                "Saga de intercambio no encontrada o corrupta."
            )

        if str(player_id) in saga["choices"]:
            raise ActionConflict(
                "Ya has elegido una carta para este intercambio."
            )

        # Validar que el jugador realmente tiene esa carta
        player_in_game = self.validator.validate_player_in_game(game, player_id)
        self.validator.validate_player_has_cards(player_in_game, [card_id])

        # AGREGACIÓN: Guardar la elección
        saga["choices"][str(player_id)] = card_id
        self.write.update_pending_saga(game_id, saga)

        # VERIFICACIÓN FINAL: ¿Eligieron todos?
        players_in_game = self.read.get_players_in_game(game_id)
        if len(saga["choices"]) == len(players_in_game):
            await self._resolve_dead_card_folly(game)

        return GeneralActionResponse(
            detail="Elección de carta registrada con éxito."
        )

    async def _resolve_dead_card_folly(self, game: Game):
        """
        Resuelve el intercambio masivo de 'Dead Card Folly'.

        Esta función es el supervisor del campo de minas. Su lógica es:
        1.  CALCULAR: Determina el nuevo dueño de cada carta basado en el orden y la dirección.
        2.  MOVER Y DETECTAR: Actualiza la ubicación de cada carta en la DB. Si una
            carta es "Devious", la añade a una lista para procesamiento posterior.
        3.  LIMPIAR Y NOTIFICAR: Resetea el estado de acción del juego y notifica
            a los clientes que sus manos han sido actualizadas.
        4.  DELEGAR: Itera sobre las Devious Cards detectadas y las "re-juega"
            a través del método principal `play_card`, usando una "llave maestra"
            para saltar las validaciones de posesión y turno.
        """
        saga = self.read.get_pending_saga(game.id)
        if not saga or saga.get("type") != "dead_card_folly":
            raise InvalidSagaState(
                "Saga de 'Dead Card Folly' no encontrada o corrupta durante la resolución."
            )

        choices = saga["choices"]  # ej: {"player_id_10": card_id_1000, ...}
        direction = saga["direction"]

        # --- PASO 1: CALCULAR MOVIMIENTOS ---
        # Obtenemos el orden de los jugadores una sola vez.
        ordered_players = self.turn_utils.sort_players_by_turn_order(
            game.players
        )
        num_players = len(ordered_players)
        player_map = {p.player_id: i for i, p in enumerate(ordered_players)}

        # Creamos un mapa detallado de cada movimiento para tener todo el contexto.
        card_movements = {}
        for player_id_str, card_id in choices.items():
            player_id = int(player_id_str)
            current_index = player_map.get(player_id)
            if current_index is None:
                continue  # Jugador no encontrado, seguridad.

            if direction == "left":
                new_owner_index = (
                    current_index - 1 + num_players
                ) % num_players
            else:  # 'right'
                new_owner_index = (current_index + 1) % num_players

            new_owner_id = ordered_players[new_owner_index].player_id
            card_movements[card_id] = {
                "old_owner_id": player_id,
                "new_owner_id": new_owner_id,
            }

        # --- PASO 2: MOVER Y DETECTAR MINAS ---
        devious_cards_to_reroute = []

        for card_id, move in card_movements.items():
            # Actualizamos la posesión de la carta en la base de datos.
            self.write.update_card_location(
                card_id=card_id,
                game_id=game.id,
                new_location=CardLocation.IN_HAND,
                owner_id=move["new_owner_id"],
            )

            # Ahora, verificamos si es una bomba. Necesitamos el objeto completo.
            card_obj = self.read.get_card(card_id, game.id)
            if card_obj and card_obj.card_type in {
                CardType.BLACKMAILED,
                CardType.SOCIAL_FAUX_PAS,
            }:
                print(
                    f"¡MINA DETECTADA! Carta '{card_obj.card_type.value}' ({card_id}) movida de {move['old_owner_id']} a {move['new_owner_id']}."
                )
                devious_cards_to_reroute.append(
                    {
                        "card": card_obj,
                        "old_owner_id": move["old_owner_id"],
                        "new_owner_id": move["new_owner_id"],
                    }
                )

        # --- PASO 3: LIMPIEZA Y NOTIFICACIÓN GENERAL ---
        # Es CRÍTICO limpiar el estado ANTES de disparar nuevos efectos para evitar conflictos.
        self.write.clear_game_action_state(game.id)

        # Notificamos a TODOS que sus manos han cambiado.
        # Los clientes ahora deben volver a pedir su mano actualizada.
        await self.notifier.notify_hands_updated(game.id)

        # --- PASO 4: DELEGAR LAS BOMBAS AL CUARTEL GENERAL (`play_card`) ---
        for devious in devious_cards_to_reroute:
            card = devious["card"]
            old_owner_id = devious["old_owner_id"]
            new_owner_id = devious["new_owner_id"]

            # Definimos quién es el "atacante" y quién es la "víctima"
            if card.card_type == CardType.BLACKMAILED:
                # El nuevo dueño "juega" la carta contra el viejo dueño.
                player_id_playing = new_owner_id
                target_id = old_owner_id
            else:  # Social Faux Pas
                # El viejo dueño "ataca" al nuevo dueño al entregarle la carta.
                player_id_playing = old_owner_id
                target_id = new_owner_id

            # Construimos una petición falsa para engañar a `play_card`.
            card = self.read.get_card(card_id=card.card_id, game_id=game.id)
            assert card is not None
            owner = card.player_id
            assert owner is not None
            reroute_request = PlayCardRequest(
                player_id=player_id_playing,
                game_id=game.id,
                action_type=PlayCardActionType.PLAY_EVENT,
                card_ids=[card.card_id],
                target_player_id=owner,
            )

            print(
                f"Re-rutando '{card.card_type.value}' al Cuartel General. Atacante: {player_id_playing}, Víctima: {target_id}"
            )

            # ¡Llamada al Cuartel General con la llave maestra!
            await self.play_card(request=reroute_request)

    async def exchange_card(
        self, request: ExchangeCardRequest
    ) -> GeneralActionResponse:
        """
        Maneja el intercambio de cartas cuando el jugador receptor selecciona
        una carta para intercambiar durante un Card Trade.
        """
        game_id = request.game_id
        player_id = request.player_id
        card_id = request.card_id

        # Validar que el juego existe y el jugador está en el juego
        game = self.validator.validate_game_exists(game_id)
        self.validator.validate_player_in_game(game, player_id)

        # Validar que estamos en el estado correcto
        if (
            game.action_state
            != GameActionState.AWAITING_SELECTION_FOR_CARD_TRADE
        ):
            raise InvalidAction("No hay un intercambio de cartas pendiente.")

        # Validar que el jugador que responde es el jugador solicitado
        if game.prompted_player_id != player_id:
            raise NotYourTurn(
                "No eres el jugador que debe seleccionar la carta."
            )

        # Obtener el iniciador del intercambio y la carta que ofreció
        initiator_id = game.action_initiator_id
        if not initiator_id:
            raise InternalGameError(
                "No se encontró el iniciador del intercambio."
            )

        # Obtener la carta que seleccionó la victima
        selected_card = self.read.get_card(card_id, game_id)
        if not selected_card:
            raise CardNotFound("La carta seleccionada no existe.")

        if selected_card.player_id != initiator_id:
            raise InvalidAction(
                "La carta no pertenece al jugador que inició el intercambio."
            )

        # Obtener la carta que ofreció el iniciador
        updated_saga = self.read.get_pending_saga(game.id)
        if not updated_saga or len(updated_saga) == 0:
            raise InternalGameError(
                "No se encontró el estado pendiente del intercambio."
            )

        offered_card_id = updated_saga.get("requested_card_id")
        if not offered_card_id:
            raise InternalGameError(
                "No se encontró la carta ofrecida en el intercambio."
            )
        offered_card = self.read.get_card(offered_card_id, game_id)
        if not offered_card:
            raise CardNotFound("La carta ofrecida no existe.")

        # Realizar el intercambio
        status_1 = self.write.update_card_location(
            card_id=selected_card.card_id,
            game_id=game_id,
            new_location=CardLocation.IN_HAND,
            owner_id=player_id,
            set_id=None,
        )

        status_2 = self.write.update_card_location(
            card_id=offered_card.card_id,
            game_id=game_id,
            new_location=CardLocation.IN_HAND,
            owner_id=initiator_id,
            set_id=None,
        )

        if status_1 != ResponseStatus.OK or status_2 != ResponseStatus.OK:
            raise InternalGameError(
                "Error al realizar el intercambio de cartas."
            )

        # --- PASO 1: DETECTAR MINAS DEVIOUS ---
        # Collect any Devious cards that were exchanged
        devious_cards_to_trigger = []

        # Check if selected_card (initiator → receiver) is Devious
        if selected_card.card_type in {
            CardType.BLACKMAILED,
            CardType.SOCIAL_FAUX_PAS,
        }:
            print(
                f"DEVIOUS DETECTED in Card Trade: {selected_card.card_type.value} "
                f"moved from initiator {initiator_id} to receiver {player_id}"
            )
            devious_cards_to_trigger.append(
                {
                    "card": selected_card,
                    "old_owner_id": initiator_id,
                    "new_owner_id": player_id,
                }
            )

        # Check if offered_card (receiver → initiator) is Devious
        if offered_card.card_type in {
            CardType.BLACKMAILED,
            CardType.SOCIAL_FAUX_PAS,
        }:
            print(
                f"DEVIOUS DETECTED in Card Trade: {offered_card.card_type.value} "
                f"moved from receiver {player_id} to initiator {initiator_id}"
            )
            devious_cards_to_trigger.append(
                {
                    "card": offered_card,
                    "old_owner_id": player_id,
                    "new_owner_id": initiator_id,
                }
            )

        # --- PASO 2: NOTIFICAR Y LIMPIAR (solo si no hay Devious) ---
        # Notificar a ambos jugadores con sus manos actualizadas
        initiator_hand = self.read.get_player_hand(
            game_id=game_id, player_id=initiator_id
        )
        receiver_hand = self.read.get_player_hand(
            game_id=game_id, player_id=player_id
        )

        if len(initiator_hand) == 0 or len(receiver_hand) == 0:
            raise InternalGameError(
                "No se pudieron obtener las manos de los jugadores."
            )

        await self.notifier.notify_hand_updated(
            game_id=game_id, player_id=initiator_id, hand=initiator_hand
        )
        await self.notifier.notify_hand_updated(
            game_id=game_id, player_id=player_id, hand=receiver_hand
        )

        # --- PASO 3: RUTA DIVERGENTE ---
        if devious_cards_to_trigger:
            # CRITICAL: Limpiar estado ANTES de disparar efectos Devious
            self.write.clear_game_action_state(game_id=game_id)

            # Disparar cada efecto Devious detectado
            for devious in devious_cards_to_trigger:
                card = devious["card"]
                old_owner = devious["old_owner_id"]
                new_owner = devious["new_owner_id"]

                # Determinar atacante y víctima según el tipo de carta
                if card.card_type == CardType.BLACKMAILED:
                    # El nuevo dueño "juega" contra el viejo dueño
                    attacker_id = new_owner
                    victim_id = old_owner
                else:  # SOCIAL_FAUX_PAS
                    # El viejo dueño "ataca" al nuevo dueño
                    attacker_id = old_owner
                    victim_id = new_owner

                # Re-rutear al play_card con "llave maestra"
                reroute_request = PlayCardRequest(
                    player_id=attacker_id,
                    game_id=game_id,
                    action_type=PlayCardActionType.PLAY_EVENT,
                    card_ids=[card.card_id],
                    target_player_id=victim_id,
                )

                print(
                    f"Re-routing Devious '{card.card_type.value}' through play_card. "
                    f"Attacker: {attacker_id}, Victim: {victim_id}"
                )

                # Delegar al cuartel general
                await self.play_card(request=reroute_request)

            # No retornar aquí - el último play_card habrá actualizado el estado
            return GeneralActionResponse(
                detail="Intercambio completado. Efecto Devious activado."
            )
        else:
            # No hay Devious, flujo normal
            self.write.clear_game_action_state(game_id=game_id)
            return GeneralActionResponse(
                detail="Intercambio de cartas completado exitosamente."
            )
        
    async def play_nsf(self, request: PlayCardRequest) -> GeneralActionResponse:
        """Procesa una jugada NSF o la decisión de no jugarlo ('pasar')."""
        game_id = request.game_id
        player_id = request.player_id

        # --- PASO 1: VALIDACIONES ---
        game = self.validator.validate_game_exists(game_id)
        if game.action_state != GameActionState.PENDING_NSF:
            raise ActionConflict("No hay una acción pendiente para cancelar.")

        pending_action = self.read.get_pending_action(game_id)
        if not pending_action:
            self.write.clear_game_action_state(game_id)
            raise InternalGameError("No se encontró la acción pendiente en BD")

        if pending_action.last_action_player_id == player_id:
            raise InvalidAction("No puedes usar 'NSF' en tu propia acción.")

        # --- PASO 2: PROCESAR LA RESPUESTA DEL JUGADOR (JUEGA NSF O PASA) ---
        if request.card_ids:
            # El jugador ha decidido jugar una carta NSF.
            if len(request.card_ids) != 1:
                raise InvalidAction("Solo puedes jugar una carta NSF a la vez.")
            player = self.validator.validate_player_in_game(game, player_id)
            played_nsf_card = self.validator.validate_player_has_cards(
                player, request.card_ids)[0]
            if played_nsf_card.card_type != CardType.NOT_SO_FAST:
                raise InvalidAction("Solo puedes jugar una carta 'NSF' ahora.")

            self.write.update_card_location(
                played_nsf_card.card_id, game_id, CardLocation.DISCARD_PILE
            )
            await self.notifier.notify_card_discarded(
                game_id, player_id, played_nsf_card
            )
            await self.notifier.notify_cards_played(
                game_id, player_id, [played_nsf_card], is_cancellable=True,
                player_name=player.player_name, action_id=pending_action.id
            )
            self.write.increment_nsf_responses(game_id, player_id, add_nsf=True)
        else:
            # El jugador ha decidido 'pasar' (no jugar NSF).
            self.write.increment_nsf_responses(game_id, player_id, add_nsf=False)

        # --- PASO 3: LÓGICA DE RESOLUCIÓN DE LA CADENA ---
        updated_action = self.read.get_pending_action(game_id)
        if not updated_action:
            raise InternalGameError("La acción pendiente no existe.")

        required_responses = len(game.players) - 1
        
        print(f"[TURN_SERVICE] Verificando si cadena NSF terminó: responses_count={updated_action.responses_count}, required={required_responses}, nsf_count={updated_action.nsf_count}")

        if updated_action.responses_count >= required_responses:
            # ¡Cadena terminada! Todos han respondido a la última acción
            is_cancelled = (updated_action.nsf_count % 2) != 0
            print(f"[TURN_SERVICE] Cadena NSF terminada. is_cancelled={is_cancelled}, action_type={updated_action.action_type}")

            if is_cancelled:
                print(f"[TURN_SERVICE] Acción CANCELADA, enviando notify_action_cancelled")
                # Se descartan las cartas canceladas que NO son Lady Eileen
                await self.notifier.notify_action_cancelled(
                    game_id=game_id,
                    player_id=updated_action.player_id,
                    cards=updated_action.cards,
                )
                # Releer las cartas de la BD para obtener su ubicación actual
                for card in updated_action.cards:
                    if card.card_type != CardType.LADY_EILEEN:
                        # Obtener el estado actual de la carta
                        current_card = self.read.get_card(card.card_id, game_id)
                        if not current_card:
                            continue  # Carta no existe, saltar
                        
                        # Solo descartar si NO está ya en DISCARD_PILE o PLAYED con set_id
                        if current_card.location == CardLocation.DISCARD_PILE:
                            continue  # Ya está descartada
                        if current_card.location == CardLocation.PLAYED and current_card.set_id:
                            # Si ya formó parte de un set, dejarla ahí
                            # (esto puede pasar si el efecto se ejecutó parcialmente)
                            continue
                        
                        status = self.write.update_card_location(
                            card.card_id,
                            game_id,
                            CardLocation.DISCARD_PILE,
                        )
                        if status != ResponseStatus.OK:
                            raise InternalGameError(
                                "Error al descartar carta cancelada."
                            )
                        # Notifico como "descarte" e individualmente,
                        # para que el front mantenga las cartas Lady Eileen
                        await self.notifier.notify_card_discarded(
                            game_id, updated_action.player_id, current_card
                        )
            else:
                print(f"[TURN_SERVICE] Acción RESUELTA, ejecutando lógica original")
                
                # Caso especial: Card Trade requiere selección de jugador objetivo ANTES de ejecutar efecto
                card_type = updated_action.cards[0].card_type if updated_action.cards else None
                if card_type == CardType.CARD_TRADE:
                    print(f"[TURN_SERVICE] Card Trade detectado, moviendo carta y esperando selección de jugador objetivo")
                    # 1. Mover carta a DISCARD_PILE
                    card_to_discard = updated_action.cards[0]
                    self.write.update_card_location(
                        card_to_discard.card_id, 
                        game_id, 
                        CardLocation.DISCARD_PILE
                    )
                    
                    # 2. Leer carta actualizada para notificación
                    updated_card = self.read.get_card(
                        card_id=card_to_discard.card_id, 
                        game_id=game_id
                    )
                    updated_cards = [updated_card] if updated_card else []
                    
                    # 3. Cambiar estado para esperar selección de jugador objetivo
                    self.write.set_game_action_state(
                        game_id=game_id,
                        state=GameActionState.AWAITING_SELECTION_FOR_CARD_TRADE,
                        prompted_player_id=updated_action.player_id,
                        initiator_id=updated_action.player_id,
                    )
                    
                    # 4. Notificar que acción se resolvió (cierra ventana NSF)
                    await self.notifier.notify_action_resolved(
                        game_id=game_id,
                        player_id=updated_action.player_id,
                        cards=updated_cards,
                        action_id=updated_action.id
                    )
                    
                    # 5. Notificar que debe seleccionar jugador objetivo
                    # TODO: Implementar notificación específica para selección de jugador objetivo
                    # Por ahora, el frontend debe detectar el estado AWAITING_SELECTION_FOR_CARD_TRADE
                else:
                    # Flujo normal: ejecutar efecto de la carta
                    play_request = PlayCardRequest(
                        player_id=updated_action.player_id,
                        game_id=updated_action.game_id,
                        action_type=updated_action.action_type,
                        card_ids=[card.card_id for card in updated_action.cards],
                        target_player_id=updated_action.target_player_id,
                        target_secret_id=updated_action.target_secret_id,
                        target_card_id=updated_action.target_card_id,
                        target_set_id=updated_action.target_set_id,
                    )
                    # Ejecutamos la lógica y obtenemos las cartas actualizadas
                    updated_cards = await self._execute_play_card_logic(
                        play_request, updated_action.cards
                    )
                    # Notificamos SIEMPRE que la acción se resolvió para que el frontend cierre ventana NSF
                    # Para cartas de evento que requieren selección, updated_cards puede estar vacío pero igual
                    # debemos notificar que la cadena NSF terminó exitosamente
                    await self.notifier.notify_action_resolved(
                        game_id=game_id,
                        player_id=updated_action.player_id,
                        cards=updated_cards if updated_cards else [],
                        action_id=updated_action.id
                    )

            # Limpiamos la pending_action
            self.write.clear_pending_action(game_id)
            
            # Solo limpiamos el estado del juego si NO quedó en un estado especial
            # (ej: AWAITING_SELECTION_FOR_CARD, AWAITING_REVEAL_FOR_CHOICE, etc.)
            game_after_effect = self.validator.validate_game_exists(game_id)
            if game_after_effect.action_state == GameActionState.PENDING_NSF:
                # Si aún está en PENDING_NSF, lo limpiamos
                self.write.clear_game_action_state(game_id)
            # Si está en otro estado (AWAITING_SELECTION_FOR_CARD, etc.), NO lo limpiamos

        return GeneralActionResponse(detail="Respuesta NSF registrada.")

    async def _move_cards_after_play(
        self,
        game_id: int,
        player_id: int,
        cards_played: List[Card], # Renombramos para mayor claridad
        request: PlayCardRequest,
    ):
        """Mueve las cartas después de que se resuelva una jugada."""
        if not cards_played:
            raise InternalGameError(
                "Error Interno: _move_cards_after_play fue llamado sin cartas.")
        
        # Query directo solo para player_name, evita cargar game completo con JOINs
        player_name = self.read.get_player_name(player_id)
        
        if not player_name:
            raise ResourceNotFound(f"Player {player_id} not found")

        cards_to_notify: List[Card] = []

        if request.action_type == PlayCardActionType.FORM_NEW_SET:
            new_set_id = self.write.create_set(
                game_id=game_id, card_ids=[c.card_id for c in cards_played]
            )
            if new_set_id == -1:
                raise InternalGameError(
                    "La base de datos falló al crear un nuevo set.")
            
            for card in cards_played:
                # Al mover la carta, también le asignamos su nuevo set_id
                self.write.update_card_location(card.card_id,
                                                game_id,
                                                CardLocation.PLAYED,
                                                player_id, set_id=new_set_id)
            
            # Para la notificación, volvemos a leer el set completo desde la BD.
            cards_to_notify = self.read.get_set(set_id=new_set_id,
                                                game_id=game_id)

        elif request.action_type == PlayCardActionType.ADD_TO_EXISTING_SET:
            if request.target_set_id is None:
                raise InternalGameError(
                    "target_set_id no puede ser None al agregar a un set.")
            
            card_to_add = cards_played[0]
            self.write.update_card_location(
                card_to_add.card_id, game_id, CardLocation.PLAYED,
                player_id, request.target_set_id
            )
            
            # Re-leemos solo la carta que se movió para la notificación
            updated_card = self.read.get_card(card_id=card_to_add.card_id,
                                                game_id=game_id)
            if updated_card:
                cards_to_notify = [updated_card]

        elif request.action_type == PlayCardActionType.PLAY_EVENT:
            card_to_discard = cards_played[0]
            self.write.update_card_location(card_to_discard.card_id, game_id,
                                            CardLocation.DISCARD_PILE)
            
            # Re-leemos la carta del descarte para la notificación
            updated_card = self.read.get_card(card_id=card_to_discard.card_id,
                                                game_id=game_id)
            if updated_card:
                cards_to_notify = [updated_card]

        if not cards_to_notify:
            # Esta excepción ahora es mucho más informativa
            raise InternalGameError(
                "La re-lectura de cartas desde la BD no devolvió resultados."
            )

        # Ya no enviamos CARDS_PLAYED aquí porque se envía ACTION_RESOLVED después
        # con las cartas actualizadas desde play_nsf()
        return cards_to_notify


    async def _execute_play_card_logic(
        self, request: PlayCardRequest, played_cards: List[Card]
    ):
        """Funcion para ejecutar la lógica completa de una jugada de carta.
        Retorna las cartas actualizadas después de moverlas."""
        # El parámetro 'played_cards' aquí son los objetos Card originales.
        flow_status: GameFlowStatus = GameFlowStatus.CONTINUE
    
        flow_status = await self.effect_executor.execute_effect(
            game_id=request.game_id,
            played_cards=played_cards, # Pasamos la lista original al ejecutor
            player_id=request.player_id,
            target_player_id=request.target_player_id,
            target_secret_id=request.target_secret_id,
            target_set_id=request.target_set_id,
            target_card_id=request.target_card_id,
            trade_direction=None,
        )
        updated_cards: List[Card] = []

        if request.action_type == PlayCardActionType.PLAY_EVENT:
            # Para cartas de evento, SIEMPRE movemos la carta a DISCARD_PILE
            # independientemente del flow_status (CONTINUE, PAUSED, o ENDED)
            # porque la carta se descarta incluso si requiere selección posterior del jugador
            updated_cards = await self._move_cards_after_play(
                request.game_id, request.player_id, played_cards, request
            )
            return updated_cards
        else:
            if flow_status == GameFlowStatus.PAUSED:
                print("Game flow PAUSED by effect. Awaiting player input.")
            if flow_status == GameFlowStatus.ENDED:
                print("Game flow ENDED by effect.")
        
            # Para FORM_NEW_SET y ADD_TO_EXISTING_SET, siempre movemos las cartas
            updated_cards = await self._move_cards_after_play(
                request.game_id, request.player_id, played_cards, request
            )
            return updated_cards
