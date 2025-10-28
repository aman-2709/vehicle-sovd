"""
Authentication service module.

Provides functions for JWT token management, password hashing/verification,
and user authentication against the database.
"""

import uuid
from datetime import datetime, timedelta

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.repositories.user_repository import get_user_by_username

logger = structlog.get_logger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: uuid.UUID, username: str, role: str) -> str:
    """
    Generate a short-lived JWT access token.

    Args:
        user_id: User's unique identifier
        username: User's username
        role: User's role (e.g., 'engineer', 'admin')

    Returns:
        Encoded JWT access token string
    """
    now = datetime.utcnow()
    expires_delta = timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    expire = now + expires_delta

    claims = {
        "user_id": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
        "iat": now,
        "type": "access"
    }

    token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    logger.info(
        "access_token_created",
        user_id=str(user_id),
        username=username,
        role=role,
        expires_at=expire.isoformat()
    )

    return token


def create_refresh_token(user_id: uuid.UUID, username: str) -> str:
    """
    Generate a long-lived JWT refresh token (7 days).

    Args:
        user_id: User's unique identifier
        username: User's username

    Returns:
        Encoded JWT refresh token string
    """
    now = datetime.utcnow()
    expires_delta = timedelta(days=7)
    expire = now + expires_delta

    claims = {
        "user_id": str(user_id),
        "username": username,
        "exp": expire,
        "iat": now,
        "type": "refresh"
    }

    token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    logger.info(
        "refresh_token_created",
        user_id=str(user_id),
        username=username,
        expires_at=expire.isoformat()
    )

    return token


def verify_access_token(token: str) -> dict | None:
    """
    Validate and decode a JWT access token.

    Args:
        token: JWT token string to validate

    Returns:
        Decoded token payload as dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify it's an access token
        if payload.get("type") != "access":
            logger.warning("token_validation_failed", reason="invalid_token_type")
            return None

        # Extract required claims
        user_id = payload.get("user_id")
        username = payload.get("username")
        role = payload.get("role")

        if not user_id or not username or not role:
            logger.warning("token_validation_failed", reason="missing_claims")
            return None

        logger.debug("access_token_validated", user_id=user_id, username=username)
        return payload

    except JWTError as e:
        logger.warning("token_validation_failed", error=str(e))
        return None


def verify_refresh_token(token: str) -> dict | None:
    """
    Validate and decode a JWT refresh token.

    Args:
        token: JWT refresh token string to validate

    Returns:
        Decoded token payload as dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            logger.warning("refresh_token_validation_failed", reason="invalid_token_type")
            return None

        # Extract required claims
        user_id = payload.get("user_id")
        username = payload.get("username")

        if not user_id or not username:
            logger.warning("refresh_token_validation_failed", reason="missing_claims")
            return None

        logger.debug("refresh_token_validated", user_id=user_id, username=username)
        return payload

    except JWTError as e:
        logger.warning("refresh_token_validation_failed", error=str(e))
        return None


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str
) -> User | None:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password to verify

    Returns:
        User object if authentication successful, None otherwise
    """
    # Query user from database
    user = await get_user_by_username(db, username)

    if not user:
        logger.warning("authentication_failed", username=username, reason="user_not_found")
        return None

    # Verify user is active
    if not user.is_active:
        logger.warning("authentication_failed", username=username, reason="user_inactive")
        return None

    # Verify password
    if not verify_password(password, user.password_hash):
        logger.warning("authentication_failed", username=username, reason="invalid_password")
        return None

    logger.info(
        "authentication_successful",
        user_id=str(user.user_id),
        username=username,
        role=user.role
    )

    return user
