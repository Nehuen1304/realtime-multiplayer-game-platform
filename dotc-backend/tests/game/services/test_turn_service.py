import pytest
from datetime import date
from unittest.mock import Mock, AsyncMock

from app.game.services.turn_service import TurnService
from app.api.schemas import (
    PlayerActionRequest,
    DiscardCardRequest,
    DrawCardRequest,
    DrawSource,
    PlayCardRequest,
    GeneralActionResponse,
    PlayCardActionType,
    RevealSecretRequest,
)
from app.domain.models import Card, PlayerInGame, PlayerInfo, Game, SecretCard, PendingAction

from app.domain.enums import (
    GameStatus,
    CardLocation,
    CardType,
    Avatar,
    ResponseStatus,
    PlayerRole,
    GameActionState,
    GameFlowStatus,
)
from app.game.exceptions import (
    NotYourTurn,
    InvalidAction,
    InternalGameError,
    CardNotFound,
    NotYourCard,
    ActionConflict,
)


@pytest.fixture
def turn_service(
    mock_queries: Mock,
    mock_commands: Mock,
    mock_validator: Mock,
    mock_notificator: AsyncMock,
    mock_executor: AsyncMock,
    mock_turn_utils: Mock,
) -> TurnService:
    """
    Creates an instance of TurnService with all its dependencies mocked.
    """
    return TurnService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
        effect_executor=mock_executor,
        turn_utils=mock_turn_utils,
    )


# =================================================================
# --- TESTS FOR draw_card ---
# =================================================================


