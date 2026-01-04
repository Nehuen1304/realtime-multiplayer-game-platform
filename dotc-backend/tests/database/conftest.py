import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from datetime import date
import random
from typing import cast, List

from app.database.orm_models import (
    Base,
    GameTable,
    PlayerTable,
    CardTable,
    SecretCardTable,
    PlayerInGameTable,
    PendingActionTable,
)

from app.domain.enums import (
    GameStatus,
    Avatar,
    CardLocation,
    CardType,
    PlayerRole,
    PlayCardActionType,
)


from app.database.commands import DatabaseCommandManager
from app.database.queries import DatabaseQueryManager

# =================================================================
# 💽 CONFIGURACIÓN Y FIXTURES BÁSICAS (Sin cambios)
# =================================================================

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def query_manager(db_session):
    return DatabaseQueryManager(db_session)


@pytest.fixture
def command_manager(db_session):
    queries = DatabaseQueryManager(
        db_session
    )  # o como se llame tu implementación de queries
    return DatabaseCommandManager(queries)


# =================================================================
# 🏭 FACTORIES BÁSICAS (Refactorizadas)
# =================================================================


@pytest.fixture
def player_factory(db_session, command_manager):
    """Factory para crear jugadores usando el comando create_player."""

    def _create_player(**kwargs):
        defaults = {
            "name": f"Player_{random.randint(1000, 9999)}",
            "birth_date": date(2000, 1, 1),
            "avatar": Avatar.DEFAULT,
        }
        defaults.update(kwargs)

        player_id = command_manager.create_player(**defaults)
        return db_session.get(PlayerTable, player_id)

    return _create_player


@pytest.fixture
def game_factory(db_session, command_manager, player_factory):
    """
    Factory para crear partidas.
    Si se le pasan argumentos extra como 'game_status', los aplica
    después de la creación inicial.
    """

    def _create_game(**kwargs):
        # 1. Separar los argumentos de creación de los de actualización
        create_args = {}
        update_args = {}

        if "host_id" not in kwargs:
            host = player_factory()
            kwargs["host_id"] = host.player_id

        # Argumentos válidos para el método create_game
        valid_create_keys = [
            "name",
            "min_players",
            "max_players",
            "host_id",
            "password",
        ]

        for key, value in kwargs.items():
            if key in valid_create_keys:
                create_args[key] = value
            else:
                update_args[key] = value

        # 2. Rellenar con valores por defecto si no se proveyeron
        if "name" not in create_args:
            create_args["name"] = f"Game_{random.randint(1000, 9999)}"
        if "min_players" not in create_args:
            create_args["min_players"] = 4
        if "max_players" not in create_args:
            create_args["max_players"] = 12

        # 3. Crear la partida con los argumentos básicos
        new_game_id = command_manager.create_game(**create_args)
        if new_game_id is None:
            # Si la creación falla, no podemos continuar
            return None

        # 4. Aplicar las actualizaciones adicionales si existen
        if "game_status" in update_args:
            command_manager.update_game_status(
                game_id=new_game_id, new_status=update_args["game_status"]
            )

        # (Aquí podrías añadir lógica para otros campos como 'current_player')
        if "current_player" in update_args:
            command_manager.set_current_turn(
                game_id=new_game_id, player_id=update_args["current_player"]
            )

        # 5. Devolver el objeto GameTable final y completo
        return db_session.get(GameTable, new_game_id)

    return _create_game


@pytest.fixture
def player_in_game_factory(db_session, game_factory, player_factory):
    """Factory para crear una asociación PlayerInGame."""

    def _create_player_in_game(**kwargs):
        if "game_id" not in kwargs:
            game = game_factory()
            kwargs["game_id"] = game.game_id
        if "player_id" not in kwargs:
            player = player_factory()
            kwargs["player_id"] = player.player_id

        iterable_roles = cast(List[PlayerRole], PlayerRole)
        defaults = {
            "player_role": random.choice(list(iterable_roles)),
            "social_disgrace": random.choice([True, False]),
        }
        defaults.update(kwargs)

        player_in_game_association = PlayerInGameTable(**defaults)
        db_session.add(player_in_game_association)
        db_session.commit()
        db_session.refresh(player_in_game_association)
        return player_in_game_association

    return _create_player_in_game


@pytest.fixture
def card_factory(db_session, game_factory, player_factory):
    """
    Factory fixture para crear instancias de CardTable para los tests.
    Crea una partida y un jugador por defecto si no se especifican.
    """

    def _factory(**kwargs):
        # Si no se provee un game_id, crea una partida por defecto.
        if "game_id" not in kwargs:
            game = game_factory()
            kwargs["game_id"] = game.game_id

        # Si no se provee un player_id, puede ser None (para cartas en mazo/descarte)
        # No es necesario crear uno por defecto aquí.

        # Valores por defecto para la carta en sí.
        if "card_type" not in kwargs:
            kwargs["card_type"] = CardType.HERCULE_POIROT
        if "location" not in kwargs:
            kwargs["location"] = CardLocation.DRAW_PILE

        # Creación y persistencia
        card = CardTable(**kwargs)
        db_session.add(card)
        db_session.commit()
        db_session.refresh(card)
        return card

    return _factory


@pytest.fixture
def card_domain_factory():
    """
    Factory para crear instancias del MODELO DE DOMINIO `Card`.
    No guarda nada en la base de datos.
    """

    def _create_domain_card(**kwargs):
        from app.domain.models import Card
        from app.domain.enums import CardType, CardLocation
        import random
        from typing import cast, List

        iterable_card_types = cast(List[CardType], CardType)

        defaults = {
            "card_id": random.randint(1, 1000),
            "game_id": random.randint(1, 1000),
            "card_type": random.choice(list(iterable_card_types)),
            "location": CardLocation.DRAW_PILE,
        }
        defaults.update(kwargs)
        return Card(**defaults)  # pyrefly: ignore

    return _create_domain_card


