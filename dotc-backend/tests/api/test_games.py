import pytest
from datetime import date
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

# --- Imports de la App ---
from app.main import app
from app.api.schemas import (
    CreateGameResponse,
    ListGamesResponse,
    GameLobbyInfo,
    StartGameResponse,
    GameStateResponse,
    PlayerHandResponse,
    DrawCardResponse,
    GeneralActionResponse,
    ConsultDeckSizeResponse,
)
from app.game.exceptions import (
    ActionConflict,
    GameNotFound,
    ForbiddenAction,
    InvalidAction,
    NotYourTurn,
    NotYourCard,
)
from app.domain.enums import GameStatus, Avatar, CardType, CardLocation
from app.domain.models import Game, PlayerInGame, PlayerInfo, Card

client = TestClient(app)


# =================================================================
# --- TESTS PARA POST /api/games (Crear Partida) ---
# =================================================================


@pytest.mark.asyncio
async def test_create_game_endpoint_success(game_manager_mocker: AsyncMock):
    # Arrange
    game_manager_mocker.create_game.return_value = CreateGameResponse(
        game_id=42
    )
    game_data = {
        "host_id": 1,
        "game_name": "Partida de Test",
        "min_players": 4,
        "max_players": 12,
    }
    # Act
    response = client.post("/api/games", json=game_data)
    # Assert
    assert response.status_code == 201
    assert response.json() == {"game_id": 42}
    game_manager_mocker.create_game.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_game_endpoint_name_conflict_returns_409(
    game_manager_mocker: AsyncMock,
):
    # Arrange
    game_manager_mocker.create_game.side_effect = ActionConflict(
        detail="Ya existe una partida con ese nombre."
    )
    game_data = {
        "host_id": 1,
        "game_name": "Nombre Repetido",
        "min_players": 4,
        "max_players": 12,
    }
    # Act
    response = client.post("/api/games", json=game_data)
    # Assert
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Ya existe una partida con ese nombre."
    }


# =================================================================
# --- TESTS PARA GET /api/games (Listar Partidas) ---
# =================================================================


def test_list_games_endpoint_success(game_manager_mocker: AsyncMock):
    # Arrange
    lobby_info = GameLobbyInfo(
        id=101,
        name="Lobby Game",
        min_players=4,
        max_players=12,
        host_id=1,
        player_count=1,
        password=None,
        game_status=GameStatus.LOBBY,
    )
    game_manager_mocker.list_games.return_value = ListGamesResponse(
        games=[lobby_info]
    )
    # Act
    response = client.get("/api/games")
    # Assert
    assert response.status_code == 200
    assert len(response.json()["games"]) == 1
    assert response.json()["games"][0]["name"] == "Lobby Game"
    game_manager_mocker.list_games.assert_called_once()


# =================================================================
# --- TESTS PARA POST /api/games/{game_id}/join (Unirse a Partida) ---
# =================================================================


@pytest.mark.asyncio
async def test_join_game_endpoint_game_not_found_returns_404(
    game_manager_mocker: AsyncMock,
):
    # Arrange
    game_manager_mocker.join_game.side_effect = GameNotFound(
        detail="La partida 999 no existe, ciego."
    )
    join_data = {"player_id": 2, "game_id": 999}
    # Act
    response = client.post("/api/games/999/join", json=join_data)
    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "La partida 999 no existe, ciego."}


# =================================================================
# --- TESTS PARA POST /api/games/{game_id}/start (Iniciar Partida) ---
# =================================================================


@pytest.mark.asyncio
async def test_start_game_endpoint_success(game_manager_mocker: AsyncMock):
    # Arrange
    game_manager_mocker.start_game.return_value = StartGameResponse(
        player_id_first_turn=2, detail="La partida ha comenzado."
    )
    start_data = {"player_id": 1, "game_id": 101}
    # Act
    response = client.post("/api/games/101/start", json=start_data)
    # Assert
    assert response.status_code == 200
    assert response.json()["player_id_first_turn"] == 2
    game_manager_mocker.start_game.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_game_not_host_returns_403(game_manager_mocker: AsyncMock):
    # Arrange
    game_manager_mocker.start_game.side_effect = ForbiddenAction(
        detail="Solo el host puede iniciar la partida."
    )
    start_data = {"player_id": 99, "game_id": 101}
    # Act
    response = client.post("/api/games/101/start", json=start_data)
    # Assert
    assert response.status_code == 403
    assert response.json() == {
        "detail": "Solo el host puede iniciar la partida."
    }


