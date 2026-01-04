import pytest
from unittest.mock import AsyncMock, Mock
from typing import Optional, List

# Importar la clase a testear y su clase base
from app.game.effects.event_effects import (
    AnotherVictimEffect,
    BaseCardEffect,
    CardTradeEffect,
    LookIntoTheAshesEffect,
    CardsOffTheTableEffect,
    AndThenThereWasOneMoreEffect,
    DelayTheMurdererEscapeEffect,
    EarlyTrainToPaddingtonEffect,
)

# Importar dependencias necesarias para mocks y datos de prueba
from app.database.interfaces import IQueryManager, ICommandManager
from app.game.helpers.notificators import Notificator
from app.game.effect_executor import EffectExecutor
from app.domain.models import Card, SecretCard
from app.domain.enums import (
    CardType,
    CardLocation,
    ResponseStatus,
    GameActionState,
    PlayerRole,
    GameFlowStatus,
)
from app.game.exceptions import (
    InvalidAction,
    ResourceNotFound,
    InternalGameError,
)


# =================================================================
# --- Fixtures Específicas para este Módulo de Tests ---
# =================================================================


@pytest.fixture
def mock_queries() -> Mock:
    """Crea un mock para el IQueryManager."""
    return Mock(spec=IQueryManager)


@pytest.fixture
def mock_commands() -> Mock:
    """Crea un mock para el ICommandManager."""
    return Mock(spec=ICommandManager)


@pytest.fixture
def mock_notificator() -> AsyncMock:
    """Crea un mock para el Notificator."""
    return AsyncMock(spec=Notificator)


@pytest.fixture
def look_into_the_ashes_effect(
    mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
) -> LookIntoTheAshesEffect:
    """Crea una instancia del efecto con sus dependencias mockeadas."""
    return LookIntoTheAshesEffect(
        queries=mock_queries, commands=mock_commands, notifier=mock_notificator
    )


@pytest.fixture
def card_domain_factory():
    """Factory para crear objetos de dominio Card para los tests."""

    def _create_card(card_id: int, position: Optional[int]):
        return Card(
            card_id=card_id,
            game_id=1,
            card_type=CardType.DEAD_CARD_FOLLY,  # El tipo no importa para esta lógica
            location=CardLocation.DISCARD_PILE,
            position=position,
        )

    return _create_card

@pytest.fixture
def card_trade_effect(
    mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
) -> CardTradeEffect:
    """Crea una instancia del efecto con sus dependencias mockeadas."""
    return CardTradeEffect(
        queries=mock_queries, commands=mock_commands, notifier=mock_notificator
    )


@pytest.fixture
def card_domain_factory_hand():
    """Factory para crear objetos de dominio Card para los tests."""

    def _create_card(
        card_id: int,
        card_type: CardType,
        location: CardLocation,
        player_id: Optional[int] = None,
    ):
        return Card(
            card_id=card_id,
            game_id=1,
            card_type=card_type,
            location=location,
            player_id=player_id,
        )

    return _create_card


# =================================================================
# --- Tests para el Efecto 'LookIntoTheAshesEffect' ---
# =================================================================


class TestLookIntoTheAshesEffect:
    @pytest.mark.asyncio
    async def test_execute_sends_last_5_cards_when_more_are_available(
        self,
        look_into_the_ashes_effect: LookIntoTheAshesEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory,
    ):
        """
        Prueba el 'happy path': si hay más de 5 cartas en el descarte,
        el efecto debe seleccionar las últimas 5 basándose en su 'position'
        y notificarlas al jugador.
        """
        # --- Arrange ---
        game_id = 101
        player_id = 1
        # Creamos 7 cartas en el descarte con posiciones claras
        discard_pile_cards = [
            card_domain_factory(card_id=i, position=i) for i in range(1, 8)
        ]
        mock_queries.get_discard_pile.return_value = discard_pile_cards

        # Las 5 cartas que esperamos que se seleccionen (las de mayor posición)
        expected_cards_to_send = discard_pile_cards[
            2:
        ]  # De la carta con pos 3 a la 7

        # --- Act ---
        result = await look_into_the_ashes_effect.execute(
            game_id=game_id,
            player_id=player_id,
            card_ids=[999],  # ID de la carta "Look into the ashes"
            target_player_id=player_id,  # El jugador que elige es el mismo que la jugó
        )

        # --- Assert ---
        # 1. Verificar que el juego se "congela" esperando la acción del jugador
        mock_commands.set_game_action_state.assert_called_once_with(
            game_id=game_id,
            state=GameActionState.AWAITING_SELECTION_FOR_CARD,
            prompted_player_id=player_id,
            initiator_id=player_id,
        )

        # 2. Verificar que se notificó al jugador correcto con las cartas correctas
        mock_notificator.notify_player_to_choose_card.assert_awaited_once_with(
            game_id=game_id, player_id=player_id, cards=expected_cards_to_send
        )

        # 3. Verificar que el resultado PAUSA el flujo
        assert result == GameFlowStatus.PAUSED

    @pytest.mark.asyncio
    async def test_execute_sends_all_cards_when_fewer_than_5(
        self,
        look_into_the_ashes_effect: LookIntoTheAshesEffect,
        mock_queries: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory,
    ):
        """
        Prueba que si hay menos de 5 cartas en el descarte,
        el efecto las envía todas.
        """
        # --- Arrange ---
        game_id = 102
        player_id = 2
        # Creamos solo 3 cartas en el descarte
        discard_pile_cards = [
            card_domain_factory(card_id=i, position=i) for i in range(1, 4)
        ]
        mock_queries.get_discard_pile.return_value = discard_pile_cards

        # --- Act ---
        await look_into_the_ashes_effect.execute(
            game_id=game_id,
            player_id=player_id,
            card_ids=[998],
            target_player_id=player_id,
        )

        # --- Assert ---
        # Verificar que se notificó al jugador con todas las cartas disponibles
        mock_notificator.notify_player_to_choose_card.assert_awaited_once_with(
            game_id=game_id,
            player_id=player_id,
            cards=discard_pile_cards,  # Deberían ser todas las 3 cartas
        )

    @pytest.mark.asyncio
    async def test_execute_handles_empty_discard_pile(
        self,
        look_into_the_ashes_effect: LookIntoTheAshesEffect,
        mock_queries: Mock,
        mock_notificator: AsyncMock,
    ):
        """
        Prueba que el efecto no falla si la pila de descarte está vacía.
        Debería notificar al jugador con una lista vacía de cartas.
        """
        # --- Arrange ---
        game_id = 103
        player_id = 3
        mock_queries.get_discard_pile.return_value = []

        # --- Act ---
        await look_into_the_ashes_effect.execute(
            game_id=game_id,
            player_id=player_id,
            card_ids=[997],
            target_player_id=player_id,
        )

        # --- Assert ---
        # Verificar que se notifica con una lista vacía
        mock_notificator.notify_player_to_choose_card.assert_awaited_once_with(
            game_id=game_id, player_id=player_id, cards=[]
        )

    @pytest.mark.asyncio
    async def test_execute_sorts_cards_correctly_with_none_positions(
        self,
        look_into_the_ashes_effect: LookIntoTheAshesEffect,
        mock_queries: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory,
    ):
        """
        Prueba que la lógica de ordenación maneja correctamente las cartas
        que puedan tener 'position=None', considerándolas como las más antiguas.
        """
        # --- Arrange ---
        game_id = 104
        player_id = 4
        # Creamos una lista desordenada con posiciones None
        card_pos_2 = card_domain_factory(card_id=2, position=2)
        card_pos_none_1 = card_domain_factory(card_id=3, position=None)
        card_pos_1 = card_domain_factory(card_id=1, position=1)
        card_pos_3 = card_domain_factory(card_id=4, position=3)
        card_pos_none_2 = card_domain_factory(card_id=5, position=None)

        # La lista que el mock devolverá
        discard_pile_cards = [
            card_pos_2,
            card_pos_none_1,
            card_pos_1,
            card_pos_3,
            card_pos_none_2,
        ]
        mock_queries.get_discard_pile.return_value = discard_pile_cards

        # El orden esperado después de la clasificación: [None, None, 1, 2, 3]
        expected_sorted_cards = [
            card_pos_none_1,
            card_pos_none_2,
            card_pos_1,
            card_pos_2,
            card_pos_3,
        ]

        # --- Act ---
        await look_into_the_ashes_effect.execute(
            game_id=game_id,
            player_id=player_id,
            card_ids=[996],
            target_player_id=player_id,
        )

        # --- Assert ---
        # Verificar que las cartas enviadas en la notificación están en el orden correcto
        mock_notificator.notify_player_to_choose_card.assert_awaited_once_with(
            game_id=game_id, player_id=player_id, cards=expected_sorted_cards
        )


