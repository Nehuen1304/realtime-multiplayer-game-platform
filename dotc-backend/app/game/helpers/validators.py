from ...database.interfaces import IQueryManager
from ...domain.models import Game, PlayerInfo, PlayerInGame, Card
from ...domain.enums import GameStatus
from ...game.exceptions import (
    ActionConflict,
    CardNotFound,
    ForbiddenAction,
    GameNotFound,
    InvalidAction,
    NotYourTurn,
    PlayerNotFound,
    PlayerNotInGame,
    NotYourCard,
)
from typing import List


class GameValidator:
    """
    Clase que agrupa métodos de validación reutilizables.
    Lanza excepciones específicas que pueden ser capturadas para dar respuestas claras.
    """

    def __init__(self, queries: IQueryManager):
        self.read = queries

    def validate_game_exists(self, game_id: int) -> Game:
        """Devuelve el objeto Game si existe, si no, lanza una excepción."""
        game = self.read.get_game(game_id)
        if not game:
            raise GameNotFound(detail=f"La partida {game_id} no existe.")
        return game

    def validate_player_exists(self, player_id: int) -> PlayerInfo:
        """Devuelve el objeto PlayerInfo si existe, si no, lanza una excepción."""
        player = self.read.get_player(player_id)
        if not player:
            raise PlayerNotFound(detail=f"El jugador {player_id} no existe.")
        return player

    def validate_game_name_is_unique(self, game_name: str):
        """Valida que el nombre de la partida no esté ya en uso."""
        if self.read.game_name_exists(game_name):
            raise ActionConflict(
                detail=f"Ya existe una partida con el nombre '{game_name}'."
            )

    def validate_game_status(self, game: Game, expected_status: GameStatus):
        """Valida que la partida está en el estado esperado."""
        if game.status != expected_status:
            raise ActionConflict(
                detail=f"La acción no es válida en el estado actual de la partida ({game.status.name})."
            )

    def validate_player_is_host(self, game: Game, player_id: int):
        """Valida que el jugador es el host de la partida."""
        if not self.read.is_player_host(game.id, player_id):
            raise ForbiddenAction(
                detail="Solo el host de la partida puede realizar esta acción."
            )

    def validate_is_players_turn(self, game: Game, player_id: int):
        """Valida que es el turno del jugador que realiza la acción."""
        if game.current_turn_player_id != player_id:
            raise NotYourTurn(
                detail="No es tu turno para realizar esta acción."
            )

    def validate_deck_has_cards(self, game: Game):
        """Valida que el mazo de robo no está vacío."""
        if not game.deck:
            raise InvalidAction(detail="No quedan cartas en el mazo de robo.")

    def validate_player_in_game(
        self, game: Game, player_id: int
    ) -> PlayerInGame:
        """
        Valida que un jugador está en la partida y devuelve su objeto PlayerInGame.
        Lanza una excepción si no lo está.
        """
        player_in_game = next(
            (p for p in game.players if p.player_id == player_id), None
        )
        if not player_in_game:
            raise PlayerNotInGame(
                detail=f"El jugador {player_id} no forma parte de la partida {game.id}."
            )
        return player_in_game

    def validate_player_has_cards(
        self, player: PlayerInGame, card_ids: List[int]
    ) -> List[Card]:
        """
        Valida que un conjunto de cartas esté en la mano del jugador.
        SI TIENE ÉXITO, DEVUELVE LA LISTA DE OBJETOS Card.
        SI FALLA, LANZA UNA EXCEPCIÓN NotYourCard.
        """
        player_hand_map = {card.card_id: card for card in player.hand}
        found_cards: List[Card] = []

        for card_id in card_ids:
            card_obj = player_hand_map.get(card_id)
            if card_obj is None:
                # La carta no está en la mano del jugador.
                raise NotYourCard(
                    detail=f"El jugador {player.player_id} no tiene la carta {card_id} en su mano."
                )
            found_cards.append(card_obj)

        return found_cards

    def validate_player_count(
        self, game: Game, players_in_game: List[PlayerInGame]
    ):
        """
        Valida que la cantidad de jugadores esté dentro del rango permitido por la partida.
        """
        player_count = len(players_in_game)
        if not (game.min_players <= player_count <= game.max_players):
            raise InvalidAction(
                detail=f"La cantidad de jugadores ({player_count}) no está dentro del rango permitido ({game.min_players}-{game.max_players})."
            )
