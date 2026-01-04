import pytest
from datetime import date
from app.game.services.lobby_service import LobbyService
from app.api.schemas import (
    CreateGameRequest,
    GameLobbyInfo,
    JoinGameRequest,
    ListGamesResponse,
    LeaveGameRequest,
    LeaveGameResponse,
)
from app.domain.models import GameStatus, Game, PlayerInfo, PlayerInGame
from app.domain.enums import Avatar, ResponseStatus
from unittest.mock import Mock, ANY
from app.game.exceptions import (
    ActionConflict,
    InternalGameError,
    GameFull,
    AlreadyJoined,
    GameNotFound,
    PlayerNotFound,
    InvalidAction,
)


@pytest.mark.asyncio
async def test_create_game_exitoso(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba el caso de éxito para la creación de una partida.
    Verifica que se llaman a los validadores y notificadores correctamente.
    """
    # 1. Arrange (Preparación)
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )
    mock_commands.create_game.return_value = 101

    mock_player = PlayerInfo(
        player_id=1,
        player_name="HostPlayer",
        player_birth_date=date(1990, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    mock_validator.validate_player_exists.return_value = mock_player

    request = CreateGameRequest(
        game_name="Mi Partida de Test",
        min_players=4,
        max_players=12,
        host_id=1,
        password=None,
    )

    # 2. Act
    response = await lobby_service.create_game(request)

    # 3. Assert (Verificación)
    assert response.game_id == 101

    # assert response.detail == "Partida creada con éxito."

    # Verificamos que las cosas importantes se hayan llamado.
    mock_validator.validate_player_exists.assert_called_once_with(1)
    mock_validator.validate_game_name_is_unique.assert_called_once_with(
        "Mi Partida de Test"
    )
    mock_commands.create_game.assert_called_once()
    mock_notificator.notify_game_created.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_game_falla_si_nombre_ya_existe(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba que la creación de la partida falla de forma controlada si el
    nombre de la partida ya está en uso, según lo detectado por el validador.
    """
    # 1. Arrange (Preparación)
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )
    error_message = "Ya existe una partida con ese nombre."
    mock_validator.validate_game_name_is_unique.side_effect = ActionConflict(
        detail=error_message
    )

    request = CreateGameRequest(
        game_name="Nombre Repetido",
        min_players=4,
        max_players=12,
        host_id=1,
        password=None,
    )

    # 2. Act & 3. Assert (Verificación)
    with pytest.raises(ActionConflict) as exc_info:
        await lobby_service.create_game(request)

    assert exc_info.value.detail == error_message

    mock_validator.validate_player_exists.assert_called_once_with(1)
    mock_validator.validate_game_name_is_unique.assert_called_once_with(
        "Nombre Repetido"
    )
    mock_commands.create_game.assert_not_called()
    mock_notificator.notify_game_created.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_game_falla_si_db_no_crea_la_partida(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba que la creación de la partida falla de forma controlada si
    la capa de comandos de la base de datos devuelve None.
    """
    # 1. Arrange (Preparación)
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )
    mock_commands.create_game.return_value = None

    request = CreateGameRequest(
        game_name="Mi Partida de Test",
        min_players=4,
        max_players=12,
        host_id=1,
        password=None,
    )

    # 2. Act & 3. Assert (Verificación)
    with pytest.raises(InternalGameError) as exc_info:
        await lobby_service.create_game(request)

    assert exc_info.value.detail == "La base de datos no pudo crear la partida."
    mock_validator.validate_player_exists.assert_called_once_with(1)
    mock_validator.validate_game_name_is_unique.assert_called_once_with(
        "Mi Partida de Test"
    )
    mock_commands.create_game.assert_called_once()
    mock_notificator.notify_game_created.assert_not_awaited()


# =================================================================
# --- TESTS PARA join_game ---
# =================================================================


@pytest.mark.asyncio
async def test_join_game_exitoso(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba el caso de éxito para unirse a una partida.
    Verifica que todas las validaciones pasan y se notifican los eventos.
    """
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )

    mock_game = Game(
        id=101,
        name="Partida Test",
        min_players=4,
        max_players=12,
        players=[
            PlayerInGame(
                player_id=99,
                player_name="Host",
                player_birth_date=date(1990, 1, 1),
                player_avatar=Avatar.DEFAULT,
            )
        ],
        status=GameStatus.LOBBY,
        host=PlayerInfo(
            player_id=99,
            player_name="Host",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        password=None,
    )
    mock_validator.validate_game_exists.return_value = mock_game

    mock_player = PlayerInfo(
        player_id=1,
        player_name="Naevier",
        player_birth_date=date(1992, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    mock_validator.validate_player_exists.return_value = mock_player

    mock_queries.is_player_in_game.return_value = False
    mock_commands.add_player_to_game.return_value = ResponseStatus.OK

    request = JoinGameRequest(game_id=101, player_id=1)

    # 2. Act
    response = await lobby_service.join_game(request)

    # 3. Assert
    assert response.detail == "Te has unido a la partida con éxito."

    mock_notificator.notify_player_joined.assert_awaited_once_with(
        101, 1, "Naevier", ANY
    )

    call_args, _ = mock_notificator.notify_player_joined.call_args
    notified_game_info = call_args[3]
    assert isinstance(notified_game_info, GameLobbyInfo)
    assert notified_game_info.id == 101
    assert notified_game_info.player_count == 2


@pytest.mark.asyncio
async def test_join_game_falla_si_partida_llena(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """Prueba que un jugador no puede unirse a una partida que ya está llena."""
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )

    players_in_game = [
        PlayerInGame(
            player_id=i,
            player_name=f"P{i}",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        )
        for i in range(4)
    ]
    mock_game = Game(
        id=101,
        name="Partida Llena",
        min_players=4,
        max_players=4,
        players=players_in_game,
        status=GameStatus.LOBBY,
        host=PlayerInfo(
            player_id=99,
            player_name="Host",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
    )
    mock_validator.validate_game_exists.return_value = mock_game

    mock_player = PlayerInfo(
        player_id=5,
        player_name="Extra",
        player_birth_date=date(1991, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    mock_validator.validate_player_exists.return_value = mock_player

    request = JoinGameRequest(game_id=101, player_id=5)

    # 2. Act & 3. Assert
    with pytest.raises(GameFull) as exc_info:
        await lobby_service.join_game(request)

    assert exc_info.value.detail == "La partida está llena."
    mock_validator.validate_game_exists.assert_called_once_with(101)
    mock_validator.validate_player_exists.assert_called_once_with(5)
    mock_validator.validate_game_status.assert_called_once_with(
        mock_game, GameStatus.LOBBY
    )
    mock_commands.add_player_to_game.assert_not_called()
    mock_notificator.notify_player_joined.assert_not_awaited()


@pytest.mark.asyncio
async def test_join_game_falla_si_jugador_ya_esta_en_partida(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """Prueba que un jugador no puede unirse a una partida en la que ya está."""
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )

    mock_game = Game(
        id=101,
        name="Partida",
        min_players=4,
        max_players=4,
        players=[
            PlayerInGame(
                player_id=1,
                player_name="Player1",
                player_birth_date=date(1990, 1, 1),
                player_avatar=Avatar.DEFAULT,
            )
        ],
        status=GameStatus.LOBBY,
        host=PlayerInfo(
            player_id=99,
            player_name="Host",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
    )
    mock_validator.validate_game_exists.return_value = mock_game

    mock_queries.is_player_in_game.return_value = True

    request = JoinGameRequest(game_id=101, player_id=1)

    # 2. Act & 3. Assert
    with pytest.raises(AlreadyJoined) as exc_info:
        await lobby_service.join_game(request)

    assert exc_info.value.detail == "El jugador ya está en la partida."
    mock_queries.is_player_in_game.assert_called_once_with(
        game_id=101, player_id=1
    )
    mock_commands.add_player_to_game.assert_not_called()
    mock_notificator.notify_player_joined.assert_not_awaited()


@pytest.mark.asyncio
async def test_join_game_falla_si_validacion_falla(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """Prueba que el servicio falla si una validación inicial (ej: partida no existe) lanza una excepción."""
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )
    error_message = "La partida 999 no existe."
    mock_validator.validate_game_exists.side_effect = GameNotFound(
        detail=error_message
    )

    request = JoinGameRequest(game_id=999, player_id=1)

    # 2. Act & 3. Assert
    with pytest.raises(GameNotFound) as exc_info:
        await lobby_service.join_game(request)

    assert exc_info.value.detail == error_message
    mock_validator.validate_game_exists.assert_called_once_with(999)
    mock_validator.validate_player_exists.assert_not_called()
    mock_commands.add_player_to_game.assert_not_called()
    mock_notificator.notify_player_joined.assert_not_awaited()


# =================================================================
# --- TESTS PARA list_games ---
# =================================================================


@pytest.mark.asyncio
async def test_list_games_exitoso_con_partidas(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba que el servicio devuelve correctamente los datos de la capa de queries.
    """
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )

    mock_lobby_info = [
        GameLobbyInfo(
            id=1,
            name="Partida 1",
            player_count=2,
            min_players=2,
            max_players=4,
            host_id=1,
            game_status=GameStatus.LOBBY,
            password=None,
        ),
        GameLobbyInfo(
            id=2,
            name="Partida 2",
            player_count=3,
            min_players=2,
            max_players=6,
            host_id=2,
            game_status=GameStatus.LOBBY,
            password=None,
        ),
    ]
    mock_queries.list_games_in_lobby.return_value = mock_lobby_info

    # 2. Act
    response = lobby_service.list_games()

    # 3. Assert
    assert isinstance(response, ListGamesResponse)
    assert len(response.games) == 2
    assert (
        response.detail == "Listado de partidas en el lobby obtenido con éxito."
    )
    assert response.games[0].name == "Partida 1"
    assert response.games[1].max_players == 6

    mock_queries.list_games_in_lobby.assert_called_once()
    mock_commands.create_game.assert_not_called()


@pytest.mark.asyncio
async def test_list_games_exitoso_sin_partidas(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba que el servicio funciona correctamente cuando no hay partidas en el lobby.
    """
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )
    mock_queries.list_games_in_lobby.return_value = []

    # 2. Act
    response = lobby_service.list_games()

    # 3. Assert
    assert isinstance(response, ListGamesResponse)
    assert len(response.games) == 0
    assert (
        response.detail == "Listado de partidas en el lobby obtenido con éxito."
    )
    assert response.games == []
    mock_queries.list_games_in_lobby.assert_called_once()


# =================================================================
# --- TESTS PARA leave_game ---
# =================================================================


@pytest.mark.asyncio
async def test_leave_game_exitoso_no_host(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba que un jugador que no es host abandona una partida correctamente.
    """
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )
    game_id = 101
    player_id_to_leave = 2
    player_name_to_leave = "Leaver"

    players_in_game = [
        PlayerInGame(
            player_id=1, player_name="Host",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT
        ),
        PlayerInGame(
            player_id=player_id_to_leave,
            player_name=player_name_to_leave,
            player_birth_date=date(1991, 1, 1),
            player_avatar=Avatar.DEFAULT
        ),
    ]
    mock_game = Game(
        id=game_id,
        name="Partida de Abandono",
        min_players=2,
        max_players=4,
        players=players_in_game,
        status=GameStatus.LOBBY,
        host=PlayerInfo(player_id=1, player_name="Host",
                        player_birth_date=date(1990, 1, 1),
                        player_avatar=Avatar.DEFAULT),
    )
    mock_validator.validate_game_exists.return_value = mock_game

    mock_player = PlayerInfo(
        player_id=player_id_to_leave,
        player_name=player_name_to_leave,
        player_birth_date=date(1991, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    mock_validator.validate_player_exists.return_value = mock_player
    mock_validator.validate_player_in_game.return_value = players_in_game[1]

    mock_commands.remove_player_from_game.return_value = ResponseStatus.OK

    request = LeaveGameRequest(game_id=game_id, player_id=player_id_to_leave)

    # 2. Act
    response = await lobby_service.leave_game(request)

    # 3. Assert
    assert isinstance(response, LeaveGameResponse)
    assert response.detail == "Has abandonado la partida con éxito."

    mock_commands.remove_player_from_game.assert_called_once_with(
        player_id=player_id_to_leave, game_id=game_id
    )
    mock_commands.delete_game.assert_not_called()
    mock_notificator.notify_player_left.assert_awaited_once_with(
        game_id, player_id_to_leave, player_name_to_leave, ANY
    )
    mock_notificator.notify_game_removed.assert_not_awaited()

    call_args, _ = mock_notificator.notify_player_left.call_args
    notified_game_info = call_args[3]
    assert isinstance(notified_game_info, GameLobbyInfo)
    assert notified_game_info.player_count == 1


@pytest.mark.asyncio
async def test_leave_game_exitoso_siendo_host(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba que si el host abandona la partida, esta se elimina.
    """
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )
    game_id = 101
    host_id = 1

    mock_game = Game(
        id=game_id,
        name="Partida a Eliminar",
        min_players=2,
        max_players=4,
        players=[PlayerInGame(player_id=host_id, player_name="Host",
                              player_birth_date=date(1990, 1, 1),
                              player_avatar=Avatar.DEFAULT)],
        status=GameStatus.LOBBY,
        host=PlayerInfo(player_id=host_id, player_name="Host",
                        player_birth_date=date(1990, 1, 1),
                        player_avatar=Avatar.DEFAULT),
    )
    mock_validator.validate_game_exists.return_value = mock_game

    mock_host_player = PlayerInfo(
        player_id=host_id,
        player_name="Host",
        player_birth_date=date(1990, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    mock_validator.validate_player_exists.return_value = mock_host_player

    mock_commands.delete_game.return_value = ResponseStatus.OK

    request = LeaveGameRequest(game_id=game_id, player_id=host_id)

    # 2. Act
    response = await lobby_service.leave_game(request)

    # 3. Assert
    assert response.detail == "Has abandonado la partida con éxito."

    mock_commands.delete_game.assert_called_once_with(game_id=game_id)
    mock_commands.remove_player_from_game.assert_not_called()

    # Se notifica la salida del jugador a la partida (aunque esté por borrarse)
    mock_notificator.notify_player_left.assert_awaited_once()
    # Se notifica al lobby general que la partida fue eliminada
    mock_notificator.notify_game_removed.assert_awaited_once_with(game_id)


@pytest.mark.asyncio
async def test_leave_game_falla_si_partida_ya_inicio(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba que un jugador no puede abandonar una partida que está en progreso.
    """
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )
    mock_game = Game(
        id=101,
        name="Partida en Progreso",
        min_players=2,
        max_players=4,
        players=[],
        status=GameStatus.IN_PROGRESS,
        host=PlayerInfo(player_id=1, player_name="Host",
                        player_birth_date=date(1990, 1, 1),
                        player_avatar=Avatar.DEFAULT),
    )
    mock_validator.validate_game_exists.return_value = mock_game

    request = LeaveGameRequest(game_id=101, player_id=2)

    # 2. Act & 3. Assert
    with pytest.raises(InvalidAction) as exc_info:
        await lobby_service.leave_game(request)

    assert exc_info.value.detail == "No puedes abandonar una partida ya iniciada."
    mock_commands.remove_player_from_game.assert_not_called()
    mock_notificator.notify_player_left.assert_not_awaited()


@pytest.mark.asyncio
async def test_leave_game_falla_si_db_falla(
    mock_queries, mock_commands, mock_validator, mock_notificator
):
    """
    Prueba que el servicio maneja un error si la DB falla al eliminar al jugador
    """
    # 1. Arrange
    lobby_service = LobbyService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )
    mock_game = Game(
        id=101,
        name="Partida de Falla",
        min_players=2,
        max_players=4,
        players=[PlayerInGame(player_id=2, player_name="Leaver",
                            player_birth_date=date(1991, 1, 1),
                            player_avatar=Avatar.DEFAULT)],
        status=GameStatus.LOBBY,
        host=PlayerInfo(player_id=1, player_name="Host",
                        player_birth_date=date(1990, 1, 1),
                        player_avatar=Avatar.DEFAULT),
    )
    player: PlayerInfo = PlayerInfo(player_id=2, player_name="Leaver",
                                    player_birth_date=date(1991, 1, 1),
                                    player_avatar=Avatar.DEFAULT)

    mock_validator.validate_game_exists.return_value = mock_game
    mock_validator.validate_player_exists.return_value = player

    mock_commands.remove_player_from_game.return_value = ResponseStatus.ERROR

    request = LeaveGameRequest(game_id=101, player_id=2)

    # 2. Act & 3. Assert
    with pytest.raises(InternalGameError) as exc_info:
        await lobby_service.leave_game(request)

    assert exc_info.value.detail == "La base de datos no pudo sacar al jugador."
    mock_commands.remove_player_from_game.assert_called_once_with(player_id=2, game_id=101)
    mock_notificator.notify_player_left.assert_not_awaited()
    