# =================================================================
# --- TESTS PARA GET /api/games/{game_id} (Obtener Estado) ---
# =================================================================


def test_get_game_state_endpoint_success(game_manager_mocker: AsyncMock):
    # Arrange
    mock_game_object = Game(
        id=101,
        name="Partida de Test",
        status=GameStatus.IN_PROGRESS,
        current_turn_player_id=1,
        players=[
            PlayerInGame(
                player_id=1,
                player_name="Lautaro",
                turn_order=1,
                player_birth_date=date(1990, 1, 1),
                player_avatar=Avatar.DEFAULT,
            )
        ],
        host=PlayerInfo(
            player_id=1,
            player_name="Lautaro",
            player_birth_date=date(1990, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        min_players=2,
        max_players=4,
    )
    mock_response = GameStateResponse(game=mock_game_object)
    game_manager_mocker.get_game_state.return_value = mock_response
    # Act
    response = client.get("/api/games/101")
    # Assert
    assert response.status_code == 200
    assert response.json()["game"]["id"] == 101
    assert response.json()["game"]["status"] == "IN_PROGRESS"
    game_manager_mocker.get_game_state.assert_called_once_with(101)


# =================================================================
# --- TESTS PARA GET /api/games/{game_id}/players/{player_id}/hand ---
# =================================================================


def test_get_player_hand_success(game_manager_mocker: AsyncMock):
    # Arrange
    mock_card = Card(
        card_id=1,
        game_id=101,
        card_type=CardType.HERCULE_POIROT,
        location=CardLocation.IN_HAND,
    )
    game_manager_mocker.get_player_hand.return_value = PlayerHandResponse(
        cards=[mock_card]
    )
    # Act
    response = client.get("/api/games/101/players/1/hand")
    # Assert
    assert response.status_code == 200
    assert len(response.json()["cards"]) == 1
    assert response.json()["cards"][0]["card_type"] == "Hercule Poirot"
    game_manager_mocker.get_player_hand.assert_called_once()


# =================================================================
# --- TESTS PARA POST /api/games/{game_id}/actions/discard ---
# =================================================================


@pytest.mark.asyncio
async def test_discard_card_success(game_manager_mocker: AsyncMock):
    # Arrange
    game_manager_mocker.discard_card.return_value = GeneralActionResponse(
        detail="Carta descartada."
    )
    discard_data = {"player_id": 1, "game_id": 101, "card_id": 5}
    # Act
    response = client.post("/api/games/101/actions/discard", json=discard_data)
    # Assert
    assert response.status_code == 200
    assert response.json()["detail"] == "Carta descartada."
    game_manager_mocker.discard_card.assert_awaited_once()


@pytest.mark.asyncio
async def test_discard_card_not_your_card_returns_403(
    game_manager_mocker: AsyncMock,
):
    # Arrange
    game_manager_mocker.discard_card.side_effect = NotYourCard(
        detail="Esa carta no está en tu mano, chorro."
    )
    discard_data = {"player_id": 1, "game_id": 101, "card_id": 99}
    # Act
    response = client.post("/api/games/101/actions/discard", json=discard_data)
    # Assert
    assert response.status_code == 403
    assert response.json()["detail"] == "Esa carta no está en tu mano, chorro."


# =================================================================
# --- TESTS PARA POST /api/games/{game_id}/actions/draw ---
# =================================================================


@pytest.mark.asyncio
async def test_draw_card_from_deck_success(game_manager_mocker: AsyncMock):
    """
    Prueba que el endpoint de robar funciona correctamente cuando la fuente es el MAZO.
    """
    # Arrange
    mock_card = Card(
        card_id=25,
        game_id=101,
        card_type=CardType.NOT_SO_FAST,
        location=CardLocation.IN_HAND,
    )
    game_manager_mocker.draw_card.return_value = DrawCardResponse(
        drawn_card=mock_card
    )

    # ¡¡¡EL JSON CORRECTO!!! Ahora incluimos la fuente.
    draw_data = {
        "player_id": 1,
        "game_id": 101,
        "source": "deck",  # <-- La clave del éxito
    }

    # Act
    response = client.post("/api/games/101/actions/draw", json=draw_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["drawn_card"]["card_type"] == "Not So Fast"
    game_manager_mocker.draw_card.assert_awaited_once()


@pytest.mark.asyncio
async def test_draw_card_from_draft_success(game_manager_mocker: AsyncMock):
    """
    Prueba que el endpoint de robar funciona correctamente cuando la fuente es el DRAFT.
    ¡Este es el test nuevo que nos da confianza en la nueva feature!
    """
    # Arrange
    mock_card = Card(
        card_id=99,
        game_id=101,
        card_type=CardType.DEAD_CARD_FOLLY,
        location=CardLocation.IN_HAND,
    )
    game_manager_mocker.draw_card.return_value = DrawCardResponse(
        drawn_card=mock_card
    )

    # El JSON para robar del draft, con el card_id específico
    draw_data = {
        "player_id": 1,
        "game_id": 101,
        "source": "draft",
        "card_id": 99,
    }

    # Act
    response = client.post("/api/games/101/actions/draw", json=draw_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["drawn_card"]["card_type"] == "Dead card folly"
    game_manager_mocker.draw_card.assert_awaited_once()


@pytest.mark.asyncio
async def test_draw_card_not_your_turn_returns_403(
    game_manager_mocker: AsyncMock,
):
    # Arrange
    game_manager_mocker.draw_card.side_effect = NotYourTurn(
        detail="No es tu turno, ansioso."
    )

    # También actualizamos este test para que mande un body válido
    draw_data = {
        "player_id": 2,
        "game_id": 101,
        "source": "deck",  # La fuente da igual, va a fallar antes
    }

    # Act
    response = client.post("/api/games/101/actions/draw", json=draw_data)

    # Assert
    assert response.status_code == 403
    assert response.json()["detail"] == "No es tu turno, ansioso."


# =================================================================
# --- TESTS PARA GET /api/games/{game_id}/size_deck ---
# =================================================================


def test_get_size_deck_success(game_manager_mocker: AsyncMock):
    """
    Prueba que el endpoint devuelve correctamente el tamaño del mazo de robo.
    """
    # Arrange
    game_manager_mocker.get_size_deck.return_value = ConsultDeckSizeResponse(
        size_deck=42
    )
    
    # Act
    response = client.get("/api/games/101/size_deck")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["size_deck"] == 42
    game_manager_mocker.get_size_deck.assert_called_once_with(101)


def test_get_size_deck_game_not_found_returns_404(
    game_manager_mocker: AsyncMock,
):
    """
    Prueba que el endpoint devuelve 404 cuando la partida no existe.
    """
    # Arrange
    game_manager_mocker.get_size_deck.side_effect = GameNotFound(
        detail="La partida 999 no existe."
    )
    
    # Act
    response = client.get("/api/games/999/size_deck")
    
    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "La partida 999 no existe."
    game_manager_mocker.get_size_deck.assert_called_once_with(999)


def test_get_size_deck_empty_deck(game_manager_mocker: AsyncMock):
    """
    Prueba que el endpoint maneja correctamente el caso de un mazo vacío.
    """
    # Arrange
    game_manager_mocker.get_size_deck.return_value = ConsultDeckSizeResponse(
        size_deck=0
    )
    
    # Act
    response = client.get("/api/games/101/size_deck")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["size_deck"] == 0
    game_manager_mocker.get_size_deck.assert_called_once_with(101)
