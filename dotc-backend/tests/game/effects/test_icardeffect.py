import pytest
from unittest.mock import Mock, AsyncMock
from typing import List, Optional, Literal
from app.game.effects.interfaces import ICardEffect
from app.domain.enums import GameFlowStatus


class DummyEffect(ICardEffect):
    async def execute(
        self,
        game_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: int = None,
        target_secret_id: int = None,
        target_card_id: int = None,
        target_set_id: int = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        # Solo para test: devuelve CONTINUE si las dependencias existen
        assert self.queries is not None
        assert self.commands is not None
        assert self.notifier is not None
        return GameFlowStatus.CONTINUE


@pytest.fixture
def mock_dependencies():
    return {
        "queries": Mock(),
        "commands": Mock(),
        "notifier": AsyncMock(),
    }


@pytest.mark.asyncio
async def test_icard_effect_execute_returns_ok(mock_dependencies):
    """Verifica que un ICardEffect concreto ejecuta correctamente y recibe dependencias."""
    effect = DummyEffect(
        mock_dependencies["queries"],
        mock_dependencies["commands"],
        mock_dependencies["notifier"],
    )
    result = await effect.execute(
        game_id=1,
        player_id=7,
        card_ids=[42],
        target_player_id=3,
        target_secret_id=4,
        target_card_id=5,
        target_set_id=6,
    )
    assert result == GameFlowStatus.CONTINUE


def test_icard_effect_dependencies_are_set(mock_dependencies):
    """Verifica que las dependencias quedan como atributos de la instancia."""
    effect = DummyEffect(
        mock_dependencies["queries"],
        mock_dependencies["commands"],
        mock_dependencies["notifier"],
    )
    assert effect.queries is mock_dependencies["queries"]
    assert effect.commands is mock_dependencies["commands"]
    assert effect.notifier is mock_dependencies["notifier"]


def test_icard_effect_is_abstract():
    """Verifica que ICardEffect no puede instanciarse directamente."""
    with pytest.raises(TypeError):
        ICardEffect(Mock(), Mock(), Mock())
