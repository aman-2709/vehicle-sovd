"""
Unit tests for authentication service.

Tests password hashing, JWT token creation/validation, and user authentication.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import uuid

import pytest
from jose import jwt

from app.config import settings
from app.models.user import User
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    authenticate_user
)


class TestPasswordHashing:
    """Test password hashing and verification functions."""

    def test_hash_password_returns_different_hash(self):
        """Test that hashing the same password twice produces different hashes."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to salt
        assert hash1 != hash2
        assert hash1 != password
        assert hash2 != password

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "correct_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test that verify_password handles empty passwords."""
        hashed = hash_password("test")
        assert verify_password("", hashed) is False


class TestAccessTokenCreation:
    """Test JWT access token creation."""

    def test_create_access_token_contains_correct_claims(self):
        """Test that access token contains all required claims."""
        user_id = uuid.uuid4()
        username = "testuser"
        role = "engineer"

        token = create_access_token(user_id, username, role)

        # Decode without verification to inspect claims
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["user_id"] == str(user_id)
        assert payload["username"] == username
        assert payload["role"] == role
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_expiration(self):
        """Test that access token has correct expiration time."""
        user_id = uuid.uuid4()
        username = "testuser"
        role = "engineer"

        token = create_access_token(user_id, username, role)

        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Check expiration is approximately JWT_EXPIRATION_MINUTES in the future
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

        # Allow 5 second tolerance for test execution time
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 5


class TestRefreshTokenCreation:
    """Test JWT refresh token creation."""

    def test_create_refresh_token_contains_correct_claims(self):
        """Test that refresh token contains required claims."""
        user_id = uuid.uuid4()
        username = "testuser"

        token = create_refresh_token(user_id, username)

        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["user_id"] == str(user_id)
        assert payload["username"] == username
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token_expiration(self):
        """Test that refresh token expires in 7 days."""
        user_id = uuid.uuid4()
        username = "testuser"

        token = create_refresh_token(user_id, username)

        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Check expiration is approximately 7 days in the future
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        expected_exp = datetime.utcnow() + timedelta(days=7)

        # Allow 5 second tolerance
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 5


class TestAccessTokenVerification:
    """Test JWT access token verification."""

    def test_verify_access_token_valid(self):
        """Test that valid access token is verified successfully."""
        user_id = uuid.uuid4()
        username = "testuser"
        role = "admin"

        token = create_access_token(user_id, username, role)
        payload = verify_access_token(token)

        assert payload is not None
        assert payload["user_id"] == str(user_id)
        assert payload["username"] == username
        assert payload["role"] == role

    def test_verify_access_token_invalid_signature(self):
        """Test that token with invalid signature is rejected."""
        user_id = uuid.uuid4()
        username = "testuser"
        role = "engineer"

        # Create token with different secret
        token = jwt.encode(
            {"user_id": str(user_id), "username": username, "role": role, "type": "access"},
            "wrong_secret",
            algorithm=settings.JWT_ALGORITHM
        )

        payload = verify_access_token(token)
        assert payload is None

    def test_verify_access_token_expired(self):
        """Test that expired token is rejected."""
        user_id = uuid.uuid4()
        username = "testuser"
        role = "engineer"

        # Create expired token
        past_time = datetime.utcnow() - timedelta(hours=1)
        claims = {
            "user_id": str(user_id),
            "username": username,
            "role": role,
            "type": "access",
            "exp": past_time,
            "iat": past_time - timedelta(hours=2)
        }

        token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        payload = verify_access_token(token)
        assert payload is None

    def test_verify_access_token_wrong_type(self):
        """Test that refresh token is rejected when verifying access token."""
        user_id = uuid.uuid4()
        username = "testuser"

        # Create refresh token
        token = create_refresh_token(user_id, username)

        # Try to verify as access token
        payload = verify_access_token(token)
        assert payload is None

    def test_verify_access_token_missing_claims(self):
        """Test that token with missing claims is rejected."""
        # Token without role claim
        claims = {
            "user_id": str(uuid.uuid4()),
            "username": "testuser",
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "iat": datetime.utcnow()
        }

        token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        payload = verify_access_token(token)
        assert payload is None

    def test_verify_access_token_malformed(self):
        """Test that malformed token is rejected."""
        payload = verify_access_token("not.a.valid.jwt.token")
        assert payload is None


class TestRefreshTokenVerification:
    """Test JWT refresh token verification."""

    def test_verify_refresh_token_valid(self):
        """Test that valid refresh token is verified successfully."""
        user_id = uuid.uuid4()
        username = "testuser"

        token = create_refresh_token(user_id, username)
        payload = verify_refresh_token(token)

        assert payload is not None
        assert payload["user_id"] == str(user_id)
        assert payload["username"] == username
        assert payload["type"] == "refresh"

    def test_verify_refresh_token_wrong_type(self):
        """Test that access token is rejected when verifying refresh token."""
        user_id = uuid.uuid4()
        username = "testuser"
        role = "engineer"

        # Create access token
        token = create_access_token(user_id, username, role)

        # Try to verify as refresh token
        payload = verify_refresh_token(token)
        assert payload is None

    def test_verify_refresh_token_expired(self):
        """Test that expired refresh token is rejected."""
        user_id = uuid.uuid4()
        username = "testuser"

        # Create expired token
        past_time = datetime.utcnow() - timedelta(days=8)
        claims = {
            "user_id": str(user_id),
            "username": username,
            "type": "refresh",
            "exp": past_time,
            "iat": past_time - timedelta(days=1)
        }

        token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        payload = verify_refresh_token(token)
        assert payload is None


class TestAuthenticateUser:
    """Test user authentication function."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mocker):
        """Test successful user authentication."""
        # Mock database session
        db_mock = AsyncMock()

        # Create mock user
        user_id = uuid.uuid4()
        password = "test_password_123"
        hashed = hash_password(password)

        mock_user = User(
            user_id=user_id,
            username="testuser",
            email="test@example.com",
            password_hash=hashed,
            role="engineer",
            is_active=True,
        )

        # Mock get_user_by_username to return our mock user
        mocker.patch(
            "app.services.auth_service.get_user_by_username",
            return_value=mock_user
        )

        # Authenticate
        result = await authenticate_user(db_mock, "testuser", password)

        assert result is not None
        assert result.user_id == user_id
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mocker):
        """Test authentication failure with wrong password."""
        db_mock = AsyncMock()

        # Create mock user with different password
        password = "correct_password"
        hashed = hash_password(password)

        mock_user = User(
            user_id=uuid.uuid4(),
            username="testuser",
            email="test@example.com",
            password_hash=hashed,
            role="engineer",
        )

        mocker.patch(
            "app.services.auth_service.get_user_by_username",
            return_value=mock_user
        )

        # Try to authenticate with wrong password
        result = await authenticate_user(db_mock, "testuser", "wrong_password")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mocker):
        """Test authentication failure when user doesn't exist."""
        db_mock = AsyncMock()

        # Mock get_user_by_username to return None
        mocker.patch(
            "app.services.auth_service.get_user_by_username",
            return_value=None
        )

        result = await authenticate_user(db_mock, "nonexistent", "password")
        assert result is None

