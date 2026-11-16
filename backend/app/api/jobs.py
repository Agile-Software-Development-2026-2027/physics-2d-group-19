import json
import logging
import shutil
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.params import ProcessingParams
from app.services.experiments_store import get_experiment, settings_path
from app.services.job_config import load_config, save_config
from app.services.jobs_store import create_job as create_stored_job
from app.services.jobs_store import job_dir, read_status, write_status
from app.services.pipeline import run_job
from app.services.uploads import upload_path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=202)
def create_job(
    background_tasks: BackgroundTasks,
    illumination: Annotated[UploadFile | None, File()] = None,
    video: Annotated[UploadFile | None, File()] = None,
    video_id: Annotated[str | None, Form()] = None,
    trajectories: Annotated[UploadFile | None, File()] = None,
    exp_id: Annotated[int, Form()] = 49,
    params: Annotated[str | None, Form()] = None,
    make_gif: Annotated[bool, Form()] = False,
) -> dict:
    provided = sum(item is not None for item in (video, video_id, trajectories))
    if provided != 1:
        raise HTTPException(422, "Provide exactly one of video, video_id, or trajectories")

    data_dir = get_settings().data_dir

    try:
        exp = get_experiment(data_dir, exp_id)
    except KeyError:
        raise HTTPException(422, f"Experiment {exp_id} has no settings") from None

    uploaded_video = None
    uploaded_video_name = None
    if video_id is not None:
        try:
            uploaded_video = upload_path(data_dir, video_id)
        except KeyError:
            raise HTTPException(404, "Video not found") from None
        meta = json.loads((uploaded_video.parent / "meta.json").read_text(encoding="utf-8"))
        uploaded_video_name = meta.get("filename", f"tAlgae{exp_id}.avi")

    if params is not None:
        try:
            parsed_params = ProcessingParams.model_validate_json(params)
        except ValidationError as exc:
            raise HTTPException(422, json.loads(exc.json())) from exc
    else:
        parsed_params = ProcessingParams()

    illumination_id = exp.ill
    stored_illumination = (
        data_dir / "experiments" / "illumination" / f"illumination{illumination_id}.tiff"
    )
    if illumination is None and not stored_illumination.is_file():
        raise HTTPException(422, f"Missing illumination image for experiment {exp_id}")

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
        else:
            source = video if video is not None else trajectories
            extension = "avi" if video is not None else "txt"
            with (input_dir / f"tAlgae{exp_id}.{extension}").open("wb") as destination:
                shutil.copyfileobj(source.file, destination)
            inputs = {("video" if video is not None else "trajectories"): source.filename}

        ill_dest = input_dir / f"illumination{illumination_id}.tiff"
        if illumination is not None:
            with ill_dest.open("wb") as destination:
                shutil.copyfileobj(illumination.file, destination)
            inputs["illumination"] = illumination.filename
        else:
            shutil.copy(stored_illumination, ill_dest)
            inputs["illumination"] = stored_illumination.name

        shutil.copy(settings_path(data_dir), input_dir / "talgae_settings.txt")
        save_config(data_dir, job_id, exp, parsed_params, inputs, make_gif=make_gif)
    except Exception as exc:
        logger.exception("Could not save input for job %s", job_id)
        try:
            write_status(data_dir, job_id, "error", error=str(exc))
        except Exception:
            logger.exception("Could not write error status for job %s", job_id)
        raise HTTPException(500, "Could not save job input") from exc

    background_tasks.add_task(run_job, data_dir, job_id)
    return {"job_id": job_id, "status": "queued"}


@router.get("/{job_id}")
def get_job_status(job_id: str) -> dict:
    try:
        return read_status(get_settings().data_dir, job_id)
    except KeyError:
        raise HTTPException(404, "Job not found") from None


@router.get("/{job_id}/config")
def get_job_config(job_id: str) -> dict:
    """The configuration the job was started with (23.1); 404 if the job has none."""
    try:
        return load_config(get_settings().data_dir, job_id)
    except KeyError:
        raise HTTPException(404, "Job config not found") from None
