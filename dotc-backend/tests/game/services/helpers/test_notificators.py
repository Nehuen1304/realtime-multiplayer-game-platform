import pytest
from unittest.mock import AsyncMock, MagicMock, ANY

from app.game.helpers.notificators import Notificator

from app.websockets.interfaces import IConnectionManager
from app.websockets.protocol import details
from app.websockets.protocol.messages import WSMessage
from app.api.schemas import GameLobbyInfo
from app.domain.models import Card
from app.domain.enums import CardType, CardLocation, GameStatus, PlayerRole

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_ws_manager() -> MagicMock:
    """
    Crea un mock del IConnectionManager.
    Se usan AsyncMock para los métodos que son 'awaitable'.
    """
    manager = MagicMock(spec=IConnectionManager)
    manager.broadcast_to_lobby = AsyncMock()
    manager.broadcast_to_game = AsyncMock()
    manager.send_to_player = AsyncMock()
    return manager


@pytest.fixture
def notificator(mock_ws_manager: MagicMock) -> Notificator:
    """Crea una instancia del Notificator inyectando el mock del manager."""
    return Notificator(ws_manager=mock_ws_manager)


@pytest.fixture
def sample_game_lobby_info() -> GameLobbyInfo:
    """Crea un objeto DTO de GameLobbyInfo para usar en los tests."""
    return GameLobbyInfo(
        id=1,
        name="Partida de Prueba",
        player_count=2,
        max_players=4,
        game_status=GameStatus.LOBBY,
        host_id=10,
        min_players=4,
        password=None,
    )


@pytest.fixture
def sample_card() -> Card:
    """Crea un objeto de dominio Card para usar en los tests."""
    return Card(
        card_id=100,
        game_id=1,
        player_id=2,
        card_type=CardType.HERCULE_POIROT,
        location=CardLocation.IN_HAND,
    )


