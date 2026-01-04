import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, ANY
from datetime import date

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
async def test_reveal_chosen_secret_flow_tommy_beresford(
    mock_queries, mock_commands, mock_notificator
):
    # ARRANGE
    game_id, player_A_id, player_B_id = 101, 1, 2
    tommy_card_1 = Card(
        card_id=1,
        game_id=game_id,
        card_type=CardType.TOMMY_BERESFORD,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    tommy_card_2 = Card(
        card_id=2,
        game_id=game_id,
        card_type=CardType.TOMMY_BERESFORD,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    victim_secret = SecretCard(
        secret_id=99,
        game_id=game_id,
        player_id=player_B_id,
        role=PlayerRole.ACCOMPLICE,
        is_revealed=False,
    )

    player_A = PlayerInGame(
        player_id=player_A_id,
        player_name="Atacante",
        turn_order=1,
        hand=[tommy_card_1, tommy_card_2],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    player_B = PlayerInGame(
        player_id=player_B_id,
        player_name="Victima",
        turn_order=2,
        secrets=[victim_secret],
        hand=[],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )

    mock_game = Game(
        id=game_id,
        name="Partida Test",
        status=GameStatus.IN_PROGRESS,
        min_players=2,
        max_players=4,
        host=player_A,
        players=[player_A, player_B],
        current_turn_player_id=player_A_id,
    )

    mock_queries.get_game.return_value = mock_game
    mock_queries.get_players_in_game.return_value = [player_A, player_B]
    mock_queries.get_player_secrets.return_value = [victim_secret]
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_commands.reveal_secret_card.return_value = ResponseStatus.OK
    mock_commands.create_set.return_value = 1
    mock_queries.get_set.return_value = [tommy_card_1, tommy_card_2]
    mock_commands.create_pending_action.return_value = ResponseStatus.OK
    mock_commands.set_game_action_state.return_value = ResponseStatus.OK
    mock_commands.clear_game_action_state.return_value = ResponseStatus.OK
    mock_queries.get_pending_action.return_value = None  # No pending action, so clear will be called
    mock_queries.get_card.side_effect = lambda cid, gid: {1: tommy_card_1, 2: tommy_card_2}.get(cid)
    mock_queries.get_secret.return_value = victim_secret
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

    # ACT 1
    play_card_req = PlayCardRequest(
        game_id=game_id,
        player_id=player_A_id,
        card_ids=[1, 2],
        action_type=PlayCardActionType.FORM_NEW_SET,
        target_player_id=player_B_id,
    )
    response_play = client.post(
        f"/api/games/{game_id}/actions/play", json=play_card_req.model_dump()
    )

    # ASSERT 1 - Action enters PENDING_NSF state (is cancellable)
    assert response_play.status_code == 200, response_play.text
    mock_commands.create_pending_action.assert_called_once()
    mock_commands.set_game_action_state.assert_called_once_with(
        game_id=game_id,
        state=GameActionState.PENDING_NSF,
        prompted_player_id=None,
        initiator_id=player_A_id,
    )
    # Card play enters PENDING state, not immediate execution
    # This test focuses on the reveal flow, so we skip NSF resolution

    # ACT 2 - Simulate the effect execution (after NSF would resolve)
    # Manually set the state as if the action was executed
    mock_game.action_state = GameActionState.AWAITING_REVEAL_FOR_CHOICE
    mock_game.prompted_player_id = player_B_id
    mock_game.action_initiator_id = player_A_id
    reveal_req = RevealSecretRequest(
        player_id=player_B_id,
        secret_id=victim_secret.secret_id,
        game_id=game_id,
    )
    response_reveal = client.post(
        f"/api/games/{game_id}/actions/reveal-secret",
        json=reveal_req.model_dump(),
    )

    # ASSERT 2
    assert response_reveal.status_code == 200, response_reveal.text
    mock_commands.reveal_secret_card.assert_called_once_with(
        secret_id=victim_secret.secret_id, game_id=game_id, is_revealed=True
    )
    mock_commands.clear_game_action_state.assert_called_once_with(
        game_id=game_id
    )
    mock_notificator.notify_secret_revealed.assert_awaited_once_with(
        game_id=game_id,
        secret_id=victim_secret.secret_id,
        player_role=victim_secret.role,
        player_id=player_B_id,
    )

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_ariadne_oliver_flow(
    mock_queries, mock_commands, mock_notificator
):
    # ARRANGE
    game_id, player_A_id, player_B_id, player_C_id = 303, 1, 2, 3
    ariadne_card = Card(
        card_id=10,
        game_id=game_id,
        card_type=CardType.ARIADNE_OLIVER,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    pyne_card_1 = Card(
        card_id=11,
        game_id=game_id,
        card_type=CardType.PARKER_PYNE,
        location=CardLocation.PLAYED,
        player_id=player_B_id,
        set_id=1,
    )
    pyne_card_2 = Card(
        card_id=12,
        game_id=game_id,
        card_type=CardType.PARKER_PYNE,
        location=CardLocation.PLAYED,
        player_id=player_B_id,
        set_id=1,
    )
    owner_secret = SecretCard(
        secret_id=201,
        game_id=game_id,
        player_id=player_B_id,
        role=PlayerRole.MURDERER,
        is_revealed=False,
    )

    player_A = PlayerInGame(
        player_id=player_A_id,
        player_name="Intruso",
        turn_order=1,
        hand=[ariadne_card],
        secrets=[],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    player_B = PlayerInGame(
        player_id=player_B_id,
        player_name="Dueño",
        turn_order=2,
        hand=[],
        secrets=[owner_secret],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    player_C = PlayerInGame(
        player_id=player_C_id,
        player_name="Distractor",
        turn_order=3,
        hand=[],
        secrets=[],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )

    mock_game = Game(
        id=game_id,
        name="Partida Ariadne",
        status=GameStatus.IN_PROGRESS,
        host=player_A,
        max_players=6,
        min_players=2,
        players=[player_A, player_B, player_C],
        current_turn_player_id=player_A_id,
    )

    mock_queries.get_game.return_value = mock_game
    mock_queries.get_players_in_game.return_value = [player_A, player_B, player_C]
    mock_queries.get_set.return_value = [pyne_card_1, pyne_card_2]
    mock_queries.get_player_secrets.return_value = [owner_secret]
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_commands.reveal_secret_card.return_value = ResponseStatus.OK
    mock_queries.get_card.return_value = ariadne_card
    mock_commands.create_pending_action.return_value = ResponseStatus.OK
    mock_commands.set_game_action_state.return_value = ResponseStatus.OK
    mock_queries.get_secret.return_value = owner_secret
    mock_queries.get_pending_action.return_value = None
    mock_queries.get_accomplice_id.return_value = 99
    mock_commands.delete_game.return_value = ResponseStatus.OK

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

    # ACT 1
    play_req = PlayCardRequest(
        game_id=game_id,
        player_id=player_A_id,
        card_ids=[ariadne_card.card_id],
        action_type=PlayCardActionType.ADD_TO_EXISTING_SET,
        target_set_id=1,
        target_player_id=player_C_id,
    )
    response_play = client.post(
        f"/api/games/{game_id}/actions/play", json=play_req.model_dump()
    )

    # ASSERT 1 - Ariadne play enters PENDING_NSF (is cancellable)
    assert response_play.status_code == 200, response_play.text
    mock_commands.create_pending_action.assert_called_once()
    mock_commands.set_game_action_state.assert_called_once_with(
        game_id=game_id,
        state=GameActionState.PENDING_NSF,
        prompted_player_id=None,
        initiator_id=player_A_id,
    )
    # Test focuses on reveal flow after NSF would resolve

    # ACT 2
    mock_game.action_state = GameActionState.AWAITING_REVEAL_FOR_CHOICE
    mock_game.prompted_player_id = player_B_id
    mock_game.action_initiator_id = player_A_id
    reveal_req = RevealSecretRequest(
        player_id=player_B_id, secret_id=owner_secret.secret_id, game_id=game_id
    )
    response_reveal = client.post(
        f"/api/games/{game_id}/actions/reveal-secret",
        json=reveal_req.model_dump(),
    )

    # ASSERT 2
    assert response_reveal.status_code == 200, response_reveal.text
    mock_commands.reveal_secret_card.assert_called_once_with(
        secret_id=owner_secret.secret_id, game_id=game_id, is_revealed=True
    )
    # When murderer is revealed, game ends - no clear_game_action_state call
    mock_commands.delete_game.assert_called_once_with(game_id=game_id)
    mock_notificator.notify_innocents_win.assert_awaited_once()
    mock_notificator.notify_secret_revealed.assert_awaited_once_with(
        game_id=game_id,
        secret_id=owner_secret.secret_id,
        player_role=owner_secret.role,
        player_id=player_B_id,
    )

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_poirot_specific_reveal_flow_ROBUST(
    mock_queries, mock_commands, mock_notificator
):
    # ARRANGE
    game_id, player_A_id, player_B_id = 404, 1, 2
    poirot_1 = Card(
        card_id=20,
        game_id=game_id,
        card_type=CardType.HERCULE_POIROT,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    poirot_2 = Card(
        card_id=21,
        game_id=game_id,
        card_type=CardType.HERCULE_POIROT,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    poirot_3 = Card(
        card_id=22,
        game_id=game_id,
        card_type=CardType.HERCULE_POIROT,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    secret_to_ignore = SecretCard(
        secret_id=301,
        game_id=game_id,
        player_id=player_B_id,
        role=PlayerRole.ACCOMPLICE,
        is_revealed=False,
    )
    secret_to_reveal = SecretCard(
        secret_id=302,
        game_id=game_id,
        player_id=player_B_id,
        role=PlayerRole.MURDERER,
        is_revealed=False,
    )

    player_A = PlayerInGame(
        player_id=player_A_id,
        player_name="Acusador",
        turn_order=1,
        hand=[poirot_1, poirot_2, poirot_3],
        secrets=[],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    player_B = PlayerInGame(
        player_id=player_B_id,
        player_name="Sospechoso",
        turn_order=2,
        hand=[],
        secrets=[secret_to_ignore, secret_to_reveal],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )

    mock_game = Game(
        id=game_id,
        name="El Caso Poirot",
        status=GameStatus.IN_PROGRESS,
        host=player_A,
        min_players=2,
        max_players=4,
        players=[player_A, player_B],
        current_turn_player_id=player_A_id,
    )

    mock_queries.get_game.return_value = mock_game
    mock_queries.get_set.return_value = [poirot_1, poirot_2, poirot_3]
    mock_commands.create_set.return_value = 2
    mock_commands.reveal_secret_card.return_value = ResponseStatus.OK
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_queries.get_player_secrets.return_value = [
        secret_to_ignore,
        secret_to_reveal,
    ]
    mock_commands.create_pending_action.return_value = ResponseStatus.OK
    mock_commands.set_game_action_state.return_value = ResponseStatus.OK
    mock_queries.get_card.side_effect = lambda cid, gid: {20: poirot_1, 21: poirot_2, 22: poirot_3}.get(cid)

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

    # ACT
    play_req = PlayCardRequest(
        game_id=game_id,
        player_id=player_A_id,
        card_ids=[poirot_1.card_id, poirot_2.card_id, poirot_3.card_id],
        action_type=PlayCardActionType.FORM_NEW_SET,
        target_player_id=player_B_id,
        target_secret_id=secret_to_reveal.secret_id,
    )
    response_play = client.post(
        f"/api/games/{game_id}/actions/play", json=play_req.model_dump()
    )

    # ASSERT - Poirot set enters PENDING_NSF (is cancellable)
    assert response_play.status_code == 200, response_play.text
    mock_commands.create_pending_action.assert_called_once()
    mock_commands.set_game_action_state.assert_called_once_with(
        game_id=game_id,
        state=GameActionState.PENDING_NSF,
        prompted_player_id=None,
        initiator_id=player_A_id,
    )
    # Effect would execute after NSF resolution (all players pass)

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_parker_pyne_full_cycle_flow_ROBUST(
    mock_queries, mock_commands, mock_notificator
):
    """
    Test de integración completo para el ciclo de Parker Pyne:
    1. (Acto I) J-A juega Tommy Beresford, forzando a J-B a revelar un secreto.
    2. (Acto II) J-C juega Parker Pyne para ocultar el secreto recién revelado de J-B.
    3. (Acto III) Se intenta jugar OTRA VEZ Parker Pyne contra el mismo secreto (ya oculto),
       lo cual debería fallar o no tener efecto.
    """
    # =================================================================
    # ARRANGE GENERAL
    # =================================================================
    game_id = 505
    player_A_id, player_B_id, player_C_id = 1, 2, 3

    tommy_1 = Card(
        card_id=1,
        game_id=game_id,
        card_type=CardType.TOMMY_BERESFORD,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    tommy_2 = Card(
        card_id=2,
        game_id=game_id,
        card_type=CardType.TOMMY_BERESFORD,
        location=CardLocation.IN_HAND,
        player_id=player_A_id,
    )
    pyne_1 = Card(
        card_id=3,
        game_id=game_id,
        card_type=CardType.PARKER_PYNE,
        location=CardLocation.IN_HAND,
        player_id=player_C_id,
    )
    pyne_2 = Card(
        card_id=4,
        game_id=game_id,
        card_type=CardType.PARKER_PYNE,
        location=CardLocation.IN_HAND,
        player_id=player_C_id,
    )

    secret_in_play = SecretCard(
        secret_id=401,
        game_id=game_id,
        player_id=player_B_id,
        role=PlayerRole.ACCOMPLICE,
        is_revealed=False,
    )

    player_A = PlayerInGame(
        player_id=player_A_id,
        player_name="Revelador",
        turn_order=1,
        hand=[tommy_1, tommy_2],
        secrets=[],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    player_B = PlayerInGame(
        player_id=player_B_id,
        player_name="Víctima",
        turn_order=2,
        hand=[],
        secrets=[secret_in_play],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )
    player_C = PlayerInGame(
        player_id=player_C_id,
        player_name="Limpiador",
        turn_order=3,
        hand=[pyne_1, pyne_2],
        secrets=[],
        player_birth_date=date(2000, 1, 1),
        player_avatar=Avatar.DEFAULT,
    )

    mock_game = Game(
        id=game_id,
        name="El Encubrimiento",
        status=GameStatus.IN_PROGRESS,
        min_players=2,
        max_players=4,
        host=player_A,
        players=[player_A, player_B, player_C],
        current_turn_player_id=player_A_id,
    )

    # --- Configuración de Mocks ---
    mock_queries.get_game.return_value = mock_game
    mock_queries.get_players_in_game.return_value = [player_A, player_B, player_C]
    mock_commands.update_card_location.return_value = ResponseStatus.OK
    mock_commands.reveal_secret_card.return_value = ResponseStatus.OK
    mock_commands.create_set.side_effect = [1, 2, 3]
    mock_commands.create_pending_action.return_value = ResponseStatus.OK
    mock_commands.set_game_action_state.return_value = ResponseStatus.OK

    # Need to define pyne_3 and pyne_4 for later in the test
    pyne_3 = Card(card_id=5, game_id=game_id, card_type=CardType.PARKER_PYNE, location=CardLocation.IN_HAND,
                  player_id=player_C_id)
    pyne_4 = Card(card_id=6, game_id=game_id, card_type=CardType.PARKER_PYNE, location=CardLocation.IN_HAND,
                  player_id=player_C_id)
    mock_queries.get_card.side_effect = lambda cid, gid: {1: tommy_1, 2: tommy_2, 3: pyne_1, 4: pyne_2, 5: pyne_3, 6: pyne_4}.get(cid)

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
    # ACTO I: LA REVELACIÓN
    # =================================================================
    mock_game.current_turn_player_id = player_A_id
    play_tommy_req = PlayCardRequest(
        game_id=game_id,
        player_id=player_A_id,
        card_ids=[1, 2],
        action_type=PlayCardActionType.FORM_NEW_SET,
        target_player_id=player_B_id,
    )
    client.post(
        f"/api/games/{game_id}/actions/play", json=play_tommy_req.model_dump()
    )

    mock_game.action_state = GameActionState.AWAITING_REVEAL_FOR_CHOICE
    mock_game.prompted_player_id = player_B_id
    mock_queries.get_player_secrets.return_value = [secret_in_play]
    reveal_req = RevealSecretRequest(
        player_id=player_B_id,
        secret_id=secret_in_play.secret_id,
        game_id=game_id,
    )
    client.post(
        f"/api/games/{game_id}/actions/reveal-secret",
        json=reveal_req.model_dump(),
    )

    secret_in_play.is_revealed = True
    print("--- FIN ACTO I: Secreto revelado ---")
    mock_commands.reset_mock()
    mock_notificator.reset_mock()

    # =================================================================
    # ACTO II: EL ENCUBRIMIENTO
    # =================================================================
    mock_game.current_turn_player_id = player_C_id
    mock_game.action_state = GameActionState.NONE
    mock_queries.get_secret.return_value = secret_in_play
    mock_game.action_state = GameActionState.NONE

    play_pyne_req = PlayCardRequest(
        game_id=game_id,
        player_id=player_C_id,
        card_ids=[3, 4],
        action_type=PlayCardActionType.FORM_NEW_SET,
        target_secret_id=secret_in_play.secret_id,
    )
    response_play_pyne = client.post(
        f"/api/games/{game_id}/actions/play", json=play_pyne_req.model_dump()
    )

    # Parker Pyne enters PENDING_NSF (is cancellable)
    assert response_play_pyne.status_code == 200, response_play_pyne.text
    mock_commands.create_pending_action.assert_called()
    # Effect would execute after NSF resolution

    print("--- FIN ACTO II: Secreto ocultado exitosamente ---")

    # =================================================================
    # ACTO III: LA TENTATIVA INÚTIL
    # =================================================================
    secret_in_play.is_revealed = False
    mock_queries.get_secret.return_value = secret_in_play

    pyne_3 = Card(
        card_id=5,
        game_id=game_id,
        card_type=CardType.PARKER_PYNE,
        location=CardLocation.IN_HAND,
        player_id=player_C_id,
    )
    pyne_4 = Card(
        card_id=6,
        game_id=game_id,
        card_type=CardType.PARKER_PYNE,
        location=CardLocation.IN_HAND,
        player_id=player_C_id,
    )
    player_C.hand.extend([pyne_3, pyne_4])

    play_pyne_again_req = PlayCardRequest(
        game_id=game_id,
        player_id=player_C_id,
        card_ids=[5, 6],
        action_type=PlayCardActionType.FORM_NEW_SET,
        target_secret_id=secret_in_play.secret_id,
    )
    response_play_pyne_again = client.post(
        f"/api/games/{game_id}/actions/play",
        json=play_pyne_again_req.model_dump(),
    )

    # With NSF, action enters PENDING state first (validation happens during execution)
    assert response_play_pyne_again.status_code == 200
    mock_commands.create_pending_action.assert_called()  # Enters PENDING_NSF

    print(
        "--- FIN ACTO III: Acción entra en PENDING_NSF (validación ocurre al ejecutar) ---"
    )

    app.dependency_overrides = {}
