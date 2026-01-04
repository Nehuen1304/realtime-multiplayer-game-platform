from abc import ABC, abstractmethod
from typing import Optional, List, Literal
from app.database.interfaces import IQueryManager, ICommandManager
from app.game.helpers.notificators import Notificator
from app.domain.enums import GameFlowStatus


class ICardEffect(ABC):
    """
    Define el contrato para la ejecución de un efecto de carta.
    Las dependencias de infraestructura se inyectan por constructor.
    """

    def __init__(
        self,
        queries: IQueryManager,
        commands: ICommandManager,
        notifier: Notificator,
    ):
        self.queries = queries
        self.commands = commands
        self.notifier = notifier

    @abstractmethod
    async def execute(
        self,
        game_id: int,
        # card_played_id: int,
        player_id: int,
        card_ids: List[int],
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        """Aplica el efecto de la carta al estado del juego."""
        pass
