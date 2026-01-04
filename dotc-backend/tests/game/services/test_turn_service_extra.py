import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock

from app.game.services.turn_service import TurnService
from app.api.schemas import DrawCardRequest, DrawSource, PlayerActionRequest
from app.domain.models import Card, PlayerInGame, PlayerInfo, Game
from app.domain.enums import CardLocation, CardType, GameStatus, ResponseStatus, GameActionState, Avatar
from app.game.exceptions import InvalidAction, InternalGameError


@pytest.mark.asyncio
async def test_draw_card_from_discard_success(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
):
    game_id = 101
    player_id = 1
    discard_card = Card(
        card_id=55,
        game_id=game_id,
        card_type=CardType.MISS_MARPLE,
        location=CardLocation.DISCARD_PILE,
    )
    game = Game(
        id=game_id,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(
            player_id=player_id,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
        discard_pile=[discard_card],
        action_state=GameActionState.AWAITING_SELECTION_FOR_CARD,
        deck=[Card(card_id=999, game_id=game_id, card_type=CardType.NOT_SO_FAST, location=CardLocation.DRAW_PILE)],
    )

    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_player_hand.return_value = []
    mock_commands.update_card_location.return_value = ResponseStatus.OK

    req = DrawCardRequest(game_id=game_id, player_id=player_id, source=DrawSource.DISCARD, card_id=55)
    resp = await turn_service.draw_card(req)

    assert resp.drawn_card.card_id == 55
    mock_commands.clear_game_action_state.assert_called_once_with(game_id=game_id)


@pytest.mark.asyncio
async def test_draw_card_from_draft_refill_none_when_deck_empty(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
):
    game_id = 202
    player_id = 1
    draft_card = Card(
        card_id=77,
        game_id=game_id,
        card_type=CardType.PARKER_PYNE,
        location=CardLocation.DRAFT,
    )
    game = Game(
        id=game_id,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(
            player_id=player_id,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
        draft=[draft_card],
        deck=[],
    )
    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_player_hand.return_value = []
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_murderer_id.return_value = 2
    mock_queries.get_accomplice_id.return_value = 3
    mock_commands.delete_game.return_value = ResponseStatus.OK

    req = DrawCardRequest(game_id=game_id, player_id=player_id, source=DrawSource.DRAFT, card_id=77)
    await turn_service.draw_card(req)

    mock_notificator.notify_draft_updated.assert_awaited_once_with(game_id, 77, None)
    mock_notificator.notify_murderer_wins.assert_awaited_once()
    mock_commands.delete_game.assert_called_once()
    mock_notificator.notify_game_removed.assert_awaited_once()


@pytest.mark.asyncio
async def test_finish_turn_raises_if_hand_less_than_six(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
):
    game_id = 303
    player_id = 1
    game = Game(
        id=game_id,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(
            player_id=player_id,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
    )
    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_player_hand.return_value = [Mock()] * 5

    req = PlayerActionRequest(game_id=game_id, player_id=player_id)
    with pytest.raises(InvalidAction):
        await turn_service.finish_turn(req)


def test_assign_next_turn_errors(
    turn_service: TurnService,
    mock_queries: Mock,
    mock_turn_utils: Mock,
    mock_commands: Mock,
):
    # No players
    mock_queries.get_players_in_game.return_value = []
    with pytest.raises(InternalGameError):
        turn_service._assign_next_turn(1)

    # Current turn None
    p = PlayerInGame(
        player_id=1,
        player_name="p",
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
        turn_order=1,
    )
    mock_queries.get_players_in_game.return_value = [p]
    mock_turn_utils.sort_players_by_turn_order.return_value = [p]
    mock_queries.get_current_turn.return_value = None
    with pytest.raises(InternalGameError):
        turn_service._assign_next_turn(1)

    # set_current_turn fails
    mock_queries.get_current_turn.return_value = 1
    mock_commands.set_current_turn.return_value = ResponseStatus.ERROR
    with pytest.raises(InternalGameError):
        turn_service._assign_next_turn(1)


@pytest.mark.asyncio
async def test_play_card_add_to_existing_set_with_ariadne(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_executor: AsyncMock,
    mock_notificator: AsyncMock,
):
    game_id, player_id = 1, 10
    ariadne = Card(card_id=5, game_id=game_id, card_type=CardType.ARIADNE_OLIVER, location=CardLocation.IN_HAND)
    existing_card = Card(card_id=6, game_id=game_id, card_type=CardType.TOMMY_BERESFORD, location=CardLocation.PLAYED)
    existing_card.player_id = 99

    mock_validator.validate_player_has_cards.return_value = [ariadne]
    mock_queries.get_set.return_value = [existing_card]
    mock_executor.classify_effect.return_value = object()
    mock_executor.execute_effect.return_value = ResponseStatus.OK
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_card.return_value = ariadne
    mock_commands.create_pending_action.return_value = ResponseStatus.OK
    mock_commands.set_game_action_state.return_value = ResponseStatus.OK

    from app.api.schemas import PlayCardRequest, PlayCardActionType

    req = PlayCardRequest(
        action_type=PlayCardActionType.ADD_TO_EXISTING_SET,
        game_id=game_id,
        player_id=player_id,
        card_ids=[5],
        target_set_id=1,
    )

    await turn_service.play_card(req)

    # Ariadne Oliver is cancellable, enters PENDING_NSF
    mock_commands.create_pending_action.assert_called_once()
    mock_commands.set_game_action_state.assert_called_once()
    mock_notificator.notify_cards_played.assert_awaited_once()
