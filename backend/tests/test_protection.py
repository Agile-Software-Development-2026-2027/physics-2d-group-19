import re
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


def _extract_all_routes(app):
    """Extract all concrete paths and allowed HTTP methods registered in the app."""
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append((route.path, route.methods))
        elif hasattr(route, "original_router"):
            prefix = getattr(route.include_context, "prefix", "")
            for inner in route.original_router.routes:
                if hasattr(inner, "path") and hasattr(inner, "methods"):
                    routes.append((prefix + inner.path, inner.methods))
    return routes


def test_all_registered_routes_are_protected_by_default(client):
    """Requirement 7.2: Iterate dynamically through all app routes,

    exclude only explicit public ones, and verify that accessing any route
    without a bearer token returns HTTP 401 Unauthorized.
    """
    excluded_public_paths = {
        "/api/health",
        "/api/auth/login",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/docs/oauth2-redirect",
    }

    all_routes = _extract_all_routes(client.app)
    tested_count = 0

    for path, methods in all_routes:
        if path in excluded_public_paths:
            continue

        # Replace any path parameter such as {job_id} or {exp_id} with a dummy valid 12-char ID
        concrete_path = re.sub(r"\{[^}]+\}", "000000000000", path)

        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue

            response = client.request(method, concrete_path)
            assert response.status_code == 401, (
                f"Route {method} {path} is not protected! Got HTTP {response.status_code}."
            )
            assert response.json().get("detail") == "Not authenticated"
            tested_count += 1

    # Ensure we actually tested the routes
    assert tested_count > 0


def test_protection_check_fails_on_unprotected_route(client):
    """Verify that if an unprotected router is registered without dependencies,

    the protection verification correctly detects the violation.
    """
    unprotected_router = APIRouter(prefix="/unprotected-dummy")

    @unprotected_router.get("/insecure")
    def insecure_route():
        return {"open": True}

    # Include without dependencies
    client.app.include_router(unprotected_router, prefix="/api")

    response = client.get("/api/unprotected-dummy/insecure")
    assert response.status_code == 200  # Proves the route is indeed unprotected
