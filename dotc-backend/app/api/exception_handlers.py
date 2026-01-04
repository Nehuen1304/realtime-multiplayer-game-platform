from fastapi import Request, status
from fastapi.responses import JSONResponse

# Importa las categorías de excepciones de tu capa de negocio
from ..game.exceptions import (
    InternalGameError,
    ResourceNotFound,
    ActionConflict,
    ForbiddenAction,
    InvalidRequest,
)


async def resource_not_found_handler(request: Request, exc: ResourceNotFound):
    """
    Manejador para todas las excepciones que indican que un recurso no fue encontrado.
    Devuelve un HTTP 404 Not Found.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.detail},
    )


async def action_conflict_handler(request: Request, exc: ActionConflict):
    """
    Manejador para acciones que no se pueden realizar por un conflicto de estado.
    Devuelve un HTTP 409 Conflict.
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.detail},
    )


async def forbidden_action_handler(request: Request, exc: ForbiddenAction):
    """
    Manejador para acciones que un jugador no tiene permiso para realizar.
    Devuelve un HTTP 403 Forbidden (o 401 para contraseñas incorrectas).
    """
    status_code = status.HTTP_403_FORBIDDEN

    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.detail},
    )


async def invalid_request_handler(request: Request, exc: InvalidRequest):
    """
    Manejador para peticiones que son lógicamente incorrectas o inválidas.
    Devuelve un HTTP 400 Bad Request.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.detail},
    )


async def internal_game_error_handler(request: Request, exc: InternalGameError):
    """
    Manejador para todas las excepciones que indican que hubo un fallo interno en el servidor.
    Devuelve un HTTP 500 Not Found. Generalmente asociado a un error con la BD.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.detail},
    )
