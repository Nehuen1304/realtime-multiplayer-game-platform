import pytest
from unittest.mock import DEFAULT, AsyncMock, MagicMock

from datetime import date
from app.domain.models import SecretCard, Game, PlayerInGame, PlayerInfo
from app.domain.enums import (
    Avatar,
    ResponseStatus,
    CardLocation,
    GameActionState,
    PlayerRole,
    GameStatus,
    GameFlowStatus,
)
from app.game.effects.set_effects import (
    BaseCardEffect,
    RevealSpecificSecretEffect,
    RevealChosenSecretEffect,
    HideSecretEffect,
    StealSecretEffect,
    BeresfordUncancellableEffect,
)
from app.game.exceptions import (
    InternalGameError,
    InvalidAction,
    ResourceNotFound,
    ActionConflict,
)

# =======================
# BaseCardEffect
# =======================


@pytest.mark.asyncio
async def test_basecardeffect_execute_not_implemented__sad_path():
    # ARRANGE
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_notifier = AsyncMock()
    effect = BaseCardEffect(mock_read, mock_write, mock_notifier)
    # ACT & ASSERT
    with pytest.raises(NotImplementedError):
        await effect.execute(1, 2, [3])


# =======================
# RevealSpecificSecretEffect
# =======================


@pytest.mark.asyncio
async def test_reveal_specific_secret_success__happy_path():
    # ARRANGE
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_notifier = AsyncMock()

    #1: Simular la respuesta de get_player_secrets!!!
    secret_to_reveal = SecretCard(
        secret_id=10, game_id=1, player_id=3, role=PlayerRole.INNOCENT
    )
    mock_read.get_player_secrets.return_value = [
        SecretCard(
            secret_id=9, game_id=1, player_id=3, role=PlayerRole.ACCOMPLICE
        ),
        secret_to_reveal,
    ]
    mock_write.reveal_secret_card.return_value = ResponseStatus.OK
    mock_read.get_secret.return_value = secret_to_reveal

    effect = RevealSpecificSecretEffect(mock_read, mock_write, mock_notifier)

    # ACT
    result = await effect.execute(
        game_id=1,
        player_id=2,
        card_ids=[7],
        target_player_id=3,
        target_secret_id=10,
    )

    # ASSERT
    assert result == GameFlowStatus.CONTINUE
    # Puede llamarse más de una vez por lógica extra (SD), verificamos que al menos se consultó el dueño.
    assert any(call.kwargs == {"game_id": 1, "player_id": 3} for call in mock_read.get_player_secrets.mock_calls)
    mock_write.reveal_secret_card.assert_called_once_with(
        secret_id=10, game_id=1, is_revealed=True
    )
    mock_notifier.notify_secret_revealed.assert_awaited_once_with(
        game_id=1, secret_id=10, player_role=PlayerRole.INNOCENT, player_id=3
    )


@pytest.mark.asyncio
async def test_reveal_specific_secret_secret_not_found__sad_path():
    # ARRANGE
    mock_read = MagicMock()
    effect = RevealSpecificSecretEffect(mock_read, MagicMock(), AsyncMock())

    #2: Simular que el secreto no está en la lista!!!
    mock_read.get_player_secrets.return_value = [
        SecretCard(
            secret_id=9, game_id=1, player_id=3, role=PlayerRole.ACCOMPLICE
        )
    ]

    # ACT & ASSERT
    with pytest.raises(
        ResourceNotFound, match="El secreto 10 no pertenece al jugador 3."
    ):
        await effect.execute(1, 2, [7], target_player_id=3, target_secret_id=10)


@pytest.mark.asyncio
async def test_reveal_specific_secret_no_target_id__sad_path():
    # ARRANGE
    effect = RevealSpecificSecretEffect(MagicMock(), MagicMock(), AsyncMock())

    # ACT & ASSERT
    with pytest.raises(
        InvalidAction,
        match="Este efecto requiere un jugador y un secreto objetivo.",
    ):
        await effect.execute(
            1, 2, [7], target_player_id=3, target_secret_id=None
        )

    with pytest.raises(
        InvalidAction,
        match="Este efecto requiere un jugador y un secreto objetivo.",
    ):
        await effect.execute(
            1, 2, [7], target_player_id=None, target_secret_id=10
        )


