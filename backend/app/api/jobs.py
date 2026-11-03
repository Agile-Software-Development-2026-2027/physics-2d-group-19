import logging
import shutil
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.resources import SETTINGS_TXT
from app.services.jobs_store import create_job as create_stored_job
from app.services.jobs_store import job_dir, read_status, write_status
from app.services.pipeline import run_job
from core.clam_pipeline.io import load_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", status_code=202)
def create_job(
    background_tasks: BackgroundTasks,
    illumination: Annotated[UploadFile, File()],
    video: Annotated[UploadFile | None, File()] = None,
    trajectories: Annotated[UploadFile | None, File()] = None,
    exp_id: Annotated[int, Form()] = 49,
) -> dict:
    if exp_id != 49:
        raise HTTPException(422, "Only experiment 49 is supported")
    if (video is None) == (trajectories is None):
        raise HTTPException(422, "Provide exactly one of video or trajectories")

    settings = load_settings(SETTINGS_TXT)
    illumination_id = int(settings.loc[settings["exps"] == exp_id, "ill"].iloc[0])
    data_dir = get_settings().data_dir
    job_id = create_stored_job(data_dir, exp_id)
    try:
        input_dir = job_dir(data_dir, job_id) / "input"
        source = video if video is not None else trajectories
        extension = "avi" if video is not None else "txt"
        with (input_dir / f"tAlgae{exp_id}.{extension}").open("wb") as destination:
            shutil.copyfileobj(source.file, destination)
        with (input_dir / f"illumination{illumination_id}.tiff").open("wb") as destination:
            shutil.copyfileobj(illumination.file, destination)
        shutil.copy(SETTINGS_TXT, input_dir / "talgae_settings.txt")
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
