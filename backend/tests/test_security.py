import pytest

from app.security.passwords import hash_password, verify_password


def test_hash_password_generates_argon2_hash():
    password = "Secret_password_123"
    hashed = hash_password(password)

    assert hashed.startswith("$argon2id$")
    assert hashed != password


def test_hash_password_unique_salt():
    password = "Secret_password_123"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Argon2 generates random salts for every hash
    assert hash1 != hash2


def test_verify_password_success():
    password = "Operator_secret"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_wrong_password():
    password = "Operator_secret"
    hashed = hash_password(password)

    assert verify_password("wrong_password", hashed) is False


def test_verify_password_case_sensitive():
    password = "OperatorSecret"
    hashed = hash_password(password)

    assert verify_password("operatorsecret", hashed) is False
    assert verify_password("OPERATORSECRET", hashed) is False


def test_verify_password_preserves_internal_spaces():
    password = "Password 1"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("Password1", hashed) is False


def test_verify_password_does_not_ignore_boundary_spaces():
    password = "secret_password"
    hashed = hash_password(password)

    assert verify_password(" secret_password", hashed) is False
    assert verify_password("secret_password ", hashed) is False


def test_verify_password_malformed_hash():
    assert verify_password("password", "not_a_valid_argon2_hash") is False
    assert verify_password("password", "$argon2id$invalid$format") is False
    assert verify_password("password", "$argon2id$") is False
    # Formato Bcrypt
    assert (
        verify_password(
            "password",
            "$2b$12$e8Mc8JwBsD16gL..eQh1heV9Zt9u5YQ5R0B9.O1pY01m8qJ/5i.C.",
        )
        is False
    )


def test_verify_password_empty_inputs():
    hashed = hash_password("valid_password")

    assert verify_password("", hashed) is False
    assert verify_password("valid_password", "") is False
    assert verify_password("valid_password", "   ") is False
    assert verify_password("", "") is False


@pytest.mark.parametrize(
    "plain,hashed",
    [
        (None, "$argon2id$v=19$m=65536,t=3,p=4$fakehash"),
        ("password", None),
        (None, None),
        (12345, "$argon2id$v=19$m=65536,t=3,p=4$fakehash"),
        ("password", 12345),
        (["password"], "$argon2id$v=19$m=65536,t=3,p=4$fakehash"),
        ("password", ["$argon2id$v=19$m=65536,t=3,p=4$fakehash"]),
    ],
)
def test_verify_password_invalid_types_return_false(plain, hashed):
    assert verify_password(plain, hashed) is False


def test_hash_password_empty_raises_value_error():
    with pytest.raises(ValueError, match="Password must be a valid non-empty string"):
        hash_password("")


def test_hash_password_whitespace_raises_value_error():
    with pytest.raises(ValueError, match="Password must be a valid non-empty string"):
        hash_password("   ")


@pytest.mark.parametrize("invalid_input", [None, 12345, False, ["password"]])
def test_hash_password_invalid_types_raise_value_error(invalid_input):
    with pytest.raises(ValueError, match="Password must be a valid non-empty string"):
        hash_password(invalid_input)


def test_hash_and_verify_unicode_and_symbols():
    password = "Pàsswörd_con_sp€ciali_&_emoji!🔑"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("Passwörd_con_speciali_&_emoji!🔑", hashed) is False


def test_hash_and_verify_long_password():
    long_password = "A" * 100
    hashed = hash_password(long_password)

    assert verify_password(long_password, hashed) is True
    assert verify_password("A" * 99, hashed) is False
