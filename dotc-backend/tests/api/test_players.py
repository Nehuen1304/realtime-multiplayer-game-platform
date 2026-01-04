import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.main import app
from app.api.schemas import CreatePlayerResponse
from app.game.exceptions import InvalidAction

client = TestClient(app)

# =================================================================
# --- TESTS PARA POST /api/players (Crear Jugador) ---
# =================================================================


def test_create_player_endpoint_success(game_manager_mocker: AsyncMock):
    """
    Prueba el 'happy path' del endpoint POST /players.
    """
    # --- Arrange ---
    # La fixture ya nos dio el mock, solo lo configuramos.
    game_manager_mocker.create_player.return_value = CreatePlayerResponse(
        player_id=123
    )
    player_data = {"name": "Lautaro", "birth_date": "2000-01-01"}

    # --- Act ---
    response = client.post("/api/players", json=player_data)

    # --- Assert ---
    assert response.status_code == 201
    assert response.json() == {"player_id": 123}
    game_manager_mocker.create_player.assert_called_once()


def test_create_player_endpoint_empty_name_returns_400(
    game_manager_mocker: AsyncMock,
):
    """
    Prueba que si el servicio lanza InvalidAction, el endpoint devuelve 400.
    """
    # --- Arrange ---
    game_manager_mocker.create_player.side_effect = InvalidAction(
        detail="El nombre no puede ser vacío."
    )
    player_data = {"name": "", "birth_date": "2000-01-01"}

    # --- Act ---
    response = client.post("/api/players", json=player_data)

    # --- Assert ---
    assert response.status_code == 400
    assert response.json() == {
        "detail": "El nombre no puede ser vacío."
    }
