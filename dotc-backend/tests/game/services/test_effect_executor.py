import pytest
from unittest.mock import Mock, AsyncMock

from app.game.effect_executor import EffectExecutor
from app.domain.models import Card
from app.domain.enums import CardType, ResponseStatus, CardLocation
from app.game.exceptions import InvalidAction, InternalGameError


@pytest.fixture
def effect_executor(
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
) -> EffectExecutor:
    """
    Creates an instance of EffectExecutor with its direct dependencies mocked.
    """
    return EffectExecutor(
        queries=mock_queries,
        commands=mock_commands,
        notifier=mock_notificator,
    )


# =================================================================
# --- TESTS FOR execute_effect ---
# =================================================================


@pytest.mark.asyncio
async def test_execute_event_effect_happy_path(
    effect_executor: EffectExecutor,
    mock_queries: Mock,
):
    """
    Tests the happy path for a single-card EVENT effect: the card is found,
    the effect class is located, instantiated, and executed.
    """
    # --- Arrange ---
    game_id = 101
    player_id = 1
    card_id = 50
    card_type_to_test = CardType.DEAD_CARD_FOLLY
    card_played = Card(
        card_id=card_id,
        game_id=game_id,
        card_type=card_type_to_test,
        location=CardLocation.IN_HAND,
    )

    # Mock the effect class and its instance
    mock_effect_instance = AsyncMock()
    mock_effect_instance.execute.return_value = ResponseStatus.OK
    mock_effect_class = Mock(return_value=mock_effect_instance)

    # Monkeypatch the specific map for EVENT cards
    effect_executor.EVENT_EFFECT_MAP[card_type_to_test] = mock_effect_class

    # --- Act ---
    result = await effect_executor.execute_effect(
        game_id=game_id,
        played_cards=[card_played],
        player_id=player_id,
        target_player_id=2,
    )

    # --- Assert ---
    mock_queries.get_card.assert_not_called()
    mock_effect_class.assert_called_once_with(
        queries=effect_executor.read, commands=effect_executor.write, notifier=effect_executor.notifier
    )
    mock_effect_instance.execute.assert_awaited_once_with(
        game_id=game_id,
        card_ids=[card_id],
        player_id=player_id,
        target_player_id=2,
        target_secret_id=None,
        target_set_id=None,
        target_card_id=None,
        trade_direction=None,
    )
    assert result == ResponseStatus.OK


@pytest.mark.asyncio
async def test_execute_set_effect_happy_path(
    effect_executor: EffectExecutor,
    mock_queries: Mock,
):
    """
    Tests the happy path for a multi-card SET effect.
    """
    # --- Arrange ---
    game_id = 102
    player_id = 2
    card_id_1, card_id_2 = 60, 61

    card_1 = Card(
        card_id=card_id_1,
        game_id=game_id,
        card_type=CardType.HERCULE_POIROT,
        location=CardLocation.IN_HAND,
    )
    card_2 = Card(
        card_id=card_id_2,
        game_id=game_id,
        card_type=CardType.HERCULE_POIROT,
        location=CardLocation.IN_HAND,
    )

    mock_effect_instance = AsyncMock(
        execute=AsyncMock(return_value=ResponseStatus.OK)
    )
    mock_effect_class = Mock(return_value=mock_effect_instance)

    # Monkeypatch the SET map
    set_key_counts = {CardType.HERCULE_POIROT: 2}
    effect_executor.SET_EFFECT_MAP.set(
        set_key_counts, mock_effect_class, priority=1
    )

    # --- Act ---
    await effect_executor.execute_effect(
        game_id=game_id,
        played_cards=[card_1, card_2],
        player_id=player_id,
    )

    # --- Assert ---
    mock_queries.get_card.assert_not_called()
    mock_effect_class.assert_called_once()
    mock_effect_instance.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_effect_fails_if_cards_not_found(
    effect_executor: EffectExecutor, mock_queries: Mock
):
    """
    Tests that InternalGameError is raised if not all played cards are found in the DB.
    """
    # --- Arrange ---
    game_id = 101
    card_id = 50
    card_type_to_test = CardType.DEAD_CARD_FOLLY
    card_played = Card(
        card_id=card_id,
        game_id=game_id,
        card_type=card_type_to_test,
        location=CardLocation.IN_HAND,
    )

    # --- Act & Assert ---
    with pytest.raises(
        InvalidAction, match="La combinación de cartas jugadas no tiene un efecto válido."
    ):
        await effect_executor.execute_effect(
            game_id=101, played_cards=[], player_id=1
        )


@pytest.mark.asyncio
async def test_execute_effect_fails_if_combo_not_in_map(
    effect_executor: EffectExecutor, mock_queries: Mock
):
    """
    Tests that InvalidAction is raised if the card combination has no defined effect.
    """
    # --- Arrange ---
    card_played = Card(
        card_id=1,
        game_id=101,
        card_type=CardType.MURDERER_ESCAPES,  # Assumed not to have a solo effect
        location=CardLocation.IN_HAND,
    )

    # --- Act & Assert ---
    with pytest.raises(
        InvalidAction,
        match="La combinación de cartas jugadas no tiene un efecto válido.",
    ):
        await effect_executor.execute_effect(
            game_id=101, played_cards=[card_played], player_id=1
        )