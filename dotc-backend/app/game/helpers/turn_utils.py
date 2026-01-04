from datetime import date
from typing import List    
from app.game.exceptions import InternalGameError
from ...domain.models import PlayerInGame

class TurnUtils:

    def get_birthday_distance(self, player: PlayerInGame) -> int:
        """
        Función auxiliar que calcula la distancia en días desde el 15/09
        """
        target_date = date(date.today().year, 9, 15)
        current_year = target_date.year
        player_birthday_this_year = date(
            current_year,
            player.player_birth_date.month,
            player.player_birth_date.day,
        )

        # 1. Calcular el delta simple (puede ser negativo)
        delta = (player_birthday_this_year - target_date).days

        # 2. Calcular los días del año actual
        year_days = (
            366
            if (
                current_year % 4 == 0
                and (current_year % 100 != 0 or current_year % 400 == 0)
            )
            else 365
        )

        # 3. Calcular la distancia absoluta (distancia "corta")
        abs_delta = abs(delta)

        # 4. Calcular la distancia "larga" (dando la vuelta al otro lado del año)
        wrap_around_distance = year_days - abs_delta

        # 5. La distancia real es la más corta de las dos
        return min(abs_delta, wrap_around_distance)

    def sort_players_by_turn_order(
        self, players: List[PlayerInGame]
    ) -> List[PlayerInGame]:
        """
        Ordena los jugadores por turno según reglas (cumpleaños 15/09).
        """
        # Ordenar la lista de jugadores usando get_birthday_distance como clave
        sorted_list = sorted(players, key=self.get_birthday_distance)
        # Asignar el orden de turno a los jugadores
        for i, player in enumerate(sorted_list):
            player.turn_order = i
        if not sorted_list:
            error_msg = "Error al ordenar los jugadores por turno."
            raise InternalGameError(detail=error_msg)
        return sorted_list
    