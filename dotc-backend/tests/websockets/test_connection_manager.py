import pytest
from unittest.mock import AsyncMock

from app.websockets.connection_manager import ConnectionManager
from app.websockets.protocol.messages import WSMessage
from app.websockets.protocol.details import GameCreatedDetails
from app.api.schemas import GameLobbyInfo, GameStatus

# Marcamos todos los tests en este módulo como asíncronos para pytest.
pytestmark = pytest.mark.asyncio


@pytest.fixture
def manager() -> ConnectionManager:
    """
    Fixture de Pytest que proporciona una instancia limpia y nueva
    del ConnectionManager para cada test, asegurando el aislamiento.
    """
    return ConnectionManager()


# =================================================================
# 🔌 TESTS PARA EL MÉTODO connect()
# =================================================================


async def test_connect_to_lobby(manager: ConnectionManager):
    """
    Verifica que una conexión sin game_id/player_id se añade al lobby.
    """
    # Arrange
    mock_websocket = AsyncMock()

    # Act
    await manager.connect(mock_websocket)

    # Assert
    mock_websocket.accept.assert_awaited_once()
    assert mock_websocket in manager.lobby_connections
    assert not manager.connections_by_game


async def test_connect_to_game(manager: ConnectionManager):
    """
    Verifica que una conexión con game_id/player_id se añade a la partida.
    """
    # Arrange
    mock_websocket = AsyncMock()
    game_id = 1
    player_id = 101

    # Act
    await manager.connect(mock_websocket, game_id=game_id, player_id=player_id)

    # Assert
    mock_websocket.accept.assert_awaited_once()
    assert manager.connections_by_game[game_id][player_id] == mock_websocket
    assert not manager.lobby_connections


# =================================================================
# 🔌 TESTS PARA EL MÉTODO disconnect()
# =================================================================


async def test_disconnect_from_lobby(manager: ConnectionManager):
    """
    Verifica que un websocket conectado al lobby se elimina correctamente.
    """
    # Arrange
    mock_websocket = AsyncMock()
    await manager.connect(mock_websocket)
    assert mock_websocket in manager.lobby_connections

    # Act
    manager.disconnect(mock_websocket)

    # Assert
    assert mock_websocket not in manager.lobby_connections


async def test_disconnect_from_game(manager: ConnectionManager):
    """
    Verifica que un websocket de una partida se elimina correctamente.
    """
    # Arrange
    mock_websocket = AsyncMock()
    game_id = 1
    player_id = 101
    await manager.connect(mock_websocket, game_id=game_id, player_id=player_id)
    assert manager.connections_by_game[game_id][player_id] == mock_websocket

    # Act
    manager.disconnect(mock_websocket)

    # Assert
    assert game_id not in manager.connections_by_game


async def test_disconnect_unconnected_socket(manager: ConnectionManager):
    """
    Verifica que desconectar un socket que no estaba registrado no da errores.
    """
    # Arrange
    mock_websocket = AsyncMock()

    # Act 
    try:
        manager.disconnect(mock_websocket)
    except Exception as e:
        pytest.fail(f"disconnect() levantó una excepción inesperada: {e}")

    # Assert
    assert not manager.lobby_connections
    assert not manager.connections_by_game


async def test_disconnect_from_game_with_remaining_players(
    manager: ConnectionManager
    ):
    """
    Verifica que al desconectar un jugador,
    la partida no se elimina si aún quedan otros jugadores.
    """
    # Arrange
    game_id = 1
    player1_ws, player2_ws = AsyncMock(), AsyncMock()
    
    await manager.connect(player1_ws, game_id=game_id, player_id=101)
    await manager.connect(player2_ws, game_id=game_id, player_id=102)
    
    assert len(manager.connections_by_game[game_id]) == 2

    # Act
    manager.disconnect(player2_ws)

    # Assert
    assert game_id in manager.connections_by_game
    assert len(manager.connections_by_game[game_id]) == 1
    assert 102 not in manager.connections_by_game[game_id]
    assert manager.connections_by_game[game_id][101] == player1_ws



# =================================================================
# 📢 TESTS PARA BROADCAST Y SEND
# =================================================================


@pytest.fixture
def sample_message() -> WSMessage:
    """Fixture que crea un mensaje de ejemplo para usar en tests."""
    game_info = GameLobbyInfo(
        id=1,
        name="Test Game",
        min_players=4,
        max_players=8,
        player_count=1,
        host_id=101,
        game_status=GameStatus.LOBBY,
        password=None,
    )
    
    details = GameCreatedDetails(game=game_info)
    return WSMessage(details=details)


async def test_broadcast_to_lobby(
    manager: ConnectionManager,
    sample_message: WSMessage
    ):
    """
    Verifica que un broadcast al lobby envía
    el mensaje a todas las conexiones del lobby.
    """
    # Arrange
    ws1, ws2 = AsyncMock(), AsyncMock()
    ws_game = AsyncMock()
    await manager.connect(ws1)
    await manager.connect(ws2)
    await manager.connect(ws_game, game_id=1, player_id=101)

    # Act
    await manager.broadcast_to_lobby(sample_message)

    # Assert
    expected_json = sample_message.model_dump_json()
    ws1.send_text.assert_awaited_once_with(expected_json)
    ws2.send_text.assert_awaited_once_with(expected_json)
    ws_game.send_text.assert_not_awaited()


