import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, ANY

from app.main import app
from app.dependencies.dependencies import get_game_manager
from app.game.game_manager import GameManager
from app.game.services.turn_service import TurnService
from app.game.helpers.validators import GameValidator
from app.game.effect_executor import EffectExecutor

from app.domain.models import Game, PlayerInGame, Card, SecretCard
from app.domain.enums import (
    GameStatus,
    CardType,
    CardLocation,
    Avatar,
    PlayerRole,
    GameActionState,
    ResponseStatus,
)
from app.api.schemas import (
    PlayCardRequest,
    RevealSecretRequest,
    PlayCardActionType,
)


@pytest.mark.asyncio
async def test_satterthwaite_quin_full_flow_ROBUST(
    mock_queries, mock_commands, mock_notificator
):
    """
    Test de integración completo para el flujo de Satterthwaite + Quin.
    """
    # =================================================================
    # ARRANGE GENERAL
    # =================================================================
    game_id = 202
    player_A_id, player_B_id, player_C_id = 1, 2, 3

    satt_card_1 = Card(
        card_id=1,
        game_id=game_id,
        card_type=CardType.MR_SATTERTHWAITE,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    quin_card = Card(
        card_id=2,
        game_id=game_id,
        card_type=CardType.HARLEY_QUIN,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    satt_card_2 = Card(
        card_id=3,
        game_id=game_id,
        card_type=CardType.MR_SATTERTHWAITE,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )

    victim_B_secret = SecretCard(
        secret_id=101,
        game_id=game_id,
        player_id=player_B_id,
        role=PlayerRole.ACCOMPLICE,
        is_revealed=False,
    )
    victim_C_secret = SecretCard(
        secret_id=102,
        game_id=game_id,
        player_id=player_C_id,
        role=PlayerRole.MURDERER,
        is_revealed=False,
    )

    player_A = PlayerInGame(
        player_id=player_A_id,
        player_name="Ladrón",
        turn_order=1,
        hand=[satt_card_1, quin_card, satt_card_2],
        secrets=[],
        player_birth_date="2000-01-01",
        player_avatar=Avatar.DEFAULT,
    )
    player_B = PlayerInGame(
        player_id=player_B_id,
        player_name="Víctima 1",
        turn_order=2,
        hand=[],
        secrets=[victim_B_secret],
        player_birth_date="2000-01-01",
        player_avatar=Avatar.DEFAULT,
    )
    player_C = PlayerInGame(
        player_id=player_C_id,
        player_name="Víctima 2",
        turn_order=3,
        hand=[],
        secrets=[victim_C_secret],
        player_birth_date="2000-01-01",
        player_avatar=Avatar.DEFAULT,
    )

    mock_game = Game(
        id=game_id,
        name="Partida de Robos",
        status=GameStatus.IN_PROGRESS,
        min_players=3,
        max_players=4,
        host=player_A,
        players=[player_A, player_B, player_C],
        current_turn_player_id=player_A_id,
        action_state=GameActionState.NONE,
        prompted_player_id=None,
        action_initiator_id=None,
        deck=[],
        discard_pile=[],
        draft=[],
    )

    mock_queries.get_game.return_value = mock_game
    mock_commands.create_set.return_value = 1
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_set.return_value = [satt_card_1, quin_card]
    mock_queries.get_card.side_effect = lambda card_id, game_id: {
        1: satt_card_1,
        2: quin_card,
        3: satt_card_2,
    }.get(card_id)
    mock_commands.create_pending_action.return_value = ResponseStatus.OK
    mock_commands.set_game_action_state.return_value = ResponseStatus.OK
    mock_queries.get_pending_action.return_value = None

    def override_get_game_manager():
        validator = GameValidator(mock_queries)
        effect_executor = EffectExecutor(
            mock_queries, mock_commands, mock_notificator
        )
        mock_turn_utils = MagicMock()
        turn_service = TurnService(
            mock_queries,
            mock_commands,
            validator,
            mock_notificator,
            effect_executor,
            mock_turn_utils,
        )
        return GameManager(
            MagicMock(), MagicMock(), MagicMock(), turn_service, MagicMock()
        )

    app.dependency_overrides[get_game_manager] = override_get_game_manager
    client = TestClient(app)

    # =================================================================
    # ACTO I: EL ROBO INICIAL (CREAR SET)
    # =================================================================
    play_req_1 = PlayCardRequest(
        game_id=game_id,
        player_id=player_A_id,
        card_ids=[satt_card_1.card_id, quin_card.card_id],
        action_type=PlayCardActionType.FORM_NEW_SET,
        target_player_id=player_B_id,
    )
    response_play_1 = client.post(
        f"/api/games/{game_id}/actions/play", json=play_req_1.model_dump()
    )

    # Satterthwaite + Quin enters PENDING_NSF (is cancellable)
    assert response_play_1.status_code == 200, response_play_1.text
    mock_commands.create_pending_action.assert_called_once()
    mock_commands.set_game_action_state.assert_called_once_with(
        game_id=game_id,
        state=GameActionState.PENDING_NSF,
        prompted_player_id=None,
        initiator_id=player_A_id,
    )
    # Effect would execute after NSF resolution

    mock_commands.reveal_secret_card.return_value = ResponseStatus.OK

    # =================================================================
    # ACTO II: LA VÍCTIMA 1 RESPONDE
    # =================================================================
    mock_game.action_state = GameActionState.AWAITING_REVEAL_FOR_STEAL
    mock_game.prompted_player_id = player_B_id
    mock_game.action_initiator_id = player_A_id

    mock_queries.get_player_secrets.return_value = [victim_B_secret]

    reveal_req_1 = RevealSecretRequest(
        player_id=player_B_id,
        secret_id=victim_B_secret.secret_id,
        game_id=game_id,
    )
    response_reveal_1 = client.post(
        f"/api/games/{game_id}/actions/reveal-secret",
        json=reveal_req_1.model_dump(),
    )

    assert response_reveal_1.status_code == 200, response_reveal_1.text
    mock_commands.reveal_secret_card.assert_any_call(
        secret_id=victim_B_secret.secret_id, game_id=game_id, is_revealed=True
    )
    mock_commands.change_secret_owner.assert_called_once_with(
        secret_id=victim_B_secret.secret_id,
        new_owner_id=player_A_id,
        game_id=game_id,
    )
    mock_commands.reveal_secret_card.assert_any_call(
        secret_id=victim_B_secret.secret_id, game_id=game_id, is_revealed=False
    )
    mock_commands.clear_game_action_state.assert_called_once_with(
        game_id=game_id
    )
    mock_notificator.notify_secret_revealed.assert_awaited_once_with(
        game_id=game_id,
        secret_id=victim_B_secret.secret_id,
        player_role=victim_B_secret.role,
        player_id=player_B_id,
    )
    mock_notificator.notify_secret_stolen.assert_awaited_once_with(
        game_id, thief_id=player_A_id, victim_id=player_B_id
    )

    # =================================================================
    # ACTO III: DOBLANDO LA APUESTA (AÑADIR A SET)
    # =================================================================
    mock_commands.reset_mock()
    mock_notificator.reset_mock()
    mock_game.action_state = GameActionState.NONE
    player_A.hand = [satt_card_2]

    existing_set = [satt_card_1, quin_card]
    mock_queries.get_set.return_value = existing_set

    play_req_2 = PlayCardRequest(
        game_id=game_id,
        player_id=player_A_id,
        card_ids=[satt_card_2.card_id],
        action_type=PlayCardActionType.ADD_TO_EXISTING_SET,
        target_player_id=player_C_id,
        target_set_id=1,
    )
    response_play_2 = client.post(
        f"/api/games/{game_id}/actions/play", json=play_req_2.model_dump()
    )

    # Adding to Satterthwaite+Quin set is still cancellable, enters PENDING_NSF
    assert response_play_2.status_code == 200, response_play_2.text
    mock_commands.create_pending_action.assert_called()  # Enters PENDING_NSF
    mock_commands.set_game_action_state.assert_called_once_with(
        game_id=game_id,
        state=GameActionState.PENDING_NSF,
        prompted_player_id=None,
        initiator_id=player_A_id,
    )
    # Effect would execute after NSF resolution

    app.dependency_overrides = {}
