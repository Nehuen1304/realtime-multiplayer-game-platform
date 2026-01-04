from fastapi import APIRouter, Body, Path, status, Depends
from ...game.game_manager import GameManager
from ...game.services.game_state_service import GameStateService
from ...dependencies.dependencies import (
    get_game_manager,
    get_game_state_service,
)

from ...api.schemas import (
    CreateGameRequest,
    CreateGameResponse,
    LeaveGameRequest,
    LeaveGameResponse,
    ListGamesResponse,
    JoinGameRequest,
    JoinGameResponse,
    StartGameResponse,
    SubmitTradeChoiceRequest,
    PlayerHandResponse,
    PlayCardRequest,
    GameStateResponse,
    PlayerActionRequest,
    RevealSecretRequest,
    DiscardCardRequest,
    DrawCardResponse,
    FinishTurnResponse,
    PlayerSecretsResponse,
    GeneralActionResponse,
    DrawCardRequest,
    ConsultDeckSizeResponse,
    VoteRequest,
    ExchangeCardRequest,
)

from ...domain.models import PlayerInGame
from typing import List

# Router para el módulo de partidas
router = APIRouter(prefix="/games", tags=["Games"])


# --- Endpoints del Lobby y Creación de Partidas ---
@router.post(
    "", response_model=CreateGameResponse, status_code=status.HTTP_201_CREATED
)
async def create_game(
    request: CreateGameRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Crea una nueva partida (en estado LOBBY)."""
    return await game_manager.create_game(request)


@router.get("", response_model=ListGamesResponse)
def list_games(game_manager: GameManager = Depends(get_game_manager)):
    """Lista todas las partidas que están en estado LOBBY."""
    return game_manager.list_games()


@router.post("/{game_id}/join", response_model=JoinGameResponse)
async def join_game(
    game_id: int = Path(..., description="ID de la partida a unirse"),
    request: JoinGameRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Permite a un jugador unirse a una partida existente."""
    request.game_id = game_id
    return await game_manager.join_game(request)


@router.post("/{game_id}/leave", response_model=LeaveGameResponse)
async def leave_game(
    game_id: int = Path(..., description="ID de la partida a abandonar"),
    request: LeaveGameRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Permite a un jugador abandonar una partida."""
    request.game_id = game_id
    return await game_manager.leave_game(request)


@router.post("/{game_id}/start", response_model=StartGameResponse)
async def start_game(
    game_id: int = Path(..., description="ID de la partida a iniciar"),
    request: PlayerActionRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Inicia una partida que está en el lobby (solo el host puede hacerlo)."""
    request.game_id = game_id
    return await game_manager.start_game(request)


# --- Endpoints de Información Durante la Partida (GET) ---
@router.get("/{game_id}", response_model=GameStateResponse)
def get_game_state(
    game_id: int = Path(..., description="ID de la partida"),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Obtiene el estado público y completo de una partida."""
    return game_manager.get_game_state(game_id)


@router.get(
    "/{game_id}/players/{player_id}/hand", response_model=PlayerHandResponse
)
def get_player_hand(
    game_id: int = Path(...),
    player_id: int = Path(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Obtiene las cartas en la mano de un jugador específico."""
    request = PlayerActionRequest(game_id=game_id, player_id=player_id)
    return game_manager.get_player_hand(request)


@router.get(
    "/{game_id}/players/{player_id}/secrets",
    response_model=PlayerSecretsResponse,
)
def get_player_secrets(
    game_id: int = Path(...),
    player_id: int = Path(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Obtiene las cartas de secreto de un jugador."""
    request = PlayerActionRequest(game_id=game_id, player_id=player_id)
    return game_manager.get_player_secrets(request)


@router.get(
    "/{game_id}/size_deck",
    response_model=ConsultDeckSizeResponse,
)
def get_size_deck(
    game_id: int = Path(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Obtiene el tamaño del mazo de la partida."""
    return game_manager.get_size_deck(game_id)


@router.get(
    "/{game_id}/players/sorted",
    response_model=List[PlayerInGame],
)
async def get_sorted_players_in_game(
    game_id: int = Path(...),
    game_state_service: GameStateService = Depends(get_game_state_service),
):
    """Devuelve los jugadores de la partida ordenados por turn order."""
    return await game_state_service.get_sorted_players(game_id)


# --- Endpoints de Acciones Durante la Partida (POST) ---
@router.post("/{game_id}/actions/discard", response_model=GeneralActionResponse)
async def discard_card(
    game_id: int = Path(...),
    request: DiscardCardRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Un jugador descarta una carta de su mano."""
    request.game_id = game_id
    return await game_manager.discard_card(request)


@router.post("/{game_id}/actions/draw", response_model=DrawCardResponse)
async def draw_card(
    game_id: int = Path(...),
    request: DrawCardRequest = Body(...),  # ¡¡¡LO CAMBIAMOS ACÁ!!!
    game_manager: GameManager = Depends(get_game_manager),
):
    """El jugador en turno roba una carta del mazo O del draft."""
    request.game_id = game_id  # Sobreescribimos por seguridad
    return await game_manager.draw_card(request)


@router.post(
    "/{game_id}/actions/finish-turn", response_model=FinishTurnResponse
)
async def finish_turn(
    game_id: int = Path(...),
    request: PlayerActionRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """El jugador actual finaliza su turno."""
    request.game_id = game_id
    return await game_manager.finish_turn(request)


@router.post("/{game_id}/actions/play", response_model=GeneralActionResponse)
async def play_card(
    game_id: int = Path(...),
    request: PlayCardRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Un jugador juega una carta de su mano, lo que puede iniciar una reacción NSF."""
    request.game_id = game_id
    # Delega al GameManager, quien decidirá si es un NSF o una ejecución inmediata
    return await game_manager.play_card(request)


@router.post(
    "/{game_id}/actions/reveal-secret",
    response_model=GeneralActionResponse,
)
async def reveal_secret(
    game_id: int = Path(...),
    request: RevealSecretRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Un jugador revela una de sus cartas de secreto."""
    request.game_id = game_id
    return await game_manager.reveal_secret(request)


@router.post(
    "/{game_id}/actions/vote",
    response_model=GeneralActionResponse,
    summary="Emitir un voto para Point Your Suspicions",
)
async def submit_vote(
    game_id: int = Path(...),
    request: VoteRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Nuevo endpoint simplificado para enviar votos durante Point Your Suspicions."""
    request.game_id = game_id
    return await game_manager.submit_vote(request)


@router.post(
    "/{game_id}/actions/donate-card",
    response_model=GeneralActionResponse,
    summary="Donar una carta a otro jugador",
)
async def donate_card_to_player(
    game_id: int = Path(...),
    request: SubmitTradeChoiceRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Un jugador dona una carta a otro jugador."""
    request.game_id = game_id
    return await game_manager.submit_trade_choice(request)


@router.post(
    "/{game_id}/actions/exchange-card",
    response_model=GeneralActionResponse,
)
async def exchange_card(
    game_id: int = Path(...),
    request: ExchangeCardRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """El jugador receptor envía el id de la carta que desea recibir en un intercambio."""
    request.game_id = game_id
    return await game_manager.exchange_card(request)
@router.post(
    "/{game_id}/actions/play-nsf",
    response_model=GeneralActionResponse,
)
async def play_nsf(
    game_id: int = Path(...),
    request: PlayCardRequest = Body(...),
    game_manager: GameManager = Depends(get_game_manager),
):
    """Un jugador juega (o no) una carta NSF como reacción a una jugada cancelable."""
    request.game_id = game_id
    return await game_manager.play_nsf(request)
