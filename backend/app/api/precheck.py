from fastapi import APIRouter

from app.config import get_settings
from app.schemas.precheck import PrecheckItem, PrecheckRequest
from app.services.precheck import precheck

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/precheck")
def precheck_experiments(body: PrecheckRequest) -> list[PrecheckItem]:
    """Say for each experiment whether it is registered, included and has its files."""
    settings = get_settings()
    return precheck(settings, settings.data_dir, body.exp_ids)
