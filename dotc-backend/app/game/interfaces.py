from abc import ABC, abstractmethod

from ..domain.enums import ResponseStatus
from ..api.schemas import (
    CreateGameRequest,
    CreateGameResponse,
    CreatePlayerResponse,
    DiscardCardRequest,
    DrawCardRequest,
    DrawCardResponse,
    FinishTurnResponse,
    GeneralActionResponse,
    JoinGameRequest,
    JoinGameResponse,
    ListGamesResponse,
    GameStateResponse,
    CreatePlayerRequest,
    PlayerActionRequest,
    StartGameResponse,
    PlayerHandResponse,
    PlayerSecretsResponse,
    ConsultDeckSizeResponse,
    LeaveGameRequest,
    LeaveGameResponse,
    ExchangeCardRequest,
)


class IGameManager(ABC):
    """
    Interfaz abstracta para GameManager. Define el contrato de la lógica de negocio.
    (La interfaz no cambia, solo su implementación mock)
    """

    @abstractmethod
    def create_player(
        self, request: CreatePlayerRequest
    ) -> CreatePlayerResponse:
        pass

    @abstractmethod
    async def create_game(
        self, request: CreateGameRequest
    ) -> CreateGameResponse:
        pass

    @abstractmethod
    def list_games(self) -> ListGamesResponse:
        pass

    @abstractmethod
    async def join_game(self, request: JoinGameRequest) -> JoinGameResponse:
        pass

    @abstractmethod
    async def start_game(
        self, request: PlayerActionRequest
    ) -> StartGameResponse:
        pass

    @abstractmethod
    async def leave_game(
        self, request: LeaveGameRequest
    ) -> LeaveGameResponse:
        pass

    @abstractmethod
    def get_game_state(
        self, game_id: int
    ) -> GameStateResponse | ResponseStatus:
        pass

    @abstractmethod
    def get_player_hand(
        self, request: PlayerActionRequest
    ) -> PlayerHandResponse:
        pass

    @abstractmethod
    def get_player_secrets(
        self, request: PlayerActionRequest
    ) -> PlayerSecretsResponse:
        pass

    @abstractmethod
    async def draw_card(self, request: DrawCardRequest) -> DrawCardResponse:
        pass

    @abstractmethod
    async def finish_turn(
        self, request: PlayerActionRequest
    ) -> FinishTurnResponse:
        pass

    @abstractmethod
    async def discard_card(
        self, request: DiscardCardRequest
    ) -> GeneralActionResponse:
        pass

    @abstractmethod
    def get_size_deck(self, game_id: int) -> ConsultDeckSizeResponse:
        pass

    @abstractmethod
    async def exchange_card(
        self, request: ExchangeCardRequest
    ) -> GeneralActionResponse:
        pass
