"""
FastAPI dependency injection functions.

Provides dependencies for authentication and authorization.
"""

import uuid
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import get_user_by_id
from app.services.auth_service import verify_access_token

logger = structlog.get_logger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to extract and validate the current user from JWT token.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session

    Returns:
        Current authenticated User object

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    token = credentials.credentials

    # Validate and decode JWT token
    payload = verify_access_token(token)
    if not payload:
        logger.warning("authentication_failed", reason="invalid_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user_id from token
    user_id_str = payload.get("user_id")
    if not user_id_str:
        logger.warning("authentication_failed", reason="missing_user_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        logger.warning(
            "authentication_failed",
            reason="invalid_user_id_format",
            user_id=user_id_str
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    user = await get_user_by_id(db, user_id)
    if not user:
        logger.warning("authentication_failed", reason="user_not_found", user_id=user_id_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user is active
    if not user.is_active:
        logger.warning("authentication_failed", reason="user_inactive", user_id=user_id_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(
        "user_authenticated",
        user_id=str(user.user_id),
        username=user.username,
        role=user.role
    )
    return user


def require_role(allowed_roles: list[str]) -> Callable[..., Any]:
    """
    Factory function to create a role-based authorization dependency.

    Args:
        allowed_roles: List of role names that are allowed (e.g., ["admin", "engineer"])

    Returns:
        Dependency function that checks user role

    Example:
        @router.post("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role(["admin"]))):
            ...
    """

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """
        Check if the current user has one of the required roles.

        Args:
            current_user: Authenticated user from get_current_user dependency

        Returns:
            User object if authorized

        Raises:
            HTTPException: 403 if user doesn't have required role
        """
        if current_user.role not in allowed_roles:
            logger.warning(
                "authorization_failed",
                user_id=str(current_user.user_id),
                username=current_user.username,
                user_role=current_user.role,
                required_roles=allowed_roles
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        logger.debug(
            "authorization_granted",
            user_id=str(current_user.user_id),
            username=current_user.username,
            role=current_user.role
        )
        return current_user

    return role_checker
