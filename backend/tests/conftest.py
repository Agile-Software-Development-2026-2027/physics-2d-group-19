import os

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
