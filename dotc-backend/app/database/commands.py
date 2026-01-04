from typing import Any, List, Optional, cast
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import update

from app.api.schemas import PlayCardRequest

from .interfaces import ICommandManager, IQueryManager
from .orm_models import (
    GameTable,
    PendingActionTable,
    PlayerTable,
    CardTable,
    SecretCardTable,
    PlayerInGameTable,
    GameStatus,
    CardLocation,
    CardType,
)

# Importa los modelos y Enums necesarios para las firmas
from ..domain.models import Card, Avatar, PlayerRole
from ..domain.enums import ResponseStatus, GameActionState

"""
El DBManager debe ser lo más "tonto" posible. Su trabajo es traducir entre el mundo de la base de datos (ORM Models) y el mundo del negocio (Domain Models).

    Inputs de los Commands: Deben ser datos primitivos (int, str, date) o modelos de dominio simples. La idea es que el GameManager le dé órdenes claras y directas.
        BIEN: create_player(name: str, birth_date: date, avatar: Avatar) -> Optional[int]
        MAL: create_player(request: CreatePlayerRequest). El DBManager no debe saber nada de los esquemas de la API.

    Outputs de los Commands: Deben ser datos primitivos (int para un nuevo ID) o un ResponseStatus. Nunca deben devolver un modelo de dominio complejo. Su trabajo es confirmar la escritura, no devolver el estado.
        BIEN: create_game(...) -> Optional[int] (devuelve el game_id).
        BIEN: update_game_status(...) -> ResponseStatus.
        MAL: create_player(...) -> Optional[PlayerInfo]. Esto es innecesario. Devolver el player_id es suficiente.
"""


