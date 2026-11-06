from app.api.deps import get_current_user
from app.security import create_access_token


def test_me_returns_the_current_user(client):
    client.app.dependency_overrides[get_current_user] = lambda: "alice"

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json() == {"username": "alice"}


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_with_bearer_token(client):
    token = create_access_token("operator")
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"username": "operator"}
