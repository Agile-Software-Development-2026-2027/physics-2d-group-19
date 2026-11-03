"""Tracking service: turns a video into cell trajectories, like the lab's tracking_algae.py."""

from pathlib import Path

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


def run_tracking(video_path: Path, out_dir: Path, cfg: TrackingConfig) -> Path:
    """Returns out_dir / f"{video_path.stem}.txt"."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_base = out_dir / video_path.stem
    h5_path = out_base.with_suffix(".h5")
    # Every job starts from scratch: a stale store would mix old and new positions.
    h5_path.unlink(missing_ok=True)

    frames, _fps, _duration = load_video_to_ram(video_path, cfg.channel)
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
