from fastapi import APIRouter, Depends

from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def me(user: str = Depends(get_current_user)) -> dict[str, str]:
    return {"username": f"{user}"}