# =================================================================
# --- Tests para el Efecto 'AnotherVictimEffect' ---
# =================================================================


@pytest.fixture
def mock_executor() -> AsyncMock:
    """Crea un mock para el EffectExecutor."""
    return AsyncMock(spec=EffectExecutor)


@pytest.fixture
def another_victim_effect(
    mock_queries: Mock,
    mock_commands: Mock,
    mock_notificator: AsyncMock,
    mock_executor: AsyncMock,
) -> AnotherVictimEffect:
    """Crea una instancia del efecto con todas sus dependencias mockeadas."""
    return AnotherVictimEffect(
        queries=mock_queries,
        commands=mock_commands,
        notifier=mock_notificator,
        executor=mock_executor,
    )


class TestAnotherVictimEffect:
    @pytest.mark.asyncio
    async def test_execute_happy_path(
        self,
        another_victim_effect: AnotherVictimEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        mock_executor: AsyncMock,
    ):
        """
        Prueba el flujo completo y exitoso: roba un set y re-ejecuta su efecto.
        """
        # --- Arrange ---
        game_id = 101
        thief_id = 1  # El jugador que juega "Another Victim"
        victim_id = 2
        set_to_steal_id = 5

        # Creamos las cartas del set que será robado
        stolen_set_cards = [
            Card(
                card_id=10,
                game_id=game_id,
                card_type=CardType.HERCULE_POIROT,
                location=CardLocation.PLAYED,
                player_id=victim_id,
                set_id=set_to_steal_id,
            ),
            Card(
                card_id=11,
                game_id=game_id,
                card_type=CardType.HERCULE_POIROT,
                location=CardLocation.PLAYED,
                player_id=victim_id,
                set_id=set_to_steal_id,
            ),
        ]

        # Configuramos los mocks
        mock_queries.get_set.return_value = stolen_set_cards
        mock_executor.execute_effect.return_value = GameFlowStatus.CONTINUE

        # --- Act ---
        result = await another_victim_effect.execute(
            game_id=game_id,
            player_id=thief_id,
            card_ids=[999],  # ID de la carta "Another Victim"
            target_set_id=set_to_steal_id,
            target_player_id=3,  # Target para el efecto del set robado
        )

        # --- Assert ---
        # 1. Verificar que se buscó el set correcto
        mock_queries.get_set.assert_called_once_with(
            set_id=set_to_steal_id, game_id=game_id
        )

        # 2. Verificar que se ordenó el robo del set
        mock_commands.steal_set.assert_called_once_with(
            set_id=set_to_steal_id, new_owner_id=thief_id, game_id=game_id
        )

        # 3. Verificar que se notificó el robo
        mock_notificator.notify_set_stolen.assert_awaited_once_with(
            game_id=game_id,
            thief_id=thief_id,
            victim_id=victim_id,
            set_id=set_to_steal_id,
            set_cards=stolen_set_cards,
        )

        # 4. Verificar que se re-ejecutó el efecto del set robado
        mock_executor.execute_effect.assert_awaited_once_with(
            game_id=game_id,
            played_cards=stolen_set_cards,
            player_id=thief_id,
            target_player_id=3,
            target_secret_id=None,
            target_set_id=None,
            target_card_id=None,
        )

        # 5. Verificar que el resultado final es CONTINUE
        assert result == GameFlowStatus.CONTINUE

    @pytest.mark.asyncio
    async def test_execute_fails_if_no_target_set_id(
        self,
        another_victim_effect: AnotherVictimEffect,
    ):
        """
        Prueba que la ejecución falla si no se provee un 'target_set_id'.
        """
        # --- Arrange ---
        # No se necesita configurar mocks, ya que debe fallar antes

        # --- Act & Assert ---
        with pytest.raises(
            InvalidAction, match="No se proporcionó un ID de set objetivo."
        ):
            await another_victim_effect.execute(
                game_id=1,
                player_id=1,
                card_ids=[999],
                target_set_id=None,  # Causa del error
            )

    @pytest.mark.asyncio
    async def test_execute_fails_if_set_not_found(
        self,
        another_victim_effect: AnotherVictimEffect,
        mock_queries: Mock,
    ):
        """
        Prueba que falla si target_set_id no corresponde a un set existente.
        """
        # --- Arrange ---
        mock_queries.get_set.return_value = []  # La DB no encuentra el set

        # --- Act & Assert ---
        with pytest.raises(
            ResourceNotFound,
            match="No se encontró un set con el ID especificado.",
        ):
            await another_victim_effect.execute(
                game_id=1,
                player_id=1,
                card_ids=[999],
                target_set_id=99,
            )

    @pytest.mark.asyncio
    async def test_execute_fails_if_set_has_no_owner(
        self,
        another_victim_effect: AnotherVictimEffect,
        mock_queries: Mock,
    ):
        """
        Prueba que falla si las cartas del set no tienen un propietario único.
        """
        # --- Arrange ---
        stolen_set_cards = [
            Card(
                card_id=10,
                game_id=1,
                card_type=CardType.HERCULE_POIROT,
                location=CardLocation.PLAYED,
                player_id=None,
                set_id=5,
            ),
        ]
        mock_queries.get_set.return_value = stolen_set_cards

        # --- Act & Assert ---
        with pytest.raises(
            InternalGameError,
            match="El set está corrupto o no tiene un propietario único.",
        ):
            await another_victim_effect.execute(
                game_id=1,
                player_id=1,
                card_ids=[999],
                target_set_id=5,
            )

    @pytest.mark.asyncio
    async def test_execute_fails_if_reexecuting_effect_fails(
        self,
        another_victim_effect: AnotherVictimEffect,
        mock_queries: Mock,
        mock_executor: AsyncMock,
    ):
        """
        Prueba que el efecto completo falla si el efecto del set robado falla.
        """
        # --- Arrange ---
        stolen_set_cards = [
            Card(
                card_id=10,
                game_id=1,
                card_type=CardType.HERCULE_POIROT,
                location=CardLocation.PLAYED,
                player_id=2,
                set_id=5,
            ),
        ]
        mock_queries.get_set.return_value = stolen_set_cards
        # Simulamos que la re-ejecución del efecto devuelve un error
        mock_executor.execute_effect.return_value = ResponseStatus.ERROR

        # --- Act ---
        result = await another_victim_effect.execute(
            game_id=1,
            player_id=1,
            card_ids=[999],
            target_set_id=5,
        )
        # --- Assert ---
        assert result == ResponseStatus.ERROR  # The error from re-execution is propagated


