from fastapi import APIRouter
from .endpoints import games, players, debug  # modulos que cree

# Router principal
api_router = APIRouter()

# routers secundarios includios en el principal
api_router.include_router(games.router)
api_router.include_router(players.router)
api_router.include_router(debug.router)