@pytest.mark.asyncio
async def test_reveal_specific_secret_reveal_fails__sad_path():
    # ARRANGE
    mock_read = MagicMock()
    mock_write = MagicMock()
    effect = RevealSpecificSecretEffect(mock_read, mock_write, AsyncMock())

    #3: Simular la respuesta de get_player_secrets!!!
    secret_to_reveal = SecretCard(
        secret_id=10, game_id=1, player_id=3, role=PlayerRole.INNOCENT
    )
    mock_read.get_player_secrets.return_value = [secret_to_reveal]
    mock_write.reveal_secret_card.return_value = ResponseStatus.ERROR
    mock_read.get_secret.return_value = secret_to_reveal

    # ACT & ASSERT
    with pytest.raises(
        InternalGameError,
        match="Fallo al revelar el secreto en la base de datos.",
    ):
        await effect.execute(
            game_id=1,
            player_id=2,
            card_ids=[7],
            target_player_id=3,
            target_secret_id=10,
        )


# =======================
# RevealChosenSecretEffect
# =======================


@pytest.mark.asyncio
async def test_reveal_chosen_secret_success__happy_path():
    # ARRANGE
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_notifier = AsyncMock()
    effect = RevealChosenSecretEffect(mock_read, mock_write, mock_notifier)
    # effect._move_cards_to_played_area = AsyncMock()
    effect._prompt_for_chosen_secret = AsyncMock()
    # ACT
    result = await effect.execute(
        game_id=1, player_id=2, card_ids=[7], target_player_id=3
    )
    # ASSERT
    # effect._move_cards_to_played_area.assert_awaited_once_with(1, [7], 2)
    effect._prompt_for_chosen_secret.assert_awaited_once_with(1, 3, 2)
    assert result == GameFlowStatus.PAUSED


@pytest.mark.asyncio
async def test_reveal_chosen_secret_no_target_player_id__sad_path():
    # ARRANGE
    effect = RevealChosenSecretEffect(MagicMock(), MagicMock(), AsyncMock())
    # ACT & ASSERT
    with pytest.raises(InvalidAction):
        await effect.execute(1, 2, [7], target_player_id=None)


@pytest.mark.asyncio
async def test_prompt_for_chosen_secret_success__happy_path():
    # ARRANGE
    effect = RevealChosenSecretEffect(MagicMock(), MagicMock(), AsyncMock())
    effect.notifier.notify_player_to_reveal_secret = AsyncMock()
    # ACT
    await effect._prompt_for_chosen_secret(1, 2, 3)
    # ASSERT
    effect.write.set_game_action_state.assert_called_once_with(
        game_id=1,
        state=GameActionState.AWAITING_REVEAL_FOR_CHOICE,
        prompted_player_id=2,
        initiator_id=3,
    )
    effect.notifier.notify_player_to_reveal_secret.assert_awaited_once_with(
        1, 2
    )


# =======================
# HideSecretEffect
# =======================


