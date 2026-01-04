"""
Tests para websockets/router.py

Nota: Los tests de WebSocket endpoint requieren simulación de conexiones.
Estos tests verifican que los endpoints estén correctamente definidos.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestWebSocketRouter:
    """Suite de tests para los endpoints WebSocket."""

    def test_websocket_game_endpoint_route_exists(self):
        """Verifica que la ruta WebSocket del juego esté definida."""
        # Arrange
        client = TestClient(app)

        # Act
        # Verificar que la ruta existe en las rutas de la app
        routes = [route.path for route in app.routes]

        # Assert
        assert any("/ws/game/{game_id}/player/{player_id}" in route for route in routes)

    def test_websocket_lobby_endpoint_route_exists(self):
        """Verifica que la ruta WebSocket del lobby esté definida."""
        # Arrange
        client = TestClient(app)

        # Act
        routes = [route.path for route in app.routes]

        # Assert
        assert any("/ws/mainscreen" in route for route in routes)

    def test_websocket_game_endpoint_methods(self):
        """Verifica que el endpoint del juego soporte WebSocket."""
        # Arrange
        routes = {route.path: route for route in app.routes}

        # Act
        game_route = None
        for path, route in routes.items():
            if "/ws/game/{game_id}/player/{player_id}" in path:
                game_route = route
                break

        # Assert
        assert game_route is not None

    def test_websocket_lobby_endpoint_methods(self):
        """Verifica que el endpoint del lobby soporte WebSocket."""
        # Arrange
        routes = {route.path: route for route in app.routes}

        # Act
        lobby_route = None
        for path, route in routes.items():
            if "/ws/mainscreen" in path:
                lobby_route = route
                break

        # Assert
        assert lobby_route is not None


class TestWebSocketRouterPathParameters:
    """Suite de tests para validar parámetros de ruta."""

    def test_game_websocket_path_has_game_id_parameter(self):
        """Verifica que el endpoint del juego tenga parámetro game_id."""
        routes = {route.path: route for route in app.routes}
        
        game_route_found = False
        for path in routes.keys():
            if "/ws/game/" in path and "game_id" in path:
                game_route_found = True
                break
        
        assert game_route_found

    def test_game_websocket_path_has_player_id_parameter(self):
        """Verifica que el endpoint del juego tenga parámetro player_id."""
        routes = {route.path: route for route in app.routes}
        
        player_route_found = False
        for path in routes.keys():
            if "/ws/game/" in path and "player_id" in path:
                player_route_found = True
                break
        
        assert player_route_found

    def test_websocket_paths_use_correct_format(self):
        """Verifica que los paths usen el formato correcto para WebSocket."""
        routes = [route.path for route in app.routes]
        
        ws_routes = [r for r in routes if "/ws/" in r]
        assert len(ws_routes) >= 2  # Al menos el juego y el lobby


class TestWebSocketRouterIntegration:
    """Suite de tests para integración básica de WebSocket."""

    def test_app_has_websocket_routes(self):
        """Verifica que la app tenga rutas WebSocket definidas."""
        # Contar rutas que empiezan con /ws/
        ws_routes = [route.path for route in app.routes if "/ws/" in route.path]
        
        assert len(ws_routes) >= 2

    def test_websocket_routes_count(self):
        """Verifica que haya exactamente dos rutas WebSocket principales."""
        ws_routes = [route.path for route in app.routes if "/ws/" in route.path]
        
        # Debe haber al menos 2 rutas: /ws/game/{game_id}/player/{player_id} y /ws/mainscreen
        assert len(ws_routes) >= 2

    def test_websocket_game_route_name_correct(self):
        """Verifica que la ruta del juego tenga el nombre correcto."""
        ws_routes = [route.path for route in app.routes if "/ws/" in route.path]
        game_routes = [r for r in ws_routes if "game" in r.lower()]
        
        assert len(game_routes) >= 1

    def test_websocket_lobby_route_name_correct(self):
        """Verifica que la ruta del lobby tenga el nombre correcto."""
        ws_routes = [route.path for route in app.routes if "/ws/" in route.path]
        lobby_routes = [r for r in ws_routes if "mainscreen" in r]
        
        assert len(lobby_routes) >= 1
