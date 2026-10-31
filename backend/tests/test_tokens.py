from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import get_settings
from app.security import create_access_token, decode_access_token

SECRET = "test-only-signing-key-with-at-least-48-bytes-for-algorithm-tests"


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch):
    monkeypatch.setenv("APP_JWT_SECRET", SECRET)
    monkeypatch.delenv("APP_JWT_EXPIRE_MINUTES", raising=False)
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("username", ["operator", "Dànilo 🔬", " operator "])
def test_roundtrip_preserves_username(username):
    assert decode_access_token(create_access_token(username)) == username


@pytest.mark.parametrize("minutes", [None, 15])
def test_expiry_uses_default_or_configured_duration(minutes, monkeypatch):
    if minutes is not None:
        monkeypatch.setenv("APP_JWT_EXPIRE_MINUTES", str(minutes))
    before = datetime.now(UTC).timestamp()
    token = create_access_token("operator")
    after = datetime.now(UTC).timestamp()
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    duration = (480 if minutes is None else minutes) * 60
    assert before + duration - 1 <= payload["exp"] <= after + duration
    assert payload["sub"] == "operator"
    assert jwt.get_unverified_header(token)["alg"] == "HS256"


def test_expired_token(monkeypatch):
    monkeypatch.setenv("APP_JWT_EXPIRE_MINUTES", "-1")
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(create_access_token("operator"))


def test_tampered_payload_is_rejected():
    token = create_access_token("operator")
    header, _, signature = token.split(".")
    other = create_access_token("attacker").split(".")[1]
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(f"{header}.{other}.{signature}")


def test_settings_are_read_at_call_time(monkeypatch):
    token = create_access_token("operator")
    monkeypatch.setenv("APP_JWT_SECRET", SECRET + "-different")
    get_settings.cache_clear()
    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(token)
    assert decode_access_token(create_access_token("operator")) == "operator"


@pytest.mark.parametrize("token", ["", "not-a-token", "a.b.c", "a.b"])
def test_malformed_token(token):
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


@pytest.mark.parametrize("algorithm", ["HS384", "none"])
def test_only_hs256_is_accepted(algorithm):
    token = jwt.encode(
        {"sub": "operator", "exp": datetime.now(UTC) + timedelta(minutes=1)},
        "" if algorithm == "none" else SECRET,
        algorithm=algorithm,
    )
    with pytest.raises(jwt.InvalidAlgorithmError):
        decode_access_token(token)


@pytest.mark.parametrize("missing", ["sub", "exp"])
def test_required_claims(missing):
    payload = {"sub": "operator", "exp": datetime.now(UTC) + timedelta(minutes=1)}
    del payload[missing]
    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(jwt.encode(payload, SECRET, algorithm="HS256"))


@pytest.mark.parametrize("username", [None, 42, "", "   "])
def test_invalid_username(username):
    with pytest.raises(ValueError):
        create_access_token(username)
    payload = {"sub": username, "exp": datetime.now(UTC) + timedelta(minutes=1)}
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(jwt.encode(payload, SECRET, algorithm="HS256"))
