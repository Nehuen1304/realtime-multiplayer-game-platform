import enum


class WSEvent(str, enum.Enum):
    """
    Define todos los tipos de eventos WebSocket que el servidor puede enviar.
    Hereda de 'str' para que pueda ser serializado a JSON fácilmente.
    """

    # Eventos de notInGame (pantalla principal) (Broadcast Lobby general)
    GAME_CREATED = "GAME_CREATED"
    GAME_UPDATED = "GAME_UPDATED"  # Ej: cambió el numero de jugadores
    GAME_REMOVED = "GAME_CANCELLED"

    # Eventos Ingame (Broadcast al game o mensaje privado a un jugador)
    NEW_TURN = "NEW_TURN"
    CARD_PLAYED = "CARD_PLAYED"
    CARD_DISCARDED = "CARD_DISCARDED"
    CARDS_NSF_DISCARDED = "CARDS_NSF_DISCARDED"
    PLAYER_DREW_FROM_DECK = "PLAYER_DREW_FROM_DECK"
    DECK_UPDATED = "DECK_UPDATED"  # Como para obligar a actualizar mazo
    DRAFT_UPDATED = "DRAFT_UPDATED"
    CARDS_PLAYED = (
        "CARDS_PLAYED"  # Notificación PÚBLICA cuando se juega un set de cartas.
    )
    SET_STOLEN = "SET_STOLEN"
    SECRET_REVEALED = "SECRET_REVEALED"
    SECRET_STOLEN = "SECRET_STOLEN"
    REQUEST_TO_DONATE = "REQUEST_TO_DONATE"
    SECRET_HIDDEN = "SECRET_HIDDEN"
    SD_APPLIED = "SD_APPLIED"
    SD_REMOVED = "SD_REMOVED"
    GAME_OVER = "GAME_OVER"

    PROMPT_REVEAL = "PROMPT_REVEAL"  # Notificación PRIVADA para ordenarle a un jugador que actúe.
    PROMPT_DRAW_FROM_DISCARD = "PROMPT_DRAW_FROM_DISCARD"  # Notificación PRIVADA para ordenarle a un jugador que robe de la pila de descarte.
    TRADE_REQUESTED = (
        "TRADE_REQUESTED"  # Notificación PRIVADA para intercambio de cartas.
    )
    HAND_UPDATED = "HAND_UPDATED"  # Notificación PRIVADA de mano actualizada.

    VOTE_STARTED = "VOTE_STARTED"
    VOTE_ENDED = "VOTE_ENDED"
    ACTION_RESOLVED = "ACTION_RESOLVED"  # Notificación PÚBLICA de que se resolvió una acción NSF.
    ACTION_CANCELLED = "ACTION_CANCELLED"  # Notificación PÚBLICA de que se canceló una acción NSF.
    
    """ Algunos eventos necesitan actualizar ambos canales """

    # Eventos de pantalla principal y partida (Broadcast a Lobby y a Game)
    PLAYER_JOINED = "PLAYER_JOINED"
    PLAYER_LEFT = "PLAYER_LEFT"
    GAME_STARTED = "GAME_STARTED"
