import pytest
from app.domain.enums import ResponseStatus, GameFlowStatus
from app.game.effects.set_effects import HideSecretEffect

class DummySecret:
    def __init__(self, secret_id:int, player_id:int, is_revealed:bool=True):
        self.secret_id=secret_id
        self.player_id=player_id
        self.is_revealed=is_revealed
        self.role=None

class DummyPlayer:
    def __init__(self, player_id:int, social_disgrace:bool):
        self.player_id=player_id
        self.social_disgrace=social_disgrace

class DummyCommands:
    def __init__(self):
        self.hidden=[]
        self.updated=[]
    def reveal_secret_card(self, secret_id:int, game_id:int, is_revealed:bool):
        self.hidden.append((secret_id,is_revealed))
        return ResponseStatus.OK
    def set_player_social_disgrace(self, player_id:int, game_id:int, is_disgraced:bool):
        self.updated.append((player_id,is_disgraced))
        return ResponseStatus.OK

class DummyQueries:
    def __init__(self, secret:DummySecret, player:DummyPlayer):
        self.secret=secret
        self.player=player
    def get_game(self, game_id:int):
        return type("G",(),{"id":game_id})
    def get_secret(self, game_id:int, secret_id:int):
        return self.secret if self.secret.secret_id==secret_id else None
    def get_players_in_game(self, game_id:int):
        return [self.player]
    # Dummy unused methods required by effect
    def get_player_role(self, player_id:int, game_id:int):
        return None
    def get_player_secrets(self, game_id:int, player_id:int):
        class _S:
            def __init__(self, is_revealed: bool):
                self.is_revealed = is_revealed
        # Simula: si el jugador está en desgracia, todos sus secretos revelados; sino, no todos
        return [_S(True)] if self.player.social_disgrace else [_S(False)]

class DummyNotifier:
    def __init__(self):
        self.hidden=[]; self.sd_removed=[]
    async def notify_secret_hidden(self, game_id:int, secret_id:int, player_id:int):
        self.hidden.append((game_id,secret_id,player_id))
    async def notify_social_disgrace_removed(self, game_id:int, player_id:int):
        self.sd_removed.append((game_id,player_id))

@pytest.mark.asyncio
async def test_hide_secret_always_removes_disgrace():
    secret=DummySecret(secret_id=10, player_id=1)
    player=DummyPlayer(player_id=1, social_disgrace=True)
    queries=DummyQueries(secret, player)
    commands=DummyCommands()
    notifier=DummyNotifier()
    effect=HideSecretEffect(queries, commands, notifier)
    status=await effect.execute(game_id=55, player_id=1, card_ids=[], target_secret_id=10)
    assert status==GameFlowStatus.CONTINUE
    # Secret hidden
    assert commands.hidden==[(10, False)]
    # Disgrace removed
    assert commands.updated==[(1, False)]
    assert notifier.sd_removed==[(55,1)]

@pytest.mark.asyncio
async def test_hide_secret_no_disgrace_no_notification():
    secret=DummySecret(secret_id=11, player_id=2)
    player=DummyPlayer(player_id=2, social_disgrace=False)
    queries=DummyQueries(secret, player)
    commands=DummyCommands()
    notifier=DummyNotifier()
    effect=HideSecretEffect(queries, commands, notifier)
    status=await effect.execute(game_id=77, player_id=2, card_ids=[], target_secret_id=11)
    assert status==GameFlowStatus.CONTINUE
    # Secret hidden
    assert commands.hidden==[(11, False)]
    # No disgrace update
    assert commands.updated==[]
    assert notifier.sd_removed==[]
