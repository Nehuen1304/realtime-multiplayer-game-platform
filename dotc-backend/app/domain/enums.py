import enum

# ---------- ENUMS USADOS POR OTROS MODELS ----------


class CardLocation(enum.Enum):
    """
    Define las posibles ubicaciones de una carta dentro del juego.
    - DRAW_PILE: Mazo de robo.
    - DISCARD_PILE: Pila de descarte.
    - IN_HAND: En la mano de un jugador.
    - DRAFT: En la selección pública de cartas (draft).
    - PLAYED: Jugada sobre la mesa, visible para todos.
    """

    DRAW_PILE = "DRAW_PILE"
    DISCARD_PILE = "DISCARD_PILE"
    IN_HAND = "IN_HAND"
    DRAFT = "DRAFT"
    PLAYED = "PLAYED"


class CardType(enum.Enum):
    """
    Define todos los tipos de cartas jugables en el juego.
    - HARLEY_QUIN
    - ARIADNE_OLIVER
    - MISS_MARPLE
    - PARKER_PYNE
    - TOMMY_BERESFORD
    - LADY_EILEEN
    - TUPPENCE_BERESFORD
    - HERCULE_POIROT
    - MR_SATTERTHWAITE
    - NOT_SO_FAST
    - BLACKMAILED
    - SOCIAL_FAUX_PAS
    - DELAY_MURDERER_ESCAPE
    - POINT_YOUR_SUSPICIONS
    - DEAD_CARD_FOLLY
    - ANOTHER_VICTIM
    - LOOK_INTO_THE_ASHES
    - CARD_TRADE
    - THERE_WAS_ONE_MORE
    - EARLY_TRAIN
    - CARDS_OFF_THE_TABLE
    - MURDERER_ESCAPES
    """

    # Detectives
    HARLEY_QUIN = "Harley Quin"
    ARIADNE_OLIVER = "Ariadne Oliver"
    MISS_MARPLE = "Miss Marple"
    PARKER_PYNE = "Parker Pyne"
    TOMMY_BERESFORD = "Tommy Beresford"
    LADY_EILEEN = "Lady Eileen"
    TUPPENCE_BERESFORD = "Tuppence Beresford"
    HERCULE_POIROT = "Hercule Poirot"
    MR_SATTERTHWAITE = "Mr Satterthwaite"
    # Instant
    NOT_SO_FAST = "Not So Fast"
    # Devious
    BLACKMAILED = "Blackmailed"
    SOCIAL_FAUX_PAS = "Social Faux Pas"
    # Event
    DELAY_MURDERER_ESCAPE = "Delay the murderer's escape!"
    POINT_YOUR_SUSPICIONS = "Point your suspicions"
    DEAD_CARD_FOLLY = "Dead card folly"
    ANOTHER_VICTIM = "Another Victim"
    LOOK_INTO_THE_ASHES = "Look into the ashes"
    CARD_TRADE = "Card trade"
    THERE_WAS_ONE_MORE = "And then there was one more..."
    EARLY_TRAIN = "Early train to Paddington"
    CARDS_OFF_THE_TABLE = "Cards off the table"
    # End of game
    MURDERER_ESCAPES = "Murderer Escapes!"


class PlayerRole(enum.Enum):
    """
    Define los roles que un jugador puede tener en la partida.
    También se usa para el tipo de las cartas de secreto.
    - MURDERER: El asesino.
    - ACCOMPLICE: El cómplice del asesino.
    - INNOCENT: Un jugador inocente.
    """

    MURDERER = "MURDERER"
    ACCOMPLICE = "ACCOMPLICE"
    INNOCENT = "INNOCENT"


class Avatar(enum.Enum):
    """
    Define los avatares seleccionables por un jugador.
    Lista a ser expandida en futura release.
    - DEFAULT
    """

    DEFAULT = "default"
    # TODO: Añadir más avatares aquí


class GameStatus(enum.Enum):
    """
    Define los estados principales del ciclo de vida de una partida.
    - LOBBY: Esperando jugadores para iniciar.
    - IN_PROGRESS: Partida en curso.
    - FINISHED: Partida finalizada.
    """

    LOBBY = "LOBBY"
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"


