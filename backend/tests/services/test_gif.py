# Unit and integration tests for trajectory GIF service

import json
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import tifffile
from PIL import Image

from app.services.gif import make_gif
from app.services.jobs_store import create_job, job_dir, read_status
from app.services.pipeline import run_job


# Generates a synthetic 2D TIFF illumination image with a Gaussian ring centered in the frame.
def _write_synthetic_illumination(path: Path, size: int = 120) -> None:
    yy, xx = np.indices((size, size))
    centre = size / 2.0
    r = np.hypot(xx - centre, yy - centre)
    # Intensity peaks at radius 20 pixels with standard deviation 6 pixels
    ring = np.exp(-((r - 20.0) ** 2) / (2 * 6.0**2)) * 255.0
    tifffile.imwrite(path, ring.astype(np.uint16))


# Generates synthetic tracks where particles start outside the ring (first half of frames)
# and move inside the illumination ring (second half), allowing verification of concentration growth
def _write_synthetic_trajectories(path: Path, n_frames: int = 20) -> None:
    rows = []
    for f in range(n_frames):
        inside = f >= (n_frames // 2)
        base_x, base_y = (60.0, 60.0) if inside else (5.0, 5.0)
        for pid in range(4):
            rows.append(
                {
                    "frame": f,
                    "particle": pid,
                    "x": base_x + pid * 0.5,
                    "y": base_y + pid * 0.5,
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False)


# Generator mimicking streaming video frame decoding without requiring a real .avi file on disk
def _synthetic_frame_reader(n_frames: int, size: int = 120):
    def _reader(_video_path: Path | None, step: int):
        for idx in range(0, n_frames, step):
            yield idx, np.full((size, size), 100, dtype=np.uint8)

    return _reader


# Test 1: Verify valid GIF file, sampled PNG frames, and concentration increase
def test_make_gif_creates_valid_gif_frames_and_concentration(tmp_path: Path) -> None:
    illum_path = tmp_path / "illumination14.tiff"
    traj_path = tmp_path / "tAlgae49.txt"
    video_path = tmp_path / "tAlgae49.avi"
    video_path.write_bytes(b"fake-avi")
    out_dir = tmp_path / "gif"

    _write_synthetic_illumination(illum_path, size=120)
    _write_synthetic_trajectories(traj_path, n_frames=20)

    gif_path = make_gif(
        video_path=video_path,
        trajectories_txt=traj_path,
        illumination=illum_path,
        out_dir=out_dir,
        step=5,
        disc_radius=30.0,
        pix=1.0,
        dt=0.1,
        power_uw=180.0,
        frame_reader=_synthetic_frame_reader(20, size=120),
    )

    # 1. Verify animated GIF file structure and frame count (20 frames with step 5 = 4 frames)
    assert gif_path == out_dir / "trajectories.gif"
    assert gif_path.exists()
    with Image.open(gif_path) as im:
        assert im.format == "GIF"
        assert im.n_frames == 4

    # 2. Verify frames.json metadata keys and concentration curve
    frames_meta = json.loads((out_dir / "frames.json").read_text(encoding="utf-8"))
    assert frames_meta["count"] == 4
    assert len(frames_meta["concentration"]) == 4
    assert len(frames_meta["cells_in_ring"]) == 4
    # Concentration must increase when synthetic particles migrate into the ring
    assert frames_meta["concentration"][-1] > frames_meta["concentration"][0]

    # 3. Verify each sampled PNG frame exists and is a valid image
    for i in range(4):
        png = out_dir / "frames" / f"{i}.png"
        assert png.exists()
        with Image.open(png) as frame_im:
            assert frame_im.format == "PNG"


# Test 2: Verify memory usage remains bounded when source frames increase 10x
def test_make_gif_memory_remains_bounded_with_more_frames(tmp_path: Path) -> None:
    illum_path = tmp_path / "illumination14.tiff"
    _write_synthetic_illumination(illum_path, size=100)

    peaks: list[int] = []
    # Compare peak RAM usage between 20 frames and 200 frames
    for total_frames in (20, 200):
        traj_path = tmp_path / f"traj_{total_frames}.txt"
        _write_synthetic_trajectories(traj_path, n_frames=total_frames)
        out_dir = tmp_path / f"gif_{total_frames}"

        tracemalloc.start()
        make_gif(
            video_path=tmp_path / "missing.avi",
            trajectories_txt=traj_path,
            illumination=illum_path,
            out_dir=out_dir,
            step=total_frames // 4,
            disc_radius=30.0,
            pix=1.0,
            frame_reader=_synthetic_frame_reader(total_frames, size=100),
        )
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peaks.append(peak)

    # A 10x increase in frames must not cause a 10x jump in memory allocation
    assert peaks[1] < peaks[0] * 2.5


# Test 3: Verify pipeline integration and error isolation in run_job
def test_run_job_calls_make_gif_and_isolates_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job_id = create_job(tmp_path, exp_id=49)
    base = job_dir(tmp_path, job_id)
    (base / "parameters" / "config.json").write_text(
        json.dumps({"make_gif": True, "params": {"analysis": {"disc_radius": 140.0}}}),
        encoding="utf-8",
    )
    (base / "input" / "tAlgae49.txt").write_text("frame,particle,x,y\n", encoding="utf-8")
    (base / "input" / "illumination14.tiff").write_bytes(b"fake")
    (base / "input" / "talgae_settings.txt").write_text(
        "49\t1\t14\t180\t1.041667\t1\t0\t0\t0\t0\n50\t0\t0\t0\t0\t0\t0\t0\t0\t0\n",
        encoding="utf-8",
    )

    # Mock tracking/analysis/plots stages to isolate GIF testing
    monkeypatch.setattr("app.services.pipeline.run_analysis", lambda *a, **kw: object())
    monkeypatch.setattr("app.services.pipeline.save_legacy_txt", lambda *a, **kw: None)
    monkeypatch.setattr("app.services.pipeline.generate_plots", lambda *a, **kw: {"flux": "ok"})

    # Simulate GIF failure
    def _boom(**_kwargs):
        raise RuntimeError("GIF rendering failed")

    monkeypatch.setattr("app.services.pipeline.make_gif", _boom)

    run_job(tmp_path, job_id)
    status = read_status(tmp_path, job_id)
    # Job status must remain 'done' even if GIF fails, with error message stored in status
    assert status["status"] == "done"
    assert status["gif_error"] == "GIF rendering failed"


# Test 4: Verify run_job does not invoke make_gif when make_gif is false
def test_run_job_skips_make_gif_when_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job_id = create_job(tmp_path, exp_id=49)
    base = job_dir(tmp_path, job_id)
    (base / "parameters" / "config.json").write_text(
        json.dumps({"make_gif": False}), encoding="utf-8"
    )
    (base / "input" / "tAlgae49.txt").write_text("frame,particle,x,y\n", encoding="utf-8")
    (base / "input" / "talgae_settings.txt").write_text(
        "49\t1\t14\t180\t1.041667\t1\t0\t0\t0\t0\n50\t0\t0\t0\t0\t0\t0\t0\t0\t0\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("app.services.pipeline.run_analysis", lambda *a, **kw: object())
    monkeypatch.setattr("app.services.pipeline.save_legacy_txt", lambda *a, **kw: None)
    monkeypatch.setattr("app.services.pipeline.generate_plots", lambda *a, **kw: {"flux": "ok"})

    called = False

    def _unexpected(**_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("app.services.pipeline.make_gif", _unexpected)

    run_job(tmp_path, job_id)
    status = read_status(tmp_path, job_id)
    assert status["status"] == "done"
    assert not called
    assert "gif_error" not in status


# Test 5: Verify input validation in make_gif (step < 1, missing trajectories, missing illumination)
def test_make_gif_validates_inputs(tmp_path: Path) -> None:
    valid_file = tmp_path / "valid.txt"
    valid_file.write_text("data", encoding="utf-8")
    missing_file = tmp_path / "missing.txt"
    out_dir = tmp_path / "out"

    # 1. Step must be >= 1
    with pytest.raises(ValueError, match="step must be >= 1"):
        make_gif(valid_file, valid_file, valid_file, out_dir, step=0)

    # 2. Missing trajectories file raises FileNotFoundError
    with pytest.raises(FileNotFoundError, match="Trajectories file not found"):
        make_gif(valid_file, missing_file, valid_file, out_dir, step=1)

    # 3. Missing illumination file raises FileNotFoundError
    with pytest.raises(FileNotFoundError, match="Illumination file not found"):
        make_gif(valid_file, valid_file, missing_file, out_dir, step=1)


# Test 6: Verify iter_video_frames and default reader behavior without injecting frame_reader
def test_iter_video_frames_and_default_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services.gif import iter_video_frames

    # When video path is None or does not exist, generator yields nothing
    assert list(iter_video_frames(None, 5)) == []
    assert list(iter_video_frames(tmp_path / "non_existent.avi", 5)) == []

    # Mock PyAV container decoding to test frame extraction without a real video file
    class DummyFrame:
        def to_ndarray(self, format="gray"):
            return np.full((50, 50), 120, dtype=np.uint8)

    class DummyContainer:
        def __init__(self):
            self.streams = type("Streams", (), {"video": [object()]})()

        def decode(self, _stream):
            return [DummyFrame(), DummyFrame(), DummyFrame()]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr("av.open", lambda *a, **kw: DummyContainer())

    fake_video = tmp_path / "sample.avi"
    fake_video.write_bytes(b"dummy-avi")

    # Verify iter_video_frames samples every `step` frames
    frames = list(iter_video_frames(fake_video, step=2))
    assert len(frames) == 2
    assert frames[0][0] == 0 and frames[1][0] == 2

    # Verify make_gif executes with frame_reader=None (using iter_video_frames naturally)
    illum_path = tmp_path / "illum.tiff"
    traj_path = tmp_path / "traj.txt"
    _write_synthetic_illumination(illum_path, size=50)
    _write_synthetic_trajectories(traj_path, n_frames=3)

    gif_path = make_gif(
        video_path=fake_video,
        trajectories_txt=traj_path,
        illumination=illum_path,
        out_dir=tmp_path / "gif_default",
        step=1,
    )
    assert gif_path.exists()
