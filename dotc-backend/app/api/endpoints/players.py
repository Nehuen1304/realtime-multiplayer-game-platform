from fastapi import APIRouter, Body, status, Depends
from ...api.schemas import CreatePlayerRequest, CreatePlayerResponse
from ...game.game_manager import GameManager
from ...dependencies.dependencies import get_game_manager

# Router especifico para todo lo relacionado a jugadores
router = APIRouter(prefix="/players", tags=["Players"])


@router.post(
    "",
    response_model=CreatePlayerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_player(
    request: CreatePlayerRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Crea un nuevo jugador en el sistema."""
    # El servicio ahora devuelve la respuesta directamente o lanza una excepción.
    # Si lanza una excepción, los HANDLERS que definiste se encargan.
    return game_manager.create_player(request)