class ResponseStatus(enum.Enum):
    """
    Define los códigos de estado para las respuestas de la API,
    permitiendo al frontend reaccionar a diferentes escenarios.
    - OK
    - ERROR
    - GAME_FULL
    - GAME_NOT_FOUND
    - WRONG_PASSWORD
    - ALREADY_JOINED
    - CARD_NOT_FOUND
    - SECRET_NOT_FOUND
    - NOT_YOUR_CARD
    - NOT_YOUR_TURN
    - INVALID_ACTION
    - GAME_ALREADY_STARTED
    - PLAYER_NOT_FOUND
    - PLAYER_NOT_IN_GAME
    - GAME_DOES_NOT_EXIST
    """

    OK = "OK"
    ERROR = "ERROR"
    GAME_FULL = "GAME_FULL"
    GAME_NOT_FOUND = "GAME_NOT_FOUND"
    WRONG_PASSWORD = "WRONG_PASSWORD"
    ALREADY_JOINED = "ALREADY_JOINED"
    CARD_NOT_FOUND = "CARD_NOT_FOUND"
    SECRET_NOT_FOUND = "SECRET_NOT_FOUND"
    NOT_YOUR_CARD = "NOT_YOUR_CARD"
    NOT_YOUR_TURN = "NOT_YOUR_TURN"
    INVALID_ACTION = "INVALID_ACTION"
    GAME_ALREADY_STARTED = "GAME_ALREADY_STARTED"
    PLAYER_NOT_FOUND = "PLAYER_NOT_FOUND"
    PLAYER_NOT_IN_GAME = "PLAYER_NOT_IN_GAME"
    GAME_DOES_NOT_EXIST = "GAME_DOES_NOT_EXIST"


class GameFlowStatus(enum.Enum):
    """Indica si el flujo del juego continúa, se pausa esperando input o terminó."""
    CONTINUE = "CONTINUE"
    PAUSED = "PAUSED"
    ENDED = "ENDED"

class GameActionState(enum.Enum):
    """
    Define los estados de acción del juego.
    - NONE
    - AWAITING_REVEAL_FOR_CHOICE: robo de carta a eleccion de la victima en proceso de juego.
    - AWAITING_REVEAL_FOR_STEAL: set Satterthwaite + Quin en proceso de juego.
    - PENDING_NSF: esperando posibles llegadas de cartas NSF.
    """

    NONE = "NONE"
    AWAITING_REVEAL_FOR_CHOICE = (
        "AWAITING_REVEAL_FOR_CHOICE"  # El Robar secreto a SU eleccion(victima)
    )
    AWAITING_REVEAL_FOR_STEAL = (
        "AWAITING_REVEAL_FOR_STEAL"  # ¡¡¡EL CASO DE SATTERTHWAITE + QUIN !!
    )
    AWAITING_SELECTION_FOR_CARD = (
        "AWAITING_SELECTION_FOR_CARD"  # El caso de look into the ashes
    )
    AWAITING_VOTES = "AWAITING_VOTES"  # Esperando votos de los jugadores
    AWAITING_CARD_DONATIONS = (
        "AWAITING_CARD_DONATIONS"  # Esperando donaciones de cartas para dcf
    )
    AWAITING_SELECTION_FOR_CARD_TRADE = (
        "AWAITING_SELECTION_FOR_CARD_TRADE"  # El caso de Card Trade
    )
    PENDING_NSF = (
        "PENDING_NSF"   # Esperando posibles llegadas de cartas NSF
    )

class PlayCardActionType(str, enum.Enum):
    """
    Define los tipos de acciones al jugar cartas.
    - PLAY_EVENT
    - FORM_NEW_SET
    - ADD_TO_EXISTING_SET
    - INSTANT
    """

    PLAY_EVENT = "PLAY_EVENT"
    FORM_NEW_SET = "FORM_NEW_SET"
    ADD_TO_EXISTING_SET = "ADD_TO_EXISTING_SET"
    INSTANT = "INSTANT"
    
