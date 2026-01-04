import pytest
from unittest.mock import AsyncMock

from app.game.helpers.notificators import Notificator
from app.websockets.interfaces import IConnectionManager
from app.domain.models import Card
from app.domain.enums import CardLocation, CardType
from app.websockets.protocol.messages import WSMessage


@pytest.mark.asyncio
async def test_notify_set_stolen_broadcasts():
    manager = AsyncMock(spec=IConnectionManager)
    n = Notificator(ws_manager=manager)

    dummy_cards = [
        Card(card_id=1, game_id=10, card_type=CardType.NOT_SO_FAST, location=CardLocation.PLAYED)
    ]

    await n.notify_set_stolen(game_id=10, thief_id=2, victim_id=3, set_id=7, set_cards=dummy_cards)

    manager.broadcast_to_game.assert_awaited_once()
    args, kwargs = manager.broadcast_to_game.await_args
    assert kwargs["game_id"] == 10
    assert isinstance(kwargs["message"], WSMessage)


@pytest.mark.asyncio
async def test_notify_player_to_choose_card_private_message():
    manager = AsyncMock(spec=IConnectionManager)
    n = Notificator(ws_manager=manager)

    cards = [Card(card_id=2, game_id=10, card_type=CardType.HERCULE_POIROT, location=CardLocation.DISCARD_PILE)]

    await n.notify_player_to_choose_card(game_id=10, player_id=5, cards=cards)

    manager.send_to_player.assert_awaited_once()
    args, kwargs = manager.send_to_player.await_args
    assert kwargs["game_id"] == 10 and kwargs["player_id"] == 5
    assert isinstance(kwargs["message"], WSMessage)


@pytest.mark.asyncio
async def test_notify_cards_nsf_discarded_broadcasts():
    manager = AsyncMock(spec=IConnectionManager)
    n = Notificator(ws_manager=manager)

    cards = [Card(card_id=3, game_id=10, card_type=CardType.NOT_SO_FAST, location=CardLocation.DISCARD_PILE)]

    await n.notify_cards_NSF_discarded(
        game_id=10, source_player_id=1, target_player_id=2, discarded_cards=cards
    )

    manager.broadcast_to_game.assert_awaited_once()
    args, kwargs = manager.broadcast_to_game.await_args
    assert kwargs["game_id"] == 10
    assert isinstance(kwargs["message"], WSMessage)
