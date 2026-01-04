from collections import Counter
from typing import Type, Optional, FrozenSet, Tuple, Any, Dict
from app.game.effects.interfaces import ICardEffect
from app.domain.enums import CardType


class PrioritizedCommutativeDict:
    def __init__(self):
        # La clave ahora es: frozenset({(CardType, count), (CardType, count)})
        # El valor es: (priority, effect_class)
        self._data: dict[FrozenSet[Tuple[CardType, int]], tuple[int, Any]] = {}

    def set(
        self, card_counts: Dict[CardType, int], value: Any, priority: int = 0
    ):
        """
        Establece un valor y prioridad para una combinación específica de cartas y sus cantidades.
        Ejemplo de card_counts: {CardType.POIROT: 2, CardType.QUIN: 1}
        """
        # Convertimos el diccionario de conteo en una clave inmutable
        key = frozenset(card_counts.items())
        self._data[key] = (priority, value)

    def get_matching_effect(
        self, played_cards_counter: Counter
    ) -> Optional[Type[ICardEffect]]:
        """
        Encuentra el efecto de mayor prioridad cuya regla de cartas es un
        subconjunto exacto (en tipos y cantidades) de las cartas jugadas.
        """
        matches = []

        # El contador de cartas jugadas. Ej: {POIROT: 3, QUIN: 1}
        played_items = played_cards_counter.items()

        for rule_key, (priority, effect_class) in self._data.items():
            # rule_key es, por ej: frozenset({(POIROT, 2), (QUIN, 1)})

            is_subset = True
            for card_type, required_count in rule_key:
                # ¿Tenemos suficientes cartas de este tipo?
                if played_cards_counter.get(card_type, 0) < required_count:
                    is_subset = False
                    break

            if is_subset:
                # La regla se cumple. La guardamos para la competencia de prioridades.
                # Guardamos (prioridad, suma de cartas requeridas, clase_efecto)
                # La suma de cartas nos ayuda a desempatar (reglas más complejas primero)
                total_cards_in_rule = sum(count for _, count in rule_key)
                matches.append((priority, total_cards_in_rule, effect_class))

        if not matches:
            return None

        # Ordenamos por prioridad (desc), luego por complejidad de la regla (desc)
        matches.sort(key=lambda x: (x[0], x[1]), reverse=True)

        return matches[0][2]  # Devolvemos la clase de efecto ganadora
