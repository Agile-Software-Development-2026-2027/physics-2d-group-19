from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.config import Settings, get_settings
from app.main import app
from app.services.jobs_store import read_status

client = TestClient(app)
FIX = Path(__file__).parent / "fixtures" / "exp49"


@pytest.fixture
def auth_client(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    app.dependency_overrides[get_settings] = lambda: Settings(data_dir=data_dir)
    app.dependency_overrides[get_current_user] = lambda: "operator"

    yield client

    app.dependency_overrides.clear()


def test_create_job(auth_client, monkeypatch):
    calls = []
    # Intercept run_job inside app.api.jobs module
    monkeypatch.setattr("app.api.jobs.run_job", lambda d, j: calls.append(j))

    files = {
        "trajectories": ("whatever.txt", (FIX / "tAlgae49.txt").read_bytes()),
        "illumination": ("ill.tiff", (FIX / "illumination14.tiff").read_bytes()),
    }

    r = auth_client.post("/api/jobs", data={"exp_id": "49"}, files=files)
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    # Assert background task was registered but not executed
    assert calls == [job_id]

    data_dir = get_settings().data_dir
    inp = data_dir / "jobs" / job_id / "input"
    assert (inp / "tAlgae49.txt").exists() and (inp / "illumination14.tiff").exists()
    assert (inp / "talgae_settings.txt").exists()

    # Confirm status stays queued in status.json
    assert read_status(data_dir, job_id)["status"] == "queued"


def test_video_and_trajectories_together(auth_client):
    files = {
        "video": ("v.avi", b"x"),
        "trajectories": ("t.txt", b"x"),
        "illumination": ("i.tiff", b"x"),
    }
    assert auth_client.post("/api/jobs", files=files).status_code == 422
