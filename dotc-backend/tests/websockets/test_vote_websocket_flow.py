import pytest
from unittest.mock import AsyncMock

from app.game.helpers.notificators import Notificator
from app.websockets.interfaces import IConnectionManager
from app.websockets.protocol.details import VoteStartedDetails, VoteEndedDetails
from app.websockets.protocol.messages import WSMessage


@pytest.mark.asyncio
async def test_notify_players_to_vote_sends_vote_started():
    manager = AsyncMock(spec=IConnectionManager)
    n = Notificator(ws_manager=manager)

    await n.notify_players_to_vote(game_id=77)

    manager.broadcast_to_game.assert_awaited_once()
    args, kwargs = manager.broadcast_to_game.await_args
    assert kwargs["game_id"] == 77
    assert isinstance(kwargs["message"], WSMessage)
    assert isinstance(kwargs["message"].details, VoteStartedDetails)


@pytest.mark.asyncio
async def test_notify_vote_result_sends_vote_ended_winner():
    manager = AsyncMock(spec=IConnectionManager)
    n = Notificator(ws_manager=manager)

    await n.notify_vote_result(game_id=55, most_voted_id=9, was_tie=False)

    manager.broadcast_to_game.assert_awaited_once()
    args, kwargs = manager.broadcast_to_game.await_args
    assert kwargs["game_id"] == 55
    message = kwargs["message"]
    assert isinstance(message, WSMessage)
    assert isinstance(message.details, VoteEndedDetails)
    assert message.details.most_voted_player_id == 9
    assert message.details.tie is False


@pytest.mark.asyncio
async def test_notify_vote_result_sends_vote_ended_tie():
    manager = AsyncMock(spec=IConnectionManager)
    n = Notificator(ws_manager=manager)

    await n.notify_vote_result(game_id=11, most_voted_id=None, was_tie=True)

    manager.broadcast_to_game.assert_awaited_once()
    args, kwargs = manager.broadcast_to_game.await_args
    assert kwargs["game_id"] == 11
    message = kwargs["message"]
    assert isinstance(message, WSMessage)
    assert isinstance(message.details, VoteEndedDetails)
    assert message.details.most_voted_player_id is None
    assert message.details.tie is True
