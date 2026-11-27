"""Find an experiment's video, trajectories and illumination in the lab folders (US-30)."""

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.schemas.experiment import ExperimentSettings

# Same order as legacy-code/clam_pipeline/cli.py: microscope2D, photonicsLab, other.
FILE_PREFIXES = ("tAlgae", "tPhot", "td")
ILLUMINATION_SUFFIXES = (".tiff", ".tif")


@dataclass(frozen=True)
class ResolvedFiles:
    """Absolute paths of the files found; None when a file is missing."""

    video: Path | None
    trajectories: Path | None
    illumination: Path | None


def _find_in(directory: Path | None, names: list[str]) -> Path | None:
    """Return the first existing regular file among names inside directory.

    Names are built by the backend from numbers only. The resolved path must stay
    inside the folder, so a symlink pointing elsewhere is ignored.
    """
    if directory is None:
        return None
    try:
        root = directory.resolve(strict=True)
    except OSError:
        return None
    if not root.is_dir():
        return None
    for name in names:
        try:
            candidate = (root / name).resolve(strict=True)
        except OSError:
            continue
        if candidate.is_relative_to(root) and candidate.is_file():
            return candidate
    return None


def resolve_files(settings: Settings, data_dir: Path, exp: ExperimentSettings) -> ResolvedFiles:
    """Look up the files of exp without reading or copying them."""
    video = _find_in(settings.video_dir, [f"{prefix}{exp.exps}.avi" for prefix in FILE_PREFIXES])
    trajectories = _find_in(
        settings.trajectories_dir,
        [f"{prefix}{exp.exps}.txt" for prefix in FILE_PREFIXES],
    )
    illumination_names = [f"illumination{exp.ill}{suffix}" for suffix in ILLUMINATION_SUFFIXES]
    # Lab folder first, then the images uploaded through the app (#75).
    illumination = _find_in(settings.illumination_dir, illumination_names) or _find_in(
        data_dir / "experiments" / "illumination", illumination_names
    )
    return ResolvedFiles(video=video, trajectories=trajectories, illumination=illumination)
