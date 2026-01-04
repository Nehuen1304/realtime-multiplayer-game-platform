from app.game.helpers.notificators import Notificator
from app.game.helpers.validators import GameValidator
from ..exceptions import (
    InvalidAction,
    InternalGameError,
)
from ...database.interfaces import (
    ICommandManager,
    IQueryManager,
)
from ...domain.enums import (
    Avatar,
)
from ...api.schemas import (
    CreatePlayerRequest,
    CreatePlayerResponse,
)


class PlayerService:
    """
    Servicio encargado de la lógica de negocio relacionada con los jugadores.
    Implementa el "Blueprint de 5 Pasos" para sus operaciones.
    """

    def __init__(
        self,
        queries: IQueryManager,
        commands: ICommandManager,
        validator: GameValidator,
        notifier: Notificator,
    ):
        self.read = queries
        self.write = commands
        self.validator = validator
        self.notifier = notifier

    def create_player(
        self, request: CreatePlayerRequest
    ) -> CreatePlayerResponse:
        """
        Crea un nuevo jugador en el sistema, siguiendo el ciclo de vida estándar.
        """
        # --- PASO 1: Entrada y Desestructuración ---
        clean_name = request.name.strip()

        # --- PASO 2: Validación y Reglas de Negocio ---
        if not clean_name:
            raise InvalidAction("El nombre del jugador no puede estar vacío.")

        # En teoria pydantic ya deberia usar avatar.default, pero me extra-aseguro aca
        avatar_to_use = (
            request.avatar if request.avatar is not None else Avatar.DEFAULT
        )

        # --- PASO 3: Ejecución del Comando Principal ---
        # Ahora estamos pasando un valor que garantizamos que es de tipo 'Avatar'.
        player_id = self.write.create_player(
            name=clean_name, birth_date=request.birth_date, avatar=avatar_to_use
        )

        # --- PASO 4: Manejo de Efectos Secundarios por WS (omitido en este caso) ---

        # --- PASO 5: Construcción de la Respuesta ---
        if player_id is None:
            raise InternalGameError(
                f"El nombre de jugador '{clean_name}' ya está en uso o hubo un error al crearlo."
            )

        return CreatePlayerResponse(player_id=player_id)
