import pytest
from unittest.mock import Mock
from datetime import date

# Importa la clase que vamos a testear
from app.game.helpers.validators import GameValidator

# Importa los modelos y enums necesarios para crear datos de prueba
from app.domain.models import Game, PlayerInfo, PlayerInGame, Card
from app.domain.enums import GameStatus, Avatar, CardType, CardLocation

# Importa las excepciones específicas que el validador debe lanzar
from app.game.exceptions import (
    GameNotFound,
    PlayerNotFound,
    ActionConflict,
    ForbiddenAction,
    NotYourTurn,
    InvalidAction,
    PlayerNotInGame,
    CardNotFound,
    NotYourCard,
)

# --- Fixtures Específicas para este Módulo de Tests ---
# (mock_queries se inyecta automáticamente desde el conftest.py principal)


@pytest.fixture
def validator(mock_queries: Mock) -> GameValidator:
    """Crea una instancia del GameValidator inyectando el mock de queries de conftest."""
    return GameValidator(queries=mock_queries)


@pytest.fixture
def sample_player_info() -> PlayerInfo:
    """Crea un objeto PlayerInfo de ejemplo."""
    return PlayerInfo(
        player_id=1,
        player_name="HostPlayer",
        player_birth_date=date(1990, 5, 15),
        player_avatar=Avatar.DEFAULT,
    )


@pytest.fixture
def sample_game(sample_player_info: PlayerInfo) -> Game:
    """Crea un objeto Game de ejemplo con datos realistas."""
    player_in_game = PlayerInGame(
        **sample_player_info.model_dump(),
        game_id=1,
        hand=[
            Card(
                card_id=101,
                game_id=1,
                player_id=1,
                card_type=CardType.NOT_SO_FAST,
                location=CardLocation.IN_HAND,
            )
        ],
    )

    return Game(
        id=1,
        name="Test Game",
        min_players=4,
        max_players=6,
        host=sample_player_info,
        status=GameStatus.LOBBY,
        password=None,
        players=[player_in_game],
        deck=[
            Card(
                card_id=201,
                game_id=1,
                player_id=None,
                card_type=CardType.HARLEY_QUIN,
                location=CardLocation.DRAW_PILE,
            )
        ],
        discard_pile=[],
        draft=[],
        current_turn_player_id=1,
    )


# --- Tests para cada método del GameValidator ---