# =================================================================
# --- Tests para el Efecto 'CardsOffTheTableEffect' ---
# =================================================================


@pytest.fixture
def cards_off_the_table_effect(
    mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
) -> CardsOffTheTableEffect:
    """Crea una instancia del efecto con sus dependencias mockeadas."""
    return CardsOffTheTableEffect(
        queries=mock_queries, commands=mock_commands, notifier=mock_notificator
    )


class TestCardsOffTheTableEffect:
    @pytest.mark.asyncio
    async def test_execute_discards_nsf_cards_from_target(
        self,
        cards_off_the_table_effect: CardsOffTheTableEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory,
    ):
        """
        Prueba el happy path: el target tiene cartas 'Not So Fast' y son descartadas.
        """
        # --- Arrange ---
        game_id = 201
        source_player_id = 1
        target_player_id = 2

        # Creamos la mano del jugador objetivo con varias cartas
        nsf_card1 = Card(
            card_id=10,
            game_id=game_id,
            card_type=CardType.NOT_SO_FAST,
            location=CardLocation.IN_HAND,
            player_id=target_player_id,
            set_id=None,
        )
        nsf_card2 = Card(
            card_id=11,
            game_id=game_id,
            card_type=CardType.NOT_SO_FAST,
            location=CardLocation.IN_HAND,
            player_id=target_player_id,
            set_id=None,
        )
        other_card = Card(
            card_id=12,
            game_id=game_id,
            card_type=CardType.HARLEY_QUIN,
            location=CardLocation.IN_HAND,
            player_id=target_player_id,
            set_id=None,
        )
        target_hand = [nsf_card1, other_card, nsf_card2]

        mock_queries.get_player_hand.return_value = target_hand
        mock_commands.update_card_location.return_value = ResponseStatus.OK

        cards_to_discard = [nsf_card1, nsf_card2]

        # --- Act ---
        result = await cards_off_the_table_effect.execute(
            game_id=game_id,
            player_id=source_player_id,
            card_ids=[999],
            target_player_id=target_player_id,
        )

        # --- Assert ---
        # 1. Verificar que se pidió la mano del target
        mock_queries.get_player_hand.assert_called_once_with(
            player_id=target_player_id, game_id=game_id
        )

        # 2. Verificar que se llamó a descartar para cada carta NSF
        assert mock_commands.update_card_location.call_count == 2

        # 3. Verificar que se notificó correctamente
        mock_notificator.notify_cards_NSF_discarded.assert_awaited_once_with(
            game_id=game_id,
            source_player_id=source_player_id,
            target_player_id=target_player_id,
            discarded_cards=cards_to_discard,
        )

        # 4. Verificar que el resultado es OK
        assert result == GameFlowStatus.CONTINUE

    @pytest.mark.asyncio
    async def test_execute_handles_target_with_no_nsf_cards(
        self,
        cards_off_the_table_effect: CardsOffTheTableEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory,
    ):
        """
        Prueba que el efecto se ejecuta sin errores si el target no tiene cartas 'Not So Fast'.
        """
        # --- Arrange ---
        game_id = 202
        source_player_id = 1
        target_player_id = 2

        # La mano del target no tiene cartas NSF
        target_hand = [
            Card(
                card_id=10,
                game_id=game_id,
                card_type=CardType.HERCULE_POIROT,
                location=CardLocation.IN_HAND,
                player_id=target_player_id,
                set_id=None,
            ),
            Card(
                card_id=11,
                game_id=game_id,
                card_type=CardType.HARLEY_QUIN,
                location=CardLocation.IN_HAND,
                player_id=target_player_id,
                set_id=None,
            ),
        ]
        mock_queries.get_player_hand.return_value = target_hand

        # --- Act ---
        result = await cards_off_the_table_effect.execute(
            game_id=game_id,
            player_id=source_player_id,
            card_ids=[999],
            target_player_id=target_player_id,
        )

        # --- Assert ---
        # 1. No se debe llamar a descartar ninguna carta
        mock_commands.update_card_location.assert_not_called()

        # 2. Se debe notificar con una lista vacía de cartas descartadas
        mock_notificator.notify_cards_NSF_discarded.assert_awaited_once_with(
            game_id=game_id,
            source_player_id=source_player_id,
            target_player_id=target_player_id,
            discarded_cards=[],
        )

        # 3. El resultado debe ser OK
        assert result == GameFlowStatus.CONTINUE

    @pytest.mark.asyncio
    async def test_execute_handles_target_with_empty_hand(
        self,
        cards_off_the_table_effect: CardsOffTheTableEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
    ):
        """
        Prueba que el efecto se ejecuta sin errores si la mano del target está vacía.
        """
        # --- Arrange ---
        game_id = 203
        source_player_id = 1
        target_player_id = 2
        mock_queries.get_player_hand.return_value = []

        # --- Act ---
        result = await cards_off_the_table_effect.execute(
            game_id=game_id,
            player_id=source_player_id,
            card_ids=[999],
            target_player_id=target_player_id,
        )

        # --- Assert ---
        mock_commands.update_card_location.assert_not_called()
        mock_notificator.notify_cards_NSF_discarded.assert_awaited_once_with(
            game_id=game_id,
            source_player_id=source_player_id,
            target_player_id=target_player_id,
            discarded_cards=[],
        )
        assert result == GameFlowStatus.CONTINUE

    @pytest.mark.asyncio
    async def test_execute_fails_if_no_target_player_id(
        self,
        cards_off_the_table_effect: CardsOffTheTableEffect,
    ):
        """
        Prueba que la ejecución falla si no se provee un 'target_player_id'.
        """
        # --- Act & Assert ---
        with pytest.raises(
            InvalidAction, match="No se proporcionó un ID de jugador objetivo."
        ):
            await cards_off_the_table_effect.execute(
                game_id=1,
                player_id=1,
                card_ids=[999],
                target_player_id=None,  # Causa del error
            )


