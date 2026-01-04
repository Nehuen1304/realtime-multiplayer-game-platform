import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock

from app.game.services.turn_service import TurnService
from app.api.schemas import DrawCardRequest, DrawSource, DiscardCardRequest, PlayCardRequest, PlayCardActionType, RevealSecretRequest, PlayerActionRequest
from app.domain.models import Card, PlayerInGame, PlayerInfo, Game, SecretCard
from app.domain.enums import CardLocation, CardType, GameStatus, ResponseStatus, GameActionState, Avatar, PlayerRole
from app.game.exceptions import InvalidAction, CardNotFound, InternalGameError, ResourceNotFound


@pytest.mark.asyncio
async def test_draw_from_discard_wrong_state_raises_invalid_action(turn_service: TurnService, mock_validator: Mock, mock_queries: Mock):
    game = Game(
        id=1,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        discard_pile=[Card(card_id=9, game_id=1, card_type=CardType.PARKER_PYNE, location=CardLocation.DISCARD_PILE)],
        action_state=None,
    )
    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_player_hand.return_value = []
    req = DrawCardRequest(game_id=1, player_id=1, source=DrawSource.DISCARD, card_id=9)
    with pytest.raises(InvalidAction):
        await turn_service.draw_card(req)


@pytest.mark.asyncio
async def test_draw_from_discard_missing_card_id(turn_service: TurnService, mock_validator: Mock, mock_queries: Mock):
    game = Game(
        id=1,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        discard_pile=[Card(card_id=9, game_id=1, card_type=CardType.PARKER_PYNE, location=CardLocation.DISCARD_PILE)],
        action_state=GameActionState.AWAITING_SELECTION_FOR_CARD,
    )
    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_player_hand.return_value = []
    req = DrawCardRequest(game_id=1, player_id=1, source=DrawSource.DISCARD)
    with pytest.raises(InvalidAction):
        await turn_service.draw_card(req)


@pytest.mark.asyncio
async def test_draw_from_discard_card_not_found(turn_service: TurnService, mock_validator: Mock, mock_queries: Mock):
    game = Game(
        id=1,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        discard_pile=[],
        action_state=GameActionState.AWAITING_SELECTION_FOR_CARD,
    )
    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_player_hand.return_value = []
    req = DrawCardRequest(game_id=1, player_id=1, source=DrawSource.DISCARD, card_id=9)
    with pytest.raises(CardNotFound):
        await turn_service.draw_card(req)


@pytest.mark.asyncio
async def test_draw_from_draft_missing_card_id(turn_service: TurnService, mock_validator: Mock, mock_queries: Mock):
    game = Game(
        id=1,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        draft=[Card(card_id=1, game_id=1, card_type=CardType.TOMMY_BERESFORD, location=CardLocation.DRAFT)],
    )
    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_player_hand.return_value = []
    req = DrawCardRequest(game_id=1, player_id=1, source=DrawSource.DRAFT)
    with pytest.raises(InvalidAction):
        await turn_service.draw_card(req)


@pytest.mark.asyncio
async def test_discard_card_db_fail(turn_service: TurnService, mock_validator: Mock, mock_commands: Mock):
    player_instance = PlayerInGame(
        player_id=1,
        player_name="P",
        player_birth_date=date(2000,1,1),
        player_avatar=Avatar.DEFAULT,
        hand=[Card(card_id=10, game_id=1, card_type=CardType.PARKER_PYNE, location=CardLocation.IN_HAND)],
    )
    mock_validator.validate_player_in_game.return_value = player_instance
    mock_commands.update_card_location.return_value = ResponseStatus.ERROR
    req = DiscardCardRequest(game_id=1, player_id=1, card_id=10)
    with pytest.raises(InternalGameError):
        await turn_service.discard_card(req)


@pytest.mark.asyncio
async def test_discard_card_inconsistent_hand_raises_internal(turn_service: TurnService, mock_validator: Mock, mock_commands: Mock):
    player_instance = PlayerInGame(
        player_id=1,
        player_name="P",
        player_birth_date=date(2000,1,1),
        player_avatar=Avatar.DEFAULT,
        hand=[],
    )
    mock_validator.validate_player_in_game.return_value = player_instance
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    req = DiscardCardRequest(game_id=1, player_id=1, card_id=10)
    with pytest.raises(InternalGameError):
        await turn_service.discard_card(req)