class TestGameValidator:
    # --- Happy Path ---
    def test_validate_game_exists_success(
        self, validator: GameValidator, mock_queries: Mock, sample_game: Game
    ):
        """Prueba que devuelve el juego si existe (Happy Path)."""
        # Arrange
        mock_queries.get_game.return_value = sample_game

        # Act
        result = validator.validate_game_exists(game_id=1)

        # Assert
        assert result == sample_game
        mock_queries.get_game.assert_called_once_with(1)

    # --- Sad Path ---
    def test_validate_game_exists_failure(
        self, validator: GameValidator, mock_queries: Mock
    ):
        """Prueba que lanza GameNotFound si el juego no existe (Sad Path)."""
        # Arrange
        mock_queries.get_game.return_value = None

        # Act & Assert
        with pytest.raises(GameNotFound, match="La partida 1 no existe."):
            validator.validate_game_exists(game_id=1)

    # --- Happy Path ---
    def test_validate_player_exists_success(
        self,
        validator: GameValidator,
        mock_queries: Mock,
        sample_player_info: PlayerInfo,
    ):
        """Prueba que devuelve el jugador si existe (Happy Path)."""
        # Arrange
        mock_queries.get_player.return_value = sample_player_info

        # Act
        result = validator.validate_player_exists(player_id=1)

        # Assert
        assert result == sample_player_info
        mock_queries.get_player.assert_called_once_with(1)

    # --- Sad Path ---
    def test_validate_player_exists_failure(
        self, validator: GameValidator, mock_queries: Mock
    ):
        """Prueba que lanza PlayerNotFound si el jugador no existe (Sad Path)."""
        # Arrange
        mock_queries.get_player.return_value = None

        # Act & Assert
        with pytest.raises(PlayerNotFound, match="El jugador 1 no existe."):
            validator.validate_player_exists(player_id=1)

    # --- Happy Path ---
    def test_validate_game_name_is_unique_success(
        self, validator: GameValidator, mock_queries: Mock
    ):
        """Prueba que no hace nada si el nombre es único (Happy Path)."""
        # Arrange
        mock_queries.game_name_exists.return_value = False

        # Act
        validator.validate_game_name_is_unique(game_name="New Game")

        # Assert
        mock_queries.game_name_exists.assert_called_once_with("New Game")

    # --- Sad Path ---
    def test_validate_game_name_is_unique_failure(
        self, validator: GameValidator, mock_queries: Mock
    ):
        """Prueba que lanza ActionConflict si el nombre ya existe (Sad Path)."""
        # Arrange
        mock_queries.game_name_exists.return_value = True

        # Act & Assert
        with pytest.raises(
            ActionConflict,
            match="Ya existe una partida con el nombre 'Existing Game'.",
        ):
            validator.validate_game_name_is_unique(game_name="Existing Game")

    # --- Happy Path ---
    def test_validate_game_status_success(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que no hace nada si el estado del juego es el esperado (Happy Path)."""
        # Arrange (sample_game status is LOBBY)

        # Act & Assert (no exception should be raised)
        try:
            validator.validate_game_status(
                game=sample_game, expected_status=GameStatus.LOBBY
            )
        except ActionConflict:
            pytest.fail(
                "validate_game_status levantó ActionConflict inesperadamente."
            )

    # --- Sad Path ---
    def test_validate_game_status_failure(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que lanza ActionConflict si el estado del juego no es el esperado (Sad Path)."""
        # Arrange (sample_game status is LOBBY)

        # Act & Assert
        with pytest.raises(
            ActionConflict,
            match="La acción no es válida en el estado actual de la partida",
        ):
            validator.validate_game_status(
                game=sample_game, expected_status=GameStatus.IN_PROGRESS
            )

    # --- Happy Path ---
    def test_validate_player_is_host_success(
        self, validator: GameValidator, mock_queries: Mock, sample_game: Game
    ):
        """Prueba que no hace nada si el jugador es el host (Happy Path)."""
        # Arrange
        mock_queries.is_player_host.return_value = True

        # Act
        validator.validate_player_is_host(game=sample_game, player_id=1)

        # Assert
        mock_queries.is_player_host.assert_called_once_with(sample_game.id, 1)

    # --- Sad Path ---
    def test_validate_player_is_host_failure(
        self, validator: GameValidator, mock_queries: Mock, sample_game: Game
    ):
        """Prueba que lanza ForbiddenAction si el jugador no es el host (Sad Path)."""
        # Arrange
        mock_queries.is_player_host.return_value = False

        # Act & Assert
        with pytest.raises(
            ForbiddenAction,
            match="Solo el host de la partida puede realizar esta acción.",
        ):
            validator.validate_player_is_host(game=sample_game, player_id=2)

    # --- Happy Path ---
    def test_validate_is_players_turn_success(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que no hace nada si es el turno del jugador (Happy Path)."""
        # Arrange
        sample_game.current_turn_player_id = 1

        # Act & Assert
        try:
            validator.validate_is_players_turn(game=sample_game, player_id=1)
        except NotYourTurn:
            pytest.fail(
                "validate_is_players_turn levantó NotYourTurn inesperadamente."
            )

    # --- Sad Path ---
    def test_validate_is_players_turn_failure(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que lanza NotYourTurn si no es el turno del jugador (Sad Path)."""
        # Arrange
        sample_game.current_turn_player_id = 2

        # Act & Assert
        with pytest.raises(
            NotYourTurn, match="No es tu turno para realizar esta acción."
        ):
            validator.validate_is_players_turn(game=sample_game, player_id=1)

    # --- Happy Path ---
    def test_validate_deck_has_cards_success(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que no hace nada si el mazo tiene cartas (Happy Path)."""
        # Arrange
        assert sample_game.deck

        # Act & Assert
        try:
            validator.validate_deck_has_cards(game=sample_game)
        except InvalidAction:
            pytest.fail(
                "validate_deck_has_cards levantó InvalidAction inesperadamente."
            )

    # --- Sad Path ---
    def test_validate_deck_has_cards_failure(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que lanza InvalidAction si el mazo está vacío (Sad Path)."""
        # Arrange
        sample_game.deck = []

        # Act & Assert
        with pytest.raises(
            InvalidAction, match="No quedan cartas en el mazo de robo."
        ):
            validator.validate_deck_has_cards(game=sample_game)

    # --- Happy Path ---
    def test_validate_player_in_game_success(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que devuelve el PlayerInGame si el jugador está en la partida (Happy Path)."""
        # Arrange
        player_id_in_game = sample_game.players[0].player_id

        # Act
        result = validator.validate_player_in_game(
            game=sample_game, player_id=player_id_in_game
        )

        # Assert
        assert isinstance(result, PlayerInGame)
        assert result.player_id == player_id_in_game

    # --- Sad Path ---
    def test_validate_player_in_game_failure(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que lanza PlayerNotInGame si el jugador no está en la partida (Sad Path)."""
        # Arrange (no setup needed)

        # Act & Assert
        with pytest.raises(
            PlayerNotInGame,
            match=f"El jugador 99 no forma parte de la partida {sample_game.id}.",
        ):
            validator.validate_player_in_game(game=sample_game, player_id=99)

    # --- Happy Path ---
    def test_validate_player_has_card_success(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que no hace nada si el jugador tiene la carta (Happy Path)."""
        # Arrange
        player = sample_game.players[0]
        card_id_in_hand = player.hand[0].card_id

        # Act & Assert
        try:
            validator.validate_player_has_cards(
                player=player, card_ids=[card_id_in_hand]
            )
        except CardNotFound:
            pytest.fail(
                "validate_player_has_card levantó CardNotFound inesperadamente."
            )

    # --- Sad Path ---
    def test_validate_player_has_card_failure(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que lanza CardNotFound si el jugador no tiene la carta (Sad Path)."""
        # Arrange
        player = sample_game.players[0]

        # Act & Assert
        with pytest.raises(
            NotYourCard, match=f"El jugador {player.player_id} no tiene la carta 999 en su mano."
        ):
            validator.validate_player_has_cards(player=player, card_ids=[999])

    # --- Sad Path ---
    def test_validate_player_count_failure_too_few(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que lanza InvalidAction si hay menos jugadores que el mínimo (Sad Path)."""
        # Arrange
        players_in_game_too_few = []

        # Act & Assert
        with pytest.raises(
            InvalidAction, match="no está dentro del rango permitido"
        ):
            validator.validate_player_count(
                game=sample_game, players_in_game=players_in_game_too_few
            )

    # --- Sad Path ---
    def test_validate_player_count_failure_too_many(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que lanza InvalidAction si hay más jugadores que el máximo (Sad Path)."""
        # Arrange
        players_in_game_too_many = sample_game.players * (
            sample_game.max_players + 1
        )

        # Act & Assert
        with pytest.raises(
            InvalidAction, match="no está dentro del rango permitido"
        ):
            validator.validate_player_count(
                game=sample_game, players_in_game=players_in_game_too_many
            )

    # --- Happy Path ---
    def test_validate_player_count_success(
        self, validator: GameValidator, sample_game: Game
    ):
        """Prueba que no hace nada si el número de jugadores es válido (Happy Path)."""
        # Arrange
        players_in_game_ok = sample_game.players * sample_game.min_players

        # Act & Assert
        try:
            validator.validate_player_count(
                game=sample_game, players_in_game=players_in_game_ok
            )
        except InvalidAction:
            pytest.fail(
                "validate_player_count levantó InvalidAction inesperadamente."
            )