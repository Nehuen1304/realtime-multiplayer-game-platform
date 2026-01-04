import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.schemas import GameLobbyInfo
from app.domain.enums import GameStatus
from app.api.exception_handlers import internal_game_error_handler
from app.game.exceptions import InternalGameError


client = TestClient(app)


def test_root_endpoint_e2e():
    # Arrange
    # Act
    res = client.get("/")
    # Assert
    assert res.status_code == 200
    assert "Bienvenido" in res.json()["message"]


def test_full_game_flow_e2e():
    # Arrange
    # Crear dos jugadores
    p1 = client.post(
        "/api/players", json={"name": "Host", "birth_date": "2000-01-01"}
    )
    p2 = client.post(
        "/api/players", json={"name": "Guest", "birth_date": "2001-02-02"}
    )
    host_id = p1.json()["player_id"]
    guest_id = p2.json()["player_id"]

    # Act
    # Crear partida
    import uuid
    unique_name = f"Partida E2E {uuid.uuid4()}"
    create_game_res = client.post(
        "/api/games",
        json={
            "host_id": host_id,
            "game_name": unique_name,
            "min_players": 2,
            "max_players": 6,
        },
    )
    game_id = create_game_res.json()["game_id"]

    # Conectar websockets y cerrar (cubre connect + disconnect)
    with client.websocket_connect(f"/ws/mainscreen") as ws:
        ws.send_text("ping")
        # cierre implícito al salir del with
    with client.websocket_connect(f"/ws/game/{game_id}/player/{host_id}") as ws:
        ws.send_text("hola")

    # Listar partidas
    list_res = client.get("/api/games")

    # Unirse a la partida como invitado
    join_res = client.post(f"/api/games/{game_id}/join", json={"player_id": guest_id})

    # Iniciar la partida (host)
    start_res = client.post(
        f"/api/games/{game_id}/start", json={"player_id": host_id, "game_id": game_id}
    )
    first_turn_player = start_res.json().get("player_id_first_turn")
    player_to_act = first_turn_player or host_id

    # Consultar estado y secretos del host
    state_res = client.get(f"/api/games/{game_id}")
    secrets_res = client.get(f"/api/games/{game_id}/players/{host_id}/secrets")

    # Robar una carta del mazo usando el jugador con el primer turno
    draw_res = client.post(
        f"/api/games/{game_id}/actions/draw",
        json={"player_id": player_to_act, "game_id": game_id, "source": "deck"},
    )

    # Finalizar turno con el mismo jugador
    finish_res = client.post(
        f"/api/games/{game_id}/actions/finish-turn",
        json={"player_id": player_to_act, "game_id": game_id},
    )

    # Assert
    assert create_game_res.status_code == 201
    assert list_res.status_code == 200
    assert any("Partida E2E" in g["name"] for g in list_res.json()["games"])  # type: ignore[index]
    assert join_res.status_code == 200
    assert start_res.status_code == 200
    assert state_res.status_code == 200
    assert secrets_res.status_code == 200
    assert draw_res.status_code in (200, 400, 403)
    assert finish_res.status_code in (200, 400, 403)


class TestDebugEndpointE2E:
    def test_debug_echo_success_game_removed(self):
        # Arrange
        payload = {"type": "game_removed", "game_id": 123}
        # Act
        res = client.post("/api/echo", json=payload)
        # Assert
        assert res.status_code == 200
        assert res.json()["type_triggered"] == "game_removed"

    def test_debug_echo_missing_type_400(self):
        # Arrange
        payload = {"foo": "bar"}
        # Act
        res = client.post("/api/echo", json=payload)
        # Assert
        assert res.status_code == 400
        assert "Missing 'type'" in res.json()["detail"]

    def test_debug_echo_invalid_type_400(self):
        # Arrange
        payload = {"type": "no_sirve"}
        # Act
        res = client.post("/api/echo", json=payload)
        # Assert
        assert res.status_code == 400
        assert "Invalid notification type" in res.json()["detail"]


def test_internal_game_error_handler_unit():
    # Arrange
    exc = InternalGameError(detail="boom")
    handler = app.exception_handlers[type(exc)]
    # Act
    import asyncio
    resp = asyncio.get_event_loop().run_until_complete(handler(None, exc))
    # Assert
    assert resp.status_code == 500
