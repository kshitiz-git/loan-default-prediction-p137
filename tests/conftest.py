import pytest
from src.api import store


@pytest.fixture(autouse=True)
def temporary_log_db(tmp_path, monkeypatch):
    """Every test writes predictions to its own throw-away SQLite file, never to logs/predictions.db."""
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "predictions_test.db")