@pytest.mark.asyncio
async def test_discard_card_early_train_triggers_effect(turn_service: TurnService, mock_validator: Mock, mock_commands: Mock, mock_executor: AsyncMock):
    card = Card(card_id=5, game_id=1, card_type=CardType.EARLY_TRAIN, location=CardLocation.IN_HAND, player_id=1)
    player_instance = PlayerInGame(
        player_id=1,
        player_name="P",
        player_birth_date=date(2000,1,1),
        player_avatar=Avatar.DEFAULT,
        hand=[card],
    )
    mock_validator.validate_player_in_game.return_value = player_instance
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    req = DiscardCardRequest(game_id=1, player_id=1, card_id=5)
    await turn_service.discard_card(req)
    mock_executor.execute_effect.assert_awaited_once()


@pytest.mark.asyncio
async def test_play_card_invalid_effect_class(turn_service: TurnService, mock_validator: Mock, mock_executor: AsyncMock):
    mock_validator.validate_player_has_cards.return_value = [Card(card_id=1, game_id=1, card_type=CardType.MISS_MARPLE, location=CardLocation.IN_HAND)]
    mock_executor.classify_effect.return_value = None
    # Añadimos estado de juego mínimo para cubrir social_disgrace logic
    turn_service.read.get_game.return_value = Game(id=1, name="g", min_players=2, max_players=4, host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT), status=GameStatus.IN_PROGRESS, players=[PlayerInGame(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT)])
    req = PlayCardRequest(action_type=PlayCardActionType.PLAY_EVENT, game_id=1, player_id=1, card_ids=[1])
    with pytest.raises(InvalidAction):
        await turn_service.play_card(req)


@pytest.mark.asyncio
async def test_play_card_add_to_existing_set_missing_target(turn_service: TurnService, mock_validator: Mock):
    mock_validator.validate_player_has_cards.return_value = [Card(card_id=1, game_id=1, card_type=CardType.MISS_MARPLE, location=CardLocation.IN_HAND)]
    req = PlayCardRequest(action_type=PlayCardActionType.ADD_TO_EXISTING_SET, game_id=1, player_id=1, card_ids=[1])
    with pytest.raises(InvalidAction):
        await turn_service.play_card(req)


@pytest.mark.asyncio
async def test_play_card_add_to_existing_set_not_found(turn_service: TurnService, mock_validator: Mock, mock_queries: Mock, mock_executor: AsyncMock):
    mock_validator.validate_player_has_cards.return_value = [Card(card_id=1, game_id=1, card_type=CardType.MISS_MARPLE, location=CardLocation.IN_HAND)]
    mock_queries.get_set.return_value = []
    req = PlayCardRequest(action_type=PlayCardActionType.ADD_TO_EXISTING_SET, game_id=1, player_id=1, card_ids=[1], target_set_id=99)
    with pytest.raises(ResourceNotFound):
        await turn_service.play_card(req)


@pytest.mark.asyncio
async def test_play_card_play_event_multiple_cards_invalid(turn_service: TurnService, mock_validator: Mock):
    mock_validator.validate_player_has_cards.return_value = [
        Card(card_id=1, game_id=1, card_type=CardType.MISS_MARPLE, location=CardLocation.IN_HAND),
        Card(card_id=2, game_id=1, card_type=CardType.TOMMY_BERESFORD, location=CardLocation.IN_HAND),
    ]
    req = PlayCardRequest(action_type=PlayCardActionType.PLAY_EVENT, game_id=1, player_id=1, card_ids=[1,2])
    with pytest.raises(InvalidAction):
        await turn_service.play_card(req)


@pytest.mark.asyncio
async def test_play_card_execute_effect_error_raises(turn_service: TurnService, mock_validator: Mock, mock_executor: AsyncMock):
    mock_validator.validate_player_has_cards.return_value = [Card(card_id=1, game_id=1, card_type=CardType.MISS_MARPLE, location=CardLocation.IN_HAND)]
    mock_executor.classify_effect.return_value = object()
    mock_executor.execute_effect.return_value = ResponseStatus.ERROR
    req = PlayCardRequest(action_type=PlayCardActionType.PLAY_EVENT, game_id=1, player_id=1, card_ids=[1])
    with pytest.raises(InternalGameError):
        await turn_service.play_card(req)