@pytest.mark.asyncio
async def test_draw_card_from_deck_success(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
):
    """Tests the happy path of drawing a card FROM THE DECK."""
    card_to_draw = [Card(
        card_id=1,
        game_id=101,
        card_type=CardType.HERCULE_POIROT,
        location=CardLocation.DRAW_PILE,
    ),
    Card(
        card_id=2,
        game_id=101,
        card_type=CardType.ANOTHER_VICTIM,
        location=CardLocation.DRAW_PILE,
    )]
    game_instance = Game(
        id=101,
        name="Test",
        min_players=4,
        max_players=12,
        host=PlayerInfo(
            player_id=1,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
        deck=card_to_draw,
    )
    mock_validator.validate_game_exists.return_value = game_instance
    mock_queries.get_player_hand.return_value = []
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    request = DrawCardRequest(game_id=101, player_id=1, source=DrawSource.DECK)
    response = await turn_service.draw_card(request)

    assert response.drawn_card is not None
    assert response.drawn_card.card_id == 1
    mock_commands.update_card_location.assert_called_once_with(
        card_id=1, game_id=101, new_location=CardLocation.IN_HAND, owner_id=1
    )
    mock_notificator.notify_player_drew.assert_awaited_once()


@pytest.mark.asyncio
async def test_draw_card_from_deck_fails_if_deck_empty(
    turn_service: TurnService, mock_validator: Mock, mock_queries: Mock
):
    mock_validator.validate_game_exists.return_value = Game(
        id=101,
        name="Test",
        min_players=4,
        max_players=12,
        host=PlayerInfo(
            player_id=1,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
        deck=[],
    )
    mock_queries.get_player_hand.return_value = []
    mock_validator.validate_deck_has_cards.side_effect = InvalidAction(
        detail="No quedan cartas."
    )
    request = DrawCardRequest(game_id=101, player_id=1, source=DrawSource.DECK)
    with pytest.raises(InvalidAction, match="No quedan cartas."):
        await turn_service.draw_card(request)


@pytest.mark.asyncio
async def test_draw_card_from_draft_success(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_commands: Mock,
    mock_queries: Mock,
    mock_notificator: AsyncMock,
):
    card_in_draft = Card(
        card_id=99,
        game_id=101,
        card_type=CardType.NOT_SO_FAST,
        location=CardLocation.DRAFT,
    )
    card_in_deck = Card(
        card_id=100,
        game_id=101,
        card_type=CardType.ANOTHER_VICTIM,
        location=CardLocation.DRAW_PILE,
    )
    game_instance = Game(
        id=101,
        name="Test",
        min_players=4,
        max_players=12,
        host=PlayerInfo(
            player_id=1,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
        draft=[card_in_draft],
        deck=[card_in_deck],
    )
    mock_validator.validate_game_exists.return_value = game_instance
    mock_queries.get_player_hand.return_value = []
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    request = DrawCardRequest(
        game_id=101, player_id=1, source=DrawSource.DRAFT, card_id=99
    )
    response = await turn_service.draw_card(request)

    assert response.drawn_card is not None
    assert response.drawn_card.card_id == 99
    mock_commands.update_card_location.assert_any_call(
        card_id=99, game_id=101, new_location=CardLocation.IN_HAND, owner_id=1
    )
    mock_commands.update_card_location.assert_any_call(
        card_id=100, game_id=101, new_location=CardLocation.DRAFT
    )
    mock_notificator.notify_draft_updated.assert_awaited_once_with(
        101, 99, card_in_deck
    )


@pytest.mark.asyncio
async def test_draw_card_from_draft_fails_if_card_not_in_draft(
    turn_service: TurnService, mock_validator: Mock, mock_queries: Mock
):
    game_instance = Game(
        id=101,
        name="Test",
        min_players=4,
        max_players=12,
        host=PlayerInfo(
            player_id=1,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
        draft=[],
    )
    mock_validator.validate_game_exists.return_value = game_instance
    mock_queries.get_player_hand.return_value = []
    request = DrawCardRequest(
        game_id=101, player_id=1, source=DrawSource.DRAFT, card_id=99
    )
    with pytest.raises(CardNotFound, match="La carta 99 no está en el draft."):
        await turn_service.draw_card(request)


@pytest.mark.asyncio
async def test_draw_card_raises_not_your_turn(
    turn_service: TurnService, mock_validator: Mock, mock_queries: Mock
):
    mock_validator.validate_is_players_turn.side_effect = NotYourTurn(
        detail="No es tu turno."
    )
    mock_queries.get_player_hand.return_value = []
    request = DrawCardRequest(game_id=101, player_id=1, source=DrawSource.DECK)
    with pytest.raises(NotYourTurn, match="No es tu turno."):
        await turn_service.draw_card(request)


@pytest.mark.asyncio
async def test_draw_card_raises_internal_error_on_db_fail(
    turn_service: TurnService, mock_validator: Mock,
    mock_commands: Mock, mock_queries: Mock
):
    """Tests that it raises InternalGameError if the DB fails."""
    card_to_draw = Card(
        card_id=1,
        game_id=101,
        card_type=CardType.HERCULE_POIROT,
        location=CardLocation.DRAW_PILE,
    )
    game_instance = Game(
        id=101,
        name="Test",
        min_players=4,
        max_players=12,
        host=PlayerInfo(
            player_id=1,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
        deck=[card_to_draw],
    )
    mock_validator.validate_game_exists.return_value = game_instance
    mock_queries.get_player_hand.return_value = []
    mock_commands.update_card_location.return_value = ResponseStatus.ERROR
    request = DrawCardRequest(game_id=101, player_id=1, source=DrawSource.DECK)
    with pytest.raises(InternalGameError):
        await turn_service.draw_card(request)

@pytest.mark.asyncio
async def test_draw_card_from_deck_ends_game_if_last_card(
    turn_service: TurnService, mock_validator: Mock, mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
):
    """Tests that drawing the last card from the deck (with draft empty) ends the game."""
    # --- Arrange ---
    game_id = 101
    murderer_id = 2
    last_card = Card(card_id=999, game_id=game_id, card_type=CardType.MURDERER_ESCAPES, location=CardLocation.DRAW_PILE)
    game_instance = Game(
        id=game_id, name="Final Turn", min_players=2, max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        deck=[last_card],  # Only one card left
        draft=[]  # Draft is empty
    )
    mock_validator.validate_game_exists.return_value = game_instance
    mock_queries.get_player_hand.return_value = []
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_murderer_id.return_value = murderer_id
    mock_queries.get_accomplice_id.return_value = None
    mock_commands.delete_game.return_value = ResponseStatus.OK

    request = DrawCardRequest(game_id=game_id, player_id=1, source=DrawSource.DECK)

    # --- Act ---
    await turn_service.draw_card(request)

    # --- Assert ---
    mock_notificator.notify_murderer_wins.assert_awaited_once_with(
        game_id=game_id, murderer_id=murderer_id, accomplice_id=None
    )
    mock_commands.delete_game.assert_called_once_with(game_id=game_id)
    mock_notificator.notify_game_removed.assert_awaited_once_with(game_id)


@pytest.mark.asyncio
async def test_draw_card_from_draft_ends_game_if_last_card(
    turn_service: TurnService, mock_validator: Mock, mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
):
    """Tests that drawing the last card from the draft (with deck empty) ends the game."""
    # --- Arrange ---
    game_id = 101
    murderer_id = 2
    last_card = Card(card_id=999, game_id=game_id, card_type=CardType.HARLEY_QUIN, location=CardLocation.DRAFT)
    game_instance = Game(
        id=game_id, name="Final Draft", min_players=2, max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        deck=[],  # Deck is empty
        draft=[last_card]  # Only one card left in draft
    )
    mock_validator.validate_game_exists.return_value = game_instance
    mock_queries.get_player_hand.return_value = []
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_murderer_id.return_value = murderer_id
    mock_queries.get_accomplice_id.return_value = 3
    mock_commands.delete_game.return_value = ResponseStatus.OK

    request = DrawCardRequest(game_id=game_id, player_id=1, source=DrawSource.DRAFT, card_id=999)

    # --- Act ---
    await turn_service.draw_card(request)

    # --- Assert ---
    mock_notificator.notify_murderer_wins.assert_awaited_once_with(
        game_id=game_id, murderer_id=murderer_id, accomplice_id=3
    )
    mock_commands.delete_game.assert_called_once_with(game_id=game_id)
    mock_notificator.notify_game_removed.assert_awaited_once_with(game_id)


# =================================================================
# --- TESTS FOR discard_card ---
# =================================================================


@pytest.mark.asyncio
async def test_discard_card_success(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
):
    """Tests the happy path of discarding a card."""
    card_to_discard = Card(
        card_id=5,
        game_id=101,
        card_type=CardType.NOT_SO_FAST,
        location=CardLocation.IN_HAND,
        player_id=1,
    )
    player_instance = PlayerInGame(
        player_id=1,
        player_name="P",
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
        hand=[card_to_discard],
    )
    mock_validator.validate_player_in_game.return_value = player_instance
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    request = DiscardCardRequest(game_id=101, player_id=1, card_id=5)
    await turn_service.discard_card(request)
    mock_commands.update_card_location.assert_called_once()
    mock_notificator.notify_card_discarded.assert_awaited_once()


@pytest.mark.asyncio
async def test_discard_card_raises_card_not_found(
    turn_service: TurnService, mock_validator: Mock
):
    """Tests that it raises CardNotFound if the player doesn't have the card."""
    player_instance = PlayerInGame(
        player_id=1,
        player_name="P",
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
        hand=[],
    )
    mock_validator.validate_player_in_game.return_value = player_instance
    mock_validator.validate_player_has_cards.side_effect = CardNotFound(
        detail="No tenés esa carta, fantasma."
    )
    request = DiscardCardRequest(game_id=101, player_id=1, card_id=99)

    with pytest.raises(CardNotFound, match="No tenés esa carta, fantasma."):
        await turn_service.discard_card(request)


# =================================================================
# --- TESTS FOR finish_turn ---
# =================================================================


@pytest.mark.asyncio
async def test_finish_turn_success(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_commands: Mock,
    mock_queries: Mock,
    mock_notificator: AsyncMock,
    mock_turn_utils: Mock,
):
    """Tests the happy path of finishing a turn."""
    p1 = PlayerInGame(
        player_id=1,
        turn_order=1,
        player_name="p1",
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    p2 = PlayerInGame(
        player_id=2,
        turn_order=2,
        player_name="p2",
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    players = [p1, p2]
    game_instance = Game(
        id=101,
        name="T",
        min_players=2,
        max_players=4,
        host=PlayerInfo(
            player_id=1,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
        status=GameStatus.IN_PROGRESS,
        players=players,
        current_turn_player_id=1,
    )

    mock_validator.validate_game_exists.return_value = game_instance
    turn_service.read.get_players_in_game.return_value = players
    mock_turn_utils.sort_players_by_turn_order.return_value = [p1, p2]
    turn_service.read.get_current_turn.return_value = 1
    mock_commands.set_current_turn.return_value = ResponseStatus.OK
    request = PlayerActionRequest(game_id=101, player_id=1)
    mock_queries.get_player_hand.return_value = [Mock()] * 6

    response = await turn_service.finish_turn(request)

    assert response.next_player_id == 2
    mock_commands.set_current_turn.assert_called_once_with(101, 2)
    mock_notificator.notify_new_turn.assert_awaited_once_with(101, 2)


# =================================================================
# --- TESTS FOR play_card ---
# =================================================================


@pytest.mark.asyncio
async def test_play_card_happy_path_uncancellable_effect(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_executor: AsyncMock,
):
    """
    Tests the happy path: a card is played, classified as uncancellable,
    and its effect is executed.
    """
    # --- Arrange ---
    player_id = 1
    game_id = 101
    card_id_played = 50
    request = PlayCardRequest(
        action_type=PlayCardActionType.PLAY_EVENT,
        game_id=game_id,
        player_id=player_id,
        card_ids=[card_id_played],
    )

    card_played = Card(
        card_id=card_id_played,
        game_id=game_id,
        card_type=CardType.CARDS_OFF_THE_TABLE,
        location=CardLocation.IN_HAND,
        player_id=player_id,
    )
    player = PlayerInGame(
        player_id=player_id,
        hand=[card_played],
        player_name="Naevier",
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    game = Game(
        id=game_id,
        players=[player],
        current_turn_player_id=player_id,
        name="t",
        min_players=4,
        max_players=12,
        host=player,
        status=GameStatus.IN_PROGRESS,
    )

    mock_validator.validate_game_exists.return_value = game
    mock_validator.validate_player_in_game.return_value = player
    mock_validator.validate_player_has_cards.return_value = [card_played]
    mock_executor.execute_effect.return_value = GameFlowStatus.CONTINUE  # Changed from ResponseStatus.OK
    # --- ADAPTACIÓN ---
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_card.return_value = card_played
    mock_queries.get_player_name.return_value = "Naevier"

    # --- Act ---
    response = await turn_service.play_card(request)

    # --- Assert ---
    mock_executor.execute_effect.assert_awaited_once_with(
        game_id=game_id,
        played_cards=[card_played],
        player_id=player_id,
        target_player_id=request.target_player_id,
        target_secret_id=request.target_secret_id,
        target_set_id=request.target_set_id,
        target_card_id=request.target_card_id,
        trade_direction=None,
    )

    assert isinstance(response, GeneralActionResponse)


@pytest.mark.asyncio
async def test_play_card_fails_if_card_not_in_hand(
    turn_service: TurnService, mock_validator: Mock
):
    """
    Tests that the function fails if player doesn't have the cards.
    """
    # --- Arrange ---
    mock_validator.validate_player_has_cards.side_effect = NotYourCard(
        detail="No tienes esa carta."
    )

    request = PlayCardRequest(
        action_type=PlayCardActionType.PLAY_EVENT,
        game_id=1,
        player_id=1,
        card_ids=[1],
    )

    # --- Act & Assert ---
    with pytest.raises(NotYourCard, match="No tienes esa carta."):
        await turn_service.play_card(request)

    turn_service.effect_executor.execute_effect.assert_not_awaited()


@pytest.mark.asyncio
async def test_play_card_fails_if_card_not_found_in_db(
    turn_service: TurnService, mock_validator: Mock, mock_queries: Mock
):
    """
    Tests that InternalGameError is raised if the card is not found in the DB
    after passing validations.
    """
    # --- Arrange ---
    mock_validator.validate_player_has_cards.side_effect = NotYourCard(
        detail="No tenes la carta."
    )

    request = PlayCardRequest(
        action_type=PlayCardActionType.PLAY_EVENT,
        game_id=1,
        player_id=1,
        card_ids=[99],
    )

    # --- Act & Assert ---
    with pytest.raises(NotYourCard, match="No tenes la carta."):
        await turn_service.play_card(request)


@pytest.mark.asyncio
async def test_play_card_beresford_set_is_uncancellable(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_executor: AsyncMock,
):
    """
    Tests that playing the Beresford set (Tommy and Tuppence) is correctly
    classified as uncancellable and its effect is executed.
    """
    # --- Arrange ---
    game_id, player_id = 101, 1
    tommy_card = Card(
        card_id=1,
        game_id=game_id,
        card_type=CardType.TOMMY_BERESFORD,
        location=CardLocation.IN_HAND,
    )
    tuppence_card = Card(
        card_id=2,
        game_id=game_id,
        card_type=CardType.TUPPENCE_BERESFORD,
        location=CardLocation.IN_HAND,
    )
    played_cards = [tommy_card, tuppence_card]
    request = PlayCardRequest(
        action_type=PlayCardActionType.FORM_NEW_SET,
        game_id=game_id,
        player_id=player_id,
        card_ids=[1, 2],
        target_player_id=123,
        target_secret_id=456,
    )

    mock_validator.validate_player_has_cards.return_value = played_cards
    mock_executor.execute_effect.return_value = GameFlowStatus.CONTINUE
    # --- ADAPTACIÓN ---
    mock_commands.create_set.return_value = 1
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_set.return_value = played_cards
    mock_queries.get_player_name.return_value = "Player"
    mock_queries.get_card.side_effect = lambda cid, gid: {1: tommy_card, 2: tuppence_card}.get(cid)

    # --- Act ---
    await turn_service.play_card(request)

    # --- Assert ---
    mock_executor.execute_effect.assert_awaited_once_with(
        game_id=game_id,
        played_cards=played_cards,
        player_id=player_id,
        target_player_id=request.target_player_id,
        target_secret_id=request.target_secret_id,
        target_set_id=request.target_set_id,
        target_card_id=request.target_card_id,
        trade_direction=None,
    )


@pytest.mark.asyncio
async def test_play_card_with_harley_quin_calls_with_both_cards(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_executor: AsyncMock,
):
    """
    Tests that when playing an action card with HARLEY_QUIN, the effect executor
    is called with both card IDs.
    """
    # --- Arrange ---
    game_id, player_id = 101, 1
    harley_card = Card(
        card_id=1,
        game_id=game_id,
        card_type=CardType.HARLEY_QUIN,
        location=CardLocation.IN_HAND,
    )
    action_card = Card(
        card_id=2,
        game_id=game_id,
        card_type=CardType.TUPPENCE_BERESFORD,
        location=CardLocation.IN_HAND,
    )
    played_cards = [harley_card, action_card]
    request = PlayCardRequest(
        action_type=PlayCardActionType.FORM_NEW_SET,
        game_id=game_id,
        player_id=player_id,
        card_ids=[1, 2],
    )

    mock_validator.validate_player_has_cards.return_value = played_cards
    mock_executor.classify_effect.return_value = Mock()
    mock_executor.execute_effect.return_value = ResponseStatus.OK
    # --- ADAPTACIÓN ---
    mock_commands.create_set.return_value = 1
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_set.return_value = played_cards
    mock_queries.get_card.side_effect = lambda cid, gid: next((c for c in played_cards if c.card_id == cid), None)
    mock_commands.create_pending_action.return_value = ResponseStatus.OK
    mock_commands.set_game_action_state.return_value = ResponseStatus.OK

    # --- Act ---
    await turn_service.play_card(request)

    # --- Assert ---
    # The most important assertion: verify that the effect executor was called
    # with a list containing BOTH card IDs.
    mock_executor.classify_effect.assert_called_once()
    mock_commands.create_pending_action.assert_called_once()
    mock_commands.set_game_action_state.assert_called_once()


@pytest.mark.asyncio
async def test_play_card_satterthwaite_with_quin_delegates_ok_to_executor(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_executor: AsyncMock,
):
    """
    Tests that playing the Satterthwaite + Quin set correctly delegates the
    execution to the effect_executor with all the required data.
    This test covers the first half of the lifecycle of the action effect.
    """
    # --- Arrange ---
    game_id, player_id, target_player_id = 101, 1, 2
    satterthwaite_card = Card(
        card_id=1,
        game_id=game_id,
        card_type=CardType.MR_SATTERTHWAITE,
        location=CardLocation.IN_HAND,
    )
    quin_card = Card(
        card_id=2,
        game_id=game_id,
        card_type=CardType.HARLEY_QUIN,
        location=CardLocation.IN_HAND,
    )
    played_cards = [satterthwaite_card, quin_card]
    request = PlayCardRequest(
        action_type=PlayCardActionType.FORM_NEW_SET,
        game_id=game_id,
        player_id=player_id,
        card_ids=[1, 2],
        target_player_id=target_player_id,
    )

    # Configure mocks for the validations and reads within turn_service
    mock_validator.validate_player_has_cards.return_value = played_cards
    mock_executor.classify_effect.return_value = Mock()
    mock_executor.execute_effect.return_value = ResponseStatus.OK
    # --- ADAPTACIÓN ---
    mock_commands.create_set.return_value = 1
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_set.return_value = played_cards
    mock_queries.get_card.side_effect = lambda cid, gid: next((c for c in played_cards if c.card_id == cid), None)
    mock_commands.create_pending_action.return_value = ResponseStatus.OK
    mock_commands.set_game_action_state.return_value = ResponseStatus.OK

    # --- Act ---
    await turn_service.play_card(request)

    # --- Assert ---
    # The responsibility of this test is to ensure that TurnService
    # correctly calls its dependency, the EffectExecutor. We don't test
    # the executor's internal logic here.
    mock_executor.classify_effect.assert_called_once()
    mock_commands.create_pending_action.assert_called_once()
    mock_commands.set_game_action_state.assert_called_once()


@pytest.mark.asyncio
async def test_play_card_reveal_secret_when_awaiting_reveal_for_steal(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
):
    # --- Arrange ---
    game_id, thief_id, victim_id, secret_id_to_steal = 101, 1, 2, 99

    #2!!! Añadimos prompted_player_id
    game_in_waiting_state = Game(
        id=game_id,
        action_state=GameActionState.AWAITING_REVEAL_FOR_STEAL,
        action_initiator_id=thief_id,
        prompted_player_id=victim_id,  # <-- ESTO FALTABA
        name="Test Game",
        min_players=2,
        max_players=4,
        status=GameStatus.IN_PROGRESS,
        host=PlayerInfo(
            player_id=1,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
    )
    mock_validator.validate_game_exists.return_value = game_in_waiting_state
    mock_commands.reveal_secret_card.return_value = ResponseStatus.OK

    #1!!! Cambiamos get_player_role por get_player_secrets
    victim_secret = SecretCard(
        secret_id=secret_id_to_steal,
        game_id=game_id,
        player_id=victim_id,
        role=PlayerRole.INNOCENT,
    )
    mock_queries.get_player_secrets.return_value = [victim_secret]
    mock_queries.get_secret.return_value = victim_secret
    mock_queries.get_pending_action.return_value = None

    request = RevealSecretRequest(
        game_id=game_id,
        player_id=victim_id,
        secret_id=secret_id_to_steal,
    )

    # --- Act ---
    await turn_service.reveal_secret(request)

    # --- Assert ---
    # Verificamos que se revela para notificar
    mock_commands.reveal_secret_card.assert_any_call(
        secret_id=secret_id_to_steal, game_id=game_id, is_revealed=True
    )
    # Verificamos que se notifica
    mock_notificator.notify_secret_revealed.assert_awaited_once_with(
        game_id=game_id,
        secret_id=secret_id_to_steal,
        player_role=PlayerRole.INNOCENT,
        player_id=victim_id,
    )
    # Verificamos que se roba
    mock_commands.change_secret_owner.assert_called_once_with(
        secret_id=secret_id_to_steal, new_owner_id=thief_id, game_id=game_id
    )
    # Verificamos que se vuelve a ocultar
    mock_commands.reveal_secret_card.assert_any_call(
        secret_id=secret_id_to_steal, game_id=game_id, is_revealed=False
    )
    # Verificamos la notificación del robo
    mock_notificator.notify_secret_stolen.assert_awaited_once_with(
        game_id, thief_id=thief_id, victim_id=victim_id
    )
    # Verificamos que se limpia el estado
    mock_commands.clear_game_action_state.assert_called_once_with(
        game_id=game_id
    )


@pytest.mark.asyncio
async def test_reveal_secret_when_awaiting_choice_reveal_for_choice(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
):
    # --- Arrange ---
    game_id, victim_player_id, secret_id_to_reveal = 101, 2, 99

    #2!!! Añadimos prompted_player_id
    game_in_waiting_state = Game(
        id=game_id,
        action_state=GameActionState.AWAITING_REVEAL_FOR_CHOICE,
        prompted_player_id=victim_player_id,  # <-- ESTO FALTABA
        name="Test Game",
        min_players=2,
        max_players=4,
        status=GameStatus.IN_PROGRESS,
        host=PlayerInfo(
            player_id=1,
            player_name="p",
            player_birth_date=date(2000, 1, 1),
            player_avatar=Avatar.DEFAULT,
        ),
    )
    mock_validator.validate_game_exists.return_value = game_in_waiting_state
    mock_commands.reveal_secret_card.return_value = ResponseStatus.OK

    #1!!! Cambiamos get_player_role por get_player_secrets
    victim_secret = SecretCard(
        secret_id=secret_id_to_reveal,
        game_id=game_id,
        player_id=victim_player_id,
        role=PlayerRole.ACCOMPLICE,
    )
    mock_queries.get_player_secrets.return_value = [victim_secret]
    mock_queries.get_secret.return_value = victim_secret
    mock_queries.get_pending_action.return_value = None

    request = RevealSecretRequest(
        game_id=game_id,
        player_id=victim_player_id,
        secret_id=secret_id_to_reveal,
    )

    # --- Act ---
    await turn_service.reveal_secret(request)

    # --- Assert ---
    mock_commands.reveal_secret_card.assert_called_once_with(
        secret_id=secret_id_to_reveal, game_id=game_id, is_revealed=True
    )
    mock_notificator.notify_secret_revealed.assert_awaited_once_with(
        game_id=game_id,
        secret_id=secret_id_to_reveal,
        player_role=PlayerRole.ACCOMPLICE,
        player_id=victim_player_id,
    )
    mock_commands.clear_game_action_state.assert_called_once_with(
        game_id=game_id
    )

@pytest.mark.asyncio
async def test_reveal_secret_ends_game_if_murderer_is_revealed(
    turn_service: TurnService, mock_validator: Mock, mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
):
    """Tests that revealing the 'MURDERER' secret card ends the game with innocents winning."""
    # --- Arrange ---
    game_id = 101
    murderer_player_id = 2
    secret_id_to_reveal = 99

    game_in_waiting_state = Game(
        id=game_id,
        action_state=GameActionState.AWAITING_REVEAL_FOR_CHOICE,
        prompted_player_id=murderer_player_id,
        name="Gotcha!", min_players=2, max_players=4, status=GameStatus.IN_PROGRESS,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
    )
    mock_validator.validate_game_exists.return_value = game_in_waiting_state
    mock_commands.reveal_secret_card.return_value = ResponseStatus.OK

    murderer_secret = SecretCard(secret_id=secret_id_to_reveal, game_id=game_id, player_id=murderer_player_id, role=PlayerRole.MURDERER)
    # This mock is for the first part of the function (notification)
    mock_queries.get_player_secrets.return_value = [murderer_secret]
    # This mock is for the end-game check
    mock_queries.get_secret.return_value = murderer_secret
    mock_queries.get_accomplice_id.return_value = None
    mock_commands.delete_game.return_value = ResponseStatus.OK

    request = RevealSecretRequest(game_id=game_id, player_id=murderer_player_id, secret_id=secret_id_to_reveal)

    # --- Act ---
    await turn_service.reveal_secret(request)

    # --- Assert ---
    mock_notificator.notify_innocents_win.assert_awaited_once_with(
        game_id=game_id, murderer_id=murderer_player_id, accomplice_id=None
    )
    mock_commands.delete_game.assert_called_once_with(game_id=game_id)
    mock_notificator.notify_game_removed.assert_awaited_once_with(game_id)


@pytest.mark.asyncio
async def test_draw_card_deck_empty_murderer_wins(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
):
    """Tests that drawing the last card from deck triggers MURDERER_WINS."""
    # ARRANGE
    game_id, player_id = 101, 1
    last_card = Card(
        card_id=1, game_id=game_id, card_type=CardType.HERCULE_POIROT, location=CardLocation.DRAW_PILE
    )
    game_instance = Game(
        id=game_id, name="Test", min_players=4, max_players=12,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        deck=[last_card],
        draft=[],
    )
    mock_validator.validate_game_exists.return_value = game_instance
    mock_queries.get_player_hand.return_value = []
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_murderer_id.return_value = 2
    mock_queries.get_accomplice_id.return_value = 3
    mock_commands.delete_game.return_value = ResponseStatus.OK

    # ACT
    request = DrawCardRequest(game_id=game_id, player_id=player_id, source=DrawSource.DECK)
    await turn_service.draw_card(request)

    # ASSERT
    mock_notificator.notify_murderer_wins.assert_awaited_once_with(
        game_id=game_id, murderer_id=2, accomplice_id=3
    )
    mock_commands.delete_game.assert_called_once_with(game_id=game_id)
    mock_notificator.notify_game_removed.assert_awaited_once_with(game_id)


@pytest.mark.asyncio
async def test_play_nsf_player_plays_nsf_card(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
):
    """Tests playing an NSF card when an action is pending."""
    # ARRANGE
    game_id, player_a_id, player_b_id = 101, 1, 2
    nsf_card = Card(
        card_id=10, game_id=game_id, card_type=CardType.NOT_SO_FAST,
        location=CardLocation.IN_HAND, player_id=player_b_id
    )
    player_b = PlayerInGame(
        player_id=player_b_id, player_name="Player B",
        player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT,
        hand=[nsf_card]
    )
    player_c = PlayerInGame(
        player_id=3, player_name="Player C",
        player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT,
    )
    game = Game(
        id=game_id, name="Test", min_players=3, max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        action_state=GameActionState.PENDING_NSF,
        players=[player_b, player_c]
    )
    pending_action = PendingAction(
        id=1, game_id=game_id, player_id=player_a_id,
        action_type=PlayCardActionType.PLAY_EVENT,
        cards=[], responses_count=0, nsf_count=0,
        last_action_player_id=player_a_id,
        target_player_id=None, target_secret_id=None, target_card_id=None, target_set_id=None
    )
    updated_pending = PendingAction(
        id=1, game_id=game_id, player_id=player_a_id,
        action_type=PlayCardActionType.PLAY_EVENT,
        cards=[], responses_count=0, nsf_count=1,
        last_action_player_id=player_b_id,
        target_player_id=None, target_secret_id=None, target_card_id=None, target_set_id=None
    )

    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_pending_action.side_effect = [pending_action, updated_pending]
    mock_validator.validate_player_in_game.return_value = player_b
    mock_validator.validate_player_has_cards.return_value = [nsf_card]
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_commands.increment_nsf_responses.return_value = ResponseStatus.OK

    # ACT
    request = PlayCardRequest(
        game_id=game_id, player_id=player_b_id, card_ids=[10],
        action_type=PlayCardActionType.INSTANT
    )
    await turn_service.play_nsf(request)

    # ASSERT
    mock_commands.update_card_location.assert_called_once_with(
        10, game_id, CardLocation.DISCARD_PILE
    )
    mock_notificator.notify_card_discarded.assert_awaited_once()
    mock_notificator.notify_cards_played.assert_awaited_once()
    mock_commands.increment_nsf_responses.assert_called_once_with(game_id, player_b_id, add_nsf=True)


@pytest.mark.asyncio
async def test_play_nsf_player_passes(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_executor: AsyncMock,
):
    """Tests passing (not playing NSF) when an action is pending."""
    # ARRANGE
    game_id, player_a_id, player_b_id = 101, 1, 2
    player_c = PlayerInGame(player_id=3, player_name="C", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT)
    player_d = PlayerInGame(player_id=4, player_name="D", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT)
    game = Game(
        id=game_id, name="Test", min_players=3, max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        action_state=GameActionState.PENDING_NSF,
        players=[player_c, player_d]
    )
    event_card = Card(card_id=10, game_id=game_id, card_type=CardType.MISS_MARPLE, location=CardLocation.IN_HAND)
    pending_action = PendingAction(
        id=1, game_id=game_id, player_id=player_a_id,
        action_type=PlayCardActionType.PLAY_EVENT,
        cards=[event_card], responses_count=0, nsf_count=0,
        last_action_player_id=player_a_id,
        target_player_id=None, target_secret_id=None, target_card_id=None, target_set_id=None
    )
    updated_pending = PendingAction(
        id=1, game_id=game_id, player_id=player_a_id,
        action_type=PlayCardActionType.PLAY_EVENT,
        cards=[event_card], responses_count=1, nsf_count=0,
        last_action_player_id=player_a_id,
        target_player_id=None, target_secret_id=None, target_card_id=None, target_set_id=None
    )

    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_pending_action.side_effect = [pending_action, updated_pending]
    mock_commands.increment_nsf_responses.return_value = ResponseStatus.OK
    mock_executor.execute_effect.return_value = ResponseStatus.OK
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_commands.clear_pending_action.return_value = ResponseStatus.OK
    mock_commands.clear_game_action_state.return_value = ResponseStatus.OK
    mock_queries.get_card.return_value = event_card

    # ACT
    request = PlayCardRequest(
        game_id=game_id, player_id=player_b_id, card_ids=[],
        action_type=PlayCardActionType.INSTANT
    )
    await turn_service.play_nsf(request)

    # ASSERT
    mock_commands.increment_nsf_responses.assert_called_once_with(game_id, player_b_id, add_nsf=False)


@pytest.mark.asyncio
async def test_play_nsf_action_cancelled_odd_nsf_count(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
):
    """Tests that action is cancelled when NSF count is odd."""
    # ARRANGE
    game_id, player_a_id = 101, 1
    cancelled_card = Card(
        card_id=5, game_id=game_id, card_type=CardType.MISS_MARPLE,
        location=CardLocation.IN_HAND
    )
    game = Game(
        id=game_id, name="Test", min_players=3, max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        action_state=GameActionState.PENDING_NSF,
        players=[
            PlayerInGame(player_id=1, player_name="A", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
            PlayerInGame(player_id=2, player_name="B", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
            PlayerInGame(player_id=3, player_name="C", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        ]
    )
    pending_action = PendingAction(
        id=1, game_id=game_id, player_id=player_a_id,
        action_type=PlayCardActionType.PLAY_EVENT,
        cards=[cancelled_card], responses_count=2, nsf_count=1,
        last_action_player_id=2,
        target_player_id=None, target_secret_id=None, target_card_id=None, target_set_id=None
    )

    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_pending_action.side_effect = [pending_action, pending_action]
    mock_commands.increment_nsf_responses.return_value = ResponseStatus.OK
    mock_commands.update_card_location.return_value = ResponseStatus.OK

    # ACT
    request = PlayCardRequest(
        game_id=game_id, player_id=3, card_ids=[],
        action_type=PlayCardActionType.INSTANT
    )
    await turn_service.play_nsf(request)

    # ASSERT
    mock_notificator.notify_action_cancelled.assert_awaited_once()
    mock_commands.update_card_location.assert_called_once_with(
        5, game_id, CardLocation.DISCARD_PILE
    )
    mock_commands.clear_pending_action.assert_called_once_with(game_id)
    mock_commands.clear_game_action_state.assert_called_once_with(game_id)


@pytest.mark.asyncio
async def test_play_nsf_action_resolved_even_nsf_count(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
    mock_executor: AsyncMock,
):
    """Tests that action is resolved when NSF count is even."""
    # ARRANGE
    game_id, player_a_id = 101, 1
    resolved_card = Card(
        card_id=5, game_id=game_id, card_type=CardType.MISS_MARPLE,
        location=CardLocation.IN_HAND
    )
    game = Game(
        id=game_id, name="Test", min_players=3, max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        action_state=GameActionState.PENDING_NSF,
        players=[
            PlayerInGame(player_id=1, player_name="A", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
            PlayerInGame(player_id=2, player_name="B", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
            PlayerInGame(player_id=3, player_name="C", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        ]
    )
    pending_action = PendingAction(
        id=1, game_id=game_id, player_id=player_a_id,
        action_type=PlayCardActionType.PLAY_EVENT,
        cards=[resolved_card], responses_count=2, nsf_count=2,
        last_action_player_id=2,
        target_player_id=None, target_secret_id=None, target_card_id=None, target_set_id=None
    )

    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_pending_action.side_effect = [pending_action, pending_action]
    mock_commands.increment_nsf_responses.return_value = ResponseStatus.OK
    mock_executor.execute_effect.return_value = GameFlowStatus.CONTINUE
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_card.return_value = resolved_card
    mock_queries.get_player_name.return_value = "A"

    # ACT
    request = PlayCardRequest(
        game_id=game_id, player_id=3, card_ids=[],
        action_type=PlayCardActionType.INSTANT
    )
    await turn_service.play_nsf(request)

    # ASSERT
    mock_notificator.notify_action_resolved.assert_awaited_once()
    mock_executor.execute_effect.assert_awaited_once()
    mock_commands.clear_pending_action.assert_called_once_with(game_id)
    mock_commands.clear_game_action_state.assert_called_once_with(game_id)


@pytest.mark.asyncio
async def test_play_nsf_no_pending_action_raises_conflict(
    turn_service: TurnService,
    mock_validator: Mock,
):
    """Tests that play_nsf raises ActionConflict when state is not PENDING_NSF."""
    # ARRANGE
    game = Game(
        id=101, name="Test", min_players=2, max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        action_state=GameActionState.NONE,
    )
    mock_validator.validate_game_exists.return_value = game

    # ACT & ASSERT
    request = PlayCardRequest(
        game_id=101, player_id=2, card_ids=[],
        action_type=PlayCardActionType.INSTANT
    )
    with pytest.raises(ActionConflict, match="No hay una acción pendiente"):
        await turn_service.play_nsf(request)


@pytest.mark.asyncio
async def test_play_nsf_player_cannot_nsf_own_action(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
):
    """Tests that a player cannot play NSF on their own action."""
    # ARRANGE
    game_id, player_id = 101, 1
    game = Game(
        id=game_id, name="Test", min_players=2, max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        action_state=GameActionState.PENDING_NSF,
    )
    pending_action = PendingAction(
        id=1, game_id=game_id, player_id=player_id,
        action_type=PlayCardActionType.PLAY_EVENT,
        cards=[], responses_count=0, nsf_count=0,
        last_action_player_id=player_id,
        target_player_id=None, target_secret_id=None, target_card_id=None, target_set_id=None
    )

    mock_validator.validate_game_exists.return_value = game
    mock_queries.get_pending_action.return_value = pending_action

    # ACT & ASSERT
    request = PlayCardRequest(
        game_id=game_id, player_id=player_id, card_ids=[],
        action_type=PlayCardActionType.INSTANT
    )
    with pytest.raises(InvalidAction, match="No puedes usar 'NSF' en tu propia acción"):
        await turn_service.play_nsf(request)


@pytest.mark.asyncio
async def test_play_card_cancellable_enters_pending_nsf(
    turn_service: TurnService,
    mock_validator: Mock,
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
    mock_executor: AsyncMock,
):
    """Tests that playing a cancellable card enters PENDING_NSF state."""
    # ARRANGE
    game_id, player_id = 101, 1
    card = Card(
        card_id=1, game_id=game_id, card_type=CardType.MISS_MARPLE,
        location=CardLocation.IN_HAND, player_id=player_id
    )
    player = PlayerInGame(
        player_id=player_id, player_name="Player", hand=[card],
        player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT
    )
    game = Game(
        id=game_id, name="Test", min_players=2, max_players=4,
        host=PlayerInfo(player_id=1, player_name="p", player_birth_date=date(2000, 1, 1), player_avatar=Avatar.DEFAULT),
        status=GameStatus.IN_PROGRESS,
        players=[player]
    )

    mock_validator.validate_game_exists.return_value = game
    mock_validator.validate_player_in_game.return_value = player
    mock_validator.validate_player_has_cards.return_value = [card]
    mock_executor.classify_effect.return_value = Mock()
    mock_commands.create_pending_action.return_value = ResponseStatus.OK
    mock_commands.set_game_action_state.return_value = ResponseStatus.OK

    # ACT
    request = PlayCardRequest(
        game_id=game_id, player_id=player_id, card_ids=[1],
        action_type=PlayCardActionType.PLAY_EVENT
    )
    await turn_service.play_card(request)

    # ASSERT
    mock_commands.create_pending_action.assert_called_once()
    mock_commands.set_game_action_state.assert_called_once_with(
        game_id=game_id, state=GameActionState.PENDING_NSF,
        prompted_player_id=None, initiator_id=player_id
    )
    mock_queries.get_pending_action.assert_called()
    mock_notificator.notify_cards_played.assert_awaited_once()