# =================================================================
# --- Tests para el Efecto 'AndThenThereWasOneMoreEffect' ---
# =================================================================


@pytest.fixture
def and_then_there_was_one_more_effect(
    mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
) -> AndThenThereWasOneMoreEffect:
    """Crea una instancia del efecto con sus dependencias mockeadas."""
    return AndThenThereWasOneMoreEffect(
        queries=mock_queries, commands=mock_commands, notifier=mock_notificator
    )


class TestAndThenThereWasOneMoreEffect:
    @pytest.mark.asyncio
    async def test_execute_happy_path(
        self,
        and_then_there_was_one_more_effect: AndThenThereWasOneMoreEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
    ):
        """
        Prueba el flujo exitoso: un secreto revelado es ocultado y transferido
        a un nuevo propietario, notificando ambas acciones.
        """
        # --- Arrange ---
        game_id = 301
        player_id = 1
        new_owner_id = 2
        original_owner_id = 3
        secret_id_to_steal = 50

        # El secreto que será robado (revelado y perteneciente a la víctima)
        revealed_secret = SecretCard(
            secret_id=secret_id_to_steal,
            game_id=game_id,
            player_id=original_owner_id,
            role=PlayerRole.INNOCENT,
            is_revealed=True,
        )
        mock_queries.get_secret.return_value = revealed_secret
        mock_commands.reveal_secret_card.return_value = ResponseStatus.OK
        mock_commands.change_secret_owner.return_value = ResponseStatus.OK

        # --- Act ---
        result = await and_then_there_was_one_more_effect.execute(
            game_id=game_id,
            player_id=player_id,
            card_ids=[999],
            target_player_id=new_owner_id,
            target_secret_id=secret_id_to_steal,
        )

        # --- Assert ---
        # 1. Verificar que se buscó el secreto correcto
        mock_queries.get_secret.assert_called_once_with(
            secret_id=secret_id_to_steal, game_id=game_id
        )

        # 2. Verificar que se ordenó ocultar el secreto
        mock_commands.reveal_secret_card.assert_called_once_with(
            secret_id=secret_id_to_steal, game_id=game_id, is_revealed=False
        )

        # 3. Verificar que se ordenó el cambio de propietario
        mock_commands.change_secret_owner.assert_called_once_with(
            secret_id=secret_id_to_steal,
            game_id=game_id,
            new_owner_id=new_owner_id,
        )

        # 4. Verificar que se notificaron ambas acciones en el orden correcto
        mock_notificator.notify_secret_hidden.assert_awaited_once_with(
            game_id=game_id, secret_id=secret_id_to_steal, player_id=original_owner_id
        )
        mock_notificator.notify_secret_stolen.assert_awaited_once_with(
            game_id=game_id, thief_id=new_owner_id, victim_id=original_owner_id
        )

        # 5. Verificar que el resultado es OK
        assert result == GameFlowStatus.CONTINUE

    @pytest.mark.asyncio
    async def test_execute_fails_if_no_target_secret_id(
        self,
        and_then_there_was_one_more_effect: AndThenThereWasOneMoreEffect,
    ):
        """Prueba que falla si no se proporciona un ID de secreto."""
        # --- Arrange ---
        # No se necesita configurar mocks

        # --- Act & Assert ---
        with pytest.raises(
            InvalidAction, match="No se proporcionó un ID de secreto objetivo."
        ):
            await and_then_there_was_one_more_effect.execute(
                game_id=1, player_id=1, card_ids=[999], target_player_id=2
            )

    @pytest.mark.asyncio
    async def test_execute_fails_if_secret_not_found(
        self,
        and_then_there_was_one_more_effect: AndThenThereWasOneMoreEffect,
        mock_queries: Mock,
    ):
        """Prueba que falla si el ID del secreto no corresponde a uno existente."""
        # --- Arrange ---
        mock_queries.get_secret.return_value = None

        # --- Act & Assert ---
        with pytest.raises(
            ResourceNotFound, match="No se encontró el secreto objetivo."
        ):
            await and_then_there_was_one_more_effect.execute(
                game_id=1,
                player_id=1,
                card_ids=[999],
                target_player_id=2,
                target_secret_id=99,
            )

    @pytest.mark.asyncio
    async def test_execute_fails_if_secret_is_not_revealed(
        self,
        and_then_there_was_one_more_effect: AndThenThereWasOneMoreEffect,
        mock_queries: Mock,
    ):
        """Prueba que falla si se intenta robar un secreto que no está revelado."""
        # --- Arrange ---
        hidden_secret = SecretCard(
            secret_id=50,
            game_id=1,
            player_id=3,
            role=PlayerRole.INNOCENT,
            is_revealed=False,
        )
        mock_queries.get_secret.return_value = hidden_secret

        # --- Act & Assert ---
        with pytest.raises(
            InvalidAction, match="El secreto objetivo no está revelado."
        ):
            await and_then_there_was_one_more_effect.execute(
                game_id=1,
                player_id=1,
                card_ids=[999],
                target_player_id=2,
                target_secret_id=50,
            )

    @pytest.mark.asyncio
    async def test_execute_raises_error_if_hide_fails(
        self,
        and_then_there_was_one_more_effect: AndThenThereWasOneMoreEffect,
        mock_queries: Mock,
        mock_commands: Mock,
    ):
        """Prueba que se lanza InternalGameError si el comando de ocultar falla."""
        # --- Arrange ---
        revealed_secret = SecretCard(
            secret_id=50,
            game_id=1,
            player_id=3,
            role=PlayerRole.INNOCENT,
            is_revealed=True,
        )
        mock_queries.get_secret.return_value = revealed_secret
        # Simulamos que la DB falla al ocultar
        mock_commands.reveal_secret_card.return_value = ResponseStatus.ERROR

        # --- Act & Assert ---
        with pytest.raises(
            InternalGameError, match="La DB no pudo ocultar el secreto objetivo"
        ):
            await and_then_there_was_one_more_effect.execute(
                game_id=1,
                player_id=1,
                card_ids=[999],
                target_player_id=2,
                target_secret_id=50,
            )

    @pytest.mark.asyncio
    async def test_execute_raises_error_if_change_owner_fails(
        self,
        and_then_there_was_one_more_effect: AndThenThereWasOneMoreEffect,
        mock_queries: Mock,
        mock_commands: Mock,
    ):
        """Prueba que se lanza InternalGameError si el comando de cambiar propietario falla."""
        # --- Arrange ---
        revealed_secret = SecretCard(
            secret_id=50,
            game_id=1,
            player_id=3,
            role=PlayerRole.INNOCENT,
            is_revealed=True,
        )
        mock_queries.get_secret.return_value = revealed_secret
        mock_commands.reveal_secret_card.return_value = ResponseStatus.OK
        # Simulamos que la DB falla al cambiar el dueño
        mock_commands.change_secret_owner.return_value = ResponseStatus.ERROR

        # --- Act & Assert ---
        with pytest.raises(
            InternalGameError,
            match="La DB no pudo cambiar el propietario del secreto",
        ):
            await and_then_there_was_one_more_effect.execute(
                game_id=1,
                player_id=1,
                card_ids=[999],
                target_player_id=2,
                target_secret_id=50,
            )


