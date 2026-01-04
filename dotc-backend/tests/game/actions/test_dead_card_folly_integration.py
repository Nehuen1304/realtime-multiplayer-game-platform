"""
NOTA: Este test fue deshabilitado porque SubmitTradeChoiceAction ya no existe como clase independiente.
La funcionalidad de Dead Card Folly ahora está integrada en:
- TurnService.submit_trade_choice() - Para enviar elecciones
- TurnService._resolve_dead_card_folly() - Para resolver el intercambio
- DeadCardFollyEffect - Para el efecto de la carta

Esta funcionalidad está siendo probada en:
- tests/game/services/test_turn_service_trading.py
- tests/game/effects/test_events.py (DeadCardFollyEffect)

Si se necesita un test de integración similar, debería usar TurnService directamente.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.enums import CardType, CardLocation, GameActionState
from types import SimpleNamespace


@pytest.fixture()
def deps():
    """Dependencias mockeadas para la Action."""
    return {
        "queries": MagicMock(),
        "commands": MagicMock(),
        "validator": MagicMock(),
        "notifier": AsyncMock(),
        "turn_utils": MagicMock(),
        "effect_executor": AsyncMock(),
    }


# @pytest.fixture()
# def action_under_test(deps):
#     """Instancia de la Action bajo prueba."""
#     return SubmitTradeChoiceAction(**deps)


# class TestDeadCardFollyResolution:
#     @pytest.mark.asyncio
#     async def test_dead_card_folly_integration_with_social_faux_pas(
#         self, action_under_test, deps
#     ):
#         """
#         INTEGRATION SUPER-TEST:
#         Verifica la resolución completa de Dead Card Folly cuando una carta 'Social Faux Pas'
#         es intercambiada y su efecto secundario se dispara correctamente.
#         
#         DESHABILITADO: La arquitectura cambió. Ahora esto se testea en:
#         - tests/game/services/test_turn_service_trading.py::test_resolve_dead_card_folly_left
#         - tests/game/services/test_turn_service_trading.py::test_resolve_dead_card_folly_right
#         """
#         pass
