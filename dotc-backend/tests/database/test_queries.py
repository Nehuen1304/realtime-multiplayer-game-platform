import pytest
from unittest.mock import MagicMock
from sqlalchemy.exc import SQLAlchemyError

# Importa la clase que vamos a testear
from app.database.queries import DatabaseQueryManager
from app.database.orm_models import (
    PlayerInGameTable,
)

# Importa todos los modelos y enums necesarios para las aserciones
from app.domain.models import Game, PlayerInGame, Card, PlayerInfo, SecretCard, PendingAction
from app.domain.enums import GameStatus, CardLocation, PlayerRole, PlayCardActionType

# =================================================================
# ✅ TESTS PARA CASOS DE ÉXITO (HAPPY PATHS)
# =================================================================


class TestDatabaseQueryManagerSuccess:
    """Agrupa todos los tests que verifican el comportamiento correcto de las queries
    contra una base de datos real en memoria, poblada por las fixtures."""

    # --- Tests para Queries de Partidas ---

    def test_get_game(
        self, query_manager: DatabaseQueryManager, populated_game
    ):
        """
        Prueba que se obtiene un objeto de dominio 'Game' completo, con todas
        sus relaciones (jugadores, cartas, host) correctamente cargadas.
        """
        # Arrange
        game_id_to_find = populated_game.game_id

        # Act
        game_dto = query_manager.get_game(game_id=game_id_to_find)

        # Assert
        assert game_dto is not None
        assert isinstance(game_dto, Game)
        assert game_dto.id == game_id_to_find
        assert game_dto.name == populated_game.game_name
        assert game_dto.status == GameStatus.IN_PROGRESS
        assert len(game_dto.players) == 4
        assert game_dto.host is not None
        assert game_dto.host.player_id == populated_game.host_id
        assert all(isinstance(p, PlayerInGame) for p in game_dto.players)
        assert len(game_dto.deck) == 10
        assert len(game_dto.discard_pile) == 5
        total_cards_in_hands = sum(len(p.hand) for p in game_dto.players)
        assert total_cards_in_hands == 8

    def test_get_game_not_found(self, query_manager: DatabaseQueryManager):
        """Prueba que get_game devuelve None si la partida no existe."""
        # Arrange
        non_existent_id = 9999

        # Act
        game_dto = query_manager.get_game(game_id=non_existent_id)

        # Assert
        assert game_dto is None

    def test_list_games_in_lobby(
        self, query_manager: DatabaseQueryManager, lobby_scenario
    ):
        """
        Prueba que solo se listan las partidas que están en estado LOBBY,
        ignorando las que están en progreso o finalizadas.
        """
        # Arrange: La fixture 'lobby_scenario' crea el escenario.

        # Act
        games_in_lobby = query_manager.list_games_in_lobby()

        # Assert
        assert len(games_in_lobby) == 2
        lobby_game_ids = {g.id for g in games_in_lobby}
        expected_ids = {g.game_id for g in lobby_scenario["lobby"]}
        assert lobby_game_ids == expected_ids

    # --- Tests para Queries de Jugadores ---

    def test_get_player(
        self, query_manager: DatabaseQueryManager, player_factory
    ):
        """Prueba que se puede obtener la información de un jugador existente."""
        # Arrange
        player_orm = player_factory(name="TestPlayer")

        # Act
        player_dto = query_manager.get_player(player_id=player_orm.player_id)

        # Assert
        assert player_dto is not None
        assert isinstance(player_dto, PlayerInfo)
        assert player_dto.player_id == player_orm.player_id
        assert player_dto.player_name == "TestPlayer"

    def test_get_players_in_game(
        self, query_manager: DatabaseQueryManager, populated_game
    ):
        """Prueba que se obtienen todos los jugadores de una partida poblada."""
        # Arrange: La fixture 'populated_game' ya tiene 4 jugadores.

        # Act
        players_list = query_manager.get_players_in_game(
            game_id=populated_game.game_id
        )

        # Assert
        assert len(players_list) == 4
        assert all(isinstance(p, PlayerInGame) for p in players_list)

    def test_get_murderer_id(
        self, query_manager: DatabaseQueryManager, game_factory, player_in_game_factory
    ):
        """Prueba que se obtiene el ID correcto del jugador con rol de Asesino."""
        # Arrange
        game = game_factory()
        murderer_player = player_in_game_factory(game_id=game.game_id, player_role=PlayerRole.MURDERER)
        player_in_game_factory(game_id=game.game_id, player_role=PlayerRole.INNOCENT)
        expected_murderer_id = murderer_player.player_id

        # Act
        murderer_id = query_manager.get_murderer_id(game_id=game.game_id)

        # Assert
        assert murderer_id is not None
        assert murderer_id == expected_murderer_id

    def test_get_murderer_id_returns_none_if_no_murderer(
        self, query_manager: DatabaseQueryManager, game_factory, player_in_game_factory
    ):
        """Prueba que devuelve None si ningún jugador tiene el rol de Asesino."""
        # Arrange
        game = game_factory()
        # Creamos jugadores pero ninguno con el rol de Asesino
        player_in_game_factory(game_id=game.game_id, player_role=PlayerRole.INNOCENT)
        player_in_game_factory(game_id=game.game_id, player_role=PlayerRole.INNOCENT)

        # Act
        murderer_id = query_manager.get_murderer_id(game_id=game.game_id)

        # Assert
        assert murderer_id is None

    def test_get_accomplice_id(
        self, query_manager: DatabaseQueryManager, game_factory, player_in_game_factory
    ):
        """Prueba que se obtiene el ID correcto del jugador con rol de Cómplice."""
        # Arrange
        game = game_factory()
        accomplice = player_in_game_factory(game_id=game.game_id, player_role=PlayerRole.ACCOMPLICE)
        player_in_game_factory(game_id=game.game_id, player_role=PlayerRole.MURDERER)
        player_in_game_factory(game_id=game.game_id, player_role=PlayerRole.INNOCENT)

        # Act
        accomplice_id = query_manager.get_accomplice_id(game_id=game.game_id)

        # Assert
        assert accomplice_id is not None
        assert accomplice_id == accomplice.player_id

    def test_get_accomplice_id_returns_none_if_no_accomplice(
        self, query_manager: DatabaseQueryManager, populated_game
    ):
        """Prueba que devuelve None si ningún jugador tiene el rol de Cómplice."""
        # Arrange
        # La fixture 'populated_game' tiene 4 jugadores, por lo que no hay cómplice.

        # Act
        accomplice_id = query_manager.get_accomplice_id(game_id=populated_game.game_id)

        # Assert
        assert accomplice_id is None

    # --- Tests para Queries de Cartas ---

    def test_get_player_hand(
        self, query_manager: DatabaseQueryManager, populated_game
    ):
        """Prueba que se obtienen las cartas correctas de la mano de un jugador."""
        # Arrange
        a_player_id = populated_game.players[0].player_id

        # Act
        hand = query_manager.get_player_hand(
            game_id=populated_game.game_id, player_id=a_player_id
        )

        # Assert
        assert len(hand) == 2
        assert all(isinstance(c, Card) for c in hand)
        assert all(c.location == CardLocation.IN_HAND for c in hand)

    def test_get_size_deck_happy_path(
        self, query_manager: DatabaseQueryManager, populated_game
    ):
        """Prueba que se obtiene el tamaño correcto del mazo de robo."""
        # Arrange
        # populated_game tiene 10 cartas en el DRAW_PILE según el conftest

        # Act
        deck_size = query_manager.get_size_deck(game_id=populated_game.game_id)

        # Assert
        assert deck_size == 10

    def test_get_size_deck_when_empty(
        self, query_manager: DatabaseQueryManager, game_factory, card_factory
    ):
        """Prueba que devuelve 0 cuando el mazo de robo está vacío."""
        # Arrange
        game = game_factory()
        # Creamos cartas en otras ubicaciones pero no en DRAW_PILE
        card_factory(game_id=game.game_id, location=CardLocation.IN_HAND)
        card_factory(game_id=game.game_id, location=CardLocation.DISCARD_PILE)
        card_factory(game_id=game.game_id, location=CardLocation.PLAYED)

        # Act
        deck_size = query_manager.get_size_deck(game_id=game.game_id)

        # Assert
        assert deck_size == 0

    def test_get_size_deck_for_nonexistent_game(
        self, query_manager: DatabaseQueryManager
    ):
        """Prueba que devuelve 0 si la partida no existe."""
        # Arrange
        non_existent_game_id = 9999

        # Act
        deck_size = query_manager.get_size_deck(game_id=non_existent_game_id)

        # Assert
        assert deck_size == 0

    def test_get_set_happy_path(
        self, query_manager: DatabaseQueryManager, game_factory, card_factory
    ):
        """Prueba que se obtienen las cartas correctas de un set específico."""
        # Arrange
        game = game_factory()
        set_id_to_find = 1

        # Creamos 3 cartas que pertenecen al set y 2 que no.
        card_factory(game_id=game.game_id, set_id=set_id_to_find)
        card_factory(game_id=game.game_id, set_id=set_id_to_find)
        card_factory(game_id=game.game_id, set_id=set_id_to_find)
        card_factory(game_id=game.game_id, set_id=2)  # Otro set
        card_factory(game_id=game.game_id, set_id=None)  # Sin set

        # Act
        set_cards = query_manager.get_set(
            set_id=set_id_to_find, game_id=game.game_id
        )

        # Assert
        assert len(set_cards) == 3
        assert all(isinstance(c, Card) for c in set_cards)
        assert all(c.set_id == set_id_to_find for c in set_cards)

    def test_get_set_when_set_does_not_exist(
        self, query_manager: DatabaseQueryManager, game_factory, card_factory
    ):
        """Prueba que devuelve una lista vacía si el set_id no existe en la partida."""
        # Arrange
        game = game_factory()
        # Creamos cartas, pero ninguna con el set_id que vamos a buscar.
        card_factory(game_id=game.game_id, set_id=1)
        card_factory(game_id=game.game_id, set_id=2)

        # Act
        set_cards = query_manager.get_set(set_id=99, game_id=game.game_id)

        # Assert
        assert set_cards == []

    def test_get_set_for_nonexistent_game(
        self, query_manager: DatabaseQueryManager
    ):
        """Prueba que devuelve una lista vacía si la partida no existe."""
        # Arrange
        non_existent_game_id = 9999

        # Act
        set_cards = query_manager.get_set(
            set_id=1, game_id=non_existent_game_id
        )

        # Assert
        assert set_cards == []

    def test_get_secret_happy_path(
        self,
        query_manager: DatabaseQueryManager,
        game_factory,
        player_factory,
        secret_card_factory,
    ):
        """Prueba que se puede obtener una carta secreta específica por su ID."""
        # Arrange
        game = game_factory()
        player = player_factory()
        secret_orm = secret_card_factory(
            game_id=game.game_id,
            player_id=player.player_id,
            role=PlayerRole.MURDERER,
        )

        # Act
        secret_dto = query_manager.get_secret(
            secret_id=secret_orm.secret_id, game_id=game.game_id
        )

        # Assert
        assert secret_dto is not None
        assert isinstance(secret_dto, SecretCard)
        assert secret_dto.secret_id == secret_orm.secret_id
        assert secret_dto.game_id == game.game_id
        assert secret_dto.player_id == player.player_id
        assert secret_dto.role == PlayerRole.MURDERER
        assert secret_dto.is_revealed is False

    def test_get_secret_not_found(
        self, query_manager: DatabaseQueryManager, game_factory
    ):
        """Prueba que get_secret devuelve None si el secreto no existe."""
        # Arrange
        game = game_factory()
        non_existent_secret_id = 9999

        # Act
        secret_dto = query_manager.get_secret(
            secret_id=non_existent_secret_id, game_id=game.game_id
        )

        # Assert
        assert secret_dto is None

    def test_get_secret_from_another_game(
        self,
        query_manager: DatabaseQueryManager,
        game_factory,
        player_factory,
        secret_card_factory,
    ):
        """Prueba que get_secret devuelve None si el secreto pertenece a otra partida."""
        # Arrange
        game1 = game_factory()
        game2 = game_factory()
        player = player_factory()
        secret_orm_game1 = secret_card_factory(
            game_id=game1.game_id, player_id=player.player_id
        )

        # Act: Intentamos buscar el secreto de game1 en game2
        secret_dto = query_manager.get_secret(
            secret_id=secret_orm_game1.secret_id, game_id=game2.game_id
        )

        # Assert
        assert secret_dto is None

    # --- Tests para Queries de Numeros ---

    def test_get_max_set_id_happy_path(
        self, query_manager: DatabaseQueryManager, game_factory, card_factory
    ):
        """Prueba que se obtiene el set_id más alto de una partida específica."""
        # Arrange
        game1 = game_factory()
        game2 = game_factory()

        # Creamos cartas en diferentes partidas, con y sin set_id
        card_factory(game_id=game1.game_id, set_id=1)
        card_factory(game_id=game1.game_id, set_id=3)  # <- El máximo para game1
        card_factory(game_id=game2.game_id, set_id=5)  # <- El máximo para game2
        card_factory(game_id=game2.game_id, set_id=2)
        card_factory(
            game_id=game1.game_id, set_id=None
        )  # Esta debe ser ignorada

        # Act
        max_set_id_game1 = query_manager.get_max_set_id(game_id=game1.game_id)
        max_set_id_game2 = query_manager.get_max_set_id(game_id=game2.game_id)

        # Assert
        assert max_set_id_game1 == 3
        assert max_set_id_game2 == 5

    def test_get_max_set_id_when_none_exist(
        self, query_manager: DatabaseQueryManager, game_factory, card_factory
    ):
        """Prueba que devuelve None si ninguna carta en la partida tiene un set_id."""
        # Arrange
        game = game_factory()
        card_factory(game_id=game.game_id, set_id=None)
        card_factory(game_id=game.game_id, set_id=None)

        # Act
        max_set_id = query_manager.get_max_set_id(game_id=game.game_id)

        # Assert
        assert max_set_id is None

    def test_get_max_set_id_with_empty_table(
        self, query_manager: DatabaseQueryManager, game_factory
    ):
        """Prueba que devuelve None si la partida no tiene cartas."""
        # Arrange: Se crea una partida, pero sin cartas.
        game = game_factory()

        # Act
        max_set_id = query_manager.get_max_set_id(game_id=game.game_id)

        # Assert
        assert max_set_id is None

    # --- Tests para Queries de Validación ---

    def test_is_player_in_game(
        self,
        query_manager: DatabaseQueryManager,
        populated_game,
        player_factory,
    ):
        """Prueba la verificación de pertenencia de un jugador a una partida."""
        # Arrange
        game = populated_game
        host_id = game.host_id
        stranger_id = player_factory().player_id

        # Act & Assert
        assert (
            query_manager.is_player_in_game(
                game_id=game.game_id, player_id=host_id
            )
            is True
        )
        assert (
            query_manager.is_player_in_game(
                game_id=game.game_id, player_id=stranger_id
            )
            is False
        )
        assert (
            query_manager.is_player_in_game(game_id=9999, player_id=host_id)
            is False
        )

    def test_is_player_host(
        self,
        query_manager: DatabaseQueryManager,
        populated_game,
        player_factory,
    ):
        """Prueba la verificación de si un jugador es el host."""
        # Arrange
        game = populated_game
        host_id = game.host_id
        guest_id = game.players[1].player_id
        stranger_id = player_factory().player_id

        # Act & Assert
        assert (
            query_manager.is_player_host(
                game_id=game.game_id, player_id=host_id
            )
            is True
        )
        assert (
            query_manager.is_player_host(
                game_id=game.game_id, player_id=guest_id
            )
            is False
        )
        assert (
            query_manager.is_player_host(
                game_id=game.game_id, player_id=stranger_id
            )
            is False
        )

    def test_game_name_exists(
        self, query_manager: DatabaseQueryManager, game_factory
    ):
        """Prueba la verificación de existencia de un nombre de partida."""
        # Arrange
        game_factory(name="PartidaExistente")

        # Act & Assert
        assert (
            query_manager.game_name_exists(game_name="PartidaExistente") is True
        )
        assert (
            query_manager.game_name_exists(game_name="PartidaInexistente")
            is False
        )

    # --- Tests para Queries de Acciones Pendientes ---

