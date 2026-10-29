# Password hashing and verification module using Argon2

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# PasswordHasher uses standard Argon2id with safe default parameters
_hasher = PasswordHasher()


# Hash a plain text password using Argon2id.
def hash_password(plain_password: str) -> str:
    if not isinstance(plain_password, str) or not plain_password.strip():
        raise ValueError("Password must be a valid non-empty string")
    return _hasher.hash(plain_password)


# Verify a plain password against an Argon2 hash
def verify_password(plain_password: str, hashed_password: str) -> bool:

    if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
        return False

    if not plain_password or not hashed_password.strip():
        return False

    try:
        return _hasher.verify(hashed_password.strip(), plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
