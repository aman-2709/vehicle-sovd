"""
Authentication API endpoints.

Provides REST API for user authentication, token management, and user profile.
"""

from datetime import datetime, timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.session import Session
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and return access and refresh tokens.

    Args:
        credentials: Username and password
        db: Database session

    Returns:
        TokenResponse with access_token, refresh_token, and expiration info

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Authenticate user
    user = await authenticate_user(db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    access_token = create_access_token(user.user_id, user.username, user.role)
    refresh_token = create_refresh_token(user.user_id, user.username)

    # Store refresh token in database
    refresh_expires_at = datetime.utcnow() + timedelta(days=7)
    session = Session(
        user_id=user.user_id,
        refresh_token=refresh_token,
        expires_at=refresh_expires_at
    )
    db.add(session)
    await db.commit()

    logger.info(
        "user_logged_in",
        user_id=str(user.user_id),
        username=user.username,
        role=user.role,
        session_id=str(session.session_id)
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60  # Convert to seconds
    )


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
) -> RefreshResponse:
    """
    Validate refresh token and issue new access token.

    Args:
        request: Refresh token
        db: Database session

    Returns:
        RefreshResponse with new access_token

    Raises:
        HTTPException: 401 if refresh token is invalid or not found in database
    """
    # Validate refresh token JWT
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        logger.warning("refresh_token_invalid", reason="jwt_validation_failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if refresh token exists in database and is not expired
    result = await db.execute(
        select(Session)
        .where(Session.refresh_token == request.refresh_token)
        .where(Session.expires_at > datetime.utcnow())
    )
    session = result.scalar_one_or_none()

    if not session:
        logger.warning(
            "refresh_token_invalid",
            reason="not_found_or_expired",
            user_id=payload.get("user_id")
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database to ensure they still exist and are active
    result = await db.execute(
        select(User).where(User.user_id == session.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(
            "refresh_token_invalid",
            reason="user_not_found",
            user_id=str(session.user_id)
        )
        # Delete invalid session
        await db.delete(session)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new access token
    access_token = create_access_token(user.user_id, user.username, user.role)

    logger.info(
        "access_token_refreshed",
        user_id=str(user.user_id),
        username=user.username,
        session_id=str(session.session_id)
    )

    return RefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60  # Convert to seconds
    )


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> LogoutResponse:
    """
    Invalidate all refresh tokens for the current user (logout).

    Args:
        current_user: Authenticated user from JWT
        db: Database session

    Returns:
        LogoutResponse with confirmation message
    """
    # Delete all sessions for the current user
    await db.execute(
        delete(Session).where(Session.user_id == current_user.user_id)
    )
    await db.commit()

    logger.info(
        "user_logged_out",
        user_id=str(current_user.user_id),
        username=current_user.username
    )

    return LogoutResponse(
        message="Logged out successfully"
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user profile from JWT token.

    Args:
        current_user: Authenticated user from JWT

    Returns:
        UserResponse with user profile information
    """
    logger.debug(
        "user_profile_retrieved",
        user_id=str(current_user.user_id),
        username=current_user.username
    )

    return UserResponse(
        user_id=str(current_user.user_id),
        username=current_user.username,
        role=current_user.role,
        email=current_user.email,
    )
