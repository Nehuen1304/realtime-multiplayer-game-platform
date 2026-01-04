from typing import Annotated, Optional, List, TYPE_CHECKING, Literal
from ...database.interfaces import IQueryManager, ICommandManager
from ...game.helpers.notificators import Notificator
from .interfaces import ICardEffect
from ...domain.models import Card
from ...domain.enums import (
    ResponseStatus,  # mantenido para comprobaciones internas si quedan
    CardLocation,
    GameActionState,
    CardType,
    GameFlowStatus,
)
from ...game.exceptions import (
    ResourceNotFound,
    InternalGameError,
    InvalidAction,
)
# from ...game.exceptions import InternalGameError, InvalidAction, PlayerNotFound

import random

if TYPE_CHECKING:
    from ..effect_executor import EffectExecutor


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


class BaseCardEffectWithExecutor(BaseCardEffect):
    """
    Una clase base extendida para efectos que necesitan una dependencia
    adicional: el propio EffectExecutor.
    """

    def __init__(
        self,
        queries: Annotated[IQueryManager, "Gestor de consultas"],
        commands: Annotated[ICommandManager, "Gestor de comandos"],
        notifier: Annotated[Notificator, "Gestor de notificaciones"],
        executor: Annotated["EffectExecutor", "Ejecutor de efectos"],
    ):
        # Llama al constructor de la clase padre
        super().__init__(queries, commands, notifier)
        # Añade la nueva dependencia
        self.executor = executor


class LookIntoTheAshesEffect(BaseCardEffect):
    """
    Implementa la lógica de la carta 'Look Into The Ashes'
    Efecto: Agarra las ultimas 1..5 cartas del mazo de descarte y le pide al jugador
    que lanzó la carta que elija una de ellas para robar.
    """

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
        # 1) Congelar el juego: usamos commands (antes en algunos archivos se llamaba write)
        self.commands.set_game_action_state(
            game_id=game_id,
            state=GameActionState.AWAITING_SELECTION_FOR_CARD,
            prompted_player_id=player_id,
            initiator_id=player_id,
        )

        # 2) Obtener pila de descarte desde queries (antes en algunos archivos se llamaba read)
        discard_pile: List[Card] = self.queries.get_discard_pile(
            game_id=game_id
        )

        # 3) Ordenar por position, tratando None como más antiguo (posición -1)
        discard_pile_sorted = sorted(
            discard_pile,
            key=lambda c: (c.position if c.position is not None else -1),
        )

        # 4) Tomar hasta 5 últimas cartas
        num_to_take = min(5, len(discard_pile_sorted))
        last_cards = (
            discard_pile_sorted[-num_to_take:] if num_to_take > 0 else []
        )

        # 5) Notificar al jugador que elija (usar notifier)
        # Target player: preferimos el parámetro explicitado; en tu test pasás target_player_id
        # Si no viene, por seguridad usamos player_id.
        chosen_player = (
            target_player_id if target_player_id is not None else player_id
        )
        await self.notifier.notify_player_to_choose_card(
            game_id=game_id, player_id=chosen_player, cards=last_cards
        )

        return GameFlowStatus.PAUSED


