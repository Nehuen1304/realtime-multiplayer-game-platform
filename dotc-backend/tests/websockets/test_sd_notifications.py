import pytest
from unittest.mock import AsyncMock

from app.game.helpers.notificators import Notificator
from app.websockets.interfaces import IConnectionManager
from app.websockets.protocol.messages import WSMessage


@pytest.mark.asyncio
async def test_notify_social_disgrace_applied_broadcasts():
    manager = AsyncMock(spec=IConnectionManager)
    n = Notificator(ws_manager=manager)

    await n.notify_social_disgrace_applied(game_id=99, player_id=5)

    manager.broadcast_to_game.assert_awaited_once()
    args, kwargs = manager.broadcast_to_game.await_args
    assert kwargs["game_id"] == 99
    assert isinstance(kwargs["message"], WSMessage)


@pytest.mark.asyncio
async def test_notify_social_disgrace_removed_broadcasts():
    manager = AsyncMock(spec=IConnectionManager)
    n = Notificator(ws_manager=manager)

    await n.notify_social_disgrace_removed(game_id=99, player_id=5)

    manager.broadcast_to_game.assert_awaited_once()
    args, kwargs = manager.broadcast_to_game.await_args
    assert kwargs["game_id"] == 99
    assert isinstance(kwargs["message"], WSMessage)
