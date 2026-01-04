from app.main import app
from app.dependencies.dependencies import setup_dependencies, IGameManager


def test_setup_dependencies_sets_override():
    setup_dependencies(app)
    assert IGameManager in app.dependency_overrides
