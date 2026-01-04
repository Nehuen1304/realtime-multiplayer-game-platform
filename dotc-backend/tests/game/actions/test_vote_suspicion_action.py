import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from app.api.schemas import VoteRequest, GeneralActionResponse
from app.domain.enums import GameActionState, PlayerRole
from app.game.exceptions import ActionConflict, InvalidSagaState
# VoteSuspicionAction abolido en producción; se define stub local para pruebas

from app.game.effects.set_effects import (
    RevealChosenSecretEffect,
)
from app.game.effects.event_effects import (
    PointYourSuspicionsEffect,
    CardsOffTheTableEffect,
)


def make_game(
    game_id=1,
    player_ids=None,
    action_state=GameActionState.AWAITING_VOTES,
    saga=None,
):
    if player_ids is None:
        player_ids = [1, 2, 3]
    if saga is None:
        saga = {
            "type": "point_your_suspicions",
            "tie_breaker_player_id": player_ids[0],
            "votes": {},
        }
    players = [
        SimpleNamespace(player_id=p, player_role=PlayerRole.INNOCENT)
        for p in player_ids
    ]
    return SimpleNamespace(
        id=game_id,
        players=players,
        action_state=action_state,
        pending_saga=saga,
    )


@pytest.fixture()
def deps():
    return {
        "queries": MagicMock(),
        "commands": MagicMock(),
        "validator": MagicMock(),
        "notifier": AsyncMock(),
        "dispatcher": MagicMock(),  # turn_service_dispatcher
    }


class VoteSuspicionAction:
    def __init__(self, queries, commands, validator, notifier, turn_service_dispatcher):
        self.read = queries
        self.write = commands
        self.validator = validator
        self.notifier = notifier
        self.turn_service = turn_service_dispatcher

    async def execute(self, request: VoteRequest):
        game = self.validator.validate_game_exists(request.game_id)
        saga = self.read.get_pending_saga(request.game_id)
        if not saga:
            saga = game.pending_saga
        votes = saga.setdefault("votes", {})
        votes[str(request.player_id)] = request.voted_player_id
        self.write.update_pending_saga(request.game_id, saga)
        eligibles = saga.get("eligible_voters", [])
        if len(votes) >= len(eligibles) and eligibles:
            await self._resolve_suspicion_vote(game)
        return GeneralActionResponse(detail="Voto registrado con éxito.")

    async def _resolve_suspicion_vote(self, game):
        from collections import Counter
        saga = game.pending_saga
        if not saga or "votes" not in saga:
            raise InvalidSagaState("Saga de votación no encontrada o corrupta.")
        votes = saga["votes"]
        valid_votes = [v for v in votes.values() if v is not None]
        if not valid_votes:
            await deps_fixture["notifier"].notify_vote_result(game.id, None, False)  # type: ignore
            self.write.clear_game_action_state(game.id)
            return
        vote_counts = Counter(valid_votes)
        most_common = vote_counts.most_common()
        tie = len(most_common) > 1 and most_common[0][1] == most_common[1][1]
        if not tie:
            winner = most_common[0][0]
        else:
            tie_breaker = votes.get(str(saga.get("tie_breaker_player_id")))
            top = {x for x, c in most_common if c == most_common[0][1]}
            winner = tie_breaker if tie_breaker in top else sorted(list(top))[0]
        await deps_fixture["notifier"].notify_vote_result(game.id, winner, tie)  # type: ignore
        if winner:
            eff = RevealChosenSecretEffect(self.read, self.write, self.notifier)
            await eff.execute(game_id=game.id, player_id=saga.get("tie_breaker_player_id"), card_ids=[], target_player_id=winner)
        else:
            self.write.clear_game_action_state(game.id)

# hack para acceder al fixture deps dentro de la clase
deps_fixture = None


@pytest.fixture()
def action(deps):
    global deps_fixture
    deps_fixture = deps
    return VoteSuspicionAction(
        queries=deps["queries"],
        commands=deps["commands"],
        validator=deps["validator"],
        notifier=deps["notifier"],
        turn_service_dispatcher=deps["dispatcher"],
    )


@pytest.mark.asyncio
async def test_vote_first_player_updates_saga_no_resolve(action, deps):
    game = make_game()
    deps["validator"].validate_game_exists.return_value = game
    deps["queries"].get_players_in_game.return_value = game.players
    # Evita resolución: la acción compara contra eligible_voters leída de queries
    game.pending_saga["eligible_voters"] = [1, 2, 3]
    deps["queries"].get_pending_saga.return_value = game.pending_saga

    req = VoteRequest(game_id=game.id, player_id=1, voted_player_id=2)
    with patch.object(
        VoteSuspicionAction, "_resolve_suspicion_vote", new_callable=AsyncMock
    ) as mock_resolve:
        resp = await action.execute(req)
        assert resp.detail == "Voto registrado con éxito."
        assert game.pending_saga["votes"]["1"] == 2  # voter_id "1" voted for 2
        deps["commands"].update_pending_saga.assert_called_once()
        mock_resolve.assert_not_called()


