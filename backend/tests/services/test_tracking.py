import av
import numpy as np
import pytest

from app.services.jobs_store import create_job, job_dir, read_status
from app.services.pipeline import run_job
from app.services.tracking import VIDEO_UNREADABLE, check_video, run_tracking
from core.clam_pipeline.io import load_trajectories_txt
from tests.core.test_smoke import N_FRAMES, SIZE, START_POSITIONS, TRACKING_CONFIG


def _fake_video(monkeypatch, frames):
    monkeypatch.setattr("app.services.tracking.check_video", lambda path: (len(frames), 10.0))
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


def _write_avi(path, n_frames=30, fps=10):
    """A small lossless .avi, like the lab's videos but synthetic."""
    with av.open(str(path), "w") as container:
        stream = container.add_stream("ffv1", rate=fps)
        stream.width, stream.height, stream.pix_fmt = 64, 48, "bgr0"
        for i in range(n_frames):
            image = np.full((48, 64, 3), i * 5, dtype=np.uint8)
            container.mux(stream.encode(av.VideoFrame.from_ndarray(image, format="rgb24")))
        container.mux(stream.encode())
    return path


def test_check_video_reads_frames_and_fps(tmp_path):
    # Same count as load_video_to_ram, which skips the last frame like the lab's code.
    assert check_video(_write_avi(tmp_path / "ok.avi")) == (29, 10.0)


@pytest.mark.parametrize("content", [b"", b"this is not a video"])
def test_check_video_rejects_unreadable_files(tmp_path, content):
    path = tmp_path / "bad.avi"
    path.write_bytes(content)
    with pytest.raises(ValueError, match=VIDEO_UNREADABLE):
        check_video(path)


def test_run_tracking_on_a_video_corrupted_further_on(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.tracking.check_video", lambda path: (10, 10.0))

    def broken_read(path, channel):
        raise OSError("decoder error at frame 7")

    monkeypatch.setattr("app.services.tracking.load_video_to_ram", broken_read)
    with pytest.raises(ValueError, match=VIDEO_UNREADABLE):
        run_tracking(tmp_path / "tAlgae49.avi", tmp_path / "out", TRACKING_CONFIG)


def test_job_with_unreadable_video_ends_with_a_clear_error(tmp_path):
    job_id = create_job(tmp_path, 49)
    (job_dir(tmp_path, job_id) / "input" / "tAlgae49.avi").write_text("this is not a video")

    run_job(tmp_path, job_id)

    status = read_status(tmp_path, job_id)
    assert status["status"] == "error"
    assert status["error"] == VIDEO_UNREADABLE
