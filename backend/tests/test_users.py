import pytest

from app.config import get_settings
from app.users import create_user, get_password_hash, list_users, main


def test_create_and_list(tmp_path):
    db = tmp_path / "users.db"
    create_user(db, "operator", "secret")
    assert list_users(db) == ["operator"]
    assert get_password_hash(db, "operator").startswith("$argon2id$")


def test_duplicate_user(tmp_path):
    db = tmp_path / "users.db"
    create_user(db, "operator", "secret")
    with pytest.raises(ValueError, match="already exists"):
        create_user(db, "operator", "other")


def test_unknown_user(tmp_path):
    assert get_password_hash(tmp_path / "users.db", "nobody") is None


def test_empty_username_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Username must not be empty"):
        create_user(tmp_path / "users.db", "  ", "secret")


def test_username_with_quote_is_stored(tmp_path):
    db = tmp_path / "users.db"
    create_user(db, "o'brien", "secret")
    assert list_users(db) == ["o'brien"]


def test_users_are_listed_alphabetically(tmp_path):
    db = tmp_path / "users.db"
    for name in ["zoe", "anna", "marco"]:
        create_user(db, name, "secret")
    assert list_users(db) == ["anna", "marco", "zoe"]


@pytest.fixture
def users_db(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield tmp_path / "users.db"
    get_settings.cache_clear()


def _type_passwords(monkeypatch, *passwords):
    answers = iter(passwords)
    monkeypatch.setattr("app.users.getpass.getpass", lambda prompt: next(answers))


def test_cli_create_and_list(users_db, monkeypatch, capsys):
    _type_passwords(monkeypatch, "secret", "secret")
    main(["create", "operator"])
    main(["list"])
    assert capsys.readouterr().out.splitlines() == ["User 'operator' created", "operator"]
    assert get_password_hash(users_db, "operator").startswith("$argon2id$")


def test_cli_different_passwords_exit_with_1(users_db, monkeypatch):
    _type_passwords(monkeypatch, "secret", "other")
    with pytest.raises(SystemExit) as exc_info:
        main(["create", "operator"])
    assert exc_info.value.code == 1
    assert list_users(users_db) == []


def test_cli_existing_user_exits_with_1(users_db, monkeypatch, capsys):
    create_user(users_db, "operator", "secret")
    _type_passwords(monkeypatch, "secret", "secret")
    with pytest.raises(SystemExit) as exc_info:
        main(["create", "operator"])
    assert exc_info.value.code == 1
    assert "already exists" in capsys.readouterr().err


def test_password_never_stored_in_plain_text(tmp_path):
    db = tmp_path / "users.db"
    raw_password = "super-secret-password-12345"
    create_user(db, "operator", raw_password)

    stored_hash = get_password_hash(db, "operator")
    assert stored_hash != raw_password
    assert raw_password not in stored_hash
    # Check that plain password byte sequence never appears inside the SQLite database file
    assert raw_password.encode("utf-8") not in db.read_bytes()


def test_duplicate_user_preserves_original_hash(tmp_path):
    db = tmp_path / "users.db"
    create_user(db, "operator", "initial-password")
    original_hash = get_password_hash(db, "operator")

    with pytest.raises(ValueError, match="already exists"):
        create_user(db, "operator", "new-attempted-password")

    # Verify that the original user's password hash remained intact
    assert get_password_hash(db, "operator") == original_hash
