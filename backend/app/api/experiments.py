from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas.experiment import ExperimentSettings
from app.services.experiments_store import get_experiment, list_experiments, save_experiment

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
        raise HTTPException(status_code=404, detail="Experiment not found")


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
