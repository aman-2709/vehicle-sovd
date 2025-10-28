"""
User repository module.

Provides async database access functions for user-related operations.
"""

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = structlog.get_logger(__name__)


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """
    Retrieve a user by username.

    Args:
        db: Async database session
        username: Username to search for

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if user:
        logger.debug("user_found_by_username", username=username, user_id=str(user.user_id))
    else:
        logger.debug("user_not_found_by_username", username=username)

    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """
    Retrieve a user by user ID.

    Args:
        db: Async database session
        user_id: User UUID to search for

    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        logger.debug("user_found_by_id", user_id=str(user_id), username=user.username)
    else:
        logger.debug("user_not_found_by_id", user_id=str(user_id))

    return user


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password_hash: str,
    role: str = "engineer"
) -> User:
    """
    Create a new user in the database.

    Args:
        db: Async database session
        username: Unique username for the user
        email: Unique email address
        password_hash: Bcrypt hashed password
        role: User role (default: 'engineer')

    Returns:
        Created User object
    """
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(
        "user_created",
        user_id=str(user.user_id),
        username=username,
        email=email,
        role=role
    )

    return user
