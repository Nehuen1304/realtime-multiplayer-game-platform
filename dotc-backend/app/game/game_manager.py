# --------------------------------------------------------------------------
# --- Importaciones de la Lógica de Negocio (Los Servicios) ---
# --------------------------------------------------------------------------
from .interfaces import IGameManager
from .services.player_service import PlayerService
from .services.lobby_service import LobbyService
from .services.game_setup_service import GameSetupService
from .services.turn_service import TurnService
from .services.game_state_service import GameStateService

# --------------------------------------------------------------------------
# --- Importaciones de la Capa de API (Schemas de Entrada/Salida) ---
# --------------------------------------------------------------------------
from ..api.schemas import (
    CreatePlayerRequest,
    CreatePlayerResponse,
    CreateGameRequest,
    CreateGameResponse,
    DiscardCardRequest,
    DrawCardRequest,
    JoinGameRequest,
    JoinGameResponse,
    LeaveGameRequest,
    LeaveGameResponse,
    PlayCardRequest,
    ListGamesResponse,
    RevealSecretRequest,
    StartGameResponse,
    GameStateResponse,
    PlayerHandResponse,
    PlayerActionRequest,
    DrawCardResponse,
    FinishTurnResponse,
    GeneralActionResponse,
    PlayerSecretsResponse,
    ConsultDeckSizeResponse,
    SubmitTradeChoiceRequest,
    VoteRequest,
    ExchangeCardRequest,
)


class GameManager(IGameManager):
    """
    Patrón Facade (Fachada).
    Punto de entrada unificado para la lógica de negocio del juego.
    Delega todas las operaciones a servicios especializados. No contiene
    lógica de negocio por sí mismo.
    """

    def __init__(
        self,
        player_service: PlayerService,
        lobby_service: LobbyService,
        game_setup_service: GameSetupService,
        turn_service: TurnService,
        game_state_service: GameStateService,
    ):
        self.player_service = player_service
        self.lobby_service = lobby_service
        self.game_setup_service = game_setup_service
        self.turn_service = turn_service
        self.game_state_service = game_state_service

    # --------------------------------------------------------------------------
    # --- Delegación a PlayerService ---
    # --------------------------------------------------------------------------
    def create_player(
        self, request: CreatePlayerRequest
    ) -> CreatePlayerResponse:
        """Delega la creación de un jugador al servicio de jugadores."""
        return self.player_service.create_player(request)

    # --------------------------------------------------------------------------
    # --- Delegación a LobbyService ---
    # --------------------------------------------------------------------------
    async def create_game(
        self, request: CreateGameRequest
    ) -> CreateGameResponse:
        """Delega la creación de una partida al servicio de lobby.
        Notifica por WS en caso de lograr crear la partida."""
        return await self.lobby_service.create_game(request)

    def list_games(self) -> ListGamesResponse:
        """Delega el listado de partidas al servicio de lobby."""
        return self.lobby_service.list_games()

    async def join_game(self, request: JoinGameRequest) -> JoinGameResponse:
        """Delega la unión a una partida al servicio de lobby.
        Notifica por WS a los jugadores de la partida actualizada con el
        nuevo jugador"""
        return await self.lobby_service.join_game(request)

    async def leave_game(self, request: LeaveGameRequest) -> LeaveGameResponse:
        """Delega la salida de un jugador de una partida al servicio de lobby.
        Notifica por WS a los jugadores de la partida actualizada."""
        return await self.lobby_service.leave_game(request)

    # --------------------------------------------------------------------------
    # --- Delegación a GameSetupService ---
    # --------------------------------------------------------------------------
    async def start_game(
        self, request: PlayerActionRequest
    ) -> StartGameResponse:
        """Delega el inicio de una partida al servicio de configuración.
        Notifica a todos los jugadores del lobby de que la partida inicio."""
        return await self.game_setup_service.start_game(
            game_id=request.game_id, player_id=request.player_id
        )

    # --------------------------------------------------------------------------
    # --- Delegación a GameStateService ---
    # --------------------------------------------------------------------------
    def get_game_state(self, game_id: int) -> GameStateResponse:
        """Delega la obtención del estado público del juego al servicio de estado."""
        return self.game_state_service.get_game_state(game_id)

    def get_player_hand(
        self, request: PlayerActionRequest
    ) -> PlayerHandResponse:
        """Delega la obtención de la mano de un jugador al servicio de estado."""
        return self.game_state_service.get_player_hand(
            game_id=request.game_id, player_id=request.player_id
        )

    def get_player_secrets(
        self, request: PlayerActionRequest
    ) -> PlayerSecretsResponse:
        """Delega la obtención de los secretos de un jugador al servicio de estado."""
        return self.game_state_service.get_player_secrets(
            game_id=request.game_id, player_id=request.player_id
        )

    def get_size_deck(self, game_id: int) -> ConsultDeckSizeResponse:
        """Delega la obtención del tamaño del mazo de una partida al servicio de estado."""
        return self.game_state_service.get_size_deck(game_id)

    # --------------------------------------------------------------------------
    # --- Delegación a TurnService ---
    # --------------------------------------------------------------------------
    async def draw_card(self, request: DrawCardRequest) -> DrawCardResponse:
        """Delega la acción de robar carta al servicio de turnos.
        Notifica a los demas jugadores que el jugador ha robado una carta y de donde.
        Pero no cual."""
        return await self.turn_service.draw_card(request=request)

    async def discard_card(
        self, request: DiscardCardRequest
    ) -> GeneralActionResponse:
        """Delega la acción de descartar carta al servicio de turnos.
        Notifica a los jugadores de la mesa la accion realizada."""
        return await self.turn_service.discard_card(request=request)

    async def finish_turn(
        self, request: PlayerActionRequest
    ) -> FinishTurnResponse:
        """Delega la finalización del turno al servicio de turnos.
        Obviamente notifica a todos los del lobby que el turno se finalizo."""
        return await self.turn_service.finish_turn(request=request)

    async def play_card(
        self, request: PlayCardRequest
    ) -> GeneralActionResponse:
        """Delega la jugada de una carta al servicio de turno."""
        return await self.turn_service.play_card(request)

    async def reveal_secret(
        self, request: RevealSecretRequest
    ) -> GeneralActionResponse:
        """Delega la revelacion de un secreto al servicio de turno."""
        return await self.turn_service.reveal_secret(request)

    async def submit_vote(self, request: VoteRequest) -> GeneralActionResponse:
        """Delega la acción de votar al servicio de turnos (nuevo flujo)."""
        return await self.turn_service.submit_vote(request)

    async def submit_trade_choice(
        self, request: SubmitTradeChoiceRequest
    ) -> GeneralActionResponse:
        """Delega la acción de donar una carta a otro jugador."""
        return await self.turn_service.submit_trade_choice(request)

    async def exchange_card(
        self, request: "ExchangeCardRequest"
    ) -> GeneralActionResponse:
        """Delega el intercambio de cartas al servicio de turno."""
        return await self.turn_service.exchange_card(request)
      
    async def play_nsf(
        self, request: PlayCardRequest
    ) -> GeneralActionResponse:
        """Delega la jugada de una carta NSF de descarte al servicio de turno."""
        return await self.turn_service.play_nsf(request)
