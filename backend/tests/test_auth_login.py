from app.security import decode_access_token
from app.users import create_user

LOGIN_URL = "/api/auth/login"
WRONG_CREDENTIALS = {"detail": "Username or password incorrect"}


def test_login_with_correct_credentials(client, tmp_path):
    # Create a user in the temporary database
    create_user(tmp_path / "users.db", "alice", "correct-password")

    data = {"username": "alice", "password": "correct-password"}
    response = client.post(LOGIN_URL, json=data)

    assert response.status_code == 200
    token = response.json()["token"]
    # The token must contain the username
    assert decode_access_token(token) == "alice"


def test_login_with_wrong_password(client, tmp_path):
    create_user(tmp_path / "users.db", "alice", "correct-password")

    data = {"username": "alice", "password": "wrong-password"}
    response = client.post(LOGIN_URL, json=data)

    assert response.status_code == 401
    assert response.json() == WRONG_CREDENTIALS


def test_login_with_unknown_user(client, tmp_path):
    create_user(tmp_path / "users.db", "alice", "correct-password")

    data = {"username": "bob", "password": "any-password"}
    response = client.post(LOGIN_URL, json=data)

    # Same error as the wrong password: nobody can find out which users exist
    assert response.status_code == 401
    assert response.json() == WRONG_CREDENTIALS