class AnotherVictimEffect(BaseCardEffectWithExecutor):
    """
    Implementa la lógica de la carta 'Another Victim'.
    Efecto: Roba un set previamente jugado por un jugador y
    vuelve a aplicar su efecto, con nuevos targets.
    """

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
        # Reuso lógica ya existente en tu versión anterior (sin cambios funcionales)
        if target_set_id is None:
            raise InvalidAction("No se proporcionó un ID de set objetivo.")
        stolen_set_cards = self.queries.get_set(
            set_id=target_set_id, game_id=game_id
        )
        if not stolen_set_cards:
            raise ResourceNotFound(
                "No se encontró un set con el ID especificado."
            )
        victim_id = stolen_set_cards[0].player_id
        if victim_id is None or any(
            c.player_id != victim_id for c in stolen_set_cards
        ):
            raise InternalGameError(
                "El set está corrupto o no tiene un propietario único."
            )

        # 2. Robar el set
        self.commands.steal_set(
            set_id=target_set_id, new_owner_id=player_id, game_id=game_id
        )

        # 3. Notificar
        await self.notifier.notify_set_stolen(
            game_id=game_id,
            thief_id=player_id,
            victim_id=victim_id,
            set_id=target_set_id,
            set_cards=stolen_set_cards,
        )

        # 4. Re-ejecutar efecto del set robado con el executor inyectado
        try:
            status = await self.executor.execute_effect(
                game_id=game_id,
                played_cards=stolen_set_cards,
                player_id=player_id,
                target_player_id=target_player_id,
                target_secret_id=target_secret_id,
                target_set_id=None,
                target_card_id=target_card_id,
            )
            return status
        except InvalidAction as e:
            # Si el efecto del set requiere target_secret_id pero no se proporcionó,
            # pausamos el juego para que el jugador seleccione el secreto
            if "secreto objetivo" in str(e).lower():
                print(f"[ANOTHER_VICTIM] Efecto del set requiere selección de secreto. Pausando juego.")
                # Cambiar estado del juego para esperar selección de secreto
                self.commands.set_game_action_state(
                    game_id=game_id,
                    state=GameActionState.AWAITING_SELECTION_FOR_SECRET,
                    prompted_player_id=player_id,
                    initiator_id=player_id,
                )
                # Guardar contexto en pending_saga para continuar después
                saga_data = {
                    "type": "another_victim_set_effect",
                    "set_id": target_set_id,
                    "set_cards": [card.card_id for card in stolen_set_cards],
                    "target_player_id": victim_id,
                }
                self.commands.update_pending_saga(game_id, saga_data)
                return GameFlowStatus.PAUSED
            else:
                # Otro tipo de error, re-lanzar
                raise


class CardsOffTheTableEffect(BaseCardEffect):
    """
    Implementa la lógica de la carta 'Cards Off The Table'.
    Efecto: Hace descartar todas las cartas de tipo 'Not So Fast' que
    tenga en su mano el jugador target.
    """

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
        if target_player_id is None:
            raise InvalidAction("No se proporcionó un ID de jugador objetivo.")

        # 1. Obtener las cartas 'Not So Fast' en la mano del jugador objetivo
        target_hand = self.queries.get_player_hand(
            player_id=target_player_id, game_id=game_id
        )
        not_so_fast_cards = [
            card
            for card in target_hand
            if card.card_type == CardType.NOT_SO_FAST
        ]

        # 2. Descarta las cartas encontradas
        for card in not_so_fast_cards:
            status = self.commands.update_card_location(
                card_id=card.card_id,
                game_id=game_id,
                new_location=CardLocation.DISCARD_PILE,
                owner_id=None,
                set_id=None,
            )
            if status != ResponseStatus.OK:
                raise InternalGameError(
                    "La DB no pudo descartar la cartas Not So Fast del target."
                )

        # 3. Notificar a todos los jugadores de la partida
        await self.notifier.notify_cards_NSF_discarded(
            game_id=game_id,
            source_player_id=player_id,
            target_player_id=target_player_id,
            discarded_cards=not_so_fast_cards,
        )

        return GameFlowStatus.CONTINUE


