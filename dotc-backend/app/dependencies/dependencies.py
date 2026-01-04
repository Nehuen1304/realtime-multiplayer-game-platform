from fastapi import Depends, FastAPI
from typing import Annotated, Generator
from sqlalchemy.orm import Session

# --------------------------------------------------------------------------
# --- 1. Importaciones de Interfaces y Clases Concretas ---
# --------------------------------------------------------------------------

# Interfaces y clases concretas de la capa de Base de Datos
from ..database.interfaces import IQueryManager, ICommandManager
from ..database.orm_models import SessionLocal
from ..database.queries import DatabaseQueryManager
from ..database.commands import DatabaseCommandManager

# Interfaz y clase concreta de la capa de WebSockets
from ..websockets.interfaces import IConnectionManager
from ..websockets.connection_manager import ConnectionManager

# Helpers reutilizables
from ..game.helpers.validators import GameValidator
from ..game.helpers.notificators import Notificator
from ..game.helpers.turn_utils import TurnUtils
from ..game.effect_executor import EffectExecutor

# Servicios de la lógica de negocio
from ..game.services.player_service import PlayerService
from ..game.services.lobby_service import LobbyService
from ..game.services.game_setup_service import GameSetupService
from ..game.services.game_state_service import GameStateService
from ..game.services.turn_service import TurnService

# La Fachada (Facade) y su Abstracción
from ..game.game_manager import GameManager
from ..game.interfaces import IGameManager


# --------------------------------------------------------------------------
# --- 2. Factorías de Dependencias ---
# --------------------------------------------------------------------------

# --- Singleton para WebSocket Manager ---
websocket_manager_singleton = ConnectionManager()


def get_websocket_manager() -> IConnectionManager:
    """Devuelve la instancia singleton del gestor de WebSockets."""
    return websocket_manager_singleton


