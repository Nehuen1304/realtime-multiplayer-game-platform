import pytest
from datetime import date
from unittest.mock import Mock

from app.api.schemas import CreatePlayerRequest, CreatePlayerResponse
from app.domain.enums import Avatar
from app.game.services.player_service import PlayerService
from app.game.exceptions import InvalidAction, InternalGameError


# ═══════════════════════════════════════════════════════════════════
# 🧪 TESTS PARA PlayerService.create_player()
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def player_service(mock_queries, mock_commands, mock_validator, mock_notificator):
    """Factory fixture para crear una instancia de PlayerService con mocks."""
    return PlayerService(
        queries=mock_queries,
        commands=mock_commands,
        validator=mock_validator,
        notifier=mock_notificator,
    )


class TestPlayerServiceCreatePlayer:
    """Suite de tests para el método create_player del PlayerService."""

    def test_create_player_success_with_explicit_avatar(self, player_service, mock_commands):
        """Debe crear un jugador exitosamente con un avatar explícito."""
        # Arrange
        mock_commands.create_player.return_value = 42
        request = CreatePlayerRequest(
            name="Juan Pérez",
            birth_date=date(1990, 5, 15),
            avatar=Avatar.DEFAULT,
        )

        # Act
        response = player_service.create_player(request)

        # Assert
        assert isinstance(response, CreatePlayerResponse)
        assert response.player_id == 42
        mock_commands.create_player.assert_called_once_with(
            name="Juan Pérez",
            birth_date=date(1990, 5, 15),
            avatar=Avatar.DEFAULT,
        )

    def test_create_player_success_with_default_avatar(self, player_service, mock_commands):
        """Debe usar avatar DEFAULT si no se proporciona uno."""
        # Arrange
        mock_commands.create_player.return_value = 50
        request = CreatePlayerRequest(
            name="María López",
            birth_date=date(1985, 10, 20),
            avatar=None,
        )

        # Act
        response = player_service.create_player(request)

        # Assert
        assert response.player_id == 50
        mock_commands.create_player.assert_called_once_with(
            name="María López",
            birth_date=date(1985, 10, 20),
            avatar=Avatar.DEFAULT,
        )

    def test_create_player_trims_whitespace(self, player_service, mock_commands):
        """Debe recortar espacios en blanco del nombre."""
        # Arrange
        mock_commands.create_player.return_value = 33
        request = CreatePlayerRequest(
            name="  Carlos Gómez  ",
            birth_date=date(1995, 3, 8),
        )

        # Act
        response = player_service.create_player(request)

        # Assert
        assert response.player_id == 33
        mock_commands.create_player.assert_called_once_with(
            name="Carlos Gómez",
            birth_date=date(1995, 3, 8),
            avatar=Avatar.DEFAULT,
        )

    def test_create_player_empty_name_raises_invalid_action(self, player_service):
        """Debe lanzar InvalidAction si el nombre está vacío o solo espacios."""
        # Arrange
        request = CreatePlayerRequest(
            name="   ",
            birth_date=date(2000, 1, 1),
        )

        # Act & Assert
        with pytest.raises(InvalidAction) as exc_info:
            player_service.create_player(request)

        assert "no puede estar vacío" in str(exc_info.value)

    def test_create_player_returns_none_raises_internal_game_error(
        self, player_service, mock_commands
    ):
        """Debe lanzar InternalGameError si el comando devuelve None."""
        # Arrange
        mock_commands.create_player.return_value = None
        request = CreatePlayerRequest(
            name="Jugador Repetido",
            birth_date=date(1980, 7, 25),
        )

        # Act & Assert
        with pytest.raises(InternalGameError) as exc_info:
            player_service.create_player(request)

        assert "Jugador Repetido" in str(exc_info.value)

    def test_create_player_multiple_avatars(
        self, player_service, mock_commands
    ):
        """Debe soportar avatares disponibles."""
        # Arrange - Solo Avatar.DEFAULT está disponible actualmente
        mock_commands.create_player.return_value = 100
        request = CreatePlayerRequest(
            name="Player_0",
            birth_date=date(2000, 1, 1),
            avatar=Avatar.DEFAULT,
        )

        # Act
        response = player_service.create_player(request)

        # Assert
        assert response.player_id == 100

    def test_create_player_different_birth_dates(self, player_service, mock_commands):
        """Debe aceptar diferentes fechas de nacimiento."""
        # Arrange
        test_dates = [
            date(1950, 1, 1),
            date(2000, 6, 15),
            date(2023, 12, 31),
        ]

        for idx, birth_date in enumerate(test_dates):
            mock_commands.create_player.return_value = 200 + idx
            request = CreatePlayerRequest(
                name=f"Birth_Date_Player_{idx}",
                birth_date=birth_date,
            )

            # Act
            response = player_service.create_player(request)

            # Assert
            assert response.player_id == 200 + idx