@pytest.fixture
def secret_card_factory(db_session, game_factory, player_factory):
    """
    Factory para crear un SecretCardTable (un secreto de un jugador en una partida).
    """

    def _create_secret_card(**kwargs):
        # Si no nos dan una partida o un jugador, los creamos
        if "game_id" not in kwargs:
            game = game_factory()
            kwargs["game_id"] = game.game_id

        if "player_id" not in kwargs:
            # Si ya hay un game_id, usamos el host de esa partida por defecto
            game_id = kwargs.get("game_id")
            game_obj = db_session.get(GameTable, game_id)
            kwargs["player_id"] = game_obj.host_id

        # Valores por defecto para un secreto
        defaults = {
            "role": PlayerRole.INNOCENT,
            "is_revealed": False,
        }
        defaults.update(kwargs)

        # Crear, guardar y devolver el objeto
        from app.database.orm_models import SecretCardTable

        secret = SecretCardTable(**defaults)
        db_session.add(secret)
        db_session.commit()
        db_session.refresh(secret)
        return secret

    return _create_secret_card


# =================================================================
# 🏛️ FIXTURES DE ESCENARIO (Refactorizadas)
# =================================================================


@pytest.fixture
def populated_game(command_manager, game_factory, player_factory, card_factory):
    """Crea un escenario de juego completo y realista para tests de queries."""
    # 1. Crear la partida (el host ya está asociado correctamente)
    game = game_factory(game_status=GameStatus.IN_PROGRESS, max_players=4)

    # 2. Añadir a los invitados usando el comando
    players = [game.players[0]]  # El host
    for i in range(3):
        player = player_factory()
        command_manager.add_player_to_game(
            player_id=player.player_id, game_id=game.game_id
        )
        players.append(player)

    # 3. Añadir cartas
    for player in players:
        card_factory(
            game_id=game.game_id,
            location=CardLocation.IN_HAND,
            player_id=player.player_id,
        )
        card_factory(
            game_id=game.game_id,
            location=CardLocation.IN_HAND,
            player_id=player.player_id,
        )
    for _ in range(10):
        card_factory(game_id=game.game_id, location=CardLocation.DRAW_PILE)
    for _ in range(5):
        card_factory(game_id=game.game_id, location=CardLocation.DISCARD_PILE)

    return game


# ... (lobby_scenario no necesita cambios) ...
@pytest.fixture
def lobby_scenario(game_factory):
    """Crea un escenario con múltiples partidas para probar el listado del lobby."""
    scen = {
        "lobby": [
            game_factory(name="Lobby Game 1", game_status=GameStatus.LOBBY),
            game_factory(name="Lobby Game 2", game_status=GameStatus.LOBBY),
        ],
        "in_progress": game_factory(
            game_name="In-Progress Game", game_status=GameStatus.IN_PROGRESS
        ),
        "finished": game_factory(
            game_name="Finished Game", game_status=GameStatus.FINISHED
        ),
    }
    return scen


@pytest.fixture
def create_secret_card(sess, secret_id=1, player_id=1, game_id=1):
    """Crea y guarda un SecretCardTable de prueba."""
    secret = SecretCardTable(
        secret_id=secret_id,
        player_id=player_id,
        game_id=game_id,
        role=PlayerRole.ACCOMPLICE,
        is_revealed=False,
    )
    sess.add(secret)
    sess.commit()
    return secret

@pytest.fixture
def pending_action_factory(db_session, game_factory, player_factory, card_factory):
    """
    Factory fixture para crear instancias de PendingActionTable para los tests.
    Crea sus propias dependencias si no se especifican.
    """

    def _factory(**kwargs):
        # 1. Asegurar una partida válida
        if "game_id" not in kwargs:
            game = game_factory()
            kwargs["game_id"] = game.game_id
        
        # 2. Asegurar un jugador iniciador válido
        if "player_id" not in kwargs:
            player = player_factory()
            # Es crucial que el jugador pertenezca a la partida
            db_session.add(PlayerInGameTable(game_id=kwargs["game_id"], player_id=player.player_id))
            db_session.commit()
            kwargs["player_id"] = player.player_id

        # <-- CAMBIO: Añadido para el nuevo campo -->
        # 3. Asegurar last_action_player_id (por defecto, el iniciador)
        if "last_action_player_id" not in kwargs:
            kwargs["last_action_player_id"] = kwargs["player_id"]
        # <-- FIN CAMBIO -->

        # 4. Asegurar un jugador objetivo válido
        if "target_player_id" not in kwargs:
             target_player = player_factory()
             db_session.add(PlayerInGameTable(game_id=kwargs["game_id"], player_id=target_player.player_id))
             db_session.commit()
             kwargs["target_player_id"] = target_player.player_id

        # 5. Asegurar cartas válidas
        if "cards" not in kwargs:
            card = card_factory(game_id=kwargs["game_id"])
            kwargs["cards"] = [card]

        # 6. Valores por defecto para el resto
        if "action_type" not in kwargs:
            kwargs["action_type"] = PlayCardActionType.PLAY_EVENT
        if "responses_count" not in kwargs:
            kwargs["responses_count"] = 0
        if "nsf_count" not in kwargs:
            kwargs["nsf_count"] = 0

        # --- Creación y persistencia ---
        pending_action = PendingActionTable(**kwargs)
        db_session.add(pending_action)
        db_session.commit()
        db_session.refresh(pending_action)
        return pending_action

    return _factory
