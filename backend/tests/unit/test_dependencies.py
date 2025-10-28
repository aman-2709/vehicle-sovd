"""
Unit tests for dependency injection functions.

Tests authentication and authorization dependencies.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.dependencies import get_current_user, require_role
from app.models.user import User


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mocker):
        """Test successful user extraction from valid token."""
        # Create mock user
        user_id = uuid.uuid4()
        mock_user = User(
            user_id=user_id,
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role="engineer",
            is_active=True,
        )

        # Mock verify_access_token to return valid payload
        mocker.patch(
            "app.dependencies.verify_access_token",
            return_value={
                "user_id": str(user_id),
                "username": "testuser",
                "role": "engineer",
                "type": "access",
            },
        )

        # Mock get_user_by_id to return mock user
        mocker.patch("app.dependencies.get_user_by_id", return_value=mock_user)

        # Create mock credentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.jwt.token")

        db_mock = AsyncMock()

        # Call dependency
        result = await get_current_user(credentials, db_mock)

        assert result == mock_user
        assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mocker):
        """Test with invalid JWT token."""
        # Mock verify_access_token to return None (invalid token)
        mocker.patch("app.dependencies.verify_access_token", return_value=None)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.jwt.token")

        db_mock = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_mock)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_missing_user_id(self, mocker):
        """Test with token missing user_id claim."""
        # Mock verify_access_token to return payload without user_id
        mocker.patch(
            "app.dependencies.verify_access_token",
            return_value={
                "username": "testuser",
                "role": "engineer",
                "type": "access",
                # Missing user_id
            },
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="token.without.userid"
        )

        db_mock = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_mock)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_uuid_format(self, mocker):
        """Test with token containing invalid UUID format."""
        # Mock verify_access_token to return payload with invalid user_id
        mocker.patch(
            "app.dependencies.verify_access_token",
            return_value={
                "user_id": "not-a-valid-uuid",
                "username": "testuser",
                "role": "engineer",
                "type": "access",
            },
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="token.with.invalid.uuid"
        )

        db_mock = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_mock)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_not_found_in_db(self, mocker):
        """Test when user_id from token doesn't exist in database."""
        user_id = uuid.uuid4()

        # Mock verify_access_token to return valid payload
        mocker.patch(
            "app.dependencies.verify_access_token",
            return_value={
                "user_id": str(user_id),
                "username": "testuser",
                "role": "engineer",
                "type": "access",
            },
        )

        # Mock get_user_by_id to return None (user not found)
        mocker.patch("app.dependencies.get_user_by_id", return_value=None)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid.token.but.user.deleted"
        )

        db_mock = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_mock)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_user(self, mocker):
        """Test when user is inactive."""
        user_id = uuid.uuid4()
        mock_user = User(
            user_id=user_id,
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role="engineer",
            is_active=False,  # Inactive user
        )

        # Mock verify_access_token
        mocker.patch(
            "app.dependencies.verify_access_token",
            return_value={
                "user_id": str(user_id),
                "username": "testuser",
                "role": "engineer",
                "type": "access",
            },
        )

        # Mock get_user_by_id to return inactive user
        mocker.patch("app.dependencies.get_user_by_id", return_value=mock_user)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid.token.inactive.user"
        )

        db_mock = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, db_mock)

        assert exc_info.value.status_code == 401
        assert "User account is inactive" in exc_info.value.detail


class TestRequireRole:
    """Test require_role authorization dependency."""

    @pytest.mark.asyncio
    async def test_require_role_single_role_success(self):
        """Test authorization succeeds for user with required role."""
        # Create admin user
        admin_user = User(
            user_id=uuid.uuid4(),
            username="admin",
            email="admin@example.com",
            password_hash="hashed",
            role="admin",
            is_active=True,
        )

        # Create dependency that requires admin role
        dependency = require_role(["admin"])

        # Call the dependency (it should return the user)
        result = await dependency(admin_user)

        assert result == admin_user

    @pytest.mark.asyncio
    async def test_require_role_multiple_roles_success(self):
        """Test authorization succeeds when user has one of multiple allowed roles."""
        # Create engineer user
        engineer_user = User(
            user_id=uuid.uuid4(),
            username="engineer",
            email="engineer@example.com",
            password_hash="hashed",
            role="engineer",
            is_active=True,
        )

        # Create dependency that allows both admin and engineer
        dependency = require_role(["admin", "engineer"])

        # Call the dependency
        result = await dependency(engineer_user)

        assert result == engineer_user

    @pytest.mark.asyncio
    async def test_require_role_forbidden(self):
        """Test authorization fails when user doesn't have required role."""
        # Create engineer user
        engineer_user = User(
            user_id=uuid.uuid4(),
            username="engineer",
            email="engineer@example.com",
            password_hash="hashed",
            role="engineer",
            is_active=True,
        )

        # Create dependency that requires admin role only
        dependency = require_role(["admin"])

        # Call the dependency - should raise 403
        with pytest.raises(HTTPException) as exc_info:
            await dependency(engineer_user)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_role_empty_role_list(self):
        """Test that empty allowed_roles list blocks all users."""
        # Create user with any role
        user = User(
            user_id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role="engineer",
            is_active=True,
        )

        # Create dependency with empty role list
        dependency = require_role([])

        # Should block the user
        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_role_user_with_none_role(self):
        """Test authorization fails when user role is None."""
        # Create user with None role
        user = User(
            user_id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role=None,  # No role assigned
            is_active=True,
        )

        # Create dependency that requires admin
        dependency = require_role(["admin"])

        # Should fail authorization
        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_role_case_sensitive(self):
        """Test that role checking is case-sensitive."""
        # Create user with "Admin" role (capitalized)
        user = User(
            user_id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash="hashed",
            role="Admin",  # Capitalized
            is_active=True,
        )

        # Create dependency that requires "admin" (lowercase)
        dependency = require_role(["admin"])

        # Should fail because roles are case-sensitive
        with pytest.raises(HTTPException) as exc_info:
            await dependency(user)

        assert exc_info.value.status_code == 403