# =================================================================
# --- Tests para el Efecto 'DelayTheMurdererEscapeEffect' ---
# =================================================================


@pytest.fixture
def delay_the_murderer_escape_effect(
    mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
) -> "DelayTheMurdererEscapeEffect":
    """Crea una instancia del efecto con sus dependencias mockeadas."""
    # Importación local para evitar dependencia circular si el archivo crece
    from app.game.effects.event_effects import DelayTheMurdererEscapeEffect

    return DelayTheMurdererEscapeEffect(
        queries=mock_queries, commands=mock_commands, notifier=mock_notificator
    )


class TestDelayTheMurdererEscapeEffect:
    @pytest.mark.asyncio
    async def test_execute_moves_5_cards_when_more_are_available(
        self,
        delay_the_murderer_escape_effect: "DelayTheMurdererEscapeEffect",
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory,
    ):
        """
        Prueba que si hay 7 cartas, se mueven las 5 con mayor 'position'.
        """
        # --- Arrange ---
        game_id = 401
        # Creamos 7 cartas en el descarte
        discard_pile = [
            card_domain_factory(card_id=i, position=i) for i in range(1, 8)
        ]
        cards_to_be_moved = discard_pile[2:]
        mock_queries.get_discard_pile.return_value = discard_pile
        mock_queries.get_deck.return_value = []  # Mazo inicial vacío para simplificar
        mock_commands.update_card_location.return_value = ResponseStatus.OK
        mock_queries.get_deck.return_value = cards_to_be_moved

        # --- Act ---
        result = await delay_the_murderer_escape_effect.execute(
            game_id=game_id, player_id=1, card_ids=[999]
        )

        # --- Assert ---
        # 1. Se debe haber llamado a mover 5 cartas
        assert mock_commands.update_card_location.call_count == 5

        # 2. Las cartas movidas deben ser las de ID 3 a 7
        moved_card_ids = {
            call.kwargs["card_id"]
            for call in mock_commands.update_card_location.call_args_list
        }
        assert moved_card_ids == {3, 4, 5, 6, 7}

        # 3. Se notificó el nuevo tamaño del mazo
        mock_notificator.notify_deck_updated.assert_awaited_once_with(
            game_id=game_id, deck_size=5
        )

        # 4. El resultado es OK
        assert result == GameFlowStatus.CONTINUE

    @pytest.mark.asyncio
    async def test_execute_moves_all_cards_when_fewer_than_5(
        self,
        delay_the_murderer_escape_effect: "DelayTheMurdererEscapeEffect",
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory,
    ):
        """
        Prueba que si hay 3 cartas, se mueven las 3.
        """
        # --- Arrange ---
        game_id = 402
        discard_pile = [
            card_domain_factory(card_id=i, position=i) for i in range(1, 4)
        ]
        initial_deck = [
            card_domain_factory(card_id=100, position=1)
        ]

        mock_queries.get_discard_pile.return_value = discard_pile
        mock_queries.get_deck.return_value = initial_deck + discard_pile
        mock_commands.update_card_location.return_value = ResponseStatus.OK

        # La llamada a get_deck() dentro del efecto devolverá el mazo inicial
        # MÁS las 3 cartas que se movieron desde el descarte.
        mock_queries.get_deck.return_value = initial_deck + discard_pile

        # --- Act ---
        await delay_the_murderer_escape_effect.execute(
            game_id=game_id, player_id=1, card_ids=[999]
        )

        # --- Assert ---
        assert mock_commands.update_card_location.call_count == 3
        mock_notificator.notify_deck_updated.assert_awaited_once_with(
            game_id=game_id, deck_size=4
        )  # 1 inicial + 3 movidas

    @pytest.mark.asyncio
    async def test_execute_does_nothing_when_discard_pile_is_empty(
        self,
        delay_the_murderer_escape_effect: "DelayTheMurdererEscapeEffect",
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
    ):
        """
        Prueba que no pasa nada (y no falla) si la pila de descarte está vacía.
        """
        # --- Arrange ---
        game_id = 403
        mock_queries.get_discard_pile.return_value = []
        mock_queries.get_deck.return_value = []

        # --- Act ---
        result = await delay_the_murderer_escape_effect.execute(
            game_id=game_id, player_id=1, card_ids=[999]
        )

        # --- Assert ---
        mock_commands.update_card_location.assert_not_called()
        mock_notificator.notify_deck_updated.assert_not_awaited()
        assert result == GameFlowStatus.CONTINUE


