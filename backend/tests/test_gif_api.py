import json

import pytest

from app.api.deps import get_current_user
from app.config import get_settings
from app.services.jobs_store import create_job, job_dir, write_status

FRAMES = {"count": 2, "concentration": [1.0, 1.1], "cells_in_ring": [3, 4]}


@pytest.fixture
def auth_client(client):
    client.app.dependency_overrides[get_current_user] = lambda: "operator"
    return client


def _job_with_gif(status="done", **extra) -> str:
    """A job with the files that make_gif (24.1) writes in gif/."""
    data_dir = get_settings().data_dir
    job_id = create_job(data_dir, 49)
    gif_dir = job_dir(data_dir, job_id) / "gif"
    (gif_dir / "frames").mkdir(parents=True)
    (gif_dir / "trajectories.gif").write_bytes(b"GIF89a-fake")
    (gif_dir / "frames.json").write_text(json.dumps(FRAMES))
    for i in range(FRAMES["count"]):
        (gif_dir / "frames" / f"{i}.png").write_bytes(b"fake-png")
    write_status(data_dir, job_id, status, **extra)
    return job_id


@pytest.fixture
def gif_job(auth_client):
    return _job_with_gif()


def test_get_gif(auth_client, gif_job):
    response = auth_client.get(f"/api/jobs/{gif_job}/gif")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"
    assert response.content == b"GIF89a-fake"


def test_get_frames(auth_client, gif_job):
    response = auth_client.get(f"/api/jobs/{gif_job}/gif/frames")

    assert response.status_code == 200
    assert response.json() == FRAMES


def test_get_one_frame(auth_client, gif_job):
    response = auth_client.get(f"/api/jobs/{gif_job}/gif/frames/1.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_job_without_gif_is_404(auth_client):
    data_dir = get_settings().data_dir
    job_id = create_job(data_dir, 49)
    write_status(data_dir, job_id, "done")

    assert auth_client.get(f"/api/jobs/{job_id}/gif").status_code == 404


def test_running_job_is_409(auth_client):
    job_id = _job_with_gif(status="plots")

    assert auth_client.get(f"/api/jobs/{job_id}/gif").status_code == 409


def test_failed_gif_is_404_with_its_reason(auth_client):
    job_id = _job_with_gif(gif_error="boom")

    response = auth_client.get(f"/api/jobs/{job_id}/gif")

    assert response.status_code == 404
    assert response.json()["detail"] == "GIF generation failed"


@pytest.mark.parametrize("filename", ["2.png", "-1.png", "abc.png", "1.txt", "..%2Fstatus.json"])
def test_invalid_frame_names_are_404(auth_client, gif_job, filename):
    response = auth_client.get(f"/api/jobs/{gif_job}/gif/frames/{filename}")

    assert response.status_code == 404
