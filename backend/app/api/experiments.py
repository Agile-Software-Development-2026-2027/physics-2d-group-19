import logging
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.schemas.experiment import ExperimentSettings, IlluminationUploadResponse
from app.services.experiments_store import get_experiment, list_experiments, save_experiment
from app.services.uploads import save_upload, upload_path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
def read_experiments() -> list[ExperimentSettings]:
    data_dir = get_settings().data_dir
    return list_experiments(data_dir)


@router.get("/{exp_id}")
def read_experiment(exp_id: int) -> ExperimentSettings:
    data_dir = get_settings().data_dir
    try:
        return get_experiment(data_dir, exp_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Experiment not found") from None


@router.post(
    "/{exp_id}/illumination",
    status_code=201,
    responses={400: {"description": "Empty file"}, 404: {"description": "Experiment not found"}},
)
def upload_illumination(
    exp_id: int,
    file: Annotated[UploadFile, File(description="Illumination image (.tif or .tiff)")],
) -> IlluminationUploadResponse:
    """Save unchanged bytes under the experiment's illumination number; replace atomically."""
    data_dir = get_settings().data_dir
    try:
        experiment = get_experiment(data_dir, exp_id)
    except KeyError:
        raise HTTPException(404, "Experiment not found") from None
    if Path(file.filename or "").suffix.lower() not in {".tif", ".tiff"}:
        raise HTTPException(422, "Only .tif and .tiff files are supported")
    if file.size == 0:
        raise HTTPException(400, "Empty file.")

    filename = f"illumination{experiment.ill}.tiff"
    directory = data_dir / "experiments" / "illumination"
    temporary = None
    try:
        upload_id = save_upload(data_dir, file.file, file.filename)
        content = upload_path(data_dir, upload_id)
        directory.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            dir=directory, prefix=".illumination-", delete=False
        ) as destination:
            temporary = Path(destination.name)
            with content.open("rb") as source:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
        os.replace(temporary, directory / filename)
    except Exception as exc:
        logger.exception("Could not save illumination for experiment %s", exp_id)
        raise HTTPException(500, "Could not save illumination") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                logger.exception(
                    "Could not clean up illumination temporary for experiment %s", exp_id
                )
    return IlluminationUploadResponse(ill=experiment.ill, filename=filename)


@router.put("/{exp_id}")
def write_experiment(exp_id: int, experiment: ExperimentSettings) -> ExperimentSettings:
    if experiment.exps != exp_id:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "loc": ["body", "exps"],
                    "msg": "exps must match the experiment number in the URL",
                    "type": "value_error",
                }
            ],
        )
    data_dir = get_settings().data_dir
    save_experiment(data_dir, experiment)
    return experiment
