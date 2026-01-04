from typing import List
from app.database.orm_models import (
    GameTable,
    PendingActionTable,
    PlayerTable,
    CardTable,
    SecretCardTable,
    PlayerInGameTable,
)
from app.domain.models import (
    Game,
    PendingAction,
    PlayerInfo,
    PlayerInGame,
    Card,
    SecretCard,
)

from app.domain.enums import GameActionState

from app.domain.enums import CardLocation
from app.api.schemas import GameLobbyInfo

# =================================================================
# 😄 MAPPER FUNCTIONS (ORM -> Domain)
# =================================================================

# --- Mappers Simples ---


def map_player_orm_to_info_dto(player_orm: PlayerTable) -> PlayerInfo:
    """Mapea PlayerTable a PlayerInfo DTO."""
    return PlayerInfo.model_validate(player_orm, from_attributes=True)


def map_card_orm_to_dto(card_orm: CardTable) -> Card:
    """Mapea CardTable a Card DTO."""
    return Card.model_validate(card_orm, from_attributes=True)


def map_secret_card_orm_to_dto(secret_orm: SecretCardTable) -> SecretCard:
    """Mapea SecretCardTable a SecretCard DTO."""
    return SecretCard.model_validate(secret_orm, from_attributes=True)


# --- Mappers Compuestos ---


def map_player_in_game_orm_to_dto(
    detail_orm: PlayerInGameTable, hand: List[Card]
) -> PlayerInGame:
    """Mapea la tabla de asociación PlayerInGameTable a un PlayerInGame DTO."""
    player_data = detail_orm.player.__dict__
    player_data.update(detail_orm.__dict__)
    player_data["hand"] = hand
    # aseguro presencia del campo social_disgrace
    player_data["social_disgrace"] = getattr(
        detail_orm, "social_disgrace", False
    )
    return PlayerInGame.model_validate(player_data, from_attributes=True)


def map_game_orm_to_lobby_dto(game_orm: GameTable) -> GameLobbyInfo:
    """Mapeo optimizado de GameTable a GameLobbyInfo DTO."""
    return GameLobbyInfo(
        id=game_orm.game_id,
        name=game_orm.game_name,
        min_players=game_orm.min_players,
        max_players=game_orm.max_players,
        player_count=len(game_orm.player_details),
        host_id=game_orm.host_id,
        game_status=game_orm.game_status,
        password=game_orm.game_password,
    )

# --- Mapper Principal ---

def map_game_orm_to_domain(db_game: GameTable) -> Game:
    """Mapea el objeto GameTable completo, con relaciones, a un Game DTO."""
    # Mapear el host - validar que existe Y que tiene datos válidos
    if db_game.host is None or db_game.host.player_name is None:
        host_info = None  # Será manejado en el constructor de Game
    else:
        host_info = map_player_orm_to_info_dto(db_game.host)

    # Mapear jugadores y sus manos
    players_in_game = []
    for detail in db_game.player_details:
        # Validar que el player existe y tiene datos válidos antes de intentar mapear
        if detail.player is None or detail.player.player_name is None:
            continue  # Saltar players con datos NULL
        
        player_hand = [
            map_card_orm_to_dto(c)
            for c in db_game.cards
            if c.player_id == detail.player_id
            and c.location == CardLocation.IN_HAND
        ]
        players_in_game.append(
            map_player_in_game_orm_to_dto(detail, player_hand)
        )

    # Mapear mazos
    deck = [
        map_card_orm_to_dto(c)
        for c in db_game.cards
        if c.location == CardLocation.DRAW_PILE
    ]
    discard_pile = [
        map_card_orm_to_dto(c)
        for c in db_game.cards
        if c.location == CardLocation.DISCARD_PILE
    ]
    draft = [
        map_card_orm_to_dto(c)
        for c in db_game.cards
        if c.location == CardLocation.DRAFT
    ]

    action_state_enum = (
        GameActionState(db_game.action_state) if db_game.action_state else None
    )

    # Construir y devolver el objeto final
    return Game(
        id=db_game.game_id,
        name=db_game.game_name,
        min_players=db_game.min_players,
        max_players=db_game.max_players,
        host=host_info,
        status=db_game.game_status,
        players=players_in_game,
        draft=draft,
        deck=deck,
        discard_pile=discard_pile,
        current_turn_player_id=db_game.current_player,
        action_state=action_state_enum,
        action_initiator_id=db_game.action_initiator_id,
        prompted_player_id=db_game.prompted_player_id,
        pending_saga=db_game.pending_saga,
    )

# --- Mapper Pending Actions ---

def map_pending_action_orm_to_dto(orm_obj: PendingActionTable) -> PendingAction:
    """Mapea PendingActionTable a PendingAction DTO, incluyendo las cartas asociadas."""
    # SQLAlchemy ya ha hecho el trabajo duro. Solo mapeamos las cartas.
    mapped_cards = [map_card_orm_to_dto(card_orm) for card_orm in orm_obj.cards]
    
    return PendingAction(
        id=orm_obj.id,
        game_id=orm_obj.game_id,
        player_id=orm_obj.player_id,
        action_type=orm_obj.action_type,
        cards=mapped_cards,
        target_player_id=orm_obj.target_player_id,
        target_secret_id=orm_obj.target_secret_id,
        target_card_id=orm_obj.target_card_id,
        target_set_id=orm_obj.target_set_id,
        responses_count=orm_obj.responses_count,
        nsf_count=orm_obj.nsf_count,
        last_action_player_id=orm_obj.last_action_player_id,
    )
