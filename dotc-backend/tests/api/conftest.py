import pytest
from unittest.mock import AsyncMock

from app.main import app
from app.dependencies.dependencies import get_game_manager
from app.game.interfaces import IGameManager


# --- La Clase Mock de Macho Alfa (Ahora sin herencia) ---
class MockGameManager(AsyncMock):
    """
    Un Mock del GameManager que es ESTRICTO y usa la interfaz.
    El 'spec' en el __init__ es el que hace toda la magia.
    """

    def __init__(self, *args, **kwargs):
        # Le pasamos la interfaz como 'spec'. Esto es lo que nos da:
        # 1. Autocompletado (si tu editor es piola).
        # 2. Si intentás usar un método que no existe.
        super().__init__(spec=IGameManager, *args, **kwargs)


# --- Las Fixtures del Arsenal (Estas quedan igual, son perfectas) ---
@pytest.fixture
def mock_game_manager() -> AsyncMock:
    """
    Fábrica de mocks: devuelve una instancia FRESCA de MockGameManager para cada test.
    """
    return MockGameManager()


@pytest.fixture
def game_manager_mocker(mock_game_manager: AsyncMock) -> AsyncMock:
    """
    Inyecta el mock en la app y limpia cuando termina.
    """
    # Setup: Inyectar el mock
    app.dependency_overrides[get_game_manager] = lambda: mock_game_manager

    # "yield" le pasa el control (y el mock) al test
    yield mock_game_manager

    # Cleanup: Limpiar el override
    app.dependency_overrides = {}
