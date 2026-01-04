from typing import Dict, Optional, List, Callable, Literal
from ..database.interfaces import IQueryManager, ICommandManager
from ..game.helpers.notificators import Notificator
from ..game.exceptions import InvalidAction
from ..domain.enums import CardType, ResponseStatus, GameFlowStatus
from ..domain.models import Card
from .effects.interfaces import ICardEffect
from collections import Counter
from functools import partial

# ¡¡¡AHORA IMPORTAMOS LAS CLASES REALES, NO FANTASMAS!!!
from app.game.effects.event_effects import (
    DeadCardFollyEffect,
    LookIntoTheAshesEffect,
    AnotherVictimEffect,
    CardsOffTheTableEffect,
    AndThenThereWasOneMoreEffect,
    DelayTheMurdererEscapeEffect,
    EarlyTrainToPaddingtonEffect,
    PointYourSuspicionsEffect,
    CardTradeEffect,
)
from .effects.set_effects import (
    RevealSpecificSecretEffect,
    RevealChosenSecretEffect,
    HideSecretEffect,
    StealSecretEffect,
    BeresfordUncancellableEffect,
)

from .effects.devious_effects import SocialFauxPasEffect

from ..game.helpers.commutative_dict import PrioritizedCommutativeDict


class EffectExecutor:
    def __init__(
        self,
        queries: IQueryManager,
        commands: ICommandManager,
        notifier: Notificator,
    ):
        self.read = queries
        self.write = commands
        self.notifier = notifier

        # --- EVENT EFFECTS (Single card plays) ---
        self.EVENT_EFFECT_MAP: Dict[CardType, Callable[..., ICardEffect]] = {
            CardType.DEAD_CARD_FOLLY: DeadCardFollyEffect,
            CardType.ANOTHER_VICTIM: partial(
                AnotherVictimEffect, executor=self
            ),
            CardType.LOOK_INTO_THE_ASHES: LookIntoTheAshesEffect,
            CardType.CARDS_OFF_THE_TABLE: CardsOffTheTableEffect,
            CardType.THERE_WAS_ONE_MORE: AndThenThereWasOneMoreEffect,
            CardType.DELAY_MURDERER_ESCAPE: DelayTheMurdererEscapeEffect,
            CardType.EARLY_TRAIN: EarlyTrainToPaddingtonEffect,
            CardType.POINT_YOUR_SUSPICIONS: PointYourSuspicionsEffect,
            CardType.SOCIAL_FAUX_PAS: SocialFauxPasEffect,
            # CardType.BLACKMAILED: BlackmailedEffect,
            CardType.CARD_TRADE: CardTradeEffect,
        }

        # --- SET EFFECTS (Combinations of cards) ---
        self.SET_EFFECT_MAP = PrioritizedCommutativeDict()
        self._initialize_set_effects()

    def _initialize_set_effects(self):
        # Priority 20: Most specific combos
        high_priority = [
            (
                {CardType.TOMMY_BERESFORD: 1, CardType.TUPPENCE_BERESFORD: 1},
                BeresfordUncancellableEffect,
            ),
            (
                {CardType.MR_SATTERTHWAITE: 1, CardType.HARLEY_QUIN: 1},
                StealSecretEffect,
            ),
        ]
        for combo, effect in high_priority:
            self.SET_EFFECT_MAP.set(combo, effect, priority=20)

        # Priority 10: Combos with Wildcard (Harley Quin)
        wildcard_combos = [
            (
                {CardType.HERCULE_POIROT: 2, CardType.HARLEY_QUIN: 1},
                RevealSpecificSecretEffect,
            ),
            (
                {CardType.HERCULE_POIROT: 1, CardType.HARLEY_QUIN: 2},
                RevealSpecificSecretEffect,
            ),
            (
                {CardType.MISS_MARPLE: 2, CardType.HARLEY_QUIN: 1},
                RevealSpecificSecretEffect,
            ),
            (
                {CardType.MISS_MARPLE: 1, CardType.HARLEY_QUIN: 2},
                RevealSpecificSecretEffect,
            ),
            (
                {CardType.TUPPENCE_BERESFORD: 1, CardType.HARLEY_QUIN: 1},
                RevealChosenSecretEffect,
            ),
            (
                {CardType.TOMMY_BERESFORD: 1, CardType.HARLEY_QUIN: 1},
                RevealChosenSecretEffect,
            ),
            (
                {CardType.LADY_EILEEN: 1, CardType.HARLEY_QUIN: 1},
                RevealChosenSecretEffect,
            ),
            (
                {CardType.PARKER_PYNE: 1, CardType.HARLEY_QUIN: 1},
                HideSecretEffect,
            ),
        ]
        for combo, effect in wildcard_combos:
            self.SET_EFFECT_MAP.set(combo, effect, priority=10)

        # Priority 0: Base sets (exact quantities)
        base_sets = [
            ({CardType.HERCULE_POIROT: 3}, RevealSpecificSecretEffect),
            ({CardType.MISS_MARPLE: 3}, RevealSpecificSecretEffect),
            ({CardType.MR_SATTERTHWAITE: 2}, RevealChosenSecretEffect),
            ({CardType.TOMMY_BERESFORD: 2}, RevealChosenSecretEffect),
            ({CardType.TUPPENCE_BERESFORD: 2}, RevealChosenSecretEffect),
            ({CardType.LADY_EILEEN: 2}, RevealChosenSecretEffect),
            ({CardType.PARKER_PYNE: 2}, HideSecretEffect),
        ]
        for combo, effect in base_sets:
            self.SET_EFFECT_MAP.set(combo, effect, priority=0)

    async def execute_effect(
        self,
        game_id: int,
        played_cards: List[Card],
        player_id: int,
        target_player_id: Optional[int] = None,
        target_secret_id: Optional[int] = None,
        target_set_id: Optional[int] = None,
        target_card_id: Optional[int] = None,
        trade_direction: Optional[Literal["left", "right"]] = None,
    ) -> GameFlowStatus:
        effect_class = self.classify_effect(played_cards)
        if not effect_class:
            raise InvalidAction(
                "La combinación de cartas jugadas no tiene un efecto válido."
            )

        effect_instance = effect_class(
            queries=self.read, commands=self.write, notifier=self.notifier
        )

        return await effect_instance.execute(
            game_id=game_id,
            card_ids=[card.card_id for card in played_cards],
            player_id=player_id,
            target_player_id=target_player_id,
            target_secret_id=target_secret_id,
            target_set_id=target_set_id,
            target_card_id=target_card_id,
            trade_direction=trade_direction,
        )

    def classify_effect(
        self, played_cards: List[Card]
    ) -> Optional[Callable[..., ICardEffect]]:
        # Special case: Ariadne Oliver
        if (
            len(played_cards) == 1
            and played_cards[0].card_type == CardType.ARIADNE_OLIVER
        ):
            return RevealChosenSecretEffect

        # Single card event
        if len(played_cards) == 1:
            return self.EVENT_EFFECT_MAP.get(played_cards[0].card_type)

        # Multiple card set
        card_types_played = Counter(card.card_type for card in played_cards)
        return self.SET_EFFECT_MAP.get_matching_effect(card_types_played)
