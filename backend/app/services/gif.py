# Service layer for trajectory GIF generation and per-frame concentration analysis.
# This service acts as the bridge between the FastAPI backend/pipeline and the core
# physics rendering routines in `core.traj_gif`.

from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterator
from pathlib import Path

import av
import numpy as np

from core.traj_gif import render_gif


# Generator that lazily decodes and yields video frames one at a time.
# Instead of loading the entire multi-gigabyte video into memory with cv2 or load_video_to_ram,
# we use PyAV (`av.open`) in streaming mode and only convert 1 frame every `step` frames
# to grayscale numpy arrays. This keeps memory usage constant (O(1) RAM).
def iter_video_frames(video_path: Path | None, step: int) -> Iterator[tuple[int, np.ndarray]]:
    """Yield (frame_index, grayscale_array) every `step` frames from a video file."""
    if video_path is None or not video_path.exists():
        return

    # Open video container and decode video stream frame by frame
    with av.open(str(video_path)) as container:
        stream = container.streams.video[0]
        for idx, frame in enumerate(container.decode(stream)):
            # Sample only frames that match our step interval (e.g. 0, 10, 20...)
            if idx % step == 0:
                yield idx, frame.to_ndarray(format="gray")


def make_gif(
    video_path: Path,
    trajectories_txt: Path,
    illumination: Path,
    out_dir: Path,
    step: int = 10,
    *,
    disc_radius: float = 130.0,
    pix: float = 1 / 0.96,
    dt: float = 0.1,
    power_uw: float | None = None,
    ctrp: int = 0,
    fps: int = 5,
    frame_reader: Callable[[Path | None, int], Iterator[tuple[int, np.ndarray]]] | None = None,
) -> Path:
    """Generate trajectories.gif, individual PNG frames, and frames.json metadata.

    Parameters:
        video_path: Path to the .avi video file (or non-existent/dummy path if running from tracks).
        trajectories_txt: Path to particle tracking coordinates CSV/txt (tAlgae<exp>.txt).
        illumination: Path to illumination TIFF image (illumination<ill>.tiff).
        out_dir: Target directory (typically jobs/<job_id>/gif).
        step: Frame sampling interval (e.g. step=10 processes every 10th frame).
        disc_radius: Physical radius of illumination disc in micrometers (default 130 um).
        pix: Spatial calibration factor in um/pixel (default 1 / 0.96).
        dt: Time interval between frames in seconds (default 0.1 s).
        power_uw: Laser/light power in microwatts (uW) displayed on the overlay.
        ctrp: Illumination center override flag (0 = auto-detect via cu.Speckle).
        fps: Playback frames per second for the output animated GIF.
        frame_reader: Optional custom frame reader generator.

    Returns:
        Path: Absolute path to the created trajectories.gif.
    """
    # 1. Validation of inputs
    if step < 1:
        raise ValueError("step must be >= 1")
    if not trajectories_txt.exists():
        raise FileNotFoundError(f"Trajectories file not found: {trajectories_txt}")
    if not illumination.exists():
        raise FileNotFoundError(f"Illumination file not found: {illumination}")

    # Ensure output directory exists (e.g. jobs/<job_id>/gif)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Set up lazy streaming iterator for video frames if video file exists
    reader = frame_reader or iter_video_frames
    video_frames = (
        reader(video_path, step) if (video_path is not None and video_path.exists()) else None
    )

    # 3. Delegate rendering to core physics module (core.traj_gif.render_gif)
    # This creates frames/0.png, frames/1.png... and trajectories.gif
    gif_path, meta = render_gif(
        trajectories_txt=trajectories_txt,
        illumination_path=illumination,
        out_dir=out_dir,
        step=step,
        disc=disc_radius,
        pix=pix,
        dt=dt,
        power=power_uw,
        ctrp=ctrp,
        fps=fps,
        video_frames=video_frames,
    )

    # 4. Atomically persist frames.json metadata
    # We write to a temporary file first (.tmp) and then use os.replace to prevent
    # frontend/API consumers from reading a partially-written JSON file.
    tmp_json = out_dir / "frames.json.tmp"
    tmp_json.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    os.replace(tmp_json, out_dir / "frames.json")

    return gif_path
