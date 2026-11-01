from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.experiment import ExperimentSettings

router = APIRouter(prefix="/experiments", tags=["experiments"])

# Mock default experiment 49
MOCK_EXP_49 = {
    "exps": 49,
    "exp_type": 1,
    "ill": 14,
    "intensity": 180,
    "pix_arr": 1.041667,
    "no_skip": True,
    "ctr": 0,
    "fluo": 0,
    "lin": 0,
    "axis": 0,
}


@router.post("", status_code=status.HTTP_201_CREATED)
def save_experiment(settings: ExperimentSettings) -> dict[str, Any]:
    """Save or update experiment settings (mock contract)."""
    return {
        "id": settings.exps,
        "settings": settings.model_dump(),
        "message": "Experiment settings saved successfully",
    }


@router.get("/{experiment_id}")
def get_experiment(experiment_id: int) -> dict[str, Any]:
    """Retrieve settings for a given experiment (mock contract)."""
    if experiment_id == 49:
        return {"id": 49, "settings": MOCK_EXP_49}
    if experiment_id < 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )
    # Generic mock for any valid ID
    mock_data = {**MOCK_EXP_49, "exps": experiment_id}
    return {"id": experiment_id, "settings": mock_data}


@router.get("")
def list_experiments() -> list[dict[str, Any]]:
    """List registered experiments (mock contract)."""
    return [{"id": 49, "settings": MOCK_EXP_49}]
