from random import shuffle
from typing import List, Dict

from app.game.exceptions import InternalGameError
from app.game.helpers.validators import GameValidator
from app.game.helpers.notificators import Notificator
from app.game.helpers.turn_utils import TurnUtils
from ...database.interfaces import IQueryManager, ICommandManager
from ...domain.models import Card, PlayerInGame
from ...api.schemas import StartGameResponse, GameLobbyInfo
from ...domain.enums import (
    GameStatus,
    ResponseStatus,
    CardLocation,
    CardType,
    PlayerRole,
)

INITIAL_DECK: Dict[CardType, int] = {
    CardType.HARLEY_QUIN: 4,
    CardType.ARIADNE_OLIVER: 3,
    CardType.MISS_MARPLE: 3,
    CardType.PARKER_PYNE: 3,
    CardType.TOMMY_BERESFORD: 2,
    CardType.LADY_EILEEN: 3,
    CardType.TUPPENCE_BERESFORD: 2,
    CardType.HERCULE_POIROT: 3,
    CardType.MR_SATTERTHWAITE: 2,
    CardType.NOT_SO_FAST: 10,
    CardType.BLACKMAILED: 1,
    CardType.SOCIAL_FAUX_PAS: 3,
    CardType.DELAY_MURDERER_ESCAPE: 3,
    CardType.POINT_YOUR_SUSPICIONS: 3,
    CardType.DEAD_CARD_FOLLY: 3,
    CardType.ANOTHER_VICTIM: 2,
    CardType.LOOK_INTO_THE_ASHES: 3,
    CardType.CARD_TRADE: 3,
    CardType.THERE_WAS_ONE_MORE: 2,
    CardType.EARLY_TRAIN: 2,
    CardType.CARDS_OFF_THE_TABLE: 1,
}
CARDS_PER_PLAYER = 6
SECRETS_PER_PLAYER = 3


