"""Tracking service: turns a video into cell trajectories, like the lab's tracking_algae.py."""

from pathlib import Path

import pims
import trackpy as tp

from core.tracking_core import (
    TrackingConfig,
    load_linked_df,
    load_video_to_ram,
    run_link_in_h5,
    run_locate_to_h5,
    save_outputs,
    subtract_background,
)

# Shown to the operator, in the job status and by the upload endpoint (17.1).
VIDEO_UNREADABLE = "Cannot read the video"


def check_video(video_path: Path) -> tuple[int, float]:
    """Returns (frames, fps) without loading the video; ValueError if it can't be read.

    Opens the file like load_video_to_ram and counts the frames with the same
    formula, so the number matches the frames the tracking will process.
    """
    try:
        video = pims.Video(str(video_path))  # reads the metadata, not the frames
        fps = float(video.frame_rate)
        n_frames = int(fps * float(video.duration) - 1)
        video[0]  # decodes only the first frame
    except Exception as exc:
        raise ValueError(VIDEO_UNREADABLE) from exc
    if n_frames <= 0 or fps <= 0:
        raise ValueError(VIDEO_UNREADABLE)
    return n_frames, fps


def run_tracking(video_path: Path, out_dir: Path, cfg: TrackingConfig) -> Path:
    """Returns out_dir / f"{video_path.stem}.txt"."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_base = out_dir / video_path.stem
    h5_path = out_base.with_suffix(".h5")
    # Every job starts from scratch: a stale store would mix old and new positions.
    h5_path.unlink(missing_ok=True)

    # Stops a broken file before allocating the whole video in RAM.
    check_video(video_path)
    try:
        frames, _fps, _duration = load_video_to_ram(video_path, cfg.channel)
    except Exception as exc:  # a file that opens but is corrupted further on
        raise ValueError(VIDEO_UNREADABLE) from exc
    n_frames = frames.shape[0]
    if cfg.background_subtraction:
        frames = subtract_background(frames, cfg.background_method)

    run_locate_to_h5(frames, h5_path, cfg)
    del frames  # the whole video is in RAM

    # Linking an empty store fails with an unclear StopIteration, so check before it.
    with tp.PandasHDFStoreBig(str(h5_path)) as store:
        if not store.frames:
            raise ValueError("No cells found in the video")

    run_link_in_h5(h5_path, cfg, nFrames=n_frames)
    save_outputs(load_linked_df(h5_path), out_base, filter_stubs=cfg.filter_stubs)
    return out_base.with_suffix(".txt")
