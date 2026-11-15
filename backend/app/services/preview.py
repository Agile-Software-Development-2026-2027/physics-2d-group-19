"""Detection preview: finds the cells on one frame with the same functions as the tracking."""

from pathlib import Path

import numpy as np
import pandas as pd
import pims
import trackpy as tp

from app.schemas.params import TrackingParams
from core.tracking_core import subtract_background

# Enough frames to estimate the background without reading the whole video.
BACKGROUND_SAMPLE_SIZE = 50


def _frame_count(video_path: Path) -> int:

    with pims.Video(str(video_path)) as video:
        fps = float(video.frame_rate)
        duration = float(video.duration)
        # Same count as load_video_to_ram, so the preview never offers a frame the tracking skips.
        return int(fps * duration - 1)


def _read_frames(video_path: Path, indices: list[int], channel: int) -> np.ndarray:
    with pims.Video(str(video_path)) as video:
        frames = []
        for i in indices:
            # Same channel slicing as load_video_to_ram, so the preview sees what the tracking sees
            frames.append(video.get_frame(i)[:, :, channel])
        return np.stack(frames).astype(np.float32)


def detect_frame(
    video_path: Path, frame: int, params: TrackingParams
) -> tuple[np.ndarray, pd.DataFrame]:
    """Finds the cells on one frame; returns the frame and the positions found by trackpy."""
    n = _frame_count(video_path)

    if frame < 0 or frame >= n:
        raise ValueError(f"Frame {frame} is outside the video (0-{n - 1})")

    if params.background_subtraction:
        sample = np.linspace(0, n - 1, num=min(BACKGROUND_SAMPLE_SIZE, n), dtype=int)
        # Include the chosen frame: the full tracking also estimates the background with it.
        with_frame = np.append(sample, frame)
        indices = np.unique(with_frame)
    else:
        indices = np.array([frame])

    frames = _read_frames(video_path, indices.tolist(), params.channel)
    # frames holds only the frames read, so look up where the chosen one is.
    position = int(np.searchsorted(indices, frame))
    image = frames[position]

    if params.background_subtraction:
        cleaned = subtract_background(frames, params.background_method)[position]
    else:
        cleaned = image

    tp.quiet()
    features = tp.locate(
        cleaned, params.diameter, minmass=params.minmass, invert=params.invert, engine="numba"
    )

    return image, features
