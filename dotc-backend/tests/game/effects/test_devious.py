import pytest
from unittest.mock import AsyncMock, Mock, MagicMock

# Importar la clase a testear y sus dependencias
from app.game.effects.devious_effects import SocialFauxPasEffect
from app.database.interfaces import IQueryManager, ICommandManager
from app.game.helpers.notificators import Notificator
from app.domain.enums import (
    ResponseStatus,
    GameActionState,
    CardLocation,
    GameFlowStatus,
)
from app.game.exceptions import InternalGameError


@pytest.fixture
def mock_queries() -> Mock:
    return Mock(spec=IQueryManager)


@pytest.fixture
def mock_commands() -> Mock:
    return Mock(spec=ICommandManager)


@pytest.fixture
def mock_notificator() -> AsyncMock:
    return AsyncMock(spec=Notificator)


@pytest.fixture
def effect(
    mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
) -> SocialFauxPasEffect:
    """Crea una instancia del efecto con dependencias mockeadas."""
    return SocialFauxPasEffect(
        queries=mock_queries, commands=mock_commands, notifier=mock_notificator
    )


class TestSocialFauxPasEffect:
    @pytest.mark.asyncio
    async def test_execute_happy_path(
        self,
        effect: SocialFauxPasEffect,
        mock_commands: Mock,
        mock_queries: Mock,
        mock_notificator: AsyncMock,
    ):
        """
        Prueba el flujo exitoso: la carta se descarta, se notifica, y se le pide a la víctima
        que revele un secreto.
        """
        # --- Arrange ---
        game_id = 701
        victim_id = 1
        card_id = 101

        # ¡¡¡LA PUTA CORRECCIÓN!!! Creamos un mock del objeto Card que el notifier espera.
        mock_card_object = MagicMock()
        mock_card_object.card_id = card_id

        # Configuramos los mocks para que devuelvan valores exitosos.
        mock_commands.update_card_location.return_value = ResponseStatus.OK
        # El efecto llama a get_card para obtener el objeto a notificar.
        mock_queries.get_card.return_value = mock_card_object

        # --- Act ---
        result = await effect.execute(
            game_id=game_id,
            player_id=victim_id,  # En SFP, el que "juega" el efecto es la víctima de la carta
            card_ids=[card_id],
        )

        # --- Assert ---
        # 1. Verificar que la carta Devious fue movida al descarte.
        mock_commands.update_card_location.assert_called_once_with(
            card_id=card_id,
            game_id=game_id,
            new_location=CardLocation.DISCARD_PILE,
            owner_id=None,
        )

        # 2. Verificar que se notificó el descarte CON EL OBJETO CARD.
        mock_queries.get_card.assert_called_once_with(
            card_id=card_id, game_id=game_id
        )
        mock_notificator.notify_card_discarded.assert_called_once_with(
            game_id=game_id,
            player_id=victim_id,
            card_discarded=mock_card_object,  # Fixed: parameter name is card_discarded, not card
        )

        # 3. Verificar que el juego se puso en estado de espera para la revelación.
        mock_commands.set_game_action_state.assert_called_once_with(
            game_id=game_id,
            state=GameActionState.AWAITING_REVEAL_FOR_CHOICE,
            prompted_player_id=victim_id,
            initiator_id=victim_id,
        )

        # 4. Verificar que se notificó a la víctima para que revele un secreto.
        mock_notificator.notify_player_to_reveal_secret.assert_awaited_once_with(
            game_id, victim_id
        )

        # 5. Verificar que el resultado final sea PAUSED (devious effects pause the game).
        assert result == GameFlowStatus.PAUSED

    @pytest.mark.asyncio
    async def test_execute_db_fail_raises_internal_error(
        self, effect: SocialFauxPasEffect, mock_commands: Mock
    ):
        """
        Prueba de robustez: Si la base de datos falla al mover la carta,
        se debe lanzar una excepción InternalGameError.
        """
        # --- Arrange ---
        mock_commands.update_card_location.return_value = ResponseStatus.ERROR

        # --- Act & Assert ---
        with pytest.raises(InternalGameError):
            await effect.execute(game_id=1, player_id=1, card_ids=[101])