@pytest.mark.asyncio
async def test_hide_secret_success__happy_path():
    # ARRANGE
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_notifier = AsyncMock()

    # Creamos un mock de Game COMPLETO y REALISTA.
    secret_to_hide = SecretCard(
        secret_id=10,
        game_id=1,
        player_id=3,
        role=PlayerRole.MURDERER,
        is_revealed=True,
    )
    player_with_secret = PlayerInGame(
        player_id=3,
        player_name="Víctima",
        secrets=[secret_to_hide],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    host_player_info = PlayerInfo(
        player_id=1,
        player_name="Host",
        player_birth_date=date(1990, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )

    mock_game = Game(
        id=1,
        name="Test Game",
        min_players=2,
        max_players=4,
        host=host_player_info,
        status=GameStatus.IN_PROGRESS,
        players=[player_with_secret],
    )
    
    mock_read.get_secret.return_value = secret_to_hide
    mock_read.get_game.return_value = mock_game
    mock_write.reveal_secret_card.return_value = ResponseStatus.OK

    effect = HideSecretEffect(mock_read, mock_write, mock_notifier)

    # ACT
    result = await effect.execute(
        game_id=1, player_id=2, card_ids=[7], target_secret_id=10
    )

    # ASSERT
    mock_read.get_game.assert_called_once_with(1)
    mock_write.reveal_secret_card.assert_called_once_with(
        secret_id=10, game_id=1, is_revealed=False
    )
    mock_notifier.notify_secret_hidden.assert_awaited_once_with(
        game_id=1, secret_id=10, player_id=3
    )
    assert result == GameFlowStatus.CONTINUE


@pytest.mark.asyncio
async def test_hide_secret_already_hidden_fails__sad_path():
    # ARRANGE
    mock_read = MagicMock()

    secret_already_hidden = SecretCard(
        secret_id=10,
        game_id=1,
        player_id=3,
        role=PlayerRole.MURDERER,
        is_revealed=False,
    )
    player_with_secret = PlayerInGame(
        player_id=3,
        player_name="Víctima",
        secrets=[secret_already_hidden],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    host_player_info = PlayerInfo(
        player_id=1,
        player_name="Host",
        player_birth_date=date(1990, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )

    mock_game = Game(
        id=1,
        name="Test Game",
        min_players=2,
        max_players=4,
        host=host_player_info,
        status=GameStatus.IN_PROGRESS,
        players=[player_with_secret],
    )

    mock_read.get_game.return_value = mock_game
    mock_read.get_secret.return_value = secret_already_hidden

    effect = HideSecretEffect(mock_read, MagicMock(), AsyncMock())

    # ACT & ASSERT
    with pytest.raises(ActionConflict, match="el secreto ya está oculto"):
        await effect.execute(
            game_id=1, player_id=2, card_ids=[7], target_secret_id=10
        )


@pytest.mark.asyncio
async def test_hide_secret_no_target_id__sad_path():
    # ARRANGE
    effect = HideSecretEffect(MagicMock(), MagicMock(), AsyncMock())

    # ACT & ASSERT
    with pytest.raises(InvalidAction, match="Se requiere un secreto objetivo"):
        await effect.execute(1, 2, [7], target_secret_id=None)


# =======================
# StealSecretEffect
# =======================


@pytest.mark.asyncio
async def test_steal_secret_success__happy_path():
    # ARRANGE
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_notifier = AsyncMock()
    effect = StealSecretEffect(mock_read, mock_write, mock_notifier)
    mock_write.set_game_action_state.return_value = None
    mock_notifier.notify_player_to_reveal_secret = AsyncMock()
    # ACT
    result = await effect.execute(1, 2, [7], target_player_id=3)
    # ASSERT
    mock_write.set_game_action_state.assert_called_once_with(
        game_id=1,
        state=GameActionState.AWAITING_REVEAL_FOR_STEAL,
        prompted_player_id=3,
        initiator_id=2,
    )
    mock_notifier.notify_player_to_reveal_secret.assert_awaited_once_with(1, 3)
    assert result == GameFlowStatus.PAUSED


@pytest.mark.asyncio
async def test_steal_secret_no_target_player_id__sad_path():
    # ARRANGE
    effect = StealSecretEffect(MagicMock(), MagicMock(), AsyncMock())
    # ACT & ASSERT
    with pytest.raises(AssertionError):
        await effect.execute(1, 2, [7], target_player_id=None)


# =======================
# BeresfordUncancellableEffect
# =======================


@pytest.mark.asyncio
async def test_beresford_uncancellable_success__happy_path():
    # ARRANGE
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_notifier = AsyncMock()
    effect = BeresfordUncancellableEffect(mock_read, mock_write, mock_notifier)
    effect.notifier.notify_player_to_reveal_secret = AsyncMock()
    # ACT
    result = await effect.execute(1, 2, [7], target_player_id=3)
    # ASSERT
    effect.notifier.notify_player_to_reveal_secret.assert_awaited_once_with(
        game_id=1, player_id=3
    )
    assert result == GameFlowStatus.PAUSED


@pytest.mark.asyncio
async def test_beresford_uncancellable_no_target_player_id__sad_path():
    # ARRANGE
    effect = BeresfordUncancellableEffect(MagicMock(), MagicMock(), AsyncMock())
    # ACT & ASSERT
    with pytest.raises(AssertionError):
        await effect.execute(1, 2, [7], target_player_id=None)


@pytest.mark.asyncio
async def test_reveal_specific_secret_murderer_ends_game__happy_path():
    # ARRANGE
    mock_read = MagicMock()
    mock_write = MagicMock()
    mock_notifier = AsyncMock()

    murderer_secret = SecretCard(
        secret_id=10, game_id=1, player_id=3, role=PlayerRole.MURDERER
    )
    mock_read.get_player_secrets.return_value = [murderer_secret]
    mock_write.reveal_secret_card.return_value = ResponseStatus.OK
    mock_read.get_secret.return_value = murderer_secret
    mock_read.get_accomplice_id.return_value = 4
    mock_write.delete_game.return_value = ResponseStatus.OK

    effect = RevealSpecificSecretEffect(mock_read, mock_write, mock_notifier)

    # ACT
    result = await effect.execute(
        game_id=1,
        player_id=2,
        card_ids=[7],
        target_player_id=3,
        target_secret_id=10,
    )

    # ASSERT
    assert result == GameFlowStatus.CONTINUE
    mock_notifier.notify_secret_revealed.assert_awaited_once_with(
        game_id=1, secret_id=10, player_role=PlayerRole.MURDERER, player_id=3
    )
    mock_notifier.notify_innocents_win.assert_awaited_once_with(
        game_id=1, murderer_id=2, accomplice_id=4
    )
    mock_write.delete_game.assert_called_once_with(game_id=1)
    mock_notifier.notify_game_removed.assert_awaited_once_with(1)
