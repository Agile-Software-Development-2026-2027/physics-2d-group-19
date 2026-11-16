from io import BytesIO

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from app.schemas.params import TrackingParams
from app.services.preview import BACKGROUND_SAMPLE_SIZE, CIRCLE_COLOR, detect_frame, render_png
from tests.core.test_smoke import N_FRAMES, SIZE, START_POSITIONS

# Lab defaults, except minmass, lowered for the small synthetic cells (as in test_smoke.py)
PARAMS = TrackingParams(minmass=50)


@pytest.fixture
def cell_frames():
    # Same synthetic video as test_smoke.py: three cells moving one pixel per frame.
    yy, xx = np.mgrid[:SIZE, :SIZE]
    out = np.zeros((N_FRAMES, SIZE, SIZE), dtype=np.float32)
    for t in range(N_FRAMES):
        for y0, x0 in START_POSITIONS:
            out[t] += 200 * np.exp(-((yy - y0) ** 2 + (xx - x0 - t) ** 2) / (2 * 1.5**2))
    return out


def _fake_video(monkeypatch, frames, n_frames=None):
    """Replaces the video reading; returns the list of frame indices read."""
    if n_frames is None:
        n_frames = len(frames)
    reads = []

    def fake_read(path, indices, channel):
        reads.append(indices)
        # The modulo lets the short synthetic video stand in for a longer one.
        return frames[np.asarray(indices) % len(frames)]

    monkeypatch.setattr("app.services.preview._frame_count", lambda path: n_frames)
    monkeypatch.setattr("app.services.preview._read_frames", fake_read)
    return reads


def test_finds_the_three_cells(tmp_path, monkeypatch, cell_frames):
    _fake_video(monkeypatch, cell_frames)

    image, features = detect_frame(tmp_path / "video.avi", 5, PARAMS)

    assert len(features) == len(START_POSITIONS)
    np.testing.assert_array_equal(image, cell_frames[5])


@pytest.mark.parametrize("frame", [-1, N_FRAMES])
def test_frame_outside_the_video(tmp_path, monkeypatch, cell_frames, frame):
    reads = _fake_video(monkeypatch, cell_frames)

    with pytest.raises(ValueError, match="outside the video"):
        detect_frame(tmp_path / "video.avi", frame, PARAMS)

    assert reads == []


@pytest.mark.parametrize("method", ["mean", "median"])
def test_background_methods(tmp_path, monkeypatch, cell_frames, method):
    _fake_video(monkeypatch, cell_frames)
    params = TrackingParams(minmass=50, background_method=method)

    _, features = detect_frame(tmp_path / "video.avi", 5, params)

    assert len(features) == len(START_POSITIONS)


def test_reads_only_a_sample(tmp_path, monkeypatch, cell_frames):
    reads = _fake_video(monkeypatch, cell_frames, n_frames=10_000)

    detect_frame(tmp_path / "video.avi", 1234, PARAMS)

    assert len(reads) == 1
    assert len(reads[0]) <= BACKGROUND_SAMPLE_SIZE + 1
    assert 1234 in reads[0]


def test_without_background_subtraction(tmp_path, monkeypatch, cell_frames):
    reads = _fake_video(monkeypatch, cell_frames)
    params = TrackingParams(minmass=50, background_subtraction=False)

    _, features = detect_frame(tmp_path / "video.avi", 5, params)

    assert reads == [[5]]
    assert len(features) == len(START_POSITIONS)


def _open_png(png):
    """Reads the PNG back as an array of RGB pixels, shaped (rows, columns, 3)."""
    image = Image.open(BytesIO(png))
    assert image.format == "PNG"
    return np.asarray(image.convert("RGB"))


def test_png_has_the_frame_size():
    frame = np.full((40, 60), 100, dtype=np.float32)
    positions = pd.DataFrame({"x": [30.0], "y": [20.0]})

    pixels = _open_png(render_png(frame, positions, 5))

    assert pixels.shape == (40, 60, 3)


def test_no_cells_leaves_the_frame_unchanged():
    frame = np.full((40, 60), 100, dtype=np.float32)
    positions = pd.DataFrame(columns=["x", "y"], dtype=float)

    pixels = _open_png(render_png(frame, positions, 5))

    assert (pixels == 100).all()


def test_draws_a_circle_around_the_cell():
    frame = np.full((40, 60), 100, dtype=np.float32)
    positions = pd.DataFrame({"x": [30.0], "y": [20.0]})

    pixels = _open_png(render_png(frame, positions, 5))

    rows, cols = np.nonzero((pixels == CIRCLE_COLOR).all(axis=-1))
    assert len(rows) > 0
    # Every red pixel lies on the circle of radius 5 around the cell (1 px of rounding).
    distance = np.hypot(rows - 20, cols - 30)
    assert (np.abs(distance - 5) <= 1).all()
    # The cell itself stays visible.
    assert tuple(pixels[20, 30]) == (100, 100, 100)


def test_renders_the_detected_cells(tmp_path, monkeypatch, cell_frames):
    _fake_video(monkeypatch, cell_frames)
    image, features = detect_frame(tmp_path / "video.avi", 5, PARAMS)

    pixels = _open_png(render_png(image, features, PARAMS.diameter))

    assert pixels.shape == (SIZE, SIZE, 3)
    assert (pixels == CIRCLE_COLOR).all(axis=-1).any()
