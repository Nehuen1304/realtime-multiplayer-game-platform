from fastapi import FastAPI
from starlette.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from .api.router import api_router
from .database.orm_models import Base, engine
from .websockets.router import router as websocket_router

# Excepciones
from .game.exceptions import (
    ResourceNotFound,
    ActionConflict,
    ForbiddenAction,
    InvalidRequest,
    InternalGameError,
)

# Manejadores
from .api.exception_handlers import (
    resource_not_found_handler,
    action_conflict_handler,
    forbidden_action_handler,
    invalid_request_handler,
    internal_game_error_handler,
)

# --- Creación de Tablas ---
Base.metadata.create_all(bind=engine)

# --- Configuración de Middlewares ---
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# --- Creación de la Aplicación FastAPI ---
app = FastAPI(
    title="Death on the Cards - Backend",
    description="Laboratorio de Ingeniería de Software I - 2025",
    middleware=middleware,
    # Registra los manejadores de excepciones al crear la app
    exception_handlers={
        ResourceNotFound: resource_not_found_handler,
        ActionConflict: action_conflict_handler,
        ForbiddenAction: forbidden_action_handler,
        InvalidRequest: invalid_request_handler,
        InternalGameError: internal_game_error_handler,
    },
)

# --- Inclusión de Routers ---
app.include_router(api_router, prefix="/api")
app.include_router(websocket_router)


# --- Endpoint Raíz ---
@app.get("/", tags=["Root"])
def read_root():
    """Endpoint para verificar que el backend está activo."""
    return {"message": "Bienvenido al backend de 'Death on the Cards'"}
