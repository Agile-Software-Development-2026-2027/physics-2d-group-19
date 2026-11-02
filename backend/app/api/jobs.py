import shutil
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.services.jobs_store import run_job
from app.services.jobs_store import create_job, job_dir

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Path to talgae_settings.txt inside app/resources/
SETTINGS_TXT_PATH = Path(__file__).resolve().parents[1] / "resources" / "talgae_settings.txt"


@router.post("", status_code=202)
def create_job_endpoint(
    background_tasks: BackgroundTasks,
    illumination: UploadFile = File(...),
    video: UploadFile | None = File(None),
    trajectories: UploadFile | None = File(None),
    exp_id: int = Form(49),
) -> dict:
    # XOR validation: exactly one of video or trajectories must be provided
    has_video = video is not None
    has_trajectories = trajectories is not None
    if (has_video and has_trajectories) or (not has_video and not has_trajectories):
        raise HTTPException(
            status_code=422,
            detail="Fornire esattamente uno tra 'video' o 'trajectories'.",
        )

    # Validate supported experiment ID
    if exp_id != 49:
        raise HTTPException(
            status_code=422,
            detail="Al momento è supportato solo exp_id=49.",
        )

    settings = get_settings()

    # Read illumination number from settings file in resources
    try:
        settings_df = pd.read_csv(SETTINGS_TXT_PATH, sep=r"\s+", comment="#")
        row = settings_df.loc[settings_df["exps"] == exp_id].iloc[0]
        ill_num = int(row["ill"])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nella lettura di SETTINGS_TXT ({SETTINGS_TXT_PATH}): {e}",
        ) from e

    # Create job instance and input directory
    job_id = create_job(settings.data_dir, exp_id)
    jdir = job_dir(settings.data_dir, job_id)
    input_dir = jdir / "input"

    # Save illumination file using chunked streaming
    illum_dest = input_dir / f"illumination{ill_num}.tiff"
    with open(illum_dest, "wb") as f:
        shutil.copyfileobj(illumination.file, f)

    # Save video or trajectories file
    if video:
        video_dest = input_dir / f"tAlgae{exp_id}.avi"
        with open(video_dest, "wb") as f:
            shutil.copyfileobj(video.file, f)
    elif trajectories:
        traj_dest = input_dir / f"tAlgae{exp_id}.txt"
        with open(traj_dest, "wb") as f:
            shutil.copyfileobj(trajectories.file, f)

    # Copy global settings file to job input directory
    shutil.copy(SETTINGS_TXT_PATH, input_dir / "talgae_settings.txt")

    # Enqueue background task
    background_tasks.add_task(run_job, settings.data_dir, job_id)

    # Return accepted status with job ID
    return {"job_id": job_id, "status": "queued"}