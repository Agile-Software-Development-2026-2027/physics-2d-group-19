from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.config import get_settings
from app.schemas.auth import LoginRequest, TokenResponse
from app.security import create_access_token, verify_password
from app.users import get_password_hash

router = APIRouter(prefix="/auth", tags=["auth"])

WRONG_CREDENTIALS = "Username or password incorrect"


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    # Path of the users database
    db_path = get_settings().data_dir / "users.db"

    # Get the saved password hash, or None if the user does not exist
    saved_hash = get_password_hash(db_path, data.username)

    # User not found: we give the same error as a wrong password
    if saved_hash is None:
        raise HTTPException(status_code=401, detail=WRONG_CREDENTIALS)

    # Wrong password
    if not verify_password(data.password, saved_hash):
        raise HTTPException(status_code=401, detail=WRONG_CREDENTIALS)

    # Everything is ok: create the token and send it back
    token = create_access_token(data.username)
    return TokenResponse(token=token)


@router.get("/me")
def me(user: str = Depends(get_current_user)) -> dict[str, str]:
    return {"username": f"{user}"}
