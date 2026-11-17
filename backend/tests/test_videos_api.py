import json

import pytest

from app.config import get_settings
from app.security import create_access_token
from app.services.tracking import VIDEO_UNREADABLE
from app.services.uploads import upload_path
from tests.services.test_tracking import _write_avi

URL = "/api/videos"


@pytest.fixture
def upload(client):
    headers = {"Authorization": f"Bearer {create_access_token('operator')}"}

    def send(filename, content, auth=True):
        return client.post(
            URL,
            files={"file": (filename, content, "application/octet-stream")},
            headers=headers if auth else {},
        )

    return send


@pytest.fixture
def avi_bytes(tmp_path):
    # 30 frames at 10 fps: the tracking reads 29 of them, like load_video_to_ram.
    return _write_avi(tmp_path / "source.avi").read_bytes()


def stored_uploads(data_dir):
    uploads = data_dir / "uploads"
    return sorted(p.name for p in uploads.iterdir()) if uploads.exists() else []


@pytest.mark.parametrize("filename", ["tAlgae49.avi", "UPPER.AVI"])
def test_valid_video_is_stored_and_described(upload, tmp_path, avi_bytes, filename):
    response = upload(filename, avi_bytes)

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == filename
    assert body["size_bytes"] == len(avi_bytes)
    assert body["frames"] == 29
    assert body["fps"] == 10.0
    assert stored_uploads(tmp_path) == [body["video_id"]]
    stored = upload_path(tmp_path, body["video_id"])
    assert stored.read_bytes() == avi_bytes  # received as is, never converted
    assert json.loads((stored.parent / "meta.json").read_text())["filename"] == filename


@pytest.mark.parametrize("filename", ["clip.mp4", "clip.avi.txt", "no_extension"])
def test_other_formats_are_rejected(upload, tmp_path, avi_bytes, filename):
    response = upload(filename, avi_bytes)

    assert response.status_code == 422
    assert stored_uploads(tmp_path) == []


@pytest.mark.parametrize("content", [b"", b"this is not a video"])
def test_unreadable_video_is_rejected_and_deleted(upload, tmp_path, content):
    response = upload("broken.avi", content)

    assert response.status_code == 422
    assert response.json()["detail"] == VIDEO_UNREADABLE
    assert stored_uploads(tmp_path) == []


def test_video_over_the_limit_is_rejected(upload, tmp_path, monkeypatch, avi_bytes):
    monkeypatch.setenv("APP_MAX_VIDEO_BYTES", str(len(avi_bytes) - 1))
    get_settings.cache_clear()

    response = upload("tAlgae49.avi", avi_bytes)

    assert response.status_code == 413
    assert stored_uploads(tmp_path) == []


def test_video_at_the_limit_is_accepted(upload, monkeypatch, avi_bytes):
    monkeypatch.setenv("APP_MAX_VIDEO_BYTES", str(len(avi_bytes)))
    get_settings.cache_clear()

    assert upload("tAlgae49.avi", avi_bytes).status_code == 201


def test_upload_requires_a_token(upload, tmp_path, avi_bytes):
    response = upload("tAlgae49.avi", avi_bytes, auth=False)

    assert response.status_code == 401
    assert stored_uploads(tmp_path) == []
