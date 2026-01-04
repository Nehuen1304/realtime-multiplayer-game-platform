from ...database.interfaces import IQueryManager, ICommandManager
from ...domain.enums import GameStatus, ResponseStatus
from ...api.schemas import (
    CreateGameRequest,
    CreateGameResponse,
    JoinGameRequest,
    JoinGameResponse,
    ListGamesResponse,
    LeaveGameResponse,
    LeaveGameRequest,
)

from ..helpers.validators import GameValidator
from ..helpers.notificators import Notificator
from ...api.schemas import GameLobbyInfo
from ..exceptions import (
    InternalGameError,
    GameNotFound,
    GameFull,
    AlreadyJoined,
    InvalidAction,
)


class LobbyService:
    """
    Servicio para manejar la lógica de negocio del lobby.
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

    async def create_game(
        self, request: CreateGameRequest
    ) -> CreateGameResponse:
        """Crea una nueva partida y la pone en estado LOBBY."""
        # --- PASO 1: Parsear Inputs (implícito en el request) ---

        # --- PASO 2: Validar ---
        self.validator.validate_player_exists(request.host_id)
        self.validator.validate_game_name_is_unique(request.game_name)

        # --- PASO 3: Lectura/Escritura en DB ---
        game_id = self.write.create_game(
            name=request.game_name,
            min_players=request.min_players,
            max_players=request.max_players,
            host_id=request.host_id,
            password=request.password,
        )
        if game_id is None:
            raise InternalGameError(detail="La base de datos no pudo crear la partida.")

        # --- PASO 4: Notificación WS ---
        # Construyo el DTO con la información recibida.
        # Esto es más eficiente que volver a llamar a la db.
        game_info = GameLobbyInfo(
            id=game_id,
            name=request.game_name,
            min_players=request.min_players,
            max_players=request.max_players,
            player_count=1,  # La partida se crea con 1 jugador (el host)
            host_id=request.host_id,
            game_status=GameStatus.LOBBY,
            password=request.password,
        )
        await self.notifier.notify_game_created(game_info)

        # --- PASO 5: Crear Response ---
        return CreateGameResponse(game_id=game_id)

    async def join_game(self, request: JoinGameRequest) -> JoinGameResponse:
        """Permite a un jugador unirse a una partida en estado LOBBY."""
        # --- PASO 1: Parsear Inputs ---
        if not request.game_id:
            raise GameNotFound(detail="No se encontró partida con ese ID.")

        game_id = request.game_id
        player_id = request.player_id

        # --- PASO 2: Validar ---
        game = self.validator.validate_game_exists(game_id)
        player = self.validator.validate_player_exists(player_id)
        self.validator.validate_game_status(game, GameStatus.LOBBY)

        if len(game.players) >= game.max_players:
            raise GameFull(detail="La partida está llena.")
        if self.read.is_player_in_game(
            game_id=game_id, player_id=player_id
        ):
            raise AlreadyJoined(detail="El jugador ya está en la partida.")

        # --- PASO 3: Lectura/Escritura en DB ---
        status = self.write.add_player_to_game(
            player_id=player_id, game_id=game_id
        )
        if status != ResponseStatus.OK:
            error_message = "La base de datos no pudo unir al jugador."
            raise InternalGameError(detail=error_message)

        # --- PASO 4: Notificación WS ---
        # Construyo el DTO con la información ya pedida.
        # Esto es más eficiente que volver a llamar a la db.
        game_info = GameLobbyInfo(
            id=game_id,
            name=game.name,
            min_players=game.min_players,
            max_players=game.max_players,
            player_count=len(game.players) + 1,  # +1 por el jugador que se une
            host_id=game.host.player_id,
            game_status=game.status,
            password=game.password,
        )
        await self.notifier.notify_player_joined(
            game_id, player.player_id, player.player_name, game_info
        )

        # --- PASO 5: Crear Response ---
        return JoinGameResponse(detail="Te has unido a la partida con éxito.")

    def list_games(self) -> ListGamesResponse:
        """Devuelve una lista de todas las partidas en estado LOBBY."""
        # --- PASOS 1 y 2 (Omitidos, no hay inputs ni validaciones complejas) ---

        # --- PASO 3: Lectura en DB ---
        games_in_lobby = self.read.list_games_in_lobby()

        # --- PASO 4 (Omitido, es una consulta) ---

        # --- PASO 5: Crear Response ---
        return ListGamesResponse(
            detail="Listado de partidas en el lobby obtenido con éxito.",
            games=games_in_lobby,
        )

    async def leave_game(self, request: LeaveGameRequest) -> LeaveGameResponse:
        """Permite a un jugador abandonar una partida."""
        # --- PASO 1: Parsear Inputs ---
        game_id = request.game_id
        player_id = request.player_id

        # --- PASO 2: Validar ---
        game = self.validator.validate_game_exists(game_id)
        player = self.validator.validate_player_exists(player_id)
        self.validator.validate_player_in_game(game, player_id)

        if game.status != GameStatus.LOBBY:
            raise InvalidAction(detail=
                                "No puedes abandonar una partida ya iniciada.")

        # --- PASO 3: Lectura/Escritura en DB ---
        is_host = game.host.player_id == player_id
        if is_host:
            status = self.write.delete_game(game_id=game_id)
            if status != ResponseStatus.OK:
                error_message = "La base de datos no pudo eliminar la partida."
                raise InternalGameError(detail=error_message)
            # notify_player_left ya incluye el atributo is_host para in game players
            await self.notifier.notify_game_removed(game_id)
        else:
            status = self.write.remove_player_from_game(
                player_id=player_id, game_id=game_id
            )
            if status != ResponseStatus.OK:
                error_message = "La base de datos no pudo sacar al jugador."
                raise InternalGameError(detail=error_message)

        # --- PASO 4: Notificación WS ---
        game_info = GameLobbyInfo(
            id=game_id,
            name=game.name,
            min_players=game.min_players,
            max_players=game.max_players,
            player_count=len(game.players) - 1,
            host_id=game.host.player_id,
            game_status=game.status,
            password=game.password,
        )
        await self.notifier.notify_player_left(
            game_id, player.player_id, player.player_name, game_info
        )
            
        # --- PASO 5: Crear Response ---
        return LeaveGameResponse(detail="Has abandonado la partida con éxito.")
    