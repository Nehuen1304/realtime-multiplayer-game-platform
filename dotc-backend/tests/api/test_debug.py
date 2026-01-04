import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.main import app
from app.api.endpoints import debug as debug_module
from app.game.helpers.notificators import Notificator
from app.dependencies.dependencies import get_notificator

client = TestClient(app)


def override_notificator():
    return AsyncMock(spec=Notificator)


@pytest.fixture(autouse=True)
def _override_notifier():
    app.dependency_overrides[get_notificator] = override_notificator
    yield
    app.dependency_overrides.pop(get_notificator, None)


def test_debug_missing_type_returns_400():
    resp = client.post("/api/echo", json={})
    assert resp.status_code == 400
    assert "Missing 'type'" in resp.json()["detail"]


def test_debug_invalid_type_returns_400():
    resp = client.post("/api/echo", json={"type": "not_a_valid_type"})
    assert resp.status_code == 400
    assert "Invalid notification type" in resp.json()["detail"]


def test_debug_no_handler_configured(monkeypatch):
    # Make the handler mapping empty to force the 'no handler configured' branch
    monkeypatch.setattr(debug_module, "NOTIFICATION_HANDLERS", {})
    resp = client.post("/api/echo", json={"type": "game_created"})
    assert resp.status_code == 400
    assert "No handler configured" in resp.json()["detail"]


def test_debug_key_error_missing_required_field(monkeypatch):
    # Use real handlers; provide missing fields for a known type to trigger KeyError
    # CARD_PLAYED expects several keys; we only provide the type
    resp = client.post("/api/echo", json={"type": "card_played"})
    assert resp.status_code == 400
    assert "Missing required field" in resp.json()["detail"]


def test_debug_internal_error_returns_500(monkeypatch):
    async def boom_handler(n: Notificator, d: dict):
        raise Exception("boom")

    monkeypatch.setitem(
        debug_module.NOTIFICATION_HANDLERS,
        debug_module.NotificationType.GAME_CREATED,
        boom_handler,
    )

    resp = client.post("/api/echo", json={"type": "game_created", "game": {"id": 1}})
    assert resp.status_code == 500
    assert "Internal error while triggering notification" in resp.json()["detail"]
