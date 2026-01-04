from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from .connection_manager import ConnectionManager
from ..dependencies.dependencies import get_websocket_manager

router = APIRouter()


@router.websocket("/ws/game/{game_id}/player/{player_id}")
async def websocket_endpoint_game(
    websocket: WebSocket,
    game_id: int,
    player_id: int,
    manager: ConnectionManager = Depends(get_websocket_manager),
):
    """Endpoint para conexiones WebSocket de un jugador específico en una partida."""
    await manager.connect(websocket, game_id=game_id, player_id=player_id)
    try:
        while True:
            # En este juego, el servidor solo envía, no recibe.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/mainscreen")
async def websocket_endpoint_lobby(
    websocket: WebSocket,
    manager: ConnectionManager = Depends(get_websocket_manager),
):
    """Endpoint para conexiones WebSocket en el lobby general."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