class GameSetupService:
    """
    Servicio responsable de la configuración e inicio de una partida.
    """

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

    async def start_game(
        self, game_id: int, player_id: int
    ) -> StartGameResponse:
        """
        Valida e inicia una partida, repartiendo cartas y asignando turnos.
        """
        """
        Pasos:
        1. Valida que jugador/partida existan y el solicitante pueda iniciarla.
        2. NO asigna un orden de turno a cada jugador.
        3. Baraja las cartas a cada jugador y al deck de la partida.
        4. Baraja los secretos a cada jugador y les asigna su rol.
        5. Actualiza el estado de la partida y establece el primer turno.
        6. Envia un mensaje WebSocket anunciando el inicio de la partida.
        7. Devuelve una respuesta con el ID del primer jugador.
        """

        # --- Validaciones de negocio ---
        player = self.validator.validate_player_exists(player_id)
        game = self.validator.validate_game_exists(game_id)
        players_in_game = self.read.get_players_in_game(game_id)
        if not players_in_game:
            error_msg = "Error al crear partida: no se encuentran jugadores."
            raise InternalGameError(detail=error_msg)

        self.validator.validate_game_status(game, GameStatus.LOBBY)
        self.validator.validate_player_is_host(game, player.player_id)
        self.validator.validate_player_count(game, players_in_game)

        # --- Calcular y persistir el estado inicial de la partida ---
        players_sorted = self.turn_utils.sort_players_by_turn_order(
            players_in_game
        )
        first_player = players_sorted[0]
        players_id_sorted = [player.player_id for player in players_sorted]

        turn_update = self.write.set_current_turn(
            game_id, first_player.player_id
        )
        if turn_update != ResponseStatus.OK:
            error_msg = "Error al establecer el turno del jugador."
            raise InternalGameError(detail=error_msg)

        await self._set_cards_in_game(players_in_game, game_id)
        await self._set_secrets_in_game(players_in_game, game_id)

        game_info = GameLobbyInfo(
            id=game_id,
            name=game.name,
            min_players=game.min_players,
            max_players=game.max_players,
            player_count=len(game.players),
            host_id=game.host.player_id,
            game_status=game.status,
            password=game.password,
        )

        response = self.write.update_game_status(
            game_id, GameStatus.IN_PROGRESS
        )
        if response != ResponseStatus.OK:
            error_msg = "Error al actualizar el estado del juego."
            raise InternalGameError(detail=error_msg)

        game_info.game_status = GameStatus.IN_PROGRESS

        # --- Notificación WS ---
        await self.notifier.notify_game_started(
            game_id=game_id,
            first_player_id=first_player.player_id,
            players_in_turn_order=players_id_sorted,
            updated_game_in_lobby=game_info,
        )

        # --- Response ---
        return StartGameResponse(
            detail="La partida ha comenzado exitosamente.",
            player_id_first_turn=first_player.player_id,
        )

    # -------------------------------------------------------------------------
    # --- Funciones auxiliares ---
    # -------------------------------------------------------------------------

    async def _set_cards_in_game(
        self, players: List[PlayerInGame], game_id: int
    ) -> None:
        """
        Crea y distribuye TODAS las cartas de la partida: manos, draft y mazo.
        """
        # --------------------------------------------------------------------
        # PASO 1: CREAR EL MAZO COMPLETO Y BARAJARLO
        # --------------------------------------------------------------------
        deck_composition = INITIAL_DECK.copy()
        number_of_players = len(players)
        if number_of_players == 2:
            deck_composition.pop(CardType.POINT_YOUR_SUSPICIONS, None)
            deck_composition.pop(CardType.BLACKMAILED, None)

        # Quitamos los NSF que se asignan a mano
        deck_composition[CardType.NOT_SO_FAST] -= number_of_players

        # Creamos todas las cartas del mazo inicial
        game_cards: List[Card] = []
        for card_type, count in deck_composition.items():
            for _ in range(count):
                game_cards.append(
                    Card(
                        card_id=0,
                        game_id=game_id,
                        card_type=card_type,
                        location=CardLocation.DRAW_PILE,
                    )
                )
        shuffle(game_cards)

        # --------------------------------------------------------------------
        # PASO 2: DISTRIBUIR LAS CARTAS EN SUS ZONAS (¡EN MEMORIA!)
        # --------------------------------------------------------------------
        all_cards_to_persist: List[Card] = []

        # A. Manos de los jugadores
        for player in players:
            # Un NSF para cada uno
            all_cards_to_persist.append(
                Card(
                    card_id=0,
                    card_type=CardType.NOT_SO_FAST,
                    location=CardLocation.IN_HAND,
                    game_id=game_id,
                    player_id=player.player_id,
                )
            )
            # Resto de la mano
            for _ in range(CARDS_PER_PLAYER - 1):
                if game_cards:
                    card = game_cards.pop(0)  # Sacamos del principio
                    card.player_id = player.player_id
                    card.location = CardLocation.IN_HAND
                    all_cards_to_persist.append(card)

        # B. Cartas del Draft
        for _ in range(3):  # Asumimos 3 cartas en el draft
            if game_cards:
                card = game_cards.pop(0)
                card.location = CardLocation.DRAFT
                all_cards_to_persist.append(card)

        # C. El resto es el mazo de robo, con "Murderer Escapes!" al final
        game_cards.append(
            Card(
                card_id=0,
                game_id=game_id,
                card_type=CardType.MURDERER_ESCAPES,
                location=CardLocation.DRAW_PILE,
            )
        )

        # Asignamos la posición al mazo
        for i, card in enumerate(game_cards):
            card.position = len(game_cards) - 1 - i

        all_cards_to_persist.extend(game_cards)

        # --------------------------------------------------------------------
        # PASO 3: PERSISTIR TODO
        # --------------------------------------------------------------------
        response = self.write.create_deck_for_game(
            game_id, all_cards_to_persist
        )
        if response != ResponseStatus.OK:
            raise InternalGameError(
                "Error al crear y distribuir las cartas para la partida."
            )

    async def _set_secrets_in_game(
        self, players: List[PlayerInGame], game_id: int
    ) -> None:
        """
        Crea y distribuye los secretos necesarios para el inicio de la partida.
        Asigna el rol a cada jugador en base a sus secretos.
        """
        players_id_to_assign = [p.player_id for p in players].copy()
        shuffle(players_id_to_assign)
        # Manejo de jugador MURDERER
        murderer_id = players_id_to_assign.pop()
        response = self.write.set_player_role(
            player_id=murderer_id, game_id=game_id, role=PlayerRole.MURDERER
        )
        if response != ResponseStatus.OK:
            error_msg = "Error al establecer el rol Asesino"
            raise InternalGameError(detail=error_msg)
        response = self.write.create_secret_card(
            player_id=murderer_id,
            game_id=game_id,
            role=PlayerRole.MURDERER,
            is_revealed=False,
        )
        if response is None:
            error_msg = "Error al crear el secreto Asesino"
            raise InternalGameError(detail=error_msg)
        for _ in range(SECRETS_PER_PLAYER - 1):
            response = self.write.create_secret_card(
                player_id=murderer_id,
                game_id=game_id,
                role=PlayerRole.INNOCENT,
                is_revealed=False,
            )
            if response is None:
                error_msg = "Error al crear los secretos Inocente del Asesino"
                raise InternalGameError(detail=error_msg)
        # Manejo de jugador ACCOMPLICE
        if len(players) > 4:
            accomplice_id = players_id_to_assign.pop()
            response = self.write.set_player_role(
                player_id=accomplice_id,
                game_id=game_id,
                role=PlayerRole.ACCOMPLICE,
            )
            if response != ResponseStatus.OK:
                error_msg = "Error al establecer el rol Complice"
                raise InternalGameError(detail=error_msg)
            response = self.write.create_secret_card(
                player_id=accomplice_id,
                game_id=game_id,
                role=PlayerRole.ACCOMPLICE,
                is_revealed=False,
            )
            if response is None:
                error_msg = "Error al crear el secreto Complice"
                raise InternalGameError(detail=error_msg)
            for _ in range(SECRETS_PER_PLAYER - 1):
                response = self.write.create_secret_card(
                    player_id=accomplice_id,
                    game_id=game_id,
                    role=PlayerRole.INNOCENT,
                    is_revealed=False,
                )
            if response is None:
                error_msg = "Error al crear los secretos Inocente del Complice"
                raise InternalGameError(detail=error_msg)
        # Manejo de jugadores INNOCENT
        for innocent_id in players_id_to_assign:
            response = self.write.set_player_role(
                player_id=innocent_id,
                game_id=game_id,
                role=PlayerRole.INNOCENT,
            )
            if response != ResponseStatus.OK:
                error_msg = "Error al establecer los roles Inocente"
                raise InternalGameError(detail=error_msg)
            for _ in range(SECRETS_PER_PLAYER):
                response = self.write.create_secret_card(
                    player_id=innocent_id,
                    game_id=game_id,
                    role=PlayerRole.INNOCENT,
                    is_revealed=False,
                )
                if response is None:
                    error_msg = "Error al crear los secretos para Inocentes"
                    raise InternalGameError(detail=error_msg)