# =================================================================
# --- Tests para el Efecto 'EarlyTrainToPaddingtonEffect' ---
# =================================================================


@pytest.fixture
def early_train_to_paddington_effect(
    mock_queries: Mock, mock_commands: Mock, mock_notificator: AsyncMock
) -> "EarlyTrainToPaddingtonEffect":
    """Crea una instancia del efecto con sus dependencias mockeadas."""
    from app.game.effects.event_effects import EarlyTrainToPaddingtonEffect

    return EarlyTrainToPaddingtonEffect(
        queries=mock_queries, commands=mock_commands, notifier=mock_notificator
    )


class TestEarlyTrainToPaddingtonEffect:
    @pytest.mark.asyncio
    async def test_execute_moves_6_cards_when_deck_is_large(
        self,
        early_train_to_paddington_effect: "EarlyTrainToPaddingtonEffect",
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory,
    ):
        """Prueba que si el mazo tiene 10 cartas, se mueven las primeras 6."""
        # --- Arrange ---
        game_id = 501
        # Creamos un mazo con 10 cartas
        deck = [
            card_domain_factory(card_id=i, position=i) for i in range(1, 11)
        ]
        mock_queries.get_deck.return_value = deck
        mock_commands.update_card_location.return_value = ResponseStatus.OK

        # --- Act ---
        result = await early_train_to_paddington_effect.execute(
            game_id=game_id, player_id=1, card_ids=[999]
        )

        # --- Assert ---
        # 1. Se debe haber llamado a mover 6 cartas
        assert mock_commands.update_card_location.call_count == 6

        # 2. Las cartas movidas deben ser las de ID 1 a 6
        moved_card_ids = {
            call.kwargs["card_id"]
            for call in mock_commands.update_card_location.call_args_list
        }
        assert moved_card_ids == {1, 2, 3, 4, 5, 6}

        # 3. Se notificó el nuevo tamaño del mazo (10 - 6 = 4)
        mock_notificator.notify_deck_updated.assert_awaited_once_with(
            game_id=game_id, deck_size=4
        )

        # 4. El resultado es OK
        assert result == GameFlowStatus.CONTINUE

    @pytest.mark.asyncio
    async def test_execute_moves_all_cards_when_deck_is_small(
        self,
        early_train_to_paddington_effect: "EarlyTrainToPaddingtonEffect",
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory,
    ):
        """Prueba que si el mazo tiene 4 cartas, se mueven las 4."""
        # --- Arrange ---
        game_id = 502
        deck = [card_domain_factory(card_id=i, position=i) for i in range(1, 5)]
        mock_queries.get_deck.return_value = deck
        mock_commands.update_card_location.return_value = ResponseStatus.OK

        # --- Act ---
        await early_train_to_paddington_effect.execute(
            game_id=game_id, player_id=1, card_ids=[999]
        )

        # --- Assert ---
        assert mock_commands.update_card_location.call_count == 4
        mock_notificator.notify_deck_updated.assert_awaited_once_with(
            game_id=game_id, deck_size=0
        )

    @pytest.mark.asyncio
    async def test_execute_does_nothing_when_deck_is_empty(
        self,
        early_train_to_paddington_effect: "EarlyTrainToPaddingtonEffect",
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
    ):
        """Prueba que no pasa nada si el mazo ya está vacío."""
        # --- Arrange ---
        game_id = 503
        mock_queries.get_deck.return_value = []

        # --- Act ---
        result = await early_train_to_paddington_effect.execute(
            game_id=game_id, player_id=1, card_ids=[999]
        )

        # --- Assert ---
        mock_commands.update_card_location.assert_not_called()
        mock_notificator.notify_deck_updated.assert_not_awaited()
        assert result == GameFlowStatus.CONTINUE

# =================================================================
# --- Tests para el Efecto 'CardTradeEffect' ---
# =================================================================


