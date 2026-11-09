"""Cut a lossless clip of video 49 and save the trajectories the legacy tracking finds on it.

The full video (1.8 GB) never goes in the repository or in CI. The clip and its expected
trajectories let a test check the tracking against the lab code (end-to-end test 14.7).

Usage (from the repository root, with the backend environment):
    python backend/scripts/make_clip_reference.py [--video docs/tAlgae49.avi] [--frames 30]

Writes backend/tests/fixtures/exp49/clip/tAlgae49_clip.avi and tAlgae49_clip.txt and
prints their md5. With the same video and library versions the output is identical.
"""

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

import av
import numpy as np
import pims

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
LEGACY_TRACKING = REPO_ROOT / "legacy-code" / "tracking_from_video"
CONFIG = LEGACY_TRACKING / "configs" / "config_tracking-49-65.json"
CLIP_DIR = BACKEND_DIR / "tests" / "fixtures" / "exp49" / "clip"
CLIP_NAME = "tAlgae49_clip"

sys.path.insert(0, str(LEGACY_TRACKING / "src"))

import trackpy  # noqa: E402
from tracking_algae import process_one  # noqa: E402
from tracking_core import load_config_json  # noqa: E402


def read_grey_frames(video: Path, n_frames: int) -> list[np.ndarray]:
    """First n_frames of the video as 8-bit grey images."""
    frames = []
    with av.open(str(video)) as container:
        for frame in container.decode(container.streams.video[0]):
            rgb = frame.to_ndarray(format="rgb24")
            # Video 49 is pal8 with a grey palette: one channel keeps every value.
            if not ((rgb[..., 0] == rgb[..., 1]).all() and (rgb[..., 1] == rgb[..., 2]).all()):
                raise SystemExit("The video is not grey: the clip would lose information")
            frames.append(rgb[..., 0])
            if len(frames) == n_frames:
                return frames
    raise SystemExit(f"The video has fewer than {n_frames} frames")


def write_clip(frames: list[np.ndarray], path: Path, fps: int) -> None:
    """Lossless clip (FFV1), the codec the planning document asks for."""
    with av.open(str(path), "w") as container:
        stream = container.add_stream("ffv1", rate=fps)
        stream.width, stream.height, stream.pix_fmt = frames[0].shape[1], frames[0].shape[0], "gray"
        for image in frames:
            container.mux(stream.encode(av.VideoFrame.from_ndarray(image, format="gray")))
        container.mux(stream.encode())


def check_same_pixels(clip: Path, video: Path, channel: int) -> int:
    """The tracking must read from the clip the same values it reads from the video."""
    v_clip, v_video = pims.Video(str(clip)), pims.Video(str(video))
    # Same count as load_video_to_ram, which skips the last frame.
    n_read = int(float(v_clip.frame_rate) * float(v_clip.duration) - 1)
    for i in range(n_read):
        clip_frame = v_clip.get_frame(i)[:, :, channel]
        if not np.array_equal(clip_frame, v_video.get_frame(i)[:, :, channel]):
            raise SystemExit(f"Frame {i} of the clip differs from the video")
    return n_read


def run_legacy_tracking(clip: Path, work_dir: Path) -> Path:
    """Legacy tracking_algae.py on the clip, in one process so the output is reproducible."""
    batch = trackpy.batch

    def one_process_batch(*args, **kwargs):
        kwargs["processes"] = 1  # the legacy code asks for "auto"
        return batch(*args, **kwargs)

    trackpy.batch = one_process_batch
    try:
        process_one(clip, work_dir, CONFIG, overwrite=True)
    finally:
        trackpy.batch = batch
    return work_dir / f"{clip.stem}.txt"


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--video", type=Path, default=REPO_ROOT / "docs" / "tAlgae49.avi")
    parser.add_argument("--frames", type=int, default=30, help="Frames to cut from the start")
    args = parser.parse_args()

    if not args.video.exists():
        raise SystemExit(f"Video not found: {args.video}")
    cfg = load_config_json(CONFIG)
    fps = round(float(pims.Video(str(args.video)).frame_rate))

    CLIP_DIR.mkdir(parents=True, exist_ok=True)
    clip = CLIP_DIR / f"{CLIP_NAME}.avi"
    write_clip(read_grey_frames(args.video, args.frames), clip, fps)
    n_read = check_same_pixels(clip, args.video, cfg.channel)

    with tempfile.TemporaryDirectory() as tmp:
        txt = run_legacy_tracking(clip, Path(tmp))
        # pandas writes CRLF on Windows: keep LF so the hash is the same everywhere.
        expected = CLIP_DIR / f"{CLIP_NAME}.txt"
        expected.write_bytes(txt.read_bytes().replace(b"\r\n", b"\n"))

    print(f"Clip: frames 0-{args.frames - 1} of {args.video.name}, {n_read} read by the tracking")
    for path in (clip, expected):
        print(f"{path.name}  {path.stat().st_size / 1e6:.1f} MB  md5 {md5(path)}")


if __name__ == "__main__":
    main()