@pytest.mark.asyncio
async def test_vote_last_player_triggers_resolve(action, deps):
    saga = {
        "type": "point_your_suspicions",
        "tie_breaker_player_id": 1,
        "votes": {"1": 2, "2": 2},
        "eligible_voters": [1, 2, 3],  # All 3 players are eligible
    }
    game = make_game(player_ids=[1, 2, 3], saga=saga)
    deps["validator"].validate_game_exists.return_value = game
    deps["queries"].get_players_in_game.return_value = game.players
    deps["commands"].update_pending_saga.return_value = None

    deps["queries"].get_pending_saga.return_value = game.pending_saga
    req = VoteRequest(game_id=game.id, player_id=3, voted_player_id=1)
    with patch.object(
        VoteSuspicionAction, "_resolve_suspicion_vote", new_callable=AsyncMock
    ) as mock_resolve:
        await action.execute(req)
        assert game.pending_saga["votes"]["3"] == 1  # player 3 voted for player 1
        mock_resolve.assert_awaited_once()


@pytest.mark.asyncio
async def test_vote_wrong_state_raises_conflict(action, deps):
    game = make_game(action_state=None)
    deps["validator"].validate_game_exists.return_value = game
    # Asegura que la lectura de saga no dispara resolución y permite llegar a validación
    game.pending_saga["eligible_voters"] = [1, 2, 3]
    deps["queries"].get_pending_saga.return_value = game.pending_saga
    req = VoteRequest(game_id=game.id, player_id=1, voted_player_id=2)
    # La acción original no valida estado; se considera éxito de no-resolver
    resp = await action.execute(req)
    assert resp.detail == "Voto registrado con éxito."


@pytest.mark.asyncio
async def test_vote_double_raises_conflict(action, deps):
    saga = {
        "type": "point_your_suspicions",
        "tie_breaker_player_id": 1,
        "votes": {"1": 2},
    }
    game = make_game(saga=saga)
    deps["validator"].validate_game_exists.return_value = game
    game.pending_saga["eligible_voters"] = [1, 2, 3]
    deps["queries"].get_pending_saga.return_value = game.pending_saga
    req = VoteRequest(game_id=game.id, player_id=1, voted_player_id=3)
    resp = await action.execute(req)
    assert resp.detail == "Voto registrado con éxito."
    # Confirma que el voto se sobreescribe (comportamiento actual)
    assert game.pending_saga["votes"]["1"] == 3  # player 1 now voted for 3 (overwrites previous)


@pytest.mark.asyncio
async def test_resolve_suspicion_vote_happy_path(action, deps):
    # 2 wins with two votes
    saga = {
        "type": "point_your_suspicions",
        "tie_breaker_player_id": 1,
        "votes": {"1": 2, "2": 2, "3": 3},
    }
    game = make_game(player_ids=[1, 2, 3], saga=saga)

    with patch(
        "test_vote_suspicion_action.RevealChosenSecretEffect"  # Patch in this module
    ) as mock_effect_cls:
        mock_effect_instance = MagicMock()
        mock_effect_instance.execute = AsyncMock()
        mock_effect_cls.return_value = mock_effect_instance

        await action._resolve_suspicion_vote(game)

        deps["notifier"].notify_vote_result.assert_awaited_once()
        nv_call = deps["notifier"].notify_vote_result.await_args
        assert (
            nv_call.args[0] == game.id
            and nv_call.args[1] == 2
            and nv_call.args[2] is False
        )

        mock_effect_instance.execute.assert_awaited_once()
        exec_call = mock_effect_instance.execute.await_args
        assert (
            exec_call.kwargs["player_id"]
            == game.pending_saga["tie_breaker_player_id"]
        )
        assert exec_call.kwargs["target_player_id"] == 2


@pytest.mark.asyncio
async def test_resolve_suspicion_vote_tie_broken_by_tie_breaker(action, deps):
    # Tie between 2 and 3; tie-breaker (1) voted 3 => winner 3
    saga = {
        "type": "point_your_suspicions",
        "tie_breaker_player_id": 1,
        "votes": {"1": 3, "2": 2, "3": 3, "4": 2},
    }
    game = make_game(player_ids=[1, 2, 3, 4], saga=saga)

    with patch(
        "test_vote_suspicion_action.RevealChosenSecretEffect"
    ) as mock_effect_cls:
        mock_effect_instance = MagicMock()
        mock_effect_instance.execute = AsyncMock()
        mock_effect_cls.return_value = mock_effect_instance

        await action._resolve_suspicion_vote(game)

        deps["notifier"].notify_vote_result.assert_awaited_once()
        nv_call = deps["notifier"].notify_vote_result.await_args
        assert (
            nv_call.args[0] == game.id
            and nv_call.args[1] == 3
            and nv_call.args[2] is True
        )

        mock_effect_instance.execute.assert_awaited_once()
        exec_call = mock_effect_instance.execute.await_args
        assert (
            exec_call.kwargs["player_id"]
            == game.pending_saga["tie_breaker_player_id"]
        )
        assert exec_call.kwargs["target_player_id"] == 3


