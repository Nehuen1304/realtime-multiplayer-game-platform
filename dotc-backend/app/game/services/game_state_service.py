from ..helpers.validators import GameValidator
from ..helpers.notificators import Notificator
from ..helpers.turn_utils import TurnUtils
from ...database.interfaces import IQueryManager, ICommandManager
from ...api.schemas import (
    GameStateResponse,
    PlayerHandResponse,
    PlayerSecretsResponse,
    ConsultDeckSizeResponse
)
from ...domain.models import PlayerInGame
from typing import List

class GameStateService:
    """
    Servicio para consultar el estado del juego y prepararlo para la API,
    ocultando información sensible.
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

    def get_game_state(self, game_id: int) -> GameStateResponse:
        """
        Obtiene el estado público de la partida, ocultando información sensible.
        """
        # --- PASO 1 y 2: Validar y Obtener Juego ---
        game = self.validator.validate_game_exists(game_id)

        # --- PASO 3: Sanitizar el objeto Game ---
        # Creamos una copia profunda para no modificar el objeto original en memoria.
        public_game_state = game.model_copy(deep=True)

        # a) Ocultamos las manos y secretos de TODOS los jugadores.
        for player in public_game_state.players:
            player.hand = []
            player.secrets = []

        # b) Ocultamos el contenido del mazo. El front puede hacer len(deck).
        # Por seguridad, es mejor no mandar las cartas.
        # Podríamos mandar solo el count, pero el modelo Game espera una lista.
        # Una lista vacía es lo más seguro y cumple el modelo.
        # OJO: Si el front necesita el count, habría que cambiar el modelo Game
        # para que tenga un `deck_size` y no `deck: List[Card]`.
        # Por ahora, esto es lo correcto según el modelo actual.
        public_game_state.deck = []

        # --- PASO 4: Notificar por WS (Omitido) ---

        # --- PASO 5: Crear Response ---
        return GameStateResponse(game=public_game_state)

    def get_player_hand(
        self, game_id: int, player_id: int
    ) -> PlayerHandResponse:
        """
        Obtiene la mano de cartas de un jugador específico.
        """
        # --- PASO 1: Parsear Inputs (implícito) ---

        # --- PASO 2: Validar ---
        # Validamos que tanto la partida como el jugador existen y que el
        # jugador realmente pertenece a esa partida.
        game = self.validator.validate_game_exists(game_id)
        self.validator.validate_player_in_game(game, player_id)

        # --- PASO 3: Lectura en DB ---
        # Pedimos a la capa de queries que nos de la mano del jugador.
        player_hand = self.read.get_player_hand(game_id, player_id)

        # --- PASO 4 (Omitido, es una consulta) ---

        # --- PASO 5: Crear Response ---
        return PlayerHandResponse(cards=player_hand)

    def get_player_secrets(
        self, game_id: int, player_id: int
    ) -> PlayerSecretsResponse:
        """
        Obtiene las cartas secretas de un jugador específico.
        """
        # --- PASO 1: Parsear Inputs (implícito) ---

        # --- PASO 2: Validar ---
        # Se valida que el juego existe y que el jugador pertenece a él.
        # Esto es crucial para no filtrar secretos de otros jugadores.
        game = self.validator.validate_game_exists(game_id)
        self.validator.validate_player_in_game(game, player_id)

        # --- PASO 3: Lectura en DB ---
        # Se piden los secretos del jugador a la capa de queries.
        player_secrets = self.read.get_player_secrets(game_id, player_id)

        # --- PASO 4 (Omitido, es una consulta) ---

        # --- PASO 5: Crear Response ---
        return PlayerSecretsResponse(secrets=player_secrets)
    
    def get_size_deck(self, game_id: int) -> ConsultDeckSizeResponse:
        """
        Obtiene el tamaño del mazo de robo de la partida.
        """
        # --- PASO 1: Parsear Inputs (implícito) ---

        # --- PASO 2: Validar ---
        # Validamos que la partida existe.
        game = self.validator.validate_game_exists(game_id)

        # --- PASO 3: Lectura en DB ---
        # Pedimos a la capa de queries que nos de el tamaño del mazo.
        size_deck = self.read.get_size_deck(game_id)

        # --- PASO 4 (Omitido, es una consulta) ---

        # --- PASO 5: Crear Response ---
        return ConsultDeckSizeResponse(size_deck=size_deck)

    async def get_sorted_players(self, game_id: int) -> List[PlayerInGame]:
        """Devuelve la lista de jugadores ordenada por turn order."""
        # 1. Validar existencia del juego (consistencia con otros métodos)
        self.validator.validate_game_exists(game_id)
        
        # 2. Obtener jugadores sin ordenar
        players = self.read.get_players_in_game(game_id)

        # 3. Ordenar utilizando TurnUtils
        sorted_players = self.turn_utils.sort_players_by_turn_order(players)
        return sorted_players
