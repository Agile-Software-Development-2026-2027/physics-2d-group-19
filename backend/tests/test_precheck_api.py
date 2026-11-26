from pathlib import Path

import pytest

from app.config import get_settings
from app.security import create_access_token

URL = "/api/jobs/precheck"


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {create_access_token('operator')}"}


@pytest.fixture
def lab(client, tmp_path, monkeypatch):
    """Lab folders in tmp_path; the client already points APP_DATA_DIR to tmp_path."""
    folders = {name: tmp_path / name for name in ("videos", "traj", "illum")}
    for folder in folders.values():
        folder.mkdir()
    monkeypatch.setenv("APP_VIDEO_DIR", str(folders["videos"]))
    monkeypatch.setenv("APP_TRAJECTORIES_DIR", str(folders["traj"]))
    monkeypatch.setenv("APP_ILLUMINATION_DIR", str(folders["illum"]))
    get_settings.cache_clear()
    yield folders
    get_settings.cache_clear()


def _touch(path: Path) -> None:
    path.write_bytes(b"x")


def _check(client, headers, exp_ids):
    response = client.post(URL, json={"exp_ids": exp_ids}, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_ready_with_video_and_illumination(client, auth_headers, lab):
    _touch(lab["videos"] / "tAlgae49.avi")
    _touch(lab["illum"] / "illumination14.tiff")

    [item] = _check(client, auth_headers, [49])

    assert item == {
        "exp_id": 49,
        "registered": True,
        "no_skip": True,
        "video": "tAlgae49.avi",
        "trajectories": None,
        "illumination": "illumination14.tiff",
        "ready": True,
        "reason": None,
    }


def test_ready_with_trajectories_only(client, auth_headers, lab):
    _touch(lab["traj"] / "tAlgae49.txt")
    _touch(lab["illum"] / "illumination14.tiff")

    [item] = _check(client, auth_headers, [49])

    assert item["ready"] is True
    assert item["trajectories"] == "tAlgae49.txt"


def test_no_video_or_trajectories(client, auth_headers, lab):
    _touch(lab["illum"] / "illumination14.tiff")

    [item] = _check(client, auth_headers, [49])

    assert item["ready"] is False
    assert item["reason"] == "no video or trajectories"


def test_no_illumination(client, auth_headers, lab):
    _touch(lab["videos"] / "tAlgae49.avi")

    [item] = _check(client, auth_headers, [49])

    assert item["ready"] is False
    assert item["reason"] == "no illumination14.tiff"


def test_excluded_experiment(client, auth_headers, lab):
    # In the lab settings file, experiment 52 has no_skip = 0.
    _touch(lab["videos"] / "tAlgae52.avi")

    [item] = _check(client, auth_headers, [52])

    assert item["registered"] is True
    assert item["no_skip"] is False
    assert item["ready"] is False
    assert item["reason"] == "excluded (no_skip = 0)"


def test_not_registered(client, auth_headers, lab):
    [item] = _check(client, auth_headers, [999])

    assert item["registered"] is False
    assert item["no_skip"] is None
    assert item["ready"] is False
    assert item["reason"] == "not registered"


def test_keeps_the_order_of_the_request(client, auth_headers, lab):
    items = _check(client, auth_headers, [999, 49, 52])

    assert [item["exp_id"] for item in items] == [999, 49, 52]


def test_works_without_lab_folders(client, auth_headers):
    [item] = _check(client, auth_headers, [49])

    assert item["registered"] is True
    assert item["reason"] == "no video or trajectories"


@pytest.mark.parametrize(
    "exp_ids",
    [[], [49, 49], [-1], list(range(51))],
    ids=["empty", "duplicates", "negative", "too-many"],
)
def test_invalid_lists_are_rejected(client, auth_headers, exp_ids):
    response = client.post(URL, json={"exp_ids": exp_ids}, headers=auth_headers)

    assert response.status_code == 422


def test_requires_token(client):
    assert client.post(URL, json={"exp_ids": [49]}).status_code == 401
