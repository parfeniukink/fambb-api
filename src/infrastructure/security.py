"""Security utilities

REASONING
(1) JWT Authentication
(2) Password Hashing


NOTES
(1) Password hashing Argon2 is used as an OWASP recommendation
"""

import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from src.config import settings

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password using Argon2"""

    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""

    try:
        _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    else:
        return True


def create_access_token(user_id: int) -> str:
    """Create a JWT access token with short expiry"""

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.auth.access_token_expire_minutes
    )

    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
        },
        settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
    )


def create_refresh_token(user_id: int) -> str:
    """Create a JWT refresh token with longer expiry (7 days by default)"""

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.auth.refresh_token_expire_days
    )

    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": expires_at,
            "type": "refresh",
        },
        settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    ERRORS
    (1) jwt.ExpiredSignatureError: if token has expired
    (2) jwt.InvalidTokenError: if token is invalid
    """

    return jwt.decode(
        token, settings.auth.secret_key, algorithms=[settings.auth.algorithm]
    )


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token using SHA256 for database storage"""

    return hashlib.sha256(token.encode()).hexdigest()
