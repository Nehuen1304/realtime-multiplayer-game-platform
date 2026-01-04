from datetime import date
from typing import List, Optional
from sqlalchemy import (
    create_engine,
    ForeignKey,
    String,
    Date,
    Boolean,
    Enum,
    JSON,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
    Mapped,
    mapped_column,
)

from ..domain.enums import (
    GameStatus,
    PlayerRole,
    CardLocation,
    CardType,
    Avatar,
    GameActionState,
    PlayCardActionType,
)

# --- (Configuración de la BD no cambia) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./sistema.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# =================================================================
# 🏛️ EL OBJETO DE ASOCIACIÓN: PlayerInGame
# =================================================================


class PlayerInGameTable(Base):
    """
    Representa la "participación" de un Jugador en una Partida.
    Guarda el estado específico de un jugador DENTRO de esa partida.
    """

    __tablename__ = "player_in_game"

    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.game_id"), primary_key=True
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id"), primary_key=True
    )

    # --- Atributos de la relación ---
    player_role: Mapped[Optional[PlayerRole]] = mapped_column(nullable=True)
    social_disgrace: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Relaciones "hacia atrás" ---
    game: Mapped["GameTable"] = relationship(back_populates="player_details")
    player: Mapped["PlayerTable"] = relationship(back_populates="game_details")


# =================================================================
# 📖 DEFINICIONES DE TABLAS PRINCIPALES (Refactorizadas)
# =================================================================


class GameTable(Base):
    """
    Partida. Ahora se relaciona con PlayerTable a través de PlayerInGame.
    """

    __tablename__ = "games"

    game_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    game_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    game_status: Mapped[GameStatus] = mapped_column(
        default=GameStatus.LOBBY, index=True
    )
    min_players: Mapped[int] = mapped_column(default=2)
    max_players: Mapped[int] = mapped_column(default=6)
    game_password: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    host_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id", use_alter=True)
    )
    current_player: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.player_id"), nullable=True
    )

    # player_prompted_to_reveal: Mapped[Optional[int]] = mapped_column(
    #     ForeignKey("players.player_id"),
    #     nullable=True,
    # )
    # --- Relaciones (Actualizadas) ---
    # Relación principal al objeto de asociación para acceder a los detalles (rol, etc.)
    player_details: Mapped[List["PlayerInGameTable"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )

    # Relación de conveniencia para acceder directamente a los objetos PlayerTable
    players: Mapped[List["PlayerTable"]] = relationship(
        secondary="player_in_game", back_populates="games", viewonly=True
    )

    host: Mapped["PlayerTable"] = relationship(foreign_keys=[host_id])
    cards: Mapped[List["CardTable"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )
    secrets: Mapped[List["SecretCardTable"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )

    # El jugador al que se le ha pedido una acción (la víctima/objetivo)
    prompted_player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.player_id"), nullable=True
    )

    # El estado de la acción que estamos esperando
    action_state: Mapped[GameActionState] = mapped_column(
        Enum(GameActionState),
        default=GameActionState.NONE,
        server_default=GameActionState.NONE.value,
        nullable=True,
    )

    # El jugador que inició la acción original (el ladrón/atacante)
    action_initiator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.player_id"), nullable=True
    )

    # Datos adicionales para la accion en curso pendiente (si aplica)
    pending_saga: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class PlayerTable(Base):
    """
    Jugador (Cuenta de Usuario). Ya NO contiene estado específico de la partida.
    """

    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_name: Mapped[str] = mapped_column(String, index=True)
    player_avatar: Mapped[Avatar] = mapped_column(default=Avatar.DEFAULT)
    player_birth_date: Mapped[date] = mapped_column(Date)

    # --- Relaciones (Actualizadas) ---
    # Relación principal al objeto de asociación
    game_details: Mapped[List["PlayerInGameTable"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )

    # Relación de conveniencia para acceder a las partidas directamente
    games: Mapped[List["GameTable"]] = relationship(
        secondary="player_in_game", back_populates="players", viewonly=True
    )

    cards: Mapped[List["CardTable"]] = relationship(back_populates="player")
    secrets: Mapped[List["SecretCardTable"]] = relationship(
        back_populates="player"
    )


# --- CardTable y SecretCardTable no necesitan cambios ---
class CardTable(Base):
    __tablename__ = "cards"
    card_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.game_id"), nullable=False
    )
    card_type: Mapped[CardType] = mapped_column()
    location: Mapped[CardLocation] = mapped_column()
    position: Mapped[Optional[int]] = mapped_column(nullable=True)
    set_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.player_id"), nullable=True
    )
    game: Mapped["GameTable"] = relationship(back_populates="cards")
    player: Mapped[Optional["PlayerTable"]] = relationship(
        back_populates="cards"
    )


class SecretCardTable(Base):
    __tablename__ = "secrets"
    secret_id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True
    )
    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id"))
    role: Mapped[Optional[PlayerRole]] = mapped_column(nullable=True)
    is_revealed: Mapped[bool] = mapped_column(Boolean, default=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"))
    game: Mapped["GameTable"] = relationship(back_populates="secrets")
    player: Mapped["PlayerTable"] = relationship(back_populates="secrets")


class PendingActionCardLinkTable(Base):
    __tablename__ = "pending_action_card_link"
    
    pending_action_id: Mapped[int] = mapped_column(
        ForeignKey("pending_actions.id", ondelete="CASCADE"), primary_key=True
    )
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.card_id"), primary_key=True
    )

class PendingActionTable(Base):
    __tablename__ = "pending_actions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id",
                                                    ondelete="CASCADE"),
                                                    index=True)

    # --- Datos de la acción original ---
    player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"))
    action_type: Mapped[PlayCardActionType] = mapped_column()

    # --- Targets de la acción ---
    target_player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.player_id"), nullable=True
    )
    target_secret_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("secrets.secret_id"), nullable=True
    )
    target_card_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cards.card_id"), nullable=True
    )
    target_set_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    # --- Seguimiento de la cadena de NSF ---
    responses_count: Mapped[int] = mapped_column(default=0)
    nsf_count: Mapped[int] = mapped_column(default=0)
    last_action_player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"))

    # --- Relación para obtener las cartas ---
    # Esto le dice a SQLAlchemy cómo unir las tablas para nosotros.
    cards: Mapped[List["CardTable"]] = relationship(
        secondary="pending_action_card_link"
    )