class AndThenThereWasOneMoreEffect(BaseCardEffect):
    """
    Implementa la lógica de la carta 'And Then There Was One More'.
    Efecto: Oculta un secreto previamente revelado y lo agrega a los
    secretos del target_player.
    """

    async def execute(
        self,
        game_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,  # Quien va a recibir el secreto
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        if target_secret_id is None:
            raise InvalidAction("No se proporcionó un ID de secreto objetivo.")
        if target_player_id is None:
            target_player_id = player_id

        # 1. Obtener el secreto a ocultar, su estado y propietario
        target_secret = self.queries.get_secret(
            secret_id=target_secret_id, game_id=game_id
        )
        if not target_secret:
            raise ResourceNotFound("No se encontró el secreto objetivo.")
        is_revealed_secret = target_secret.is_revealed
        if not is_revealed_secret:
            raise InvalidAction("El secreto objetivo no está revelado.")
        secret_owner_id = target_secret.player_id
        if secret_owner_id == target_player_id:
            player_target = player_id
        else:
            player_target = target_player_id

        # 2. Ocultar el secreto
        status = self.commands.reveal_secret_card(
            secret_id=target_secret_id,
            game_id=game_id,
            is_revealed=False,
        )
        if status != ResponseStatus.OK:
            raise InternalGameError("La DB no pudo ocultar el secreto objetivo")

        # 3. Cambia el propietario del secreto al jugador objetivo
        status = self.commands.change_secret_owner(
            secret_id=target_secret_id,
            game_id=game_id,
            new_owner_id=player_target,
        )
        if status != ResponseStatus.OK:
            raise InternalGameError(
                "La DB no pudo cambiar el propietario del secreto"
            )

        # 4. Notificar a todos los jugadores de la partida
        await self.notifier.notify_secret_hidden(
            game_id=game_id,
            secret_id=target_secret_id,
            player_id=secret_owner_id,  # Primero se oculta, despues se roba
        )
        await self.notifier.notify_secret_stolen(
            game_id=game_id,
            thief_id=player_target,
            victim_id=secret_owner_id,
        )

        return GameFlowStatus.CONTINUE


class DelayTheMurdererEscapeEffect(BaseCardEffect):
    """
    Implementa la lógica de 'Delay The Murderer Escape'.
    Efecto: Toma las últimas (top) 5 cartas del descarte, las baraja
    y las devuelve al mazo de robo.
    """

    async def execute(
        self,
        game_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,  # Quien va a recibir el secreto
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        # 1. Obtener pila de descarte
        discard_pile = self.queries.get_discard_pile(game_id=game_id)

        if not discard_pile:
            return (
                GameFlowStatus.CONTINUE
            )  # No hay nada que hacer, la acción es exitosa.

        # 2. Ordenar y seleccionar las "top 5" (mayor 'position')
        # Trata None como la posición más baja (-1)
        discard_pile_sorted = sorted(
            discard_pile,
            key=lambda c: (c.position if c.position is not None else -1),
        )
        num_to_move = min(5, len(discard_pile_sorted))
        cards_to_move = discard_pile_sorted[-num_to_move:]

        # 3. Barajar las cartas seleccionadas
        random.shuffle(cards_to_move)

        # 4. Mover cada carta al mazo de robo
        for card in cards_to_move:
            status = self.commands.update_card_location(
                card_id=card.card_id,
                game_id=game_id,
                new_location=CardLocation.DRAW_PILE,
                owner_id=None,
                set_id=None,  # Limpiamos el set_id por si acaso
            )
            if status != ResponseStatus.OK:
                raise InternalGameError(
                    f"La DB no pudo mover la carta {card.card_id} al mazo."
                )

        # 5. Notificar el cambio en el tamaño del mazo
        # Calculamos el nuevo tamaño esperado para la notificación
        new_deck_size = len(
            self.queries.get_deck(game_id=game_id)
        )  # Ya tiene las cartas nuevas
        await self.notifier.notify_deck_updated(
            game_id=game_id, deck_size=new_deck_size
        )

        return GameFlowStatus.CONTINUE


class EarlyTrainToPaddingtonEffect(BaseCardEffect):
    """
    Implementa la lógica de 'Early Train To Paddington'.
    Efecto: Mueve las "top 6" cartas del mazo de robo al descarte.
    """

    async def execute(
        self,
        game_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,  # Quien va a recibir el secreto
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        # 1. Obtener mazo de robo
        deck = self.queries.get_deck(game_id=game_id)

        # 2. Determinar cuántas cartas mover
        num_to_move = min(6, len(deck))
        if num_to_move == 0:
            return GameFlowStatus.CONTINUE  # No hay nada que hacer

        cards_to_move = deck[:num_to_move]

        # 3. Mover cada carta a la pila de descarte
        for card in cards_to_move:
            status = self.commands.update_card_location(
                card_id=card.card_id,
                game_id=game_id,
                new_location=CardLocation.DISCARD_PILE,
                owner_id=None,
                set_id=None,
            )
            if status != ResponseStatus.OK:
                raise InternalGameError(
                    f"La DB no pudo mover la carta {card.card_id} al descarte."
                )

        # 4. Notificar el cambio en el tamaño del mazo
        new_deck_size = len(deck) - num_to_move
        await self.notifier.notify_deck_updated(
            game_id=game_id, deck_size=new_deck_size
        )

        return GameFlowStatus.CONTINUE


class PointYourSuspicionsEffect(BaseCardEffect):
    """Especialista: realiza el censo y configura la saga de votación."""

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
        players_in_game = self.queries.get_players_in_game(game_id)
        eligible_voters = [p.player_id for p in players_in_game]
        print(
            f"!!! [CENSUS_EFFECT] Censo realizado: {len(eligible_voters)} votantes elegibles: {eligible_voters}"
        )
        votation_saga = {
            "type": "point_your_suspicions",
            "source_card_id": card_ids[0],
            "initiator_id": player_id,
            "votes": {},
            "eligible_voters": eligible_voters,
        }
        self.commands.update_pending_saga(game_id, votation_saga)
        self.commands.set_game_action_state(
            game_id=game_id,
            state=GameActionState.AWAITING_VOTES,
            prompted_player_id=None,
            initiator_id=player_id,
        )
        await self.notifier.notify_players_to_vote(game_id)
        return GameFlowStatus.PAUSED


class DeadCardFollyEffect(BaseCardEffect):
    """
    Efecto: Inicia un intercambio de cartas circular entre todos los jugadores.
    La dirección del intercambio la decide el jugador que juega la carta.
    """

    async def execute(
        self,
        game_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,  # El jugador que desempata
        # --- Parámetros opcionales ---
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = "right",
    ) -> GameFlowStatus:
        if trade_direction is None:
            raise InvalidAction(
                "Dead Card Folly requiere una dirección de intercambio (left o right)."
            )

        # 1. CONGELAR EL JUEGO: Nuevo estado de espera.
        self.commands.set_game_action_state(
            game_id=game_id,
            state=GameActionState.AWAITING_CARD_DONATIONS,
            prompted_player_id=None,
            initiator_id=player_id,
        )

        # 2. CREAR LA SAGA DE INTERCAMBIO: Guardamos el estado en la DB.
        trade_saga = {
            "type": "dead_card_folly",
            "direction": trade_direction,
            "choices": {},  # Aquí se almacenarán las cartas elegidas: {"player_id": "card_id"}
        }
        self.commands.update_pending_saga(game_id, trade_saga)

        # 3. NOTIFICAR A TODOS: ¡A ELEGIR QUÉ SACRIFICAR, CARAJO!
        await self.notifier.notify_request_to_donate_card_dcf(
            game_id=game_id, direction=trade_direction
        )

        return GameFlowStatus.PAUSED


class CardTradeEffect(BaseCardEffect):
    """
    Implementa la lógica de la carta 'Card Trade'.
    Efecto: Intercambia una carta de la mano del jugador que juega
    la carta con una carta de la mano del jugador objetivo.
    """

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
        # 1 - Verificaciones iniciales
        if not target_card_id:
            raise InvalidAction(
                "No se proporcionó el ID de la carta a intercambiar."
            )
        requested_card = self.queries.get_card(target_card_id, game_id)
        if not requested_card:
            raise ResourceNotFound("Carta objetivo no encontrada.")
        if target_player_id is None:
            target_player_id = requested_card.player_id
        if target_player_id is None:
            raise InvalidAction(
                "La carta seleccionada no pertenece a un jugador."
            )

        player_hand = self.queries.get_player_hand(
            player_id=player_id, game_id=game_id
        )
        if len(player_hand) < 2:
            raise InvalidAction(
                "El jugador no tiene suficientes cartas para intercambiar."
            )

        # 2 - Actualizar el estado de la partida para esperar selección
        status = self.commands.set_game_action_state(
            game_id=game_id,
            state=GameActionState.AWAITING_SELECTION_FOR_CARD_TRADE,
            prompted_player_id=target_player_id,
            initiator_id=player_id,
        )
        if status != ResponseStatus.OK:
            raise InternalGameError(
                "No se pudo actualizar el estado de la partida."
            )

        trade_saga = {
            "type": "card_trade",
            "initiator_player_id": player_id,
            "requested_card_id": target_card_id,
        }
        self.commands.update_pending_saga(game_id, trade_saga)

        # 3 - Notificar al jugador target para que seleccione una carta
        await self.notifier.notify_player_to_choose_card_for_trade(
            game_id=game_id,
            player_id=target_player_id,
            initiator_player_id=player_id,
        )

        return GameFlowStatus.PAUSED
