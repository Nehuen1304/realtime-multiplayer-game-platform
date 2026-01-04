import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.main import app
from app.api.schemas import LeaveGameResponse, PlayerActionRequest

client = TestClient(app)


def test_leave_game_success(game_manager_mocker: AsyncMock):
    game_manager_mocker.leave_game.return_value = LeaveGameResponse(detail="ok")
    data = {"player_id": 1, "game_id": 123}
    resp = client.post("/api/games/123/leave", json=data)
    assert resp.status_code == 200
    game_manager_mocker.leave_game.assert_awaited_once()


def test_leave_game_forbidden(game_manager_mocker: AsyncMock):
    from app.game.exceptions import InvalidAction

    game_manager_mocker.leave_game.side_effect = InvalidAction(detail="boom")
    data = {"player_id": 1, "game_id": 123}
    resp = client.post("/api/games/123/leave", json=data)
    assert resp.status_code == 400
