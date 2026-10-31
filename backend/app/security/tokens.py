"""HS256 access tokens; callers translate JWT errors into API responses."""

from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings


def create_access_token(username: str) -> str:
    """Sign a username and UTC expiry using the current application settings."""
    if not isinstance(username, str) or not username.strip():
        raise ValueError("Username must be a non-empty string")
    settings = get_settings()
    return jwt.encode(
        {
            "sub": username,
            "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> str:
    """Return the username, propagating InvalidTokenError and its subclasses."""
    payload = jwt.decode(
        token,
        get_settings().jwt_secret,
        algorithms=["HS256"],
        options={"require": ["sub", "exp"]},
    )
    username = payload["sub"]
    if not isinstance(username, str) or not username.strip():
        raise jwt.InvalidTokenError("Token subject must be a non-empty string")
    return username
