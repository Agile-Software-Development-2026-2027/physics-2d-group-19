from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)] = None,
) -> str:
    """Validate Bearer token and return username.

    Raises 401 if credentials are missing or token is invalid/expired.
    """
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_access_token(creds.credentials)
    except jwt.InvalidTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
