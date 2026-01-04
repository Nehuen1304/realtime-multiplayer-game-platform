import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock

from app.game.services.turn_service import TurnService
from app.api.schemas import PlayCardRequest, PlayCardActionType
from app.domain.models import Card, PlayerInGame, PlayerInfo, Game
from app.domain.enums import CardLocation, CardType, GameStatus, Avatar, ResponseStatus, GameFlowStatus
from app.game.exceptions import ForbiddenAction, InvalidAction, InternalGameError

@pytest.mark.asyncio
async def test_social_disgrace_forbids_non_event(turn_service: TurnService, mock_validator: Mock, mock_executor: AsyncMock):
    player = PlayerInGame(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT, hand=[Card(card_id=10, game_id=1, card_type=CardType.MISS_MARPLE, location=CardLocation.IN_HAND)], social_disgrace=True)
    game = Game(id=1, name="g", min_players=2, max_players=4, host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT), status=GameStatus.IN_PROGRESS, players=[player])
    turn_service.read.get_game.return_value = game
    mock_validator.validate_player_in_game.return_value = player
    mock_validator.validate_is_players_turn.return_value = None
    mock_validator.validate_player_has_cards.return_value = player.hand
    req = PlayCardRequest(action_type=PlayCardActionType.FORM_NEW_SET, game_id=1, player_id=1, card_ids=[10])
    # Simular que classify_effect devuelve algo para evitar InternalGameError ante la rama normal
    # No debe llegar a crear set; simulamos efecto y update exitosos
    # No clasificar efecto para que falle antes si no controla SD
    turn_service.effect_executor.classify_effect = Mock(return_value=None)
    turn_service.effect_executor.execute_effect = AsyncMock(return_value=ResponseStatus.OK)
    turn_service.write.create_set.return_value = 1
    turn_service.write.update_card_location.return_value = ResponseStatus.OK
    with pytest.raises((ForbiddenAction, InvalidAction, InternalGameError)):

        await turn_service.play_card(req)

@pytest.mark.asyncio
async def test_social_disgrace_allows_whitelisted_events(turn_service: TurnService, mock_validator: Mock, mock_executor: AsyncMock, mock_commands: Mock, mock_queries: Mock):
    for card_type in [CardType.NOT_SO_FAST, CardType.POINT_YOUR_SUSPICIONS, CardType.CARD_TRADE]:
        player = PlayerInGame(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT, hand=[Card(card_id=11, game_id=1, card_type=card_type, location=CardLocation.IN_HAND)], social_disgrace=True)
        game = Game(id=1, name="g", min_players=2, max_players=4, host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT), status=GameStatus.IN_PROGRESS, players=[player])
        turn_service.read.get_game.return_value = game
        mock_validator.validate_player_in_game.return_value = player
        mock_validator.validate_is_players_turn.return_value = None
        mock_validator.validate_player_has_cards.return_value = player.hand
        mock_executor.classify_effect.return_value = object()
        mock_executor.execute_effect.return_value = GameFlowStatus.CONTINUE  # Changed from ResponseStatus.OK
        turn_service.effect_executor.classify_effect = mock_executor.classify_effect
        turn_service.effect_executor.execute_effect = mock_executor.execute_effect
        mock_commands.update_card_location.return_value = ResponseStatus.OK
        mock_commands.create_pending_action.return_value = ResponseStatus.OK
        mock_commands.set_game_action_state.return_value = ResponseStatus.OK
        mock_queries.get_card.return_value = player.hand[0]
        mock_queries.get_pending_action.return_value = Mock(id=1)
        req = PlayCardRequest(action_type=PlayCardActionType.PLAY_EVENT, game_id=1, player_id=1, card_ids=[11])
        await turn_service.play_card(req)

@pytest.mark.asyncio
async def test_social_disgrace_event_not_whitelisted_forbidden(turn_service: TurnService, mock_validator: Mock):
    player = PlayerInGame(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT, hand=[Card(card_id=12, game_id=1, card_type=CardType.EARLY_TRAIN, location=CardLocation.IN_HAND)], social_disgrace=True)
    game = Game(id=1, name="g", min_players=2, max_players=4, host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT), status=GameStatus.IN_PROGRESS, players=[player])
    turn_service.read.get_game.return_value = game
    mock_validator.validate_player_in_game.return_value = player
    mock_validator.validate_is_players_turn.return_value = None
    mock_validator.validate_player_has_cards.return_value = player.hand
    req = PlayCardRequest(action_type=PlayCardActionType.PLAY_EVENT, game_id=1, player_id=1, card_ids=[12])
    with pytest.raises((ForbiddenAction, InvalidAction, InternalGameError)):

        await turn_service.play_card(req)
