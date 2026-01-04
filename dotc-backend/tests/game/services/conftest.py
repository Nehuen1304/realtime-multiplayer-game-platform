import pytest
from unittest.mock import Mock, AsyncMock

# --------------------------------------------------------------------------
# --- 1. Importaciones de Interfaces y Clases a Mockear ---
# --------------------------------------------------------------------------

# Interfaces de la capa de datos
from app.database.interfaces import IQueryManager, ICommandManager

# Clases concretas de los helpers que serán mockeadas
from app.game.effect_executor import EffectExecutor
from app.game.helpers.validators import GameValidator
from app.game.helpers.notificators import Notificator
from app.game.helpers.turn_utils import TurnUtils


# --------------------------------------------------------------------------
# --- 2. Fixtures para Mocks de la Capa de Datos ---
# --------------------------------------------------------------------------


@pytest.fixture
def mock_queries() -> Mock:
    """
    Fixture que crea y devuelve un mock para IQueryManager.
    El mock se reinicia para cada test, garantizando aislamiento.
    """
    # Usar 'spec' asegura que el mock se comporte como la interfaz real.
    # Si llamas a un método que no existe en IQueryManager, el test fallará.
    mock = Mock(spec=IQueryManager)
    return mock


@pytest.fixture
def mock_commands() -> Mock:
    """
    Fixture que crea y devuelve un mock para ICommandManager.
    Se reinicia para cada test.
    """
    mock = Mock(spec=ICommandManager)
    return mock


# --------------------------------------------------------------------------
# --- 3. Fixtures para Mocks de la Capa de Helpers ---
# --------------------------------------------------------------------------


@pytest.fixture
def mock_validator() -> Mock:
    """
    Fixture que crea y devuelve un mock para GameValidator.
    Permite simular los resultados de las validaciones en los tests de los servicios.
    """
    # puedo hacer spec sobre la clase concreta, no hace falta que sea una interfaz...
    mock = Mock(spec=GameValidator)
    return mock


@pytest.fixture
def mock_notificator() -> AsyncMock:
    """
    Fixture que crea y devuelve un AsyncMock para Notificator.
    Permite 'await' en sus métodos y verificarlos con 'assert_awaited_once'.
    """
    # puedo hacer spec sobre la clase concreta, no hace falta que sea una interfaz...
    mock = AsyncMock(spec=Notificator)
    return mock


# --------------------------------------------------------------------------
# --- 3. Fixtures para Mocks de la Capa de Helpers ---
# --------------------------------------------------------------------------
@pytest.fixture
def mock_executor() -> AsyncMock:
    """
    Crea y devuelve un AsyncMock para EffectExecutor
    """
    # puedo hacer spec sobre la clase concreta, no hace falta que sea una interfaz...
    mock = AsyncMock(spec=EffectExecutor)
    return mock


# NOTE: No necesito un mock para el ConnectionManager aca, porque
# los servicios no dependen de el directamente. Dependen del Notificator
# entonces mockeo eso
#


@pytest.fixture
def db_mocks():
    """
    Proporciona mocks para las interfaces de la base de datos.
    """
    mock_queries = Mock()
    mock_commands = Mock()  # Usamos AsyncMock para métodos 'async'
    return mock_queries, mock_commands


@pytest.fixture
def mock_turn_utils():
    """Fixture que provee un mock para TurnUtils."""
    mock = Mock(spec=TurnUtils)
    return mock


# --------------------------------------------------------------------------
# --- 4. Fixture compartida de TurnService para todos los tests del módulo ---
# --------------------------------------------------------------------------
from app.game.services.turn_service import TurnService


@pytest.fixture
def turn_service(
    mock_queries: Mock,
    mock_commands: Mock,
    mock_validator: Mock,
    mock_notificator: AsyncMock,
    mock_executor: AsyncMock,
    mock_turn_utils: Mock,
) -> TurnService:
    """Instancia TurnService con dependencias mockeadas, reusable."""
    return TurnService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
        effect_executor=mock_executor,
        turn_utils=mock_turn_utils,
    )
