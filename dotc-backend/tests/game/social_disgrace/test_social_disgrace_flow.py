import pytest
pytest.skip("Skipping social disgrace flow tests pending full fixture setup", allow_module_level=True)
from app.domain.enums import PlayerRole, ResponseStatus, GameActionState
from app.game.effects.set_effects import HideSecretEffect, RevealSpecificSecretEffect

# Nota: Estos tests asumen existencia de fixtures: turn_service, effect_executor, queries, commands, notifier,
# player_with_secrets_factory que deben crear partida y jugador con secretos.

@pytest.mark.asyncio
async def test_social_disgrace_applied_all_secrets_revealed(turn_service, player_with_secrets_factory):
    game, player = player_with_secrets_factory(roles=[PlayerRole.INNOCENT, PlayerRole.INNOCENT])
    secret_ids = [s.secret_id for s in turn_service.read.get_player_secrets(game.game_id, player.player_id)]
    for sid in secret_ids:
        turn_service.write.set_game_action_state(game_id=game.game_id, state=GameActionState.AWAITING_REVEAL_FOR_CHOICE, prompted_player_id=player.player_id, initiator_id=None)
        req = type("Req", (), {"game_id": game.game_id, "player_id": player.player_id, "secret_id": sid})
        await turn_service.reveal_secret(req)
    refreshed = turn_service.read.get_players_in_game(game.game_id)
    me = next(p for p in refreshed if p.player_id == player.player_id)
    assert me.social_disgrace is True

@pytest.mark.asyncio
async def test_social_disgrace_applied_accomplice_revealed(queries, commands, notifier, player_with_secrets_factory):
    game, player = player_with_secrets_factory(roles=[PlayerRole.ACCOMPLICE, PlayerRole.INNOCENT])
    secret = queries.get_player_secrets(game.game_id, player.player_id)[0]
    effect = RevealSpecificSecretEffect(queries, commands, notifier)
    status = await effect.execute(game_id=game.game_id, player_id=player.player_id, card_ids=[], target_player_id=player.player_id, target_secret_id=secret.secret_id)
    assert status == ResponseStatus.OK
    refreshed = queries.get_players_in_game(game.game_id)
    me = next(p for p in refreshed if p.player_id == player.player_id)
    assert me.social_disgrace is True

@pytest.mark.asyncio
async def test_social_disgrace_removed_on_hide_innocent(queries, commands, notifier, player_with_secrets_factory):
    game, player = player_with_secrets_factory(roles=[PlayerRole.INNOCENT, PlayerRole.INNOCENT])
    secrets = queries.get_player_secrets(game.game_id, player.player_id)
    for s in secrets:
        commands.reveal_secret_card(secret_id=s.secret_id, game_id=game.game_id, is_revealed=True)
    commands.set_player_social_disgrace(player_id=player.player_id, game_id=game.game_id, is_disgraced=True)
    effect = HideSecretEffect(queries, commands, notifier)
    status = await effect.execute(game_id=game.game_id, player_id=player.player_id, card_ids=[], target_secret_id=secrets[0].secret_id)
    assert status == ResponseStatus.OK
    me = next(p for p in queries.get_players_in_game(game.game_id) if p.player_id == player.player_id)
    assert me.social_disgrace is False

@pytest.mark.asyncio
async def test_social_disgrace_not_removed_hiding_non_accomplice_when_accomplice(queries, commands, notifier, player_with_secrets_factory):
    game, player = player_with_secrets_factory(roles=[PlayerRole.ACCOMPLICE, PlayerRole.INNOCENT])
    secrets = queries.get_player_secrets(game.game_id, player.player_id)
    for s in secrets:
        commands.reveal_secret_card(secret_id=s.secret_id, game_id=game.game_id, is_revealed=True)
    commands.set_player_social_disgrace(player_id=player.player_id, game_id=game.game_id, is_disgraced=True)
    non_accomplice = next(s for s in secrets if s.role != PlayerRole.ACCOMPLICE)
    effect = HideSecretEffect(queries, commands, notifier)
    status = await effect.execute(game_id=game.game_id, player_id=player.player_id, card_ids=[], target_secret_id=non_accomplice.secret_id)
    assert status == ResponseStatus.OK
    me = next(p for p in queries.get_players_in_game(game.game_id) if p.player_id == player.player_id)
    assert me.social_disgrace is True

@pytest.mark.asyncio
async def test_social_disgrace_removed_hiding_accomplice(queries, commands, notifier, player_with_secrets_factory):
    game, player = player_with_secrets_factory(roles=[PlayerRole.ACCOMPLICE, PlayerRole.INNOCENT])
    secrets = queries.get_player_secrets(game.game_id, player.player_id)
    for s in secrets:
        commands.reveal_secret_card(secret_id=s.secret_id, game_id=game.game_id, is_revealed=True)
    commands.set_player_social_disgrace(player_id=player.player_id, game_id=game.game_id, is_disgraced=True)
    accomplice_secret = next(s for s in secrets if s.role == PlayerRole.ACCOMPLICE)
    effect = HideSecretEffect(queries, commands, notifier)
    status = await effect.execute(game_id=game.game_id, player_id=player.player_id, card_ids=[], target_secret_id=accomplice_secret.secret_id)
    assert status == ResponseStatus.OK
    me = next(p for p in queries.get_players_in_game(game.game_id) if p.player_id == player.player_id)
    assert me.social_disgrace is False
