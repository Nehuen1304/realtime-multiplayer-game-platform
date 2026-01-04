from fastapi import APIRouter, Body, status, Depends, Request, HTTPException
from enum import Enum

from app.game.helpers.notificators import Notificator
from ...dependencies.dependencies import get_notificator


# --- ENUM de tipos de notificación ---
class NotificationType(str, Enum):
    GAME_CREATED = "game_created"
    GAME_REMOVED = "game_removed"
    NEW_TURN = "new_turn"
    CARD_PLAYED = "card_played"
    CARD_DISCARDED = "card_discarded"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    SET_CREATED = "set_created"
    SECRET_REVEALED = "secret_revealed"
    SECRET_HIDDEN = "secret_hidden"
    SECRET_STOLEN = "secret_stolen"
    MURDERER_WINS = "murderer_wins"
    INNOCENTS_WIN = "innocents_win"


# --- Mapeo de ENUM → función lambda que llama al Notificator ---
NOTIFICATION_HANDLERS = {
    NotificationType.GAME_CREATED: lambda n, d: n.notify_game_created(
        d["game"]
    ),
    NotificationType.GAME_REMOVED: lambda n, d: n.notify_game_removed(
        d["game_id"]
    ),
    NotificationType.MURDERER_WINS: lambda n, d: n.notify_murderer_wins(
        d["game_id"], d["murderer_id"], d["accomplice_id"]
    ),
    NotificationType.INNOCENTS_WIN: lambda n, d: n.notify_innocents_win(
        d["game_id"], d["murderer_id"], d["accomplice_id"]
    ),
    NotificationType.PLAYER_LEFT: lambda n, d: n.notify_player_left(
        d["game_id"], d["player_id"], d["player_name"],
        d["updated_game_in_lobby"]
    ),
    NotificationType.NEW_TURN: lambda n, d: n.notify_new_turn(
        d["game_id"], d["turn_player_id"]
    ),
    NotificationType.CARD_PLAYED: lambda n, d: n.notify_card_played(
        d["game_id"], d["player_id"], d["card_played"], d["is_cancellable"], d["player_name"]
    ),
    NotificationType.CARD_DISCARDED: lambda n, d: n.notify_card_discarded(
        d["game_id"], d["player_id"], d["card_discarded"]
    ),
    NotificationType.PLAYER_JOINED: lambda n, d: n.notify_player_joined(
        d["game_id"],
        d["player_id"],
        d["player_name"],
        d["updated_game_in_lobby"],
    ),
    NotificationType.SET_CREATED: lambda n, d: n.notify_set_created(
        d["game_id"], d["player_id"], d["set_cards"], d["is_cancellable"]
    ),
    NotificationType.SECRET_REVEALED: lambda n, d: n.notify_secret_revealed(
        d["game_id"], d["secret_id"], d["player_role"], d["player_id"]
    ),
    NotificationType.SECRET_HIDDEN: lambda n, d: n.notify_secret_hidden(
        d["game_id"], d["secret_id"], d["player_id"]
    ),
    NotificationType.SECRET_STOLEN: lambda n, d: n.notify_secret_stolen(
        d["game_id"], d["thief_id"], d["victim_id"]
    ),
}

# --- Router FastAPI ---
router = APIRouter()


@router.post("/echo")
async def trigger_notification(
    request: Request,
    notificator: Notificator = Depends(get_notificator),
):
    """
    Endpoint genérico para disparar notificaciones WebSocket.
    Recibe un JSON con al menos:
    {
        "type": "<valor de NotificationType>",
        ... otros campos requeridos para esa notificación
    }
    """
    data = await request.json()
    notif_type_str = data.get("type")

    if not notif_type_str:
        raise HTTPException(400, "Missing 'type' field in request body")

    try:
        notif_type = NotificationType(notif_type_str)
    except ValueError:
        raise HTTPException(400, f"Invalid notification type: {notif_type_str}")

    handler = NOTIFICATION_HANDLERS.get(notif_type)
    if not handler:
        raise HTTPException(
            400, f"No handler configured for type {notif_type.value}"
        )

    try:
        await handler(notificator, data)
    except KeyError as e:
        raise HTTPException(
            400,
            f"Missing required field '{e.args[0]}' for notification type {notif_type.value}",
        )
    except Exception as e:
        raise HTTPException(
            500,
            f"Internal error while triggering notification: {e}",
        )

    return {"status": "ok", "type_triggered": notif_type.value}
