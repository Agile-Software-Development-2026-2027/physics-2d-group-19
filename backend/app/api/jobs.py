import json
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.params import ProcessingParams
from app.services.job_config import load_config
from app.services.job_factory import (
    JobInputNotFoundError,
    JobInputStorageError,
    JobInputValidationError,
    prepare_job,
)
from app.services.jobs_store import read_status
from app.services.pipeline import run_job

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
    if params is not None:
        try:
            parsed_params = ProcessingParams.model_validate_json(params)
        except ValidationError as exc:
            raise HTTPException(422, json.loads(exc.json())) from exc
    else:
        parsed_params = ProcessingParams()

    settings = get_settings()
    data_dir = settings.data_dir
    try:
        job_id = prepare_job(
            data_dir=data_dir,
            settings=settings,
            exp_id=exp_id,
            params=parsed_params,
            make_gif=make_gif,
            video=video,
            video_id=video_id,
            trajectories=trajectories,
            illumination=illumination,
        )
    except JobInputValidationError as exc:
        raise HTTPException(422, str(exc)) from None
    except JobInputNotFoundError as exc:
        raise HTTPException(404, exc.args[0]) from None
    except JobInputStorageError as exc:
        raise HTTPException(500, str(exc)) from exc

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
