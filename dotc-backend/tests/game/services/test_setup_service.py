import pytest
from unittest.mock import ANY, AsyncMock
from datetime import date

from app.game.services.game_setup_service import GameSetupService
from app.api.schemas import (
    StartGameResponse,
    GameLobbyInfo,
)
from app.domain.enums import (
    GameStatus,
    ResponseStatus,
    CardType,
    Avatar,
    CardLocation,
    PlayerRole,
)
from app.game.exceptions import InvalidAction, ActionConflict, InternalGameError
from app.domain.models import PlayerInGame, Game, PlayerInfo


@pytest.fixture
def game_setup_service(
    mock_queries, mock_commands, mock_validator, mock_notificator, mock_turn_utils
) -> GameSetupService:
    """
    Crea una instancia de GameSetupService con todas sus dependencias mockeadas.
    """
    return GameSetupService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
        turn_utils=mock_turn_utils,
    )


# --- 2. Tests para el Happy Path ---


@pytest.mark.asyncio
async def test_start_game_happy_path(
    game_setup_service: GameSetupService,
    mock_validator,
    mock_commands,
    mock_notificator,
    mock_queries,
    mock_turn_utils,
):
    """
    Prueba el flujo completo y exitoso de iniciar una partida.
    Verifica que se llaman a todos los métodos dependientes en el orden correcto
    y que la respuesta final es la esperada.
    """
    # --- Arrange ---
    game_id = 101
    host_id = 1

    mock_player = PlayerInGame(
        player_id=host_id,
        player_name="HostPlayer",
        player_birth_date=date(1990, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    mock_validator.validate_player_exists.return_value = mock_player

    player1 = PlayerInGame(
        player_id=55,
        player_name="Player 1",
        player_birth_date=date(2025, 10, 20),
        player_avatar=Avatar.DEFAULT,
    )
    player2 = PlayerInGame(
        player_id=66,
        player_name="Player 2",
        player_birth_date=date(2025, 1, 15),
        player_avatar=Avatar.DEFAULT,
    )
    player3 = PlayerInGame(
        player_id=77,
        player_name="Player 3",
        player_birth_date=date(2025, 5, 25),
        player_avatar=Avatar.DEFAULT,
    )
    player4 = PlayerInGame(
        player_id=host_id,
        player_name="HostPlayer",
        player_birth_date=date(2025, 12, 30),
        player_avatar=Avatar.DEFAULT,
    )

    mock_players_in_game = [player2, player1, player4, player3]
    mock_queries.get_players_in_game.return_value = mock_players_in_game

    mock_game = Game(
        id=game_id,
        name="Partida de Test",
        min_players=4,
        max_players=12,
        host=PlayerInfo(
            player_id=host_id,
            player_name="HostPlayer",
            player_birth_date=date(1989, 12, 30),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.LOBBY,
        password="secreto",
        players=mock_players_in_game,
    )
    mock_validator.validate_game_exists.return_value = mock_game

    # El servicio ahora delega el ordenamiento, lo mockeamos para tener un resultado predecible
    players_sorted_by_turn = [player1, player2, player3, player4]
    mock_turn_utils.sort_players_by_turn_order.return_value = players_sorted_by_turn

    mock_commands.update_game_status.return_value = ResponseStatus.OK
    mock_commands.set_current_turn.return_value = ResponseStatus.OK

    game_setup_service._set_cards_in_game = AsyncMock()
    game_setup_service._set_secrets_in_game = AsyncMock()

    # --- Act ---
    response = await game_setup_service.start_game(game_id, host_id)

    # --- Assert ---
    assert isinstance(response, StartGameResponse)
    assert response.detail == "La partida ha comenzado exitosamente."
    assert response.player_id_first_turn == player1.player_id

    mock_turn_utils.sort_players_by_turn_order.assert_called_once_with(mock_players_in_game)
    
    expected_players_in_order = [p.player_id for p in players_sorted_by_turn]

    mock_notificator.notify_game_started.assert_awaited_once_with(
        game_id=game_id,
        first_player_id=player1.player_id,
        players_in_turn_order=expected_players_in_order,
        updated_game_in_lobby=ANY,
    )

    call_kwargs = mock_notificator.notify_game_started.call_args.kwargs
    notified_lobby_info = call_kwargs["updated_game_in_lobby"]
    assert isinstance(notified_lobby_info, GameLobbyInfo)
    assert notified_lobby_info.player_count == len(mock_players_in_game)
    assert notified_lobby_info.game_status == GameStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_start_game_fails_if_game_is_not_in_lobby(
    game_setup_service: GameSetupService,
    mock_validator
):
    """
    Prueba que la partida no se inicia si su estado no es LOBBY.
    """
    # --- Arrange ---
    game_id = 101
    host_id = 1
    error_message = "La acción no es válida en el estado actual de la partida (IN_PROGRESS)."
    mock_validator.validate_game_status.side_effect = ActionConflict(
        detail=error_message
    )
    mock_validator.validate_player_exists.return_value = PlayerInfo(player_id=host_id, player_name="test", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT)
    mock_validator.validate_game_exists.return_value = Game(id=game_id, name="test", min_players=4, max_players=4, host=PlayerInfo(player_id=host_id, player_name="test", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT), status=GameStatus.IN_PROGRESS)

    # --- Act & Assert ---
    with pytest.raises(ActionConflict) as exc_info:
        await game_setup_service.start_game(game_id, host_id)

    assert exc_info.value.detail == error_message
    mock_validator.validate_game_status.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "player_count",
    [3, 6],
)
async def test_start_game_fails_if_player_count_is_invalid(
    player_count,
    game_setup_service: GameSetupService,
    mock_validator,
    mock_queries
):
    """
    Prueba que la partida no se inicia si el validador de número de jugadores falla.
    """
    # --- Arrange ---
    game_id = 101
    host_id = 1

    mock_validator.validate_player_exists.return_value = PlayerInfo(player_id=host_id, player_name="test", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT)
    mock_game = Game(
        id=game_id,
        name="Partida Inválida",
        min_players=4,
        max_players=5,
        host=PlayerInfo(
            player_id=host_id,
            player_name="Host",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.LOBBY,
    )
    mock_validator.validate_game_exists.return_value = mock_game

    mock_players_in_game = [
        PlayerInGame(
            player_id=i,
            player_name=f"P{i}",
            player_birth_date=date(1990, 1, i + 1),
            player_avatar=Avatar.DEFAULT,
        )
        for i in range(player_count)
    ]
    mock_queries.get_players_in_game.return_value = mock_players_in_game

    error_message = f"La cantidad de jugadores ({player_count}) no está dentro del rango permitido (4-5)."
    mock_validator.validate_player_count.side_effect = InvalidAction(
        detail=error_message
    )

    # --- Act & Assert ---
    with pytest.raises(InvalidAction) as exc_info:
        await game_setup_service.start_game(game_id, host_id)

    assert exc_info.value.detail == error_message
    mock_validator.validate_player_count.assert_called_once_with(
        mock_game, mock_players_in_game
    )


@pytest.mark.asyncio
async def test_start_game_fails_if_db_command_fails(
    game_setup_service: GameSetupService,
    mock_validator,
    mock_queries,
    mock_commands,
    mock_notificator,
    mock_turn_utils,
):
    """
    Prueba que el servicio maneja un error si un comando de escritura en la BD falla.
    """
    # --- Arrange ---
    game_id = 101
    host_id = 1

    mock_player = PlayerInGame(player_id=host_id, player_name="H", player_birth_date=date(1990,1,1), player_avatar=Avatar.DEFAULT)
    mock_players_in_game = [mock_player for _ in range(4)]
    mock_game = Game(
        id=game_id, name="Test", min_players=4, max_players=4,
        host=PlayerInfo(player_id=host_id, player_name="H", player_birth_date=date(1990,1,1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.LOBBY,
    )

    mock_validator.validate_player_exists.return_value = mock_player
    mock_validator.validate_game_exists.return_value = mock_game
    mock_queries.get_players_in_game.return_value = mock_players_in_game
    mock_turn_utils.sort_players_by_turn_order.return_value = mock_players_in_game

    mock_commands.set_current_turn.return_value = ResponseStatus.ERROR
    error_message = "Error al establecer el turno del jugador."

    # --- Act & Assert ---
    with pytest.raises(InternalGameError) as exc_info:
        await game_setup_service.start_game(game_id, host_id)

    assert exc_info.value.detail == error_message
    
    # Verificamos que se intentó llamar al comando que falla
    mock_commands.set_current_turn.assert_called_once()
    # Y que las operaciones posteriores no se ejecutaron
    mock_commands.update_game_status.assert_not_called()
    mock_notificator.notify_game_started.assert_not_awaited()


# --- Tests Unitarios para los Métodos Helper ---


@pytest.mark.asyncio
async def test_set_cards_in_game_happy_path(
    game_setup_service: GameSetupService, mock_commands
):
    """
    Prueba que la distribución de cartas se persiste en UNA SOLA llamada a la BD.
    """
    # --- Arrange ---
    game_id = 1
    players = [
        PlayerInGame(
            player_id=i,
            player_name=f"P{i}",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        )
        for i in range(4)
    ]
    mock_commands.create_deck_for_game.return_value = ResponseStatus.OK

    # --- Act ---
    await game_setup_service._set_cards_in_game(players, game_id)

    # --- Assert ---
    mock_commands.create_deck_for_game.assert_called_once()

    call_args = mock_commands.create_deck_for_game.call_args.args
    persisted_cards = call_args[1]

    assert len(persisted_cards) > 0
    assert any(c.location == CardLocation.IN_HAND for c in persisted_cards)
    assert any(c.location == CardLocation.DRAFT for c in persisted_cards)
    assert any(c.location == CardLocation.DRAW_PILE for c in persisted_cards)


@pytest.mark.asyncio
async def test_set_cards_in_game_for_two_players(
    game_setup_service: GameSetupService, mock_commands
):
    """
    Caso Borde: Verifica la regla para 2 jugadores en la ÚNICA lista de cartas.
    """
    # --- Arrange ---
    game_id = 1
    players = [
        PlayerInGame(
            player_id=i,
            player_name=f"P{i}",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        )
        for i in range(2)
    ]
    mock_commands.create_deck_for_game.return_value = ResponseStatus.OK

    # --- Act ---
    await game_setup_service._set_cards_in_game(players, game_id)

    # --- Assert ---
    mock_commands.create_deck_for_game.assert_called_once()
    all_created_cards = mock_commands.create_deck_for_game.call_args.args[1]

    card_types_created = {card.card_type for card in all_created_cards}

    assert CardType.POINT_YOUR_SUSPICIONS not in card_types_created
    assert CardType.BLACKMAILED not in card_types_created


@pytest.mark.asyncio
async def test_set_cards_in_game_db_failure(
    game_setup_service: GameSetupService, mock_commands
):
    """
    Caso de Error: Verifica que si falla la ÚNICA escritura a la BD, se lanza la excepción correcta.
    """
    # --- Arrange ---
    game_id = 1
    players = [
        PlayerInGame(
            player_id=i,
            player_name=f"P{i}",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        )
        for i in range(2)
    ]

    mock_commands.create_deck_for_game.return_value = ResponseStatus.ERROR
    error_message = "Error al crear y distribuir las cartas para la partida."

    # --- Act & Assert ---
    with pytest.raises(InternalGameError) as exc_info:
        await game_setup_service._set_cards_in_game(players, game_id)

    assert exc_info.value.detail == error_message
    mock_commands.create_deck_for_game.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("player_count", [4, 5])
async def test_set_secrets_in_game_happy_path(
    player_count, game_setup_service: GameSetupService, mock_commands
):
    """
    Prueba la lógica de asignación de roles y secretos, verificando las llamadas a la BD.
    """
    # --- Arrange ---
    game_id = 1
    players = [
        PlayerInGame(
            player_id=i,
            player_name=f"P{i}",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        )
        for i in range(1, player_count + 1)
    ]
    mock_commands.set_player_role.return_value = ResponseStatus.OK
    mock_commands.create_secret_card.return_value = 1

    # --- Act ---
    await game_setup_service._set_secrets_in_game(players, game_id)

    # --- Assert ---
    assert mock_commands.set_player_role.call_count > 0
    assert mock_commands.create_secret_card.call_count > 0


@pytest.mark.asyncio
async def test_set_secrets_in_game_db_failure_on_set_role(
    game_setup_service: GameSetupService, mock_commands
):
    """
    Caso de Error: Verifica que si falla la asignación de un rol, el proceso se detiene.
    """
    # --- Arrange ---
    game_id = 1
    players = [
        PlayerInGame(
            player_id=i,
            player_name=f"P{i}",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        )
        for i in range(1, 5)
    ]
    mock_commands.set_player_role.return_value = ResponseStatus.ERROR
    error_message = "Error al establecer el rol Asesino"

    # --- Act & Assert ---
    with pytest.raises(InternalGameError) as exc_info:
        await game_setup_service._set_secrets_in_game(players, game_id)

    assert exc_info.value.detail == error_message
    mock_commands.set_player_role.assert_called()
    mock_commands.create_secret_card.assert_not_called()