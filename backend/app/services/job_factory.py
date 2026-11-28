"""Job preparation service shared by single-job and batch endpoints."""

import json
import logging
import shutil
from pathlib import Path

from fastapi import UploadFile

from app.config import Settings
from app.schemas.params import ProcessingParams
from app.services.experiments_store import get_experiment, settings_path
from app.services.file_resolver import ResolvedFiles, resolve_files
from app.services.job_config import save_config
from app.services.jobs_store import create_job as create_stored_job
from app.services.jobs_store import job_dir, write_status
from app.services.uploads import upload_path

logger = logging.getLogger(__name__)


class JobInputValidationError(ValueError):
    """Raised when job input arguments or required files are invalid/missing."""


class JobInputNotFoundError(KeyError):
    """Raised when a referenced uploaded video ID does not exist."""


class JobInputStorageError(RuntimeError):
    """Raised when persisting job inputs to disk fails."""


def prepare_job(
    data_dir: Path,
    settings: Settings,
    exp_id: int,
    params: ProcessingParams,
    make_gif: bool = False,
    video: UploadFile | None = None,
    video_id: str | None = None,
    trajectories: UploadFile | None = None,
    illumination: UploadFile | None = None,
) -> str:
    """Validate inputs, create a queued job directory, copy inputs, and save config.json."""
    provided = sum(item is not None for item in (video, video_id, trajectories))
    if provided > 1:
        raise JobInputValidationError("Provide at most one of video, video_id, or trajectories")

    try:
        exp = get_experiment(data_dir, exp_id)
    except KeyError as exc:
        raise JobInputValidationError(f"Experiment {exp_id} has no settings") from exc

    uploaded_video = None
    uploaded_video_name = None
    if video_id is not None:
        try:
            uploaded_video = upload_path(data_dir, video_id)
        except KeyError as exc:
            raise JobInputNotFoundError("Video not found") from exc
        meta_path = uploaded_video.parent / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        uploaded_video_name = meta.get("filename", f"tAlgae{exp_id}.avi")

    resolved: ResolvedFiles | None = None
    if provided == 0 or illumination is None:
        resolved = resolve_files(settings, data_dir, exp)

    if provided == 0 and resolved.video is None and resolved.trajectories is None:
        raise JobInputValidationError(f"Missing video or trajectories for experiment {exp_id}")

    illumination_id = exp.ill
    if illumination is None and (resolved is None or resolved.illumination is None):
        raise JobInputValidationError(f"Missing illumination illumination{illumination_id}.tiff")

    job_id = create_stored_job(data_dir, exp_id)
    try:
        input_dir = job_dir(data_dir, job_id) / "input"
        if uploaded_video is not None:
            with (
                uploaded_video.open("rb") as source_file,
                (input_dir / f"tAlgae{exp_id}.avi").open("wb") as destination,
            ):
                shutil.copyfileobj(source_file, destination)
            inputs = {"video": uploaded_video_name, "video_id": video_id}
        elif video is not None or trajectories is not None:
            source = video if video is not None else trajectories
            extension = "avi" if video is not None else "txt"
            with (input_dir / f"tAlgae{exp_id}.{extension}").open("wb") as destination:
                shutil.copyfileobj(source.file, destination)
            inputs = {("video" if video is not None else "trajectories"): source.filename}
        elif resolved.video is not None:
            inputs = {"video": resolved.video.name, "video_path": str(resolved.video)}
        else:
            shutil.copy(resolved.trajectories, input_dir / f"tAlgae{exp_id}.txt")
            inputs = {"trajectories": resolved.trajectories.name}

        ill_dest = input_dir / f"illumination{illumination_id}.tiff"
        if illumination is not None:
            with ill_dest.open("wb") as destination:
                shutil.copyfileobj(illumination.file, destination)
            inputs["illumination"] = illumination.filename
        else:
            shutil.copy(resolved.illumination, ill_dest)
            inputs["illumination"] = resolved.illumination.name

        shutil.copy(settings_path(data_dir), input_dir / "talgae_settings.txt")
        save_config(data_dir, job_id, exp, params, inputs, make_gif=make_gif)
    except Exception as exc:
        logger.exception("Could not save input for job %s", job_id)
        try:
            write_status(data_dir, job_id, "error", error=str(exc))
        except Exception:
            logger.exception("Could not write error status for job %s", job_id)
        raise JobInputStorageError("Could not save job input") from exc

    return job_id