def test_get_pending_action_happy_path(query_manager: DatabaseQueryManager, pending_action_factory, game_factory, player_factory, card_factory, db_session):
    """Prueba que se obtiene una acción pendiente existente con sus cartas."""
    # Arrange
    game = game_factory()
    player = player_factory()
    # Aseguramos que el jugador pertenece a la partida
    db_session.add(PlayerInGameTable(game_id=game.game_id, player_id=player.player_id))
    db_session.commit()

    card1 = card_factory(game_id=game.game_id)
    card2 = card_factory(game_id=game.game_id)
    
    # Creamos un jugador objetivo válido para usar en el test
    target_player = player_factory()
    db_session.add(PlayerInGameTable(game_id=game.game_id, player_id=target_player.player_id))
    db_session.commit()

    # Creamos la acción, ahora pasando un target_player_id que SÍ existe.
    action = pending_action_factory(
        game_id=game.game_id,
        player_id=player.player_id,
        action_type=PlayCardActionType.PLAY_EVENT,
        cards=[card1, card2],
        target_player_id=target_player.player_id,  # <-- Usamos el ID válido
        last_action_player_id=player.player_id # <-- Se setea por defecto, pero lo hacemos explícito
    )
    db_session.flush()

    # Act
    pending_action_dto = query_manager.get_pending_action(game_id=action.game_id)

    # Assert
    assert pending_action_dto is not None
    assert isinstance(pending_action_dto, PendingAction)
    assert pending_action_dto.game_id == action.game_id
    assert pending_action_dto.player_id == action.player_id
    assert pending_action_dto.last_action_player_id == player.player_id # <-- CAMBIO: Verificar nuevo campo
    assert pending_action_dto.action_type == PlayCardActionType.PLAY_EVENT
    assert pending_action_dto.target_player_id == target_player.player_id # Verificamos contra el ID válido
    assert len(pending_action_dto.cards) == 2
    assert {c.card_id for c in pending_action_dto.cards} == {card1.card_id, card2.card_id}
    assert isinstance(pending_action_dto.cards[0], Card)