async def test_broadcast_to_game(
    manager: ConnectionManager,
    sample_message: WSMessage
    ):
    """
    Verifica que un broadcast a una partida envía el mensaje
    solo a los jugadores de esa partida.
    """
    # Arrange
    game1_ws1, game1_ws2 = AsyncMock(), AsyncMock()
    game2_ws = AsyncMock()  # Jugador de otra partida.
    lobby_ws = AsyncMock()  # Conexión de lobby.

    await manager.connect(game1_ws1, game_id=1, player_id=101)
    await manager.connect(game1_ws2, game_id=1, player_id=102)
    await manager.connect(game2_ws, game_id=2, player_id=201)
    await manager.connect(lobby_ws)

    # Act
    await manager.broadcast_to_game(sample_message, game_id=1)

    # Assert
    expected_json = sample_message.model_dump_json()
    game1_ws1.send_text.assert_awaited_once_with(expected_json)
    game1_ws2.send_text.assert_awaited_once_with(expected_json)
    game2_ws.send_text.assert_not_awaited()
    lobby_ws.send_text.assert_not_awaited()

async def test_broadcast_to_nonexistent_game_does_not_fail(
    manager: ConnectionManager,
    sample_message: WSMessage
):
    """
    Verifies that broadcasting to a game_id that has no connections
    does not raise an error and completes gracefully.
    """
    # Arrange
    non_existent_game_id = 9999
    # Ensure there are other connections to prove they are not affected
    ws1 = AsyncMock()
    await manager.connect(ws1, game_id=1, player_id=101)

    # Act
    try:
        await manager.broadcast_to_game(sample_message, game_id=non_existent_game_id)
    except Exception as e:
        pytest.fail(f"broadcast_to_game() raised an unexpected exception: {e}")

    # Assert
    # Verify that no messages were sent to any other existing connection
    ws1.send_text.assert_not_awaited()

async def test_send_to_player(
    manager: ConnectionManager,
    sample_message: WSMessage
    ):
    """
    Verifica que un mensaje se envía a un único jugador específico.
    """
    # Arrange
    player_ws = AsyncMock()
    other_player_ws = AsyncMock()
    
    await manager.connect(player_ws, game_id=1, player_id=101)
    await manager.connect(other_player_ws, game_id=1, player_id=102)

    # Act
    await manager.send_to_player(sample_message, game_id=1, player_id=101)

    # Assert
    expected_json = sample_message.model_dump_json()
    player_ws.send_text.assert_awaited_once_with(expected_json)
    other_player_ws.send_text.assert_not_awaited()

async def test_send_to_nonexistent_player_does_not_fail(
    manager: ConnectionManager,
    sample_message: WSMessage
):
    """
    Verifies that sending a message to a non-existent player or game
    does not raise an error and does not send messages to other players.
    This tests the 'else' branch of send_to_player.
    """
    # Arrange
    game_id = 1
    player_id = 101
    non_existent_player_id = 999
    non_existent_game_id = 888

    player_ws = AsyncMock()
    await manager.connect(player_ws, game_id=game_id, player_id=player_id)

    # Act
    # Case 1: Player does not exist in an existing game
    await manager.send_to_player(sample_message, game_id=game_id, player_id=non_existent_player_id)

    # Case 2: Game does not exist
    await manager.send_to_player(sample_message, game_id=non_existent_game_id, player_id=player_id)

    # Assert
    # Verify that the existing player did not receive any messages
    player_ws.send_text.assert_not_awaited()

async def test_player_in_multiple_games_receives_correct_broadcasts(
    manager: ConnectionManager, 
    sample_message: WSMessage
    ):
    """
    Verifica el escenario donde un mismo jugador está en dos partidas a la vez.
    Debe recibir broadcasts solo de la partida a la que se emite.
    """
    # Arrange
    player_id = 101
    game1_id = 1
    game2_id = 2

    # El jugador 101 se conecta a las partidas 1 y 2
    ws_game1 = AsyncMock()
    await manager.connect(ws_game1, game_id=game1_id, player_id=player_id)
    ws_game2 = AsyncMock()
    await manager.connect(ws_game2, game_id=game2_id, player_id=player_id)

    # El jugador 102 se conecta a la partida 1
    other_player_ws = AsyncMock()
    await manager.connect(other_player_ws, game_id=game1_id, player_id=102)

    assert manager.connections_by_game[game1_id][player_id] is ws_game1
    assert manager.connections_by_game[game2_id][player_id] is ws_game2

    # Act
    # Broadcast a la partida 1
    await manager.broadcast_to_game(sample_message, game_id=game1_id)

    # Assert
    expected_json = sample_message.model_dump_json()
    ws_game1.send_text.assert_awaited_once_with(expected_json)
    other_player_ws.send_text.assert_awaited_once_with(expected_json)
    ws_game2.send_text.assert_not_awaited()
    