@pytest.mark.asyncio
async def test_play_event_update_db_fail_raises(turn_service: TurnService, mock_validator: Mock, mock_executor: AsyncMock, mock_commands: Mock):
    mock_validator.validate_player_has_cards.return_value = [Card(card_id=1, game_id=1, card_type=CardType.MISS_MARPLE, location=CardLocation.IN_HAND)]
    mock_executor.classify_effect.return_value = object()
    mock_executor.execute_effect.return_value = ResponseStatus.OK
    mock_commands.update_card_location.return_value = ResponseStatus.ERROR
    req = PlayCardRequest(action_type=PlayCardActionType.PLAY_EVENT, game_id=1, player_id=1, card_ids=[1])
    with pytest.raises(InternalGameError):
        await turn_service.play_card(req)


@pytest.mark.asyncio
async def test_play_event_updated_card_missing_raises(turn_service: TurnService, mock_validator: Mock, mock_executor: AsyncMock, mock_commands: Mock, mock_queries: Mock):
    # Ajuste: el flujo actual levanta CardNotFound si la carta inicial no se obtiene,
    # por lo que simulamos que la primera lectura existe y la segunda (post-update) falla.
    initial_card = Card(card_id=1, game_id=1, card_type=CardType.MISS_MARPLE, location=CardLocation.IN_HAND)
    mock_validator.validate_player_has_cards.return_value = [initial_card]
    mock_executor.classify_effect.return_value = object()
    mock_executor.execute_effect.return_value = ResponseStatus.OK
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    # Primera llamada (antes de jugar) retorna la carta; segunda (después de update) None
    mock_queries.get_card.side_effect = [initial_card, None]
    req = PlayCardRequest(action_type=PlayCardActionType.PLAY_EVENT, game_id=1, player_id=1, card_ids=[1])
    with pytest.raises(InternalGameError):
        await turn_service.play_card(req)


@pytest.mark.asyncio
async def test_reveal_secret_choice_resource_not_found(turn_service: TurnService, mock_validator: Mock, mock_commands: Mock, mock_queries: Mock):
    game = Game(
        id=1,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        action_state=GameActionState.AWAITING_REVEAL_FOR_CHOICE,
    )
    mock_validator.validate_game_exists.return_value = game
    mock_commands.reveal_secret_card.return_value = ResponseStatus.OK
    mock_queries.get_player_secrets.return_value = []
    req = RevealSecretRequest(game_id=1, player_id=1, secret_id=5)
    with pytest.raises(ResourceNotFound):
        await turn_service.reveal_secret(req)


@pytest.mark.asyncio
async def test_reveal_secret_steal_reveal_error(turn_service: TurnService, mock_validator: Mock, mock_commands: Mock):
    game = Game(
        id=1,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        action_state=GameActionState.AWAITING_REVEAL_FOR_STEAL,
        action_initiator_id=2,
    )
    mock_validator.validate_game_exists.return_value = game
    mock_commands.reveal_secret_card.return_value = ResponseStatus.ERROR
    req = RevealSecretRequest(game_id=1, player_id=1, secret_id=5)
    with pytest.raises(InternalGameError):
        await turn_service.reveal_secret(req)


@pytest.mark.asyncio
async def test_reveal_secret_steal_hide_error(turn_service: TurnService, mock_validator: Mock, mock_commands: Mock, mock_queries: Mock, mock_notificator: AsyncMock):
    game = Game(
        id=1,
        name="t",
        min_players=2,
        max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000,1,1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        action_state=GameActionState.AWAITING_REVEAL_FOR_STEAL,
        action_initiator_id=2,
    )
    mock_validator.validate_game_exists.return_value = game
    mock_commands.reveal_secret_card.side_effect = [ResponseStatus.OK, ResponseStatus.ERROR]
    mock_queries.get_player_secrets.return_value = [SecretCard(secret_id=5, game_id=1, player_id=1, role=PlayerRole.INNOCENT, is_revealed=True)]
    req = RevealSecretRequest(game_id=1, player_id=1, secret_id=5)
    with pytest.raises(InternalGameError):
        await turn_service.reveal_secret(req)
