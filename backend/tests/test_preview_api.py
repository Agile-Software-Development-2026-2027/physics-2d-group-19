import base64
import io

import numpy as np
import pandas as pd
import pytest

from app.config import get_settings
from app.security import create_access_token
from app.services import preview as preview_service
from app.services.uploads import save_upload


@pytest.fixture
def headers():
    return {"Authorization": f"Bearer {create_access_token('operator')}"}


@pytest.fixture
def video_id(client):
    # The content is never read: the service is replaced in every test.
    return save_upload(get_settings().data_dir, io.BytesIO(b"fake"), "clip.avi")


@pytest.fixture
def fake_service(monkeypatch):
    calls = {}

    def fake_detect(video_path, frame, params):
        calls["frame"] = frame
        calls["params"] = params
        return np.zeros((4, 6)), pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [1.0, 2.0, 3.0]})

    monkeypatch.setattr(preview_service, "detect_frame", fake_detect)
    monkeypatch.setattr(preview_service, "render_png", lambda frame, positions, diameter: b"png")
    return calls


def url(video_id, query=""):
    return f"/api/videos/{video_id}/preview{query}"


def test_preview_returns_frame_count_and_image(client, headers, video_id, fake_service):
    response = client.get(
        url(video_id, "?frame=5&diameter=7&minmass=100&background_method=median"),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "frame": 5,
        "cell_count": 3,
        "image": "data:image/png;base64," + base64.b64encode(b"png").decode(),
    }
    # The query values reached the service.
    assert fake_service["frame"] == 5
    assert fake_service["params"].diameter == 7
    assert fake_service["params"].minmass == 100
    assert fake_service["params"].background_method == "median"


def test_missing_query_values_use_lab_defaults(client, headers, video_id, fake_service):
    response = client.get(url(video_id), headers=headers)

    assert response.status_code == 200
    assert fake_service["frame"] == 0
    assert fake_service["params"].diameter == 5
    assert fake_service["params"].minmass == 180
    assert fake_service["params"].background_method == "mean"


def test_preview_without_token(client, video_id, fake_service):
    response = client.get(url(video_id))

    assert response.status_code == 401


def test_unknown_video(client, headers, fake_service):
    response = client.get(url("000000000000"), headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Video not found"


def test_even_diameter(client, headers, video_id, fake_service):
    response = client.get(url(video_id, "?diameter=6"), headers=headers)

    assert response.status_code == 422


def test_frame_outside_video(client, headers, video_id, monkeypatch):
    def out_of_range(video_path, frame, params):
        raise ValueError("Frame 999 is outside the video (0-28)")

    monkeypatch.setattr(preview_service, "detect_frame", out_of_range)

    response = client.get(url(video_id, "?frame=999"), headers=headers)

    assert response.status_code == 422
    assert response.json()["detail"] == "Frame 999 is outside the video (0-28)"
