"""Security utilities: JWT creation/verification, password hashing, TOTP."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password: The plain-text password to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain: The plain-text password provided by the user.
        hashed: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Claims to embed in the token payload.
        expires_delta: Optional custom expiry duration. Defaults to
            ``ACCESS_TOKEN_EXPIRE_MINUTES`` from settings.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    to_encode["type"] = "access"
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a signed JWT refresh token with a longer expiry.

    Args:
        data: Claims to embed in the token payload.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode["exp"] = expire
    to_encode["type"] = "refresh"
    to_encode["jti"] = secrets.token_hex(16)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Args:
        token: The JWT string to decode.

    Returns:
        The token payload as a dictionary.

    Raises:
        HTTPException: 401 if the token is invalid, expired, or malformed.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise credentials_exception


def generate_totp_secret() -> str:
    """Generate a new random TOTP secret.

    Returns:
        A base32-encoded random secret string.
    """
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, issuer: str = "GestionSiniestros") -> str:
    """Build an otpauth:// URI suitable for QR code generation.

    Args:
        secret: The TOTP secret in base32 encoding.
        email: The user's email address (used as the account name).
        issuer: The issuer name shown in authenticator apps.

    Returns:
        An otpauth:// URI string.
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against a secret.

    Args:
        secret: The user's stored TOTP secret.
        code: The 6-digit TOTP code provided by the user.

    Returns:
        True if the code is valid within the allowed window, False otherwise.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