class TestNotificator:
    # --- Tests para notificaciones al Lobby ---

    async def test_notify_game_created(
        self,
        notificator: Notificator,
        mock_ws_manager: MagicMock,
        sample_game_lobby_info: GameLobbyInfo,
    ):
        """
        Prueba que se notifique correctamente la creación de una partida al lobby.
        """
        # Act
        await notificator.notify_game_created(game=sample_game_lobby_info)

        # Assert
        mock_ws_manager.broadcast_to_lobby.assert_awaited_once()
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_lobby.call_args.args[0]
        )

        assert isinstance(called_message.details, details.GameCreatedDetails)
        assert called_message.details.game == sample_game_lobby_info

    async def test_notify_game_removed(
        self, notificator: Notificator, mock_ws_manager: MagicMock
    ):
        """
        Prueba que se notifique correctamente la eliminación de una partida al lobby.
        """
        # Arrange
        game_id_to_remove = 5

        # Act
        await notificator.notify_game_removed(game_id=game_id_to_remove)

        # Assert
        mock_ws_manager.broadcast_to_lobby.assert_awaited_once()
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_lobby.call_args.args[0]
        )

        assert isinstance(called_message.details, details.GameRemovedDetails)
        assert called_message.details.game_id == game_id_to_remove

    # --- Tests para notificaciones InGame ---

    async def test_notify_new_turn(
        self, notificator: Notificator, mock_ws_manager: MagicMock
    ):
        # Act
        await notificator.notify_new_turn(game_id=1, turn_player_id=2)

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=1, message=ANY
        )
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.NewTurnDetails)
        assert called_message.details.turn_player_id == 2

    async def test_notify_card_played(
        self,
        notificator: Notificator,
        mock_ws_manager: MagicMock,
        sample_card: Card,
    ):
        # Act
        await notificator.notify_card_played(
            game_id=1, player_id=2, card_played=sample_card
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=1, message=ANY
        )
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.CardPlayedDetails)
        assert called_message.details.player_id == 2
        assert called_message.details.card_played == sample_card

    async def test_notify_card_discarded(
        self,
        notificator: Notificator,
        mock_ws_manager: MagicMock,
        sample_card: Card,
    ):
        # Act
        await notificator.notify_card_discarded(
            game_id=1, player_id=2, card_discarded=sample_card
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=1, message=ANY
        )
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.CardDiscardedDetails)
        assert called_message.details.player_id == 2
        assert called_message.details.card == sample_card

    async def test_notify_player_drew(
        self, notificator: Notificator, mock_ws_manager: MagicMock
    ):
        # Act
        await notificator.notify_player_drew(
            game_id=1, player_id=2, deck_size=25
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=1, message=ANY
        )
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(
            called_message.details, details.PlayerDrewFromDeckDetails
        )
        assert called_message.details.player_id == 2
        assert called_message.details.deck_size == 25

    async def test_notify_deck_updated(
        self, notificator: Notificator, mock_ws_manager: MagicMock
    ):
        # Act
        await notificator.notify_deck_updated(game_id=1, deck_size=24)

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=1, message=ANY
        )
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.DeckUpdatedDetails)
        assert called_message.details.deck_size == 24

    async def test_notify_draft_updated(
        self,
        notificator: Notificator,
        mock_ws_manager: MagicMock,
        sample_card: Card,
    ):
        # Act
        await notificator.notify_draft_updated(
            game_id=1, card_taken_id=99, new_card=sample_card
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=1, message=ANY
        )
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.DraftUpdatedDetails)
        assert called_message.details.card_taken_id == 99
        assert called_message.details.new_card == sample_card

    async def test_notify_cards_played(
        self, notificator: Notificator, mock_ws_manager: AsyncMock
    ):
        # Arrange
        game_id = 101
        player_id = 1
        cards = [
            Card(
                card_id=1,
                game_id=game_id,
                card_type=CardType.HERCULE_POIROT,
                location=CardLocation.PLAYED,
            ),
            Card(
                card_id=2,
                game_id=game_id,
                card_type=CardType.HARLEY_QUIN,
                location=CardLocation.PLAYED,
            ),
        ]

        # Act
        await notificator.notify_cards_played(
            game_id=game_id, player_id=player_id,
            cards_played=cards, is_cancellable=True
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once()
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.CardsPlayedDetails)
        assert called_message.details.player_id == player_id
        assert called_message.details.cards_played == cards
        assert called_message.details.is_cancellable is True

    async def test_notify_secret_revealed(
        self, notificator: Notificator, mock_ws_manager: AsyncMock
    ):
        # Arrange
        game_id = 101
        secret_id = 202
        player_role = PlayerRole.MURDERER
        player_id = 303

        # Act
        await notificator.notify_secret_revealed(
            game_id=game_id,
            secret_id=secret_id,
            player_role=player_role,
            player_id=player_id,
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once()
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.SecretRevealedDetails)
        assert called_message.details.game_id == game_id
        assert called_message.details.secret_id == secret_id
        assert called_message.details.role == player_role
        assert called_message.details.player_id == player_id

    async def test_notify_secret_hidden(
        self, notificator: Notificator, mock_ws_manager: AsyncMock
    ):
        # Arrange
        game_id = 101
        secret_id = 202
        player_id = 303

        # Act
        await notificator.notify_secret_hidden(
            game_id=game_id, secret_id=secret_id, player_id=player_id
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once()
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.SecretHiddenDetails)
        assert called_message.details.secret_id == secret_id

    async def test_notify_secret_stolen(
        self, notificator: Notificator, mock_ws_manager: AsyncMock
    ):
        # Arrange
        game_id = 101
        thief_id = 1
        victim_id = 2

        # Act
        await notificator.notify_secret_stolen(
            game_id=game_id, thief_id=thief_id, victim_id=victim_id
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once()
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.SecretStolenDetails)
        assert called_message.details.thief_id == thief_id
        assert called_message.details.victim_id == victim_id

    async def test_notify_set_created(
        self,
        notificator: Notificator,
        mock_ws_manager: MagicMock,
        sample_card: Card,
    ):
        # Arrange
        set_cards = [sample_card, sample_card]

        # Act
        await notificator.notify_set_created(
            game_id=1, player_id=2, set_cards=set_cards, is_cancellable=True
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=1, message=ANY
        )
        called_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(called_message.details, details.CardsPlayedDetails)
        assert called_message.details.player_id == 2
        assert called_message.details.cards_played == set_cards
        assert called_message.details.is_cancellable is True

    # --- Tests para notificaciones compuestas (Lobby y Partida) ---

    async def test_notify_player_joined(
        self,
        notificator: Notificator,
        mock_ws_manager: MagicMock,
        sample_game_lobby_info: GameLobbyInfo,
    ):
        """
        Prueba que se notifique a la partida y al lobby cuando un jugador se une.
        """
        # Arrange
        game_id = 1
        player_id = 2
        player_name = "TestPlayer"

        # Act
        await notificator.notify_player_joined(
            game_id=game_id,
            player_id=player_id,
            player_name=player_name,
            updated_game_in_lobby=sample_game_lobby_info,
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=game_id, message=ANY
        )
        game_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(game_message.details, details.PlayerJoinedDetails)
        assert game_message.details.player_id == player_id

        mock_ws_manager.broadcast_to_lobby.assert_awaited_once()
        lobby_message: WSMessage = (
            mock_ws_manager.broadcast_to_lobby.call_args.args[0]
        )
        assert isinstance(lobby_message.details, details.GameUpdatedDetails)
        assert lobby_message.details.game == sample_game_lobby_info

    async def test_notify_player_left(
        self,
        notificator: Notificator,
        mock_ws_manager: MagicMock,
        sample_game_lobby_info: GameLobbyInfo,
    ):
        """
        Prueba que se notifique a la partida y al lobby cuando un jugador se va.
        """
        # Arrange
        game_id = 1
        player_id = 2
        player_name = "LeavingPlayer"

        # Act
        await notificator.notify_player_left(
            game_id=game_id,
            player_id=player_id,
            player_name=player_name,
            updated_game_in_lobby=sample_game_lobby_info,
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=game_id, message=ANY
        )
        game_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(game_message.details, details.PlayerLeftDetails)
        assert game_message.details.player_id == player_id

        mock_ws_manager.broadcast_to_lobby.assert_awaited_once()
        lobby_message: WSMessage = (
            mock_ws_manager.broadcast_to_lobby.call_args.args[0]
        )
        assert isinstance(lobby_message.details, details.GameUpdatedDetails)
        assert lobby_message.details.game == sample_game_lobby_info

    async def test_notify_game_started(
        self,
        notificator: Notificator,
        mock_ws_manager: MagicMock,
        sample_game_lobby_info: GameLobbyInfo,
    ):
        """
        Prueba que se notifique a la partida y al lobby cuando una partida comienza.
        """
        # Arrange
        game_id = 1
        first_player_id = 3
        players_in_turn_order = [3, 4, 1, 2]
        sample_game_lobby_info.game_status = GameStatus.IN_PROGRESS

        # Act
        await notificator.notify_game_started(
            game_id=game_id,
            first_player_id=first_player_id,
            players_in_turn_order=players_in_turn_order,
            updated_game_in_lobby=sample_game_lobby_info,
        )

        # Assert
        mock_ws_manager.broadcast_to_game.assert_awaited_once_with(
            game_id=game_id, message=ANY
        )
        game_message: WSMessage = (
            mock_ws_manager.broadcast_to_game.call_args.kwargs["message"]
        )
        assert isinstance(game_message.details, details.GameStartedDetails)
        assert game_message.details.first_player_id == first_player_id
        assert (
            game_message.details.players_in_turn_order == players_in_turn_order
        )

        mock_ws_manager.broadcast_to_lobby.assert_awaited_once()
        lobby_message: WSMessage = (
            mock_ws_manager.broadcast_to_lobby.call_args.args[0]
        )
        assert isinstance(lobby_message.details, details.GameUpdatedDetails)
        assert lobby_message.details.game == sample_game_lobby_info

    # --- Test para notificación a un jugador específico ---

    async def test_notify_player_to_reveal_secret(
        self, notificator: Notificator, mock_ws_manager: AsyncMock
    ):
        """
        Prueba que la notificación para que un jugador revele un secreto
        se envía de forma privada.
        """
        # Arrange
        game_id = 101
        player_id = 1

        # Act
        await notificator.notify_player_to_reveal_secret(
            game_id=game_id, player_id=player_id
        )

        # Assert
        mock_ws_manager.send_to_player.assert_awaited_once()
        mock_ws_manager.broadcast_to_game.assert_not_awaited()

        call_args = mock_ws_manager.send_to_player.call_args
        sent_message: WSMessage = call_args.kwargs["message"]

        assert isinstance(
            sent_message.details, details.PlayerToRevealSecretDetails
        )
        assert call_args.kwargs["game_id"] == game_id
        assert call_args.kwargs["player_id"] == player_id