class TestCardTradeEffect:
    """Tests para el efecto de la carta 'Card Trade'."""

    # --- HAPPY PATH TESTS ---

    @pytest.mark.asyncio
    async def test_execute_happy_path_sets_state_and_notifies(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory_hand: Mock,
    ):
        """
        Happy path: El iniciador tiene suficientes cartas, selecciona una carta
        válida del oponente, el estado se actualiza correctamente y se notifica.
        """
        # --- Arrange ---
        game_id = 101
        initiator_id = 1
        target_player_id = 2
        target_card_id = 50  # Carta en la mano del oponente

        # El iniciador tiene 3 cartas (CARD_TRADE + 2 más)
        initiator_hand = [
            card_domain_factory_hand(10, CardType.CARD_TRADE, CardLocation.IN_HAND, initiator_id),
            card_domain_factory_hand(11, CardType.TOMMY_BERESFORD, CardLocation.IN_HAND, initiator_id),
            card_domain_factory_hand(12, CardType.PARKER_PYNE, CardLocation.IN_HAND, initiator_id),
        ]
        mock_queries.get_player_hand.return_value = initiator_hand

        # La carta objetivo existe y pertenece al oponente
        target_card = card_domain_factory_hand(
            target_card_id, CardType.MISS_MARPLE, CardLocation.IN_HAND, target_player_id
        )
        mock_queries.get_card.return_value = target_card

        # Los comandos tienen éxito
        mock_commands.set_game_action_state.return_value = ResponseStatus.OK
        mock_commands.update_pending_saga.return_value = ResponseStatus.OK

        # --- Act ---
        result = await card_trade_effect.execute(
            game_id=game_id,
            player_id=initiator_id,
            card_ids=[10],  # ID de la carta CARD_TRADE
            target_card_id=target_card_id,
        )

        # --- Assert ---
        # 1. Verifica que se consultó la mano del iniciador
        mock_queries.get_player_hand.assert_called_once_with(
            player_id=initiator_id, game_id=game_id
        )

        # 2. Verifica que se consultó la carta objetivo
        mock_queries.get_card.assert_called_once_with(target_card_id, game_id)

        # 3. Verifica que se actualizó el estado del juego
        mock_commands.set_game_action_state.assert_called_once_with(
            game_id=game_id,
            state=GameActionState.AWAITING_SELECTION_FOR_CARD_TRADE,
            prompted_player_id=target_player_id,
            initiator_id=initiator_id,
        )

        # 4. Verifica que se guardó el pending_saga
        mock_commands.update_pending_saga.assert_called_once()
        saga_call = mock_commands.update_pending_saga.call_args
        assert saga_call[0][0] == game_id
        saga_data = saga_call[0][1]
        assert saga_data["type"] == "card_trade"
        assert saga_data["initiator_player_id"] == initiator_id
        assert saga_data["requested_card_id"] == target_card_id

        # 5. Verifica que se notificó al oponente
        mock_notificator.notify_player_to_choose_card_for_trade.assert_awaited_once_with(
            game_id=game_id,
            player_id=target_player_id,
            initiator_player_id=initiator_id,
        )

        # 6. Verifica que el resultado fue OK
        assert result == GameFlowStatus.PAUSED

    @pytest.mark.asyncio
    async def test_execute_infers_target_player_from_card_owner(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory_hand: Mock,
    ):
        """
        Prueba que si no se proporciona target_player_id, se infiere del dueño
        de la carta objetivo.
        """
        # --- Arrange ---
        game_id = 102
        initiator_id = 1
        target_card_id = 60
        inferred_target_id = 3

        initiator_hand = [
            card_domain_factory_hand(20, CardType.CARD_TRADE, CardLocation.IN_HAND, initiator_id),
            card_domain_factory_hand(21, CardType.HARLEY_QUIN, CardLocation.IN_HAND, initiator_id),
            card_domain_factory_hand(22, CardType.HERCULE_POIROT, CardLocation.IN_HAND, initiator_id),
        ]
        mock_queries.get_player_hand.return_value = initiator_hand

        target_card = card_domain_factory_hand(
            target_card_id,
            CardType.LADY_EILEEN,
            CardLocation.IN_HAND,
            inferred_target_id,
        )
        mock_queries.get_card.return_value = target_card
        mock_commands.set_game_action_state.return_value = ResponseStatus.OK
        mock_commands.update_pending_saga.return_value = ResponseStatus.OK

        # --- Act ---
        result = await card_trade_effect.execute(
            game_id=game_id,
            player_id=initiator_id,
            card_ids=[20],
            target_card_id=target_card_id,
            target_player_id=None,  # No se proporciona explícitamente
        )

        # --- Assert ---
        # Verifica que se usó el player_id inferido de la carta
        mock_commands.set_game_action_state.assert_called_once_with(
            game_id=game_id,
            state=GameActionState.AWAITING_SELECTION_FOR_CARD_TRADE,
            prompted_player_id=inferred_target_id,
            initiator_id=initiator_id,
        )
        mock_notificator.notify_player_to_choose_card_for_trade.assert_awaited_once_with(
            game_id=game_id,
            player_id=inferred_target_id,
            initiator_player_id=initiator_id,
        )
        assert result == GameFlowStatus.PAUSED

    # --- SAD PATH TESTS (Errores de Validación) ---

    @pytest.mark.asyncio
    async def test_execute_fails_when_target_card_id_missing(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
    ):
        """
        Prueba que el efecto falla si no se proporciona target_card_id.
        """
        # --- Arrange ---
        game_id = 201
        initiator_id = 1

        # --- Act & Assert ---
        with pytest.raises(InvalidAction, match="No se proporcionó el ID de la carta"):
            await card_trade_effect.execute(
                game_id=game_id,
                player_id=initiator_id,
                card_ids=[10],
                target_card_id=None,  # Missing!
            )

    @pytest.mark.asyncio
    async def test_execute_fails_when_target_card_not_found(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
    ):
        """
        Prueba que el efecto falla si la carta objetivo no existe en la BD.
        """
        # --- Arrange ---
        game_id = 202
        initiator_id = 1
        target_card_id = 999

        mock_queries.get_card.return_value = None  # Carta no encontrada

        # --- Act & Assert ---
        with pytest.raises(ResourceNotFound, match="Carta objetivo no encontrada"):
            await card_trade_effect.execute(
                game_id=game_id,
                player_id=initiator_id,
                card_ids=[10],
                target_card_id=target_card_id,
            )

    @pytest.mark.asyncio
    async def test_execute_fails_when_target_card_has_no_owner(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
        card_domain_factory_hand: Mock,
    ):
        """
        Prueba que el efecto falla si la carta objetivo no tiene dueño
        (por ejemplo, está en el draft o en el mazo).
        """
        # --- Arrange ---
        game_id = 203
        initiator_id = 1
        target_card_id = 70

        # Carta sin dueño (player_id = None)
        target_card = card_domain_factory_hand(
            target_card_id, CardType.MISS_MARPLE, CardLocation.DRAFT, None
        )
        mock_queries.get_card.return_value = target_card

        # --- Act & Assert ---
        with pytest.raises(
            InvalidAction, match="La carta seleccionada no pertenece a un jugador"
        ):
            await card_trade_effect.execute(
                game_id=game_id,
                player_id=initiator_id,
                card_ids=[10],
                target_card_id=target_card_id,
            )

    @pytest.mark.asyncio
    async def test_execute_fails_when_initiator_has_insufficient_cards(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
        card_domain_factory_hand: Mock,
    ):
        """
        Prueba que el efecto falla si el iniciador tiene menos de 2 cartas
        (incluyendo la CARD_TRADE que está jugando).
        """
        # --- Arrange ---
        game_id = 204
        initiator_id = 1
        target_player_id = 2
        target_card_id = 80

        # El iniciador solo tiene 1 carta (la CARD_TRADE)
        initiator_hand = [
            card_domain_factory_hand(
                30, CardType.CARD_TRADE, CardLocation.IN_HAND, initiator_id
            ),
        ]
        mock_queries.get_player_hand.return_value = initiator_hand

        target_card = card_domain_factory_hand(
            target_card_id,
            CardType.PARKER_PYNE,
            CardLocation.IN_HAND,
            target_player_id,
        )
        mock_queries.get_card.return_value = target_card

        # --- Act & Assert ---
        with pytest.raises(
            InvalidAction, match="no tiene suficientes cartas para intercambiar"
        ):
            await card_trade_effect.execute(
                game_id=game_id,
                player_id=initiator_id,
                card_ids=[30],
                target_card_id=target_card_id,
            )

    @pytest.mark.asyncio
    async def test_execute_fails_when_set_game_action_state_fails(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        card_domain_factory_hand: Mock,
    ):
        """
        Prueba que el efecto falla si no se puede actualizar el estado del juego.
        """
        # --- Arrange ---
        game_id = 205
        initiator_id = 1
        target_player_id = 2
        target_card_id = 90

        initiator_hand = [
            card_domain_factory_hand(40, CardType.CARD_TRADE, CardLocation.IN_HAND, initiator_id),
            card_domain_factory_hand(41, CardType.TOMMY_BERESFORD, CardLocation.IN_HAND, initiator_id),
        ]
        mock_queries.get_player_hand.return_value = initiator_hand

        target_card = card_domain_factory_hand(
            target_card_id,
            CardType.HERCULE_POIROT,
            CardLocation.IN_HAND,
            target_player_id,
        )
        mock_queries.get_card.return_value = target_card

        # Simular fallo al actualizar estado
        mock_commands.set_game_action_state.return_value = ResponseStatus.ERROR

        # --- Act & Assert ---
        with pytest.raises(
            InternalGameError, match="No se pudo actualizar el estado de la partida"
        ):
            await card_trade_effect.execute(
                game_id=game_id,
                player_id=initiator_id,
                card_ids=[40],
                target_card_id=target_card_id,
            )

    # --- BORDER/EDGE CASE TESTS ---

    @pytest.mark.asyncio
    async def test_execute_with_exactly_two_cards(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory_hand: Mock,
    ):
        """
        Prueba el caso límite donde el iniciador tiene exactamente 2 cartas
        (el mínimo permitido: CARD_TRADE + 1 otra carta).
        """
        # --- Arrange ---
        game_id = 301
        initiator_id = 1
        target_player_id = 2
        target_card_id = 100

        # Exactamente 2 cartas
        initiator_hand = [
            card_domain_factory_hand(50, CardType.CARD_TRADE, CardLocation.IN_HAND, initiator_id),
            card_domain_factory_hand(51, CardType.MISS_MARPLE, CardLocation.IN_HAND, initiator_id),
        ]
        mock_queries.get_player_hand.return_value = initiator_hand

        target_card = card_domain_factory_hand(
            target_card_id,
            CardType.LADY_EILEEN,
            CardLocation.IN_HAND,
            target_player_id,
        )
        mock_queries.get_card.return_value = target_card
        mock_commands.set_game_action_state.return_value = ResponseStatus.OK
        mock_commands.update_pending_saga.return_value = ResponseStatus.OK

        # --- Act ---
        result = await card_trade_effect.execute(
            game_id=game_id,
            player_id=initiator_id,
            card_ids=[50],
            target_card_id=target_card_id,
        )

        # --- Assert ---
        # Debe pasar sin errores
        assert result == GameFlowStatus.PAUSED
        mock_notificator.notify_player_to_choose_card_for_trade.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_targeting_another_card_trade(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory_hand: Mock,
    ):
        """
        Prueba que es posible (aunque quizá no deseado) intercambiar
        otra carta CARD_TRADE del oponente.
        
        Nota: Este test documenta el comportamiento actual. Si se decide
        que esto NO debería permitirse, este test debería cambiar a
        expect una excepción.
        """
        # --- Arrange ---
        game_id = 302
        initiator_id = 1
        target_player_id = 2
        target_card_id = 110

        initiator_hand = [
            card_domain_factory_hand(60, CardType.CARD_TRADE, CardLocation.IN_HAND, initiator_id),
            card_domain_factory_hand(61, CardType.HARLEY_QUIN, CardLocation.IN_HAND, initiator_id),
        ]
        mock_queries.get_player_hand.return_value = initiator_hand

        # El oponente tiene otra CARD_TRADE
        target_card = card_domain_factory_hand(
            target_card_id,
            CardType.CARD_TRADE,  # ¡Otra Card Trade!
            CardLocation.IN_HAND,
            target_player_id,
        )
        mock_queries.get_card.return_value = target_card
        mock_commands.set_game_action_state.return_value = ResponseStatus.OK
        mock_commands.update_pending_saga.return_value = ResponseStatus.OK

        # --- Act ---
        result = await card_trade_effect.execute(
            game_id=game_id,
            player_id=initiator_id,
            card_ids=[60],
            target_card_id=target_card_id,
        )

        # --- Assert ---
        # Actualmente esto está PERMITIDO (no hay validación que lo impida)
        assert result == GameFlowStatus.PAUSED
        mock_notificator.notify_player_to_choose_card_for_trade.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_with_maximum_hand_size(
        self,
        card_trade_effect: CardTradeEffect,
        mock_queries: Mock,
        mock_commands: Mock,
        mock_notificator: AsyncMock,
        card_domain_factory_hand: Mock,
    ):
        """
        Prueba que el efecto funciona correctamente cuando el iniciador
        tiene el máximo de cartas (6).
        """
        # --- Arrange ---
        game_id = 303
        initiator_id = 1
        target_player_id = 2
        target_card_id = 120

        # Mano completa (6 cartas)
        initiator_hand = [
            card_domain_factory_hand(70 + i, CardType.CARD_TRADE, CardLocation.IN_HAND, initiator_id)
            for i in range(6)
        ]
        mock_queries.get_player_hand.return_value = initiator_hand

        target_card = card_domain_factory_hand(
            target_card_id,
            CardType.PARKER_PYNE,
            CardLocation.IN_HAND,
            target_player_id,
        )
        mock_queries.get_card.return_value = target_card
        mock_commands.set_game_action_state.return_value = ResponseStatus.OK
        mock_commands.update_pending_saga.return_value = ResponseStatus.OK

        # --- Act ---
        result = await card_trade_effect.execute(
            game_id=game_id,
            player_id=initiator_id,
            card_ids=[70],
            target_card_id=target_card_id,
        )

        # --- Assert ---
        assert result == GameFlowStatus.PAUSED
        # El oponente tendrá 5 cartas del iniciador para elegir después de que
        # se descarte CARD_TRADE
        mock_notificator.notify_player_to_choose_card_for_trade.assert_awaited_once()
