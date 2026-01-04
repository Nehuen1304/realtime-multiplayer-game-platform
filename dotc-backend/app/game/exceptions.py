class GameError(Exception):
    """
    Excepción base para todos los errores controlados de la lógica de negocio.
    Permite capturar cualquier error del juego de forma genérica si es necesario.
    """

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


# --------------------------------------------------------------------------
# --- CATEGORÍA: Recurso no Encontrado (mapeará a HTTP 404) ---
# --------------------------------------------------------------------------


class ResourceNotFound(GameError):
    """Excepción base para errores donde un recurso específico no se encuentra."""

    pass


class GameNotFound(ResourceNotFound):
    """Se lanza cuando una partida con el ID especificado no existe."""

    pass  # Hereda el comportamiento de ResourceNotFound


class PlayerNotFound(ResourceNotFound):
    """Se lanza cuando un jugador con el ID especificado no existe."""

    pass


class CardNotFound(ResourceNotFound):
    """Se lanza cuando una carta con el ID especificado no existe en el contexto actual."""

    pass


class SecretNotFound(ResourceNotFound):
    """Se lanza cuando una carta de secreto con el ID especificado no existe."""

    pass


# --------------------------------------------------------------------------
# --- CATEGORÍA: Conflicto de Estado (mapeará a HTTP 409) ---
# --------------------------------------------------------------------------


class ActionConflict(GameError):
    """Excepción base para acciones que no se pueden realizar debido al estado actual del juego."""

    pass


class GameFull(ActionConflict):
    """Se lanza al intentar unirse a una partida que ya ha alcanzado su capacidad máxima."""

    pass


class AlreadyJoined(ActionConflict):
    """Se lanza si un jugador intenta unirse a una partida en la que ya está."""

    pass


class GameAlreadyStarted(ActionConflict):
    """Se lanza al intentar realizar una acción de lobby (ej: unirse) en una partida que ya comenzó."""

    pass


# --------------------------------------------------------------------------
# --- CATEGORÍA: Acción No Permitida (mapeará a HTTP 403 o 401) ---
# --------------------------------------------------------------------------


class ForbiddenAction(GameError):
    """Excepción base para acciones que el jugador no tiene permiso para realizar."""

    pass


class NotYourTurn(ForbiddenAction):
    """Se lanza cuando un jugador intenta una acción (ej: robar, descartar) fuera de su turno."""

    pass


class NotYourCard(ForbiddenAction):
    """Se lanza cuando un jugador intenta jugar o descartar una carta que no posee."""

    pass


class WrongPassword(ForbiddenAction):
    """Se lanza al intentar unirse a una partida privada con una contraseña incorrecta."""

    pass


# --------------------------------------------------------------------------
# --- CATEGORÍA: Petición Inválida (mapeará a HTTP 400) ---
# --------------------------------------------------------------------------


class InvalidRequest(GameError):
    """Excepción base para peticiones que son lógicamente incorrectas."""

    pass


class InvalidAction(InvalidRequest):
    """
    Excepción genérica para una acción que no es válida en el contexto actual,
    pero no se debe a un conflicto de estado o a un problema de permisos.
    (Ej: intentar iniciar una partida sin suficientes jugadores).
    """

    pass


class PlayerNotInGame(InvalidRequest):
    """Se lanza cuando se intenta una acción para un jugador que no está en la partida."""

    pass


# --------------------------------------------------------------------------
# --- CATEGORÍA: Error Interno del Servidor (mapeará a HTTP 500) ---
# --------------------------------------------------------------------------


class InternalGameError(GameError):
    """
    Excepción para errores inesperados o no controlados en la lógica de negocio.
    Indica un problema en el servidor, no en la petición del cliente.
    """

    pass


class InvalidSagaState(GameError):
    """
    Excepción para cuando se intenta interactuar con una saga
    (votación, trade) pero el estado guardado en la DB es incorrecto o no existe.
    """

    pass
