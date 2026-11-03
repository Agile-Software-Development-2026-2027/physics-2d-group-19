import numpy as np
import pytest

from app.services.tracking import run_tracking
from core.clam_pipeline.io import load_trajectories_txt
from tests.core.test_smoke import N_FRAMES, SIZE, START_POSITIONS, TRACKING_CONFIG


def _fake_video(monkeypatch, frames):
    monkeypatch.setattr(
        "app.services.tracking.load_video_to_ram", lambda path, channel: (frames, 10.0, 1.0)
    )


@pytest.fixture
def cell_frames():
    # Same synthetic video as test_smoke.py: three cells moving one pixel per frame.
    yy, xx = np.mgrid[:SIZE, :SIZE]
    out = np.zeros((N_FRAMES, SIZE, SIZE), dtype=np.float32)
    for t in range(N_FRAMES):
        for y0, x0 in START_POSITIONS:
            out[t] += 200 * np.exp(-((yy - y0) ** 2 + (xx - x0 - t) ** 2) / (2 * 1.5**2))
    return out


def test_run_tracking_on_synthetic_frames(tmp_path, monkeypatch, cell_frames):
    _fake_video(monkeypatch, cell_frames)
    txt = run_tracking(tmp_path / "tAlgae49.avi", tmp_path / "out", TRACKING_CONFIG)
    assert txt == tmp_path / "out" / "tAlgae49.txt"
    trajectories = load_trajectories_txt(txt)
    assert trajectories["tag"].nunique() == len(START_POSITIONS)
    assert len(trajectories) == N_FRAMES * len(START_POSITIONS)


@pytest.mark.filterwarnings("ignore:Image is completely black")
def test_no_cells(tmp_path, monkeypatch):
    _fake_video(monkeypatch, np.zeros((N_FRAMES, SIZE, SIZE), dtype=np.float32))
    with pytest.raises(ValueError, match="No cells found in the video"):
        run_tracking(tmp_path / "tAlgae49.avi", tmp_path / "out", TRACKING_CONFIG)
