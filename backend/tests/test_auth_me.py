from app.api.deps import get_current_user


def test_me_returns_the_current_user(client):
    client.app.dependency_overrides[get_current_user] = lambda: "alice"

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json() == {"username": "alice"}


def test_me_uses_the_mock_operator_until_tokens_are_checked(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json() == {"username": "operator"}