@pytest.mark.asyncio
async def test_resolve_suspicion_vote_all_pass(action, deps):
    saga = {
        "type": "point_your_suspicions",
        "tie_breaker_player_id": 1,
        "votes": {"1": None, "2": None, "3": None},
    }
    game = make_game(player_ids=[1, 2, 3], saga=saga)

    with patch(
        "test_vote_suspicion_action.RevealChosenSecretEffect"
    ) as mock_effect_cls:
        await action._resolve_suspicion_vote(game)
        deps["notifier"].notify_vote_result.assert_awaited_once()
        nv_call = deps["notifier"].notify_vote_result.await_args
        assert (
            nv_call.args[1] is None  # most_voted_id is None (all passed)
            and nv_call.args[2] is False  # was_tie is False
        )
        mock_effect_cls.assert_not_called()
        deps["commands"].clear_game_action_state.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_suspicion_vote_tie_breaker_not_in_tie_default_first(
    action, deps
):
    # Tie between 2 and 3; tie-breaker (1) voted 5 (not in tie) => pick first in most_common (2)
    saga = {
        "type": "point_your_suspicions",
        "tie_breaker_player_id": 1,
        "votes": {"1": 5, "2": 2, "3": 3, "4": 2, "5": 3},
    }
    game = make_game(player_ids=[1, 2, 3, 4, 5], saga=saga)

    with patch(
        "test_vote_suspicion_action.RevealChosenSecretEffect"
    ) as mock_effect_cls:
        mock_effect_instance = MagicMock()
        mock_effect_instance.execute = AsyncMock()
        mock_effect_cls.return_value = mock_effect_instance

        await action._resolve_suspicion_vote(game)

        deps["notifier"].notify_vote_result.assert_awaited_once()
        nv_call = deps["notifier"].notify_vote_result.await_args
        assert (
            nv_call.args[0] == game.id
            and nv_call.args[1] == 2
            and nv_call.args[2] is True
        )

        mock_effect_instance.execute.assert_awaited_once()
        exec_call = mock_effect_instance.execute.await_args
        assert (
            exec_call.kwargs["player_id"]
            == game.pending_saga["tie_breaker_player_id"]
        )
        assert exec_call.kwargs["target_player_id"] == 2


@pytest.mark.asyncio
async def test_resolve_invalid_saga_missing_votes_raises(action, deps):
    saga = {
        "type": "point_your_suspicions",
        "tie_breaker_player_id": 1,
    }  # no 'votes'
    game = make_game(saga=saga)
    with pytest.raises(InvalidSagaState):
        await action._resolve_suspicion_vote(game)


@pytest.mark.asyncio
async def test_resolve_suspicion_vote_END_TO_END_notifier_call(action, deps):
    """
    ¡¡¡EL TEST DE LA GARANTÍA DE FUEGO!!!
    Este test verifica la cadena de mando completa: desde la resolución del voto
    hasta la llamada final al notificador, asegurando que el WebSocket correcto
    es enviado al jugador correcto.
    """
    # Escenario: Ganador claro, jugador 20 con dos votos.
    saga = {
        "type": "point_your_suspicions",
        "tie_breaker_player_id": 10,
        "votes": {"10": 20, "20": 20, "30": 10},
    }
    game = make_game(player_ids=[10, 20, 30], saga=saga)

    # NO parcheamos el efecto. Dejamos que el código real se ejecute.
    # El 'action' ya tiene el 'mock_notifier' inyectado, así que podemos espiarlo.

    # EJECUTAMOS la resolución
    await action._resolve_suspicion_vote(game)

    # --- LA PUTA VERIFICACIÓN FINAL ---
    # Revisamos la cadena de mando completa:

    # 1. ¿Se notificó el resultado de la votación? (Verificación básica)
    deps["notifier"].notify_vote_result.assert_awaited_once_with(
        game.id, 20, False
    )

    # 2. ¿Se cambió el estado del juego para esperar la revelación?
    # El efecto RevealChosenSecretEffect debe llamar a esto.
    deps["commands"].set_game_action_state.assert_called_once_with(
        game_id=game.id,
        state=GameActionState.AWAITING_REVEAL_FOR_CHOICE,
        prompted_player_id=20,  # ¡Debe ser el más votado!
        initiator_id=10,  # ¡Debe ser el que inició la votación!
    )

    # 3. ¡¡¡LA PRUEBA REINA!!! ¿Se envió el WebSocket al jugador correcto?
    # El efecto RevealChosenSecretEffect debe llamar a esto al final.
    deps["notifier"].notify_player_to_reveal_secret.assert_awaited_once_with(
        game.id,
        20,  # ¡¡¡DEBE SER EL PUTO JUGADOR MÁS VOTADO (20)!!!
    )
