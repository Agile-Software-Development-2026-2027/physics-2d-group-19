from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.config import get_settings
from app.security import create_access_token


@pytest.fixture
def test_app_client(client):
    """Client with a dedicated test router to test router-level protection."""
    router = APIRouter(prefix="/test-protected")

    @router.get("/resource")
    def get_resource():
        return {"status": "ok"}

    client.app.include_router(
        router,
        prefix="/api",
        dependencies=[Depends(get_current_user)],
    )
    return client


def test_health_stays_public(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_login_stays_public(client):
    # Public endpoint: bad credentials return 401, not missing bearer error
    response = client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Username or password incorrect"


def test_no_token_returns_401(test_app_client):
    response = test_app_client.get("/api/test-protected/resource")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers.get("www-authenticate") == "Bearer"


def test_bad_token_returns_401(test_app_client):
    response = test_app_client.get(
        "/api/test-protected/resource",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
    assert response.headers.get("www-authenticate") == "Bearer"


def test_expired_token_returns_401(test_app_client):
    settings = get_settings()
    expired_payload = {
        "sub": "operator",
        "exp": datetime.now(UTC) - timedelta(minutes=10),
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret, algorithm="HS256")

    response = test_app_client.get(
        "/api/test-protected/resource",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_tampered_token_returns_401(test_app_client):
    token = create_access_token("operator") + "tampered"
    response = test_app_client.get(
        "/api/test-protected/resource",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_valid_token_allows_access(test_app_client):
    token = create_access_token("operator")
    response = test_app_client.get(
        "/api/test-protected/resource",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_existing_plots_endpoint_is_protected(client):
    # Verify that the existing plots router registered in main.py is protected
    response = client.get("/api/jobs/abc/plots")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
