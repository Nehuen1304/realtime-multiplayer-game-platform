import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from app.api.router import api_router
from app.dependencies.dependencies import get_game_state_service
from app.game.services.game_state_service import GameStateService
from app.domain.models import PlayerInGame


class DummyGameStateService:
    def __init__(self, players):
        self._players = players

    async def get_sorted_players(self, game_id: int):
        return self._players


@pytest.fixture()
def app_with_override():
    app = FastAPI()
    app.include_router(api_router)
    yield app


def _make_player(pid, order):
    p = MagicMock(spec=PlayerInGame)
    p.player_id = pid
    p.turn_order = order
    return p


# Unit test for GameStateService.get_sorted_players (with TurnUtils)
@pytest.mark.asyncio
async def test_service_sorts_players_by_turn_order():
    # Arrange: create unsorted players
    players = [_make_player(3, 2), _make_player(1, 0), _make_player(2, 1)]

    # Mock dependencies
    mock_queries = MagicMock()
    mock_queries.get_players_in_game.return_value = players
    mock_validator = MagicMock()
    mock_validator.validate_game_exists.return_value = MagicMock()
    # Use a dummy TurnUtils that sorts by turn_order for this unit test
    class _DummyTurnUtils:
        def sort_players_by_turn_order(self, players):
            return sorted(players, key=lambda p: getattr(p, "turn_order", 0))

    service = GameStateService(
        queries=mock_queries,
        commands=MagicMock(),
        validator=mock_validator,
        notifier=MagicMock(),
        turn_utils=_DummyTurnUtils(),
    )

    # Act
    sorted_players = await service.get_sorted_players(game_id=42)

    # Assert: order is by turn_order: 0,1,2 -> player_ids 1,2,3
    assert [p.player_id for p in sorted_players] == [1, 2, 3]
    mock_validator.validate_game_exists.assert_called_once_with(42)
    mock_queries.get_players_in_game.assert_called_once_with(42)


# End-to-End test for the new endpoint
@pytest.mark.asyncio
async def test_api_get_sorted_players_endpoint_returns_sorted(app_with_override, monkeypatch, anyio_backend):
    # Arrange: prepare sorted players fixture
    sorted_players = [_make_player(1, 0), _make_player(2, 1), _make_player(3, 2)]

    # Override dependency to return our dummy service
    def override_get_game_state_service():
        return DummyGameStateService(players=sorted_players)

    # Override directly via app dependency overrides (cleaner than monkeypatch attr)
    app_with_override.dependency_overrides[get_game_state_service] = override_get_game_state_service

    client = TestClient(app_with_override)

    # Act
    resp = client.get("/games/1/players/sorted")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    # Should preserve order [1,2,3]
    assert [item.get("player_id") for item in data] == [1, 2, 3]
