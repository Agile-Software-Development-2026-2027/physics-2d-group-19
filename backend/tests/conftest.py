import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

# The core calls plt.show(): draw in memory so tests never open a window.
os.environ.setdefault("MPLBACKEND", "Agg")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c
    get_settings.cache_clear()


EXP49_FIXTURES = Path(__file__).parent / "fixtures" / "exp49"


@pytest.fixture(scope="session")
def exp49_outputs():
    """Analysis of experiment 49 with the lab parameters, run once for the whole session.

    The analysis takes several seconds (much more under coverage), so every test that
    only needs its outputs shares this result. Tests must read it, never modify it.
    """
    from app.services.analysis import run_analysis

    return run_analysis(
        49,
        EXP49_FIXTURES / "talgae_settings.txt",
        EXP49_FIXTURES / "tAlgae49.txt",
        EXP49_FIXTURES,
    )
