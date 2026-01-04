import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock

# Importa la clase que vamos a testear
from app.game.services.game_state_service import GameStateService

# Importa los modelos y enums necesarios para crear datos de prueba
from app.domain.models import Card, PlayerInGame, PlayerInfo, Game, SecretCard
from app.domain.enums import (
    GameStatus,
    CardLocation,
    CardType,
    Avatar,
    PlayerRole,
)

# Importa las excepciones que esperamos que el servicio lance
from app.game.exceptions import GameNotFound, PlayerNotInGame


# =================================================================
# ⚙️ FIXTURES: CONFIGURACIÓN PARA LOS TESTS DE ESTE MÓDULO
# =================================================================


@pytest.fixture
def game_state_service(
    mock_queries: Mock,
    mock_commands: Mock,
    mock_validator: Mock,
    mock_notificator: AsyncMock,
) -> GameStateService:
    """Crea una instancia de GameStateService con dependencias mockeadas."""
    # Arrange
    from app.game.helpers.turn_utils import TurnUtils
    return GameStateService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
        turn_utils=TurnUtils,
    )


# =================================================================
# --- TESTS PARA get_game_state ---
# =================================================================


def test_get_game_state_exitoso_y_sanitizado(
    game_state_service: GameStateService, mock_validator: Mock
):
    """
    Prueba el caso de éxito para obtener el estado del juego y verifica
    que la información sensible (manos, secretos, mazo) se oculta.
    """
    # --- Arrange ---
    # Creamos un objeto 'Game' completo y complejo que simula venir de la base de datos
    mock_player1 = PlayerInGame(
        player_id=1,
        player_name="Lautaro",
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
        hand=[
            Card(
                card_id=1,
                game_id=101,
                card_type=CardType.NOT_SO_FAST,
                location=CardLocation.IN_HAND,
            )
        ],
        secrets=[
            SecretCard(
                secret_id=1,
                game_id=101,
                player_id=1,
                role=PlayerRole.MURDERER,
                is_revealed=False,
            )
        ],
    )
    mock_game = Game(
        id=101,
        name="Partida de Test",
        min_players=4,
        max_players=12,
        host=PlayerInfo(
            player_id=1,
            player_name="Lautaro",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
        players=[mock_player1],
        deck=[
            Card(
                card_id=3,
                game_id=101,
                card_type=CardType.DEAD_CARD_FOLLY,
                location=CardLocation.DRAW_PILE,
            )
        ],
        password=None,
        discard_pile=[],
        draft=[],
        current_turn_player_id=1,
    )
    mock_validator.validate_game_exists.return_value = mock_game

    # --- Act ---
    # El servicio ahora devuelve directamente el objeto 'Game' sanitizado
    response = game_state_service.get_game_state(game_id=101)

    # --- Assert ---
    mock_validator.validate_game_exists.assert_called_once_with(101)

    # Verificamos que el objeto devuelto es del tipo correcto y tiene los datos públicos
    assert isinstance(response.game, Game)
    assert response.game.id == 101

    # Verificamos que la información sensible fue eliminada (sanitizada)
    assert response.game.deck == []  # El mazo debe estar vacío
    assert len(response.game.players) == 1
    assert (
        response.game.players[0].hand == []
    )  # La mano del jugador debe estar vacía
    # los secretos tmb no se ven
    assert response.game.players[0].secrets == []


def test_get_game_state_falla_si_juego_no_existe(
    game_state_service: GameStateService, mock_validator: Mock
):
    """
    Prueba que el servicio lanza 'GameNotFound' si el validador no encuentra el juego.
    """
    # --- Arrange ---
    # ¡LA CLAVE! Simulamos que el validador lanza la excepción de negocio correcta.
    mock_validator.validate_game_exists.side_effect = GameNotFound(
        "La partida no existe."
    )

    # --- Act & Assert ---
    # CORRECCIÓN: Usamos pytest.raises para verificar que se lanza la excepción esperada.
    with pytest.raises(GameNotFound, match="La partida no existe."):
        game_state_service.get_game_state(game_id=999)

    # Verificamos que el flujo se detuvo en la validación.
    mock_validator.validate_game_exists.assert_called_once_with(999)


# =================================================================
# --- TESTS PARA get_player_hand ---
# =================================================================


def test_get_player_hand_exitoso(
    game_state_service: GameStateService,
    mock_validator: Mock,
    mock_queries: Mock,
):
    """
    Prueba el caso de éxito para obtener la mano de un jugador.
    """
    # --- Arrange ---
    mock_hand = [
        Card(
            card_id=1,
            game_id=101,
            card_type=CardType.HERCULE_POIROT,
            location=CardLocation.IN_HAND,
        )
    ]
    mock_queries.get_player_hand.return_value = mock_hand

    # --- Act ---
    # El servicio ahora devuelve directamente la lista de cartas.
    response = game_state_service.get_player_hand(game_id=101, player_id=1)

    # --- Assert ---
    assert isinstance(response.cards, list)
    assert len(response.cards) == 1
    assert response.cards[0].card_id == 1

    # Verificamos que se hicieron las validaciones y la consulta correctas.
    mock_validator.validate_game_exists.assert_called_once_with(101)
    mock_validator.validate_player_in_game.assert_called_once()
    mock_queries.get_player_hand.assert_called_once_with(101, 1)


def test_get_player_hand_falla_si_juego_no_existe(
    game_state_service: GameStateService,
    mock_validator: Mock,
    mock_queries: Mock,
):
    """
    Prueba que se lanza 'GameNotFound' si el validador no encuentra el juego.
    """
    # --- Arrange ---
    mock_validator.validate_game_exists.side_effect = GameNotFound(
        "La partida no existe."
    )

    # --- Act & Assert ---
    # CORRECCIÓN: Usamos pytest.raises para verificar que se lanza la excepción.
    with pytest.raises(GameNotFound, match="La partida no existe."):
        game_state_service.get_player_hand(game_id=999, player_id=1)

    # Verificamos que el flujo se detuvo en la validación y no se consultó la DB.
    mock_validator.validate_game_exists.assert_called_once_with(999)
    mock_queries.get_player_hand.assert_not_called()


# =================================================================
# --- TESTS PARA get_player_secrets ---
# =================================================================


def test_get_player_secrets_exitoso(
    game_state_service: GameStateService,
    mock_validator: Mock,
    mock_queries: Mock,
):
    """
    Prueba el caso de éxito para obtener los secretos de un jugador.
    """
    # --- Arrange ---
    mock_secrets = [
        SecretCard(
            secret_id=1,
            game_id=101,
            player_id=1,
            role=PlayerRole.MURDERER,
            is_revealed=False,
        )
    ]
    mock_queries.get_player_secrets.return_value = mock_secrets

    # --- Act ---
    response = game_state_service.get_player_secrets(game_id=101, player_id=1)

    # --- Assert ---
    assert isinstance(response.secrets, list)
    assert len(response.secrets) == 1
    assert response.secrets[0].role == PlayerRole.MURDERER
    mock_validator.validate_game_exists.assert_called_once_with(101)
    mock_validator.validate_player_in_game.assert_called_once()
    mock_queries.get_player_secrets.assert_called_once_with(101, 1)


def test_get_player_secrets_falla_si_jugador_no_en_partida(
    game_state_service: GameStateService,
    mock_validator: Mock,
    mock_queries: Mock,
):
    """
    Prueba que se lanza 'PlayerNotInGame' si el jugador no pertenece a la partida.
    """
    # --- Arrange ---
    # Simulamos que la primera validación (juego existe) pasa, pero la segunda falla.
    mock_validator.validate_player_in_game.side_effect = PlayerNotInGame(
        "El jugador no forma parte de la partida."
    )

    # --- Act & Assert ---
    # CORRECCIÓN: Usamos pytest.raises para verificar que se lanza la excepción.
    with pytest.raises(
        PlayerNotInGame, match="El jugador no forma parte de la partida."
    ):
        game_state_service.get_player_secrets(game_id=101, player_id=999)

    # Verificamos que se intentó validar, pero no se consultaron los secretos.
    mock_validator.validate_player_in_game.assert_called_once()
    mock_queries.get_player_secrets.assert_not_called()


# =================================================================
# --- TESTS PARA get_size_deck ---
# =================================================================


def test_get_size_deck_exitoso(
    game_state_service: GameStateService,
    mock_validator: Mock,
    mock_queries: Mock,
):
    """
    Prueba el caso de éxito para obtener el tamaño del mazo de robo.
    """
    # --- Arrange ---
    mock_game = Mock()
    mock_validator.validate_game_exists.return_value = mock_game
    mock_queries.get_size_deck.return_value = 42

    # --- Act ---
    response = game_state_service.get_size_deck(game_id=101)

    # --- Assert ---
    assert response.size_deck == 42
    mock_validator.validate_game_exists.assert_called_once_with(101)
    mock_queries.get_size_deck.assert_called_once_with(101)


def test_get_size_deck_mazo_vacio(
    game_state_service: GameStateService,
    mock_validator: Mock,
    mock_queries: Mock,
):
    """
    Prueba que el servicio maneja correctamente el caso de un mazo vacío.
    """
    # --- Arrange ---
    mock_game = Mock()
    mock_validator.validate_game_exists.return_value = mock_game
    mock_queries.get_size_deck.return_value = 0

    # --- Act ---
    response = game_state_service.get_size_deck(game_id=101)

    # --- Assert ---
    assert response.size_deck == 0
    mock_validator.validate_game_exists.assert_called_once_with(101)
    mock_queries.get_size_deck.assert_called_once_with(101)


def test_get_size_deck_falla_si_juego_no_existe(
    game_state_service: GameStateService,
    mock_validator: Mock,
    mock_queries: Mock,
):
    """
    Prueba que se lanza 'GameNotFound' si el validador no encuentra el juego.
    """
    # --- Arrange ---
    mock_validator.validate_game_exists.side_effect = GameNotFound(
        "La partida no existe."
    )

    # --- Act & Assert ---
    with pytest.raises(GameNotFound, match="La partida no existe."):
        game_state_service.get_size_deck(game_id=999)

    # Verificamos que el flujo se detuvo en la validación y no se consultó la DB.
    mock_validator.validate_game_exists.assert_called_once_with(999)
    mock_queries.get_size_deck.assert_not_called()