class DatabaseCommandManager(ICommandManager):
    """
    Implementación concreta de ICommandManager.
    Maneja todas las operaciones de ESCRITURA (Commands) en la base de datos
    siguiendo el principio de "operaciones atómicas y simples".
    """

    def __init__(self, queries: IQueryManager):
        self.queries = queries
        self.session: Session = cast(Any, queries).session

    # ═══════════════════════════════════════════════════════════
    # 👤 COMMANDS DE JUGADORES (PlayerTable)
    # ═══════════════════════════════════════════════════════════

    def create_player(
        self, name: str, birth_date: date, avatar: Avatar
    ) -> Optional[int]:
        """Crea un nuevo jugador. Devuelve el ID del jugador creado o None si falla."""
        try:
            db_player = PlayerTable(
                player_name=name,
                player_birth_date=birth_date,
                player_avatar=avatar,
            )
            self.session.add(db_player)
            self.session.commit()
            self.session.refresh(db_player)
            return cast(int, db_player.player_id)
        except Exception as e:
            self.session.rollback()
            print(f"Error al crear un nuevo jugador: {e}")
            return None

    def delete_player(self, player_id: int) -> ResponseStatus:
        """Elimina un jugador completamente."""
        try:
            jugador_a_borrar = self._get_player_by_id(player_id)
            if not jugador_a_borrar:
                return ResponseStatus.PLAYER_NOT_FOUND

            self.session.delete(jugador_a_borrar)
            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al eliminar el jugador: {e}")
            return ResponseStatus.ERROR

    def set_player_role(
        self, player_id: int, game_id: int, role: PlayerRole
    ) -> ResponseStatus:
        """Actualiza el campo 'player_role' de un jugador."""
        try:
            jugador = self._get_player_in_game_by_id(
                player_id=player_id, game_id=game_id
            )
            if not jugador:
                return ResponseStatus.PLAYER_NOT_FOUND

            jugador.player_role = role

            self.session.commit()
            return ResponseStatus.OK

        except Exception as e:
            self.session.rollback()
            print(f"Error al setear el rol: {e}")
            return ResponseStatus.ERROR

    def set_player_social_disgrace(
        self, player_id: int, game_id: int, is_disgraced: bool
    ) -> ResponseStatus:
        """Actualiza el campo 'social_disgrace' de un jugador."""
        try:
            jugador = self._get_player_in_game_by_id(player_id, game_id)
            if not jugador:
                return ResponseStatus.PLAYER_NOT_FOUND

            jugador.social_disgrace = is_disgraced

            self.session.commit()
            return ResponseStatus.OK

        except Exception as e:
            self.session.rollback()
            print(f"Error al setear el rol: {e}")
            return ResponseStatus.ERROR


    # ═══════════════════════════════════════════════════════════
    # 🎮 COMMANDS DE PARTIDAS (GameTable & PlayersGames)
    # ═══════════════════════════════════════════════════════════

    def create_game(
        self,
        name: str,
        min_players: int,
        max_players: int,
        host_id: int,
        password: Optional[str] = None,
    ) -> Optional[int]:
        """Crea una nueva partida y asocia al host. Devuelve el ID de la partida o None."""
        try:
            if not self._get_player_by_id(host_id):
                return None

            db_game = GameTable(
                game_name=name,
                min_players=min_players,
                max_players=max_players,
                game_password=password,
                host_id=host_id,
                game_status=GameStatus.LOBBY,
            )
            self.session.add(db_game)
            self.session.flush()

            host_association = PlayerInGameTable(
                game_id=db_game.game_id, player_id=host_id
            )

            self.session.add(host_association)
            self.session.commit()
            self.session.refresh(db_game)

            return cast(int, db_game.game_id)
        except Exception as e:
            self.session.rollback()
            print(f"Error al crear la partida: {e}")
            return None

    def delete_game(self, game_id: int) -> ResponseStatus:
        try:
            partida_a_borrar = self._get_game_by_id(game_id)
            if not partida_a_borrar:
                return ResponseStatus.GAME_NOT_FOUND
            self.session.delete(partida_a_borrar)
            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al eliminar la partida: {e}")
            return ResponseStatus.ERROR

    def add_player_to_game(
        self, player_id: int, game_id: int
    ) -> ResponseStatus:
        try:
            if self._get_player_in_game_by_id(player_id, game_id):
                return ResponseStatus.ALREADY_JOINED
            if not self._get_player_by_id(player_id):
                return ResponseStatus.PLAYER_NOT_FOUND
            if not self._get_game_by_id(game_id):
                return ResponseStatus.GAME_NOT_FOUND

            player_in_game = PlayerInGameTable(
                player_id=player_id, game_id=game_id
            )
            self.session.add(player_in_game)
            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error en add_player_to_game: {e}")
            return ResponseStatus.ERROR

    def remove_player_from_game(
        self, player_id: int, game_id: int
    ) -> ResponseStatus:
        try:
            player_in_game_to_remove = self._get_player_in_game_by_id(
                player_id, game_id
            )

            if not player_in_game_to_remove:
                return ResponseStatus.PLAYER_NOT_IN_GAME

            self.session.delete(player_in_game_to_remove)
            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error en remove_player_from_game: {e}")
            return ResponseStatus.ERROR

    def update_game_status(
        self, game_id: int, new_status: GameStatus
    ) -> ResponseStatus:
        """Actualiza el campo 'game_status' de una partida."""
        try:
            partida = self._get_game_by_id(game_id)
            if not partida:
                return ResponseStatus.GAME_NOT_FOUND

            partida.game_status = new_status

            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al cambiar el estado de la partida: {e}")
            return ResponseStatus.ERROR

    def set_current_turn(self, game_id: int, player_id: int) -> ResponseStatus:
        """Actualiza el campo 'current_player' de una partida."""
        try:
            partida = self._get_game_by_id(game_id)
            if not partida:
                return ResponseStatus.GAME_NOT_FOUND

            partida.current_player = player_id

            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al setear el turno: {e}")
            return ResponseStatus.ERROR

    # ═══════════════════════════════════════════════════════════
    # 🃏 COMMANDS DE CARTAS Y SETS (CardTable)
    # ═══════════════════════════════════════════════════════════

    def create_card(
        self,
        card_type: CardType,
        location: CardLocation,
        game_id: int,
        position: Optional[int] = None,
        set_id: Optional[int] = None,
        player_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Crea una nueva carta en la base de datos.
        Devuelve el ID autogenerado de la carta, o None si falla.
        """
        try:
            # 1. Creamos la instancia de CardTable.
            #    NO le pasamos 'card_id', porque la base de datos lo genera.
            db_card = CardTable(
                card_type=card_type,
                location=location,
                game_id=game_id,
                position=position,
                set_id=set_id,
                player_id=player_id,
            )

            # 2. Añadimos, confirmamos y refrescamos.
            self.session.add(db_card)
            self.session.commit()
            self.session.refresh(db_card)

            # 3. Devolvemos el 'card_id' que la BD acaba de generar.
            #    El 'cast' es solo para que el linter no se queje.
            return cast(int, db_card.card_id)

        except Exception as e:
            self.session.rollback()
            # Cambié el mensaje de error para que sea más útil
            print(f"Error al crear la carta: {e}")
            return None

    # ... (dentro de la clase DatabaseCommandManager)

    def create_deck_for_game(
        self, game_id: int, cards: List[Card]
    ) -> ResponseStatus:
        """
        Crea un conjunto de cartas (mazo) a partir de una lista de modelos de dominio `Card`.
        """
        try:
            if not self._get_game_by_id(game_id):
                return ResponseStatus.GAME_NOT_FOUND

            card_mappings = [
                {
                    "game_id": game_id,  # Asigna el game_id correcto
                    "card_type": card.card_type,
                    "location": card.location,
                    "position": card.position,
                    "player_id": card.player_id,
                }
                for card in cards
            ]

            if card_mappings:
                self.session.bulk_insert_mappings(
                    CardTable.__mapper__, card_mappings
                )
                self.session.commit()

            return ResponseStatus.OK

        except Exception as e:
            self.session.rollback()
            print(f"Error en create_deck_for_game: {e}")
            return ResponseStatus.ERROR

    def update_card_location(
        self,
        card_id: int,
        game_id: int,
        new_location: CardLocation,
        owner_id: Optional[int] = None,
        set_id: Optional[int] = None,
    ) -> ResponseStatus:
        """Mueve una carta a una nueva ubicación."""
        try:
            carta = self._get_card_in_game(card_id, game_id)
            if not carta:
                return ResponseStatus.CARD_NOT_FOUND

            carta.location = new_location
            carta.player_id = owner_id
            carta.set_id = set_id

            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            print(f"Error al mover la carta: {e}")
            self.session.rollback()
            return ResponseStatus.ERROR

    def update_card_position(
        self, card_id: int, game_id: int, new_position: int
    ) -> ResponseStatus:
        """Mueve una carta a una nueva ubicación."""
        try:
            carta = self._get_card_in_game(card_id, game_id)
            if not carta:
                return ResponseStatus.CARD_NOT_FOUND

            carta.position = new_position

            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            print(f"Error al cambiar la posicion de la carta: {e}")
            self.session.rollback()
            return ResponseStatus.ERROR

    def update_cards_to_set(
        self,
        game_id: int,
        card_ids: List[int],
        player_id: int,
        set_id: int,
    ) -> ResponseStatus:
        """Actualiza un grupo de cartas para formar un set."""
        try:
            stmt = (
                update(CardTable)
                .where(
                    CardTable.card_id.in_(card_ids),
                    CardTable.game_id == game_id,
                    CardTable.player_id
                    == player_id,  # Es crucial que sean del mismo jugador
                )
                .values(
                    location=CardLocation.PLAYED,
                    set_id=set_id,
                )
            )
            result = self.session.execute(stmt)

            # Debe asegurarse de que todas las cartas requeridas fueron actualizadas (atomicidad)
            if result.rowcount != len(card_ids):
                self.session.rollback()
                return (
                    ResponseStatus.INVALID_ACTION
                )  # Algo falló (ej. el jugador no tenía todas las cartas)

            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al crear el set de cartas: {e}")
            return ResponseStatus.ERROR

    def setear_set_id(
        self, card_id: int, game_id: int, target_set_id: int
    ) -> ResponseStatus:
        """Actualiza el campo 'set_id' de una carta."""
        try:
            card = self._get_card_in_game(card_id=card_id, game_id=game_id)
            if not card:
                return ResponseStatus.CARD_NOT_FOUND
            card.set_id = target_set_id
            self.session.commit()
            return ResponseStatus.OK

        except Exception as e:
            self.session.rollback()
            print(f"Error al setear el set de la carta: {e}")
            return ResponseStatus.ERROR

    def create_set(self, card_ids: List[int], game_id: int) -> int:
        # 1. Obtenemos el ID más alto de set que ya exista en la partida.
        try:
            max_set_id = self.queries.get_max_set_id(game_id=game_id)
            new_set_id = (max_set_id or 0) + 1

            # 2. Asignamos el nuevo set_id a todas las cartas proporcionadas.
            stmt = (
                update(CardTable)
                .where(
                    (CardTable.card_id.in_(card_ids))
                    & (CardTable.game_id == game_id)
                )
                .values(set_id=new_set_id)
            )
            self.session.execute(stmt)
            self.session.commit()
            return new_set_id
        except Exception as e:
            self.session.rollback()
            print(f"Error al crear el set: {e}")
            return -1

    def add_card_to_set(self, card_id: int, set_id: int, game_id: int) -> None:
        try:
            stmt = (
                update(CardTable)
                .where(
                    (CardTable.card_id == card_id)
                    & (CardTable.game_id == game_id)
                )
                .values(set_id=set_id)
            )
            self.session.execute(stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"Error al agregar la carta al set: {e}")

    def steal_set(self, set_id: int, new_owner_id: int, game_id: int) -> None:
        try:
            stmt = (
                update(CardTable)
                .where(
                    (CardTable.set_id == set_id)
                    & (CardTable.game_id == game_id)
                )
                .values(player_id=new_owner_id)
            )
            self.session.execute(stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"Error al robar el set: {e}")

    # ═══════════════════════════════════════════════════════════
    # 🤫 COMMANDS DE SECRETOS (SecretCardTable)
    # ═══════════════════════════════════════════════════════════

    def create_secret_card(
        self, player_id: int, game_id: int, role: PlayerRole, is_revealed: bool
    ) -> Optional[int]:
        """
        Crea un nuevo secreto en la base de datos.
        Devuelve el ID autogenerado del secreto, o None si falla.
        """
        try:
            db_secret = SecretCardTable(
                game_id=game_id,
                role=role,
                is_revealed=is_revealed,
                player_id=player_id,
            )

            self.session.add(db_secret)
            self.session.commit()
            self.session.refresh(db_secret)

            return cast(int, db_secret.secret_id)

        except Exception as e:
            self.session.rollback()
            print(f"Error al crear el secreto: {e}")
            return None

    def reveal_secret_card(
        self, secret_id: int, game_id: int, is_revealed: bool
    ) -> ResponseStatus:
        """Actualiza el campo 'is_revealed' de un secreto."""
        ...
        try:
            secreto = self._get_secret_in_game(
                secret_id=secret_id, game_id=game_id
            )
            if not secreto:
                return ResponseStatus.SECRET_NOT_FOUND

            secreto.is_revealed = is_revealed

            self.session.commit()
            return ResponseStatus.OK

        except Exception as e:
            self.session.rollback()
            print(f"Error al setear el revelado del secreto: {e}")
            return ResponseStatus.ERROR

    def change_secret_owner(
        self, secret_id: int, new_owner_id: int, game_id: int
    ):
        """
        Cambia el propietario de una carta secreta (SecretCard) en una partida.
        - secret_id: ID de la carta secreta a transferir.
        - new_owner_id: ID del nuevo jugador propietario.
        - game_id: ID de la partida.

        Devuelve ResponseStatus.OK si se realizó el cambio, ResponseStatus.ERROR si no se encontró la carta.
        """
        try:
            secret = (
                self.session.query(SecretCardTable)
                .filter_by(secret_id=secret_id, game_id=game_id)
                .first()
            )
            if not secret:
                return ResponseStatus.ERROR
            secret.player_id = new_owner_id
            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al cambiar el propietario del secreto: {e}")
            return ResponseStatus.ERROR

    # ═══════════════════════════════════════════════════════════
    # 🌐 COMMANDS DE GAME STATE
    # ═══════════════════════════════════════════════════════════

    def set_game_action_state(
        self,
        game_id: int,
        state: GameActionState,
        prompted_player_id: Optional[int],
        initiator_id: Optional[int],
    ) -> ResponseStatus:
        """
        Actualiza el estado de acción de la partida (action_state, prompted_player_id, action_initiator_id).
        """
        try:
            stmt = (
                update(GameTable)
                .where(GameTable.game_id == game_id)
                .values(
                    action_state=state,
                    prompted_player_id=prompted_player_id,
                    action_initiator_id=initiator_id,
                )
            )
            result = self.session.execute(stmt)
            self.session.commit()
            if result.rowcount == 0:
                return ResponseStatus.ERROR
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al setear el estado de acción del juego: {e}")
            return ResponseStatus.ERROR

    def clear_game_action_state(self, game_id: int) -> ResponseStatus:
        """
        Resetea el estado de acción de la partida (pone action_state en NONE y los otros en None).
        """
        try:
            stmt = (
                update(GameTable)
                .where(GameTable.game_id == game_id)
                .values(
                    action_state=GameActionState.NONE,
                    prompted_player_id=None,
                    action_initiator_id=None,
                )
            )
            result = self.session.execute(stmt)
            self.session.commit()
            if result.rowcount == 0:
                return ResponseStatus.ERROR
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al limpiar el estado de acción del juego: {e}")
            return ResponseStatus.ERROR

    # ═══════════════════════════════════════════════════════════
    # 🔧 HELPERS PRIVADOS (para uso interno de los comandos)
    # ═══════════════════════════════════════════════════════════

    def _get_game_by_id(self, game_id: int) -> Optional[GameTable]:
        return (
            self.session.query(GameTable)
            .filter(GameTable.game_id == game_id)
            .first()
        )

    def _get_player_by_id(self, player_id: int) -> Optional[PlayerTable]:
        return (
            self.session.query(PlayerTable)
            .filter(
                PlayerTable.player_id == player_id,
            )
            .first()
        )

    def _get_player_in_game_by_id(
        self, player_id: int, game_id: int
    ) -> Optional[PlayerInGameTable]:
        return (
            self.session.query(PlayerInGameTable)
            .filter(
                PlayerInGameTable.player_id == player_id,
                PlayerInGameTable.game_id == game_id,
            )
            .first()
        )

    def _get_secret_in_game(
        self, secret_id: int, game_id: int
    ) -> Optional[PlayerInGameTable]:
        return (
            self.session.query(SecretCardTable)
            .filter(SecretCardTable.secret_id == secret_id)
            .filter(SecretCardTable.game_id == game_id)
            .first()
        )

    def _get_card_in_game(
        self, card_id: int, game_id: int
    ) -> Optional[CardTable]:
        return (
            self.session.query(CardTable)
            .filter(CardTable.card_id == card_id, CardTable.game_id == game_id)
            .first()
        )

    def update_pending_saga(
        self, game_id: int, saga_data: Optional[dict]
    ) -> ResponseStatus:
        """
        Actualiza o limpia la columna 'pending_saga' en la GameTable.
        Si saga_data es None, la columna se limpia.
        """
        try:
            stmt = (
                update(GameTable)
                .where(GameTable.game_id == game_id)
                .values(pending_saga=saga_data)
            )
            self.session.execute(stmt)
            self.session.commit()
            print(
                f"Saga pendiente actualizada para la partida {game_id}: {saga_data}"
            )
            return ResponseStatus.OK
        except Exception as e:
            print(f"Error en update_pending_saga: {e}")
            self.session.rollback()
            return ResponseStatus.ERROR
        
    # ═══════════════════════════════════════════════════════════
    # ⏳ COMMANDS DE ACCIONES PENDIENTES (PendingActionTable)
    # ═══════════════════════════════════════════════════════════

    def create_pending_action(self, game_id: int, player_id: int,
                                request: PlayCardRequest) -> ResponseStatus:
        try:
            # Borramos cualquier acción previa para esta partida
            self.session.query(PendingActionTable).filter_by(game_id=game_id).delete()
            self.session.flush() # Asegura que el delete se ejecute antes del insert

            # Obtenemos los objetos ORM de las cartas que se están jugando
            cards_to_link = self.session.query(CardTable).filter(
                CardTable.card_id.in_(request.card_ids)).all()

            if len(cards_to_link) != len(request.card_ids):
                # Si no encontramos todas las cartas, algo está mal.
                self.session.rollback()
                return ResponseStatus.CARD_NOT_FOUND

            # Creamos la acción pendiente
            new_action = PendingActionTable(
                game_id=game_id,
                player_id=player_id,
                action_type=request.action_type,
                target_player_id=request.target_player_id,
                target_secret_id=request.target_secret_id,
                target_card_id=request.target_card_id,
                target_set_id=request.target_set_id,
                responses_count=0,
                nsf_count=0,
                last_action_player_id=player_id,
                # Asignamos la lista de objetos ORM de las cartas a la relación
                cards=cards_to_link
            )
            
            self.session.add(new_action)
            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al crear la acción pendiente: {e}")
            return ResponseStatus.ERROR

    def increment_nsf_responses(self, game_id: int, player_id: int, add_nsf: bool) -> ResponseStatus:
        try:
            action = self.session.query(PendingActionTable).filter_by(
                game_id=game_id).first()
            if not action:
                return ResponseStatus.ERROR

            action.responses_count += 1
            if add_nsf:
                action.nsf_count += 1
                action.responses_count = 0 
                action.last_action_player_id = player_id

            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al incrementar las respuestas NSF: {e}")
            return ResponseStatus.ERROR

    def clear_pending_action(self, game_id: int) -> ResponseStatus:
        try:
            # Primero obtenemos el ID de la pending_action
            pending_action = self.session.query(PendingActionTable).filter_by(
                game_id=game_id).first()
            
            if pending_action:
                # Borrar manualmente la tabla de enlace (SQLite no siempre ejecuta CASCADE)
                from app.database.orm_models import PendingActionCardLinkTable
                self.session.query(PendingActionCardLinkTable).filter_by(
                    pending_action_id=pending_action.id
                ).delete()
                
                # Ahora borrar la pending_action
                self.session.query(PendingActionTable).filter_by(
                    game_id=game_id).delete()
            
            self.session.commit()
            return ResponseStatus.OK
        except Exception as e:
            self.session.rollback()
            print(f"Error al limpiar la acción pendiente: {e}")
            return ResponseStatus.ERROR       
