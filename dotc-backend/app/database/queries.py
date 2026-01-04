from typing import List, Optional
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import select, func

from .interfaces import IQueryManager
from .orm_models import (
    GameTable,
    PendingActionTable,
    PlayerInGameTable,
    PlayerTable,
    CardTable,
    SecretCardTable,
    GameStatus,
    CardLocation,
    PlayerRole,
)
from ..domain.models import Game, PendingAction, PlayerInfo, Card, SecretCard, PlayerInGame
from ..api.schemas import GameLobbyInfo

from app.database import mappers

"""
Outputs de los Queries: Deben ser Modelos de Dominio (Game, PlayerInfo, Card). El QueryManager es una "fábrica" de modelos de dominio a partir de los datos crudos de la BD.

    BIEN: get_game(game_id: int) -> Optional[Game].
    BIEN: get_player(player_id: int) -> Optional[PlayerInfo].
    BIEN: list_games_in_lobby() -> List[GameLobbyInfo]. (Aquí GameLobbyInfo actúa como un DTO - Data Transfer Object - específico para esa consulta, lo cual es perfecto).
"""


class DatabaseQueryManager(IQueryManager):
    """
    Implementación concreta de IQueryManager.
    Maneja todas las operaciones de LECTURA (Queries) de la base de datos.
    """

    def __init__(self, session: Session):
        self.session = session

    # ═══════════════════════════════════════════════════════════
    # 🎮 QUERIES DE PARTIDAS (GameTable)
    # ═══════════════════════════════════════════════════════════

    def get_game(self, game_id: int) -> Optional[Game]:
        """
        Obtiene el objeto de dominio 'Game' completo, con todas sus relaciones cargadas.
        NOTA: Si falla la validación Pydantic por datos NULL en relaciones,
        intenta cargar sin las relaciones de players.
        """
        try:
            # 1. Construir la consulta con select() y cargar eficientemente las relaciones.
            stmt = (
                select(GameTable)
                .options(
                    # Cargar el host directamente (relación uno a uno).
                    joinedload(GameTable.host),
                    # Cargar todas las cartas de la partida en una segunda consulta.
                    selectinload(GameTable.cards),
                    # Cargar los detalles de la asociación (PlayerInGameTable) y, para cada uno,
                    # cargar el objeto PlayerTable completo. Esto es crucial.
                    selectinload(GameTable.player_details).joinedload(
                        PlayerInGameTable.player
                    ),
                )
                .filter(GameTable.game_id == game_id)
            )

            # 2. Ejecutar la consulta y obtener un único resultado o None.
            db_game = self.session.execute(stmt).scalar_one_or_none()

            if not db_game:
                return None

            return mappers.map_game_orm_to_domain(db_game)

        except Exception as e:
            print(f"Error en get_game: {e}")
            # Si falló por validación Pydantic, intentar sin cargar players
            try:
                stmt_simple = (
                    select(GameTable)
                    .options(
                        joinedload(GameTable.host),
                        selectinload(GameTable.cards),
                    )
                    .filter(GameTable.game_id == game_id)
                )
                db_game_simple = self.session.execute(stmt_simple).scalar_one_or_none()
                if not db_game_simple:
                    return None
                # Mapear sin players
                return mappers.map_game_orm_to_domain(db_game_simple)
            except Exception as e2:
                print(f"Error en get_game (fallback sin players): {e2}")
                self.session.rollback()
                return None

    def list_games_in_lobby(self) -> List[GameLobbyInfo]:
        """Devuelve una lista optimizada de partidas en estado LOBBY."""
        try:
            # Usamos options() para cargar eficientemente el host y los detalles del jugador.
            lobby_games_orm = (
                self.session.query(GameTable)
                .options(
                    joinedload(GameTable.host),
                    selectinload(GameTable.player_details),
                )
                .filter(GameTable.game_status == GameStatus.LOBBY)
                .all()
            )

            return [
                mappers.map_game_orm_to_lobby_dto(game_orm)
                for game_orm in lobby_games_orm
            ]
        except Exception as e:
            print(f"Error al listar las partidas: {e}")
            self.session.rollback()
            return []

    def get_game_status(self, game_id: int) -> Optional[GameStatus]:
        """Obtiene únicamente el estado de una partida de forma eficiente."""
        try:
            # Pide explícitamente solo la columna 'game_status'.
            stmt = select(GameTable.game_status).where(
                GameTable.game_id == game_id
            )
            # .scalar_one_or_none() devuelve el valor directamente o None.
            return self.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            print(f"Error en get_game_status: {e}")
            self.session.rollback()
            return None

    def get_current_turn(self, game_id: int) -> Optional[int]:
        """Obtiene únicamente el ID del jugador cuyo turno es actual."""
        try:
            return self.session.execute(
                select(GameTable.current_player).where(
                    GameTable.game_id == game_id
                )
            ).scalar_one_or_none()

        except Exception as e:
            print(f"Error en get_current_turn: {e}")
            self.session.rollback()
            return None

    def get_pending_saga(self, game_id: int) -> Optional[dict]:
        """Obtiene el JSON de 'pending_saga' para una partida dada, forzando una lectura nueva."""
        try:
            game_to_refresh = self.session.get(GameTable, game_id)
            if game_to_refresh:
                self.session.expire(game_to_refresh)
            stmt = select(GameTable.pending_saga).where(GameTable.game_id == game_id)
            return self.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            print(f"Error en get_pending_saga: {e}")
            self.session.rollback()
            return None

    # ═══════════════════════════════════════════════════════════
    # 👤 QUERIES DE JUGADORES (PlayerTable)
    # ═══════════════════════════════════════════════════════════

    def get_player(self, player_id: int) -> Optional[PlayerInfo]:
        """Obtiene la información básica de un jugador por su ID."""
        try:
            player_orm = (
                self.session.query(PlayerTable)
                .filter(PlayerTable.player_id == player_id)
                .first()
            )
            return (
                mappers.map_player_orm_to_info_dto(player_orm)
                if player_orm
                else None
            )
        except Exception as e:
            print(f"Error en get_player: {e}")
            self.session.rollback()
            return None

    def get_players_in_game(self, game_id: int) -> List[PlayerInGame]:
        """
        Obtiene la lista de jugadores (como DTOs PlayerInGame) de una partida específica.
        """
        try:
            # 1. Construir la consulta con select() y cargar las relaciones necesarias.
            stmt = (
                select(GameTable)
                .options(
                    # Cargamos los detalles de la asociación y, para cada uno, el jugador.
                    selectinload(GameTable.player_details).joinedload(
                        PlayerInGameTable.player
                    ),
                    # También cargamos las cartas para poder construir la mano.
                    selectinload(GameTable.cards),
                )
                .where(GameTable.game_id == game_id)
            )
            # 2. Ejecutar la consulta.
            game = self.session.execute(stmt).scalar_one_or_none()

            if not game:
                return []

            # 3. Usar el mapper para construir la lista de jugadores.
            # Esto reutiliza la lógica que ya funciona en get_game.
            players_in_game = []
            for detail in game.player_details:
                player_hand = [
                    mappers.map_card_orm_to_dto(c)
                    for c in game.cards
                    if c.player_id == detail.player_id
                    and c.location == CardLocation.IN_HAND
                ]
                players_in_game.append(
                    mappers.map_player_in_game_orm_to_dto(detail, player_hand)
                )
            return players_in_game

        except Exception as e:
            print(f"Error en get_players_in_game: {e}")
            self.session.rollback()
            return []

    def get_player_name(self, player_id: int) -> Optional[str]:
        """Obtiene solo el nombre de un jugador sin validación Pydantic."""
        try:
            result = self.session.execute(
                select(PlayerTable.player_name).where(
                    PlayerTable.player_id == player_id
                )
            ).scalar_one_or_none()
            return result
        except Exception as e:
            print(f"Error en get_player_name: {e}")
            return None

    def get_player_role(
        self, player_id: int, game_id: int
    ) -> Optional[PlayerRole]:
        """Obtiene el rol de un jugador en una partida específica de forma eficiente."""
        try:
            # Construimos una consulta directa a la tabla de asociación.
            # Solo pedimos la columna 'player_role' para máxima eficiencia.
            stmt = select(PlayerInGameTable.player_role).where(
                PlayerInGameTable.game_id == game_id,
                PlayerInGameTable.player_id == player_id,
            )
            # .scalar_one_or_none() es perfecto: devuelve el rol, o None si no se encuentra la fila.
            return self.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            print(f"Error en get_player_role: {e}")
            self.session.rollback()
            return None

    def get_murderer_id(self, game_id: int) -> Optional[int]:
        """Obtiene el ID del jugador con el rol de Asesino en una partida."""
        try:
            stmt = select(PlayerInGameTable.player_id).where(
                PlayerInGameTable.game_id == game_id,
                PlayerInGameTable.player_role == PlayerRole.MURDERER,
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            print(f"Error en get_murderer_id: {e}")
            self.session.rollback()
            return None

    def get_accomplice_id(self, game_id: int) -> Optional[int]:
        """Obtiene el ID del jugador con el rol de Cómplice en una partida."""
        try:
            stmt = select(PlayerInGameTable.player_id).where(
                PlayerInGameTable.game_id == game_id,
                PlayerInGameTable.player_role == PlayerRole.ACCOMPLICE,
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            print(f"Error en get_accomplice_id: {e}")
            self.session.rollback()
            return None

    # ═══════════════════════════════════════════════════════════
    # 🃏 QUERIES DE CARTAS (CardTable & SecretCardTable)
    # ═══════════════════════════════════════════════════════════

    def get_card(self, card_id: int, game_id: int) -> Optional[Card]:
        """Obtiene una instancia de carta específica por su ID y el ID de la partida."""
        try:
            stmt = select(CardTable).where(
                CardTable.card_id == card_id, CardTable.game_id == game_id
            )
            card_orm = self.session.execute(stmt).scalar_one_or_none()
            return mappers.map_card_orm_to_dto(card_orm) if card_orm else None
        except Exception as e:
            print(f"Error en get_card: {e}")
            self.session.rollback()
            return None

    def get_secret(self, secret_id: int, game_id: int) -> Optional[SecretCard]:
        """Obtiene una instancia de carta secreta específica por su ID y el ID de la partida."""
        try:
            stmt = select(SecretCardTable).where(
                SecretCardTable.secret_id == secret_id,
                SecretCardTable.game_id == game_id
            )
            secret_orm = self.session.execute(stmt).scalar_one_or_none()
            return mappers.map_secret_card_orm_to_dto(secret_orm) if secret_orm else None
        except Exception as e:
            print(f"Error en get_secret: {e}")
            self.session.rollback()
            return None

    def get_set(self, set_id: int, game_id: int) -> List[Card]:
        """
        Obtiene una lista de cartas que pertenecen a un set específico
        dentro de una partida.
        """
        try:
            stmt = select(CardTable).where(
                CardTable.game_id == game_id,
                CardTable.set_id == set_id,
            )
            cards_orm = self.session.execute(stmt).scalars().all()
            return [mappers.map_card_orm_to_dto(c) for c in cards_orm]
        except Exception as e:
            print(f"Error al obtener las cartas del set: {e}")
            self.session.rollback()
            return []
    
    def get_player_hand(self, game_id: int, player_id: int) -> List[Card]:
        """Obtiene todas las cartas en la mano de un jugador."""
        try:
            stmt = select(CardTable).where(
                CardTable.game_id == game_id,
                CardTable.player_id == player_id,
                CardTable.location == CardLocation.IN_HAND,
            )
            cards_orm = self.session.execute(stmt).scalars().all()
            return [mappers.map_card_orm_to_dto(c) for c in cards_orm]
        except Exception as e:
            print(f"Error al obtener la mano del jugador: {e}")
            self.session.rollback()
            return []

    def get_deck(self, game_id: int) -> List[Card]:
        """Obtiene todas las cartas del mazo de robo de una partida."""
        try:
            stmt = select(CardTable).where(
                CardTable.game_id == game_id,
                CardTable.location == CardLocation.DRAW_PILE,
            )
            cards_orm = self.session.execute(stmt).scalars().all()
            return [mappers.map_card_orm_to_dto(c) for c in cards_orm]
        except Exception as e:
            print(f"Error al obtener el mazo de robo: {e}")
            self.session.rollback()
            return []

    def get_discard_pile(self, game_id: int) -> List[Card]:
        """Obtiene todas las cartas del mazo de descarte de una partida."""
        try:
            stmt = select(CardTable).where(
                CardTable.game_id == game_id,
                CardTable.location == CardLocation.DISCARD_PILE,
            )
            cards_orm = self.session.execute(stmt).scalars().all()
            return [mappers.map_card_orm_to_dto(c) for c in cards_orm]
        except Exception as e:
            print(f"Error al obtener el mazo de descarte: {e}")
            self.session.rollback()
            return []

    def get_player_secrets(
        self, game_id: int, player_id: int
    ) -> List[SecretCard]:
        """Obtiene las cartas secretas de un jugador en una partida."""
        try:
            secrets_orm = (
                self.session.query(SecretCardTable)
                .filter(
                    SecretCardTable.game_id == game_id,
                    SecretCardTable.player_id == player_id,
                )
                .all()
            )
            # Usamos el mapper para una transformación limpia y consistente.
            return [mappers.map_secret_card_orm_to_dto(s) for s in secrets_orm]
        except Exception as e:
            print(f"Error al obtener los secretos del jugador: {e}")
            self.session.rollback()
            return []

    # ═══════════════════════════════════════════════════════════
    # ✅ QUERIES DE NUMEROS (maximos minimos etc)
    # ═══════════════════════════════════════════════════════════

    def get_max_set_id(self, game_id: int) -> Optional[int]:
        """
        Obtiene el valor más alto de 'set_id' presente en toda la tabla de cartas.

        Returns:
            El 'set_id' máximo como un entero, o None si no hay cartas con set_id.
        """
        try:
            stmt = select(func.max(CardTable.set_id)).where(CardTable.game_id == game_id)
            max_set_id = self.session.execute(stmt).scalar_one_or_none()
            print(f"DATABASE: El set_id máximo encontrado es: {max_set_id}")
            return max_set_id
        except Exception as e:
            print(f"Error al obtener el set_id máximo: {e}")
            self.session.rollback()
            return None

    def get_size_deck(self, game_id: int) -> int:
        """
        Obtiene el número de cartas en el mazo de robo (DRAW_PILE) de una partida.

        Args:
            game_id: ID de la partida.

        Returns:
            El número de cartas en el mazo de robo. Devuelve 0 si el mazo está
            vacío o la partida no existe.
        """
        try:
            stmt = select(func.count()).select_from(CardTable).where(
                CardTable.game_id == game_id,
                CardTable.location == CardLocation.DRAW_PILE,
            )
            deck_size = self.session.execute(stmt).scalar_one()
            return deck_size
        except Exception as e:
            print(f"Error al obtener el tamaño del mazo: {e}")
            self.session.rollback()
            return 0

    # ═══════════════════════════════════════════════════════════
    # ✅ QUERIES DE VALIDACIÓN (Booleanos y Existencia)
    # ═══════════════════════════════════════════════════════════

    def is_player_in_game(self, game_id: int, player_id: int) -> bool:
        """Verifica si un jugador es parte de una partida. Usa una consulta EXISTS para ser eficiente."""
        try:
            # Consulta directa a la tabla de asociación, es lo más rápido.
            stmt = select(PlayerInGameTable).where(
                PlayerInGameTable.game_id == game_id,
                PlayerInGameTable.player_id == player_id,
            )
            # preguntamos si existe al menos una fila que cumpla la condición.
            return self.session.query(stmt.exists()).scalar()
        except Exception as e:
            print(f"Error al verificar si el jugador está en la partida: {e}")
            self.session.rollback()
            return False

    def is_player_host(self, game_id: int, player_id: int) -> bool:
        """Verifica si un jugador es el host de una partida de forma eficiente."""
        try:
            # Pedimos solo la columna host_id, no toda la fila de la partida.
            stmt = select(GameTable.host_id).where(GameTable.game_id == game_id)
            host_id = self.session.execute(stmt).scalar_one_or_none()
            # Comparamos el resultado directamente. Si host_id es None, la comparación será False.
            return host_id == player_id
        except Exception as e:
            print(f"Error en is_player_host: {e}")
            self.session.rollback()
            return False

    def game_name_exists(self, game_name: str) -> bool:
        """Verifica si ya existe una partida con un nombre determinado."""
        try:
            stmt = select(GameTable).where(GameTable.game_name == game_name)
            # Usamos .exists() para que la DB haga el trabajo y solo devuelva True/False.
            return self.session.query(stmt.exists()).scalar()
        except Exception as e:
            print(f"Error en game_name_exists: {e}")
            self.session.rollback()
            # En caso de error, es más seguro asumir que existe para evitar duplicados.
            return True
        

    # ═══════════════════════════════════════════════════════════
    # ⏳ QUERIES DE ACCIONES PENDIENTES (PendingActionTable)
    # ═══════════════════════════════════════════════════════════
    
    def get_pending_action(self, game_id: int) -> Optional[PendingAction]:
        try:
            # Usamos 'selectinload' para cargar las cartas asociadas de forma eficiente
            stmt = select(PendingActionTable).options(selectinload(PendingActionTable.cards)).filter_by(game_id=game_id)
            orm_obj = self.session.execute(stmt).scalar_one_or_none()
            
            if not orm_obj:
                return None
            
            return mappers.map_pending_action_orm_to_dto(orm_obj)
        except Exception as e:
            print(f"Error en get_pending_action: {e}")
            self.session.rollback()
            return None