# --- sesion de BD por request ---
def get_db_session() -> Generator[Session, None, None]:
    """Generador de sesión de BD. Crea una nueva sesión por petición y la cierra al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- gestores de BD por request ---
def get_query_manager(
    session: Annotated[Session, Depends(get_db_session)],
) -> IQueryManager:
    """Factoría que crea el gestor de queries con una sesión fresca."""
    return DatabaseQueryManager(session=session)


def get_command_manager(
    queries: Annotated[IQueryManager, Depends(get_query_manager)],
) -> ICommandManager:
    """
    Factoría que crea el gestor de comandos.
    Ya no necesita una sesión propia, la tomará del gestor de queries.
    """
    return DatabaseCommandManager(queries=queries)

# --------------------------------------------------------------------------
# --- 3. Factorías de Helpers (Herramientas de Apoyo) ---
# --------------------------------------------------------------------------


def get_validator(
    queries: Annotated[IQueryManager, Depends(get_query_manager)],
) -> GameValidator:
    """Factoría para crear el GameValidator, inyectándole el gestor de queries."""
    return GameValidator(queries=queries)


def get_notificator(
    ws_manager: Annotated[IConnectionManager, Depends(get_websocket_manager)],
) -> Notificator:
    """Factoría para crear el Notificator, inyectándole el gestor de websockets."""
    return Notificator(ws_manager=ws_manager)

def get_turn_utils() -> TurnUtils:
    """Factoría que crea el gestor de turnos."""
    return TurnUtils()


def get_effect_executor(
    queries: Annotated[IQueryManager, Depends(get_query_manager)],
    commands: Annotated[ICommandManager, Depends(get_command_manager)],
    notifier: Annotated[Notificator, Depends(get_notificator)],
) -> EffectExecutor:
    """Factoría para crear el EffectExecutor, inyectando sus dependencias."""
    return EffectExecutor(queries=queries, commands=commands, notifier=notifier)


# --------------------------------------------------------------------------
# --- 4. Factorías de Servicios de Negocio ---
# --------------------------------------------------------------------------


# Asumo que PlayerService también necesita un validador. Si no, puedes quitarlo.
def get_player_service(
    queries: Annotated[IQueryManager, Depends(get_query_manager)],
    commands: Annotated[ICommandManager, Depends(get_command_manager)],
    validator: Annotated[GameValidator, Depends(get_validator)],
    notifier: Annotated[Notificator, Depends(get_notificator)],
) -> PlayerService:
    """Factoría para crear y devolver el PlayerService."""
    return PlayerService(
        queries=queries,
        commands=commands,
        validator=validator,
        notifier=notifier,
    )


def get_lobby_service(
    queries: Annotated[IQueryManager, Depends(get_query_manager)],
    commands: Annotated[ICommandManager, Depends(get_command_manager)],
    validator: Annotated[GameValidator, Depends(get_validator)],
    notifier: Annotated[Notificator, Depends(get_notificator)],
) -> LobbyService:
    """Factoría para crear y devolver el LobbyService."""
    return LobbyService(
        queries=queries,
        commands=commands,
        validator=validator,
        notifier=notifier,
    )


def get_game_setup_service(
    queries: Annotated[IQueryManager, Depends(get_query_manager)],
    commands: Annotated[ICommandManager, Depends(get_command_manager)],
    validator: Annotated[GameValidator, Depends(get_validator)],
    notifier: Annotated[Notificator, Depends(get_notificator)],
    turn_utils: Annotated[TurnUtils, Depends(get_turn_utils)],
) -> GameSetupService:
    """Factoría para crear y devolver el GameSetupService."""
    return GameSetupService(
        queries=queries,
        commands=commands,
        validator=validator,
        notifier=notifier,
        turn_utils=turn_utils,
    )


def get_game_state_service(
    queries: Annotated[IQueryManager, Depends(get_query_manager)],
    commands: Annotated[ICommandManager, Depends(get_command_manager)],
    validator: Annotated[GameValidator, Depends(get_validator)],
    notifier: Annotated[Notificator, Depends(get_notificator)],
    turn_utils: Annotated[TurnUtils, Depends(get_turn_utils)],
) -> GameStateService:
    """Factoría para crear y devolver el GameStateService."""
    return GameStateService(
        queries=queries,
        commands=commands,
        validator=validator,
        notifier=notifier,
        turn_utils=turn_utils,
    )


def get_turn_service(
    queries: Annotated[IQueryManager, Depends(get_query_manager)],
    commands: Annotated[ICommandManager, Depends(get_command_manager)],
    validator: Annotated[GameValidator, Depends(get_validator)],
    notifier: Annotated[Notificator, Depends(get_notificator)],
    effect_executor: Annotated[EffectExecutor, Depends(get_effect_executor)],
    turn_utils: Annotated[TurnUtils, Depends(get_turn_utils)],
) -> TurnService:
    """Factoría para crear y devolver el TurnService."""
    return TurnService(
        queries=queries,
        commands=commands,
        validator=validator,
        notifier=notifier,
        effect_executor=effect_executor,
        turn_utils=turn_utils,
    )


# --------------------------------------------------------------------------
# --- 5. Factoría de la Fachada (Facade) ---
# --------------------------------------------------------------------------


def get_game_manager(
    player_service: Annotated[PlayerService, Depends(get_player_service)],
    lobby_service: Annotated[LobbyService, Depends(get_lobby_service)],
    game_setup_service: Annotated[
        GameSetupService, Depends(get_game_setup_service)
    ],
    game_state_service: Annotated[
        GameStateService, Depends(get_game_state_service)
    ],
    turn_service: Annotated[TurnService, Depends(get_turn_service)],
) -> GameManager:
    """Factoría principal que construye el GameManager (Facade) inyectando todos los servicios."""
    return GameManager(
        player_service=player_service,
        lobby_service=lobby_service,
        game_setup_service=game_setup_service,
        game_state_service=game_state_service,
        turn_service=turn_service,
    )


# --------------------------------------------------------------------------
# --- 6. Configuración de la App de FastAPI ---
# --------------------------------------------------------------------------


def setup_dependencies(app: FastAPI) -> None:
    """
    Configura el override de dependencias para la aplicación FastAPI.
    Le dice a la app que cuando un endpoint pida un `AbstractGameManager`,
    debe ejecutar `get_game_manager` para obtener la instancia concreta.
    """
    app.dependency_overrides[IGameManager] = get_game_manager