# =================================================================
# ❌ TESTS PARA MANEJO DE EXCEPCIONES
# =================================================================


@pytest.fixture
def mock_session_with_exceptions() -> MagicMock:
    """
    Fixture que crea un mock de la sesión de SQLAlchemy configurado para lanzar errores.
    Esto nos permite probar los bloques 'except' de nuestro código.
    """
    # Arrange
    session = MagicMock()
    error = SQLAlchemyError("Simulated Database Error")
    session.execute.side_effect = error
    session.query.side_effect = error

    # Mock para la cadena de llamadas .exists().scalar() que usan algunas queries
    mock_exists_chain = MagicMock()
    mock_exists_chain.scalar.side_effect = error
    session.query.return_value.exists.return_value = mock_exists_chain

    return session


@pytest.fixture
def query_manager_with_exceptions(
    mock_session_with_exceptions: MagicMock,
) -> DatabaseQueryManager:
    """Fixture que inyecta la sesión que lanza errores en el Query Manager."""
    # Arrange
    return DatabaseQueryManager(session=mock_session_with_exceptions)


class TestDatabaseQueryManagerExceptions:
    """Agrupa todos los tests que verifican el manejo robusto de excepciones de la base de datos."""

    def test_all_methods_handle_exceptions_gracefully(
        self,
        query_manager_with_exceptions: DatabaseQueryManager,
        mock_session_with_exceptions: MagicMock,
    ):
        """
        Prueba que todos los métodos del query manager capturan excepciones,
        hacen rollback y devuelven un valor seguro por defecto.
        """
        # Act & Assert

        # Métodos que deben devolver None en caso de error
        assert query_manager_with_exceptions.get_game(game_id=1) is None
        assert query_manager_with_exceptions.get_game_status(game_id=1) is None
        assert query_manager_with_exceptions.get_current_turn(game_id=1) is None
        assert query_manager_with_exceptions.get_player(player_id=1) is None
        assert (
            query_manager_with_exceptions.get_player_role(
                player_id=1, game_id=1
            )
            is None
        )
        assert (
            query_manager_with_exceptions.get_card(card_id=1, game_id=1) is None
        )
        assert query_manager_with_exceptions.get_max_set_id(game_id=1) is None
        assert (
            query_manager_with_exceptions.get_secret(secret_id=1, game_id=1)
            is None
        )
        assert query_manager_with_exceptions.get_murderer_id(game_id=1) is None
        assert query_manager_with_exceptions.get_accomplice_id(game_id=1) is None
        assert query_manager_with_exceptions.get_pending_action(game_id=1) is None

        # Métodos que deben devolver una lista vacía [] en caso de error
        assert query_manager_with_exceptions.list_games_in_lobby() == []
        assert (
            query_manager_with_exceptions.get_players_in_game(game_id=1) == []
        )
        assert (
            query_manager_with_exceptions.get_player_hand(
                game_id=1, player_id=1
            )
            == []
        )
        assert query_manager_with_exceptions.get_deck(game_id=1) == []
        assert query_manager_with_exceptions.get_discard_pile(game_id=1) == []
        assert (
            query_manager_with_exceptions.get_player_secrets(
                game_id=1, player_id=1
            )
            == []
        )
        assert query_manager_with_exceptions.get_set(set_id=1, game_id=1) == []

        # Métodos que deben devolver un booleano seguro en caso de error
        assert (
            query_manager_with_exceptions.is_player_in_game(
                game_id=1, player_id=1
            )
            is False
        )
        assert (
            query_manager_with_exceptions.is_player_host(game_id=1, player_id=1)
            is False
        )
        assert (
            query_manager_with_exceptions.game_name_exists(game_name="any")
            is True
        )  # Consistente con tu implementación

        # Verificación final: el rollback debe haber sido llamado por cada método
        assert mock_session_with_exceptions.rollback.call_count == 21
        