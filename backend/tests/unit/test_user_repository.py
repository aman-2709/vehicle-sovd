"""
Unit tests for user repository.

Tests database access functions for user operations.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user_repository import (
    create_user,
    get_user_by_id,
    get_user_by_username,
)
from app.services.auth_service import hash_password


class TestGetUserByUsername:
    """Test get_user_by_username repository function."""

    @pytest.mark.asyncio
    async def test_get_user_by_username_found(self, db_session: AsyncSession):
        """Test retrieving existing user by username."""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Retrieve user
        result = await get_user_by_username(db_session, "testuser")

        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.role == "engineer"

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, db_session: AsyncSession):
        """Test retrieving non-existent user returns None."""
        result = await get_user_by_username(db_session, "nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_username_case_sensitive(self, db_session: AsyncSession):
        """Test that username lookup is case-sensitive."""
        # Create user with lowercase username
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Try to retrieve with different case
        result = await get_user_by_username(db_session, "TestUser")

        # Should not find (case-sensitive)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_username_empty_string(self, db_session: AsyncSession):
        """Test retrieving user with empty username."""
        result = await get_user_by_username(db_session, "")

        assert result is None


class TestGetUserById:
    """Test get_user_by_id repository function."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, db_session: AsyncSession):
        """Test retrieving existing user by UUID."""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="admin",
        )
        db_session.add(user)
        await db_session.commit()

        user_id = user.user_id

        # Retrieve user by ID
        result = await get_user_by_id(db_session, user_id)

        assert result is not None
        assert result.user_id == user_id
        assert result.username == "testuser"
        assert result.role == "admin"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        """Test retrieving non-existent user by UUID returns None."""
        # Generate random UUID that doesn't exist
        non_existent_id = uuid.uuid4()

        result = await get_user_by_id(db_session, non_existent_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_returns_correct_user(self, db_session: AsyncSession):
        """Test that get_user_by_id returns the correct user when multiple exist."""
        # Create multiple users
        user1 = User(
            username="user1",
            email="user1@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            password_hash=hash_password("password"),
            role="admin",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.commit()

        # Retrieve user2 by ID
        result = await get_user_by_id(db_session, user2.user_id)

        assert result is not None
        assert result.user_id == user2.user_id
        assert result.username == "user2"
        assert result.email == "user2@example.com"


class TestCreateUser:
    """Test create_user repository function."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession):
        """Test successful user creation."""
        password_hash = hash_password("test_password")

        user = await create_user(
            db_session,
            username="newuser",
            email="newuser@example.com",
            password_hash=password_hash,
            role="engineer",
        )

        assert user is not None
        assert user.user_id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.password_hash == password_hash
        assert user.role == "engineer"
        assert user.is_active is True

    @pytest.mark.asyncio
    async def test_create_user_default_role(self, db_session: AsyncSession):
        """Test that create_user uses 'engineer' as default role."""
        password_hash = hash_password("test_password")

        user = await create_user(
            db_session,
            username="defaultroleuser",
            email="default@example.com",
            password_hash=password_hash,
            # No role specified
        )

        assert user.role == "engineer"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, db_session: AsyncSession):
        """Test that creating user with duplicate username fails."""
        password_hash = hash_password("password")

        # Create first user
        await create_user(
            db_session, username="duplicate", email="user1@example.com", password_hash=password_hash
        )

        # Try to create second user with same username
        with pytest.raises(IntegrityError):
            await create_user(
                db_session,
                username="duplicate",  # Same username
                email="user2@example.com",
                password_hash=password_hash,
            )

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, db_session: AsyncSession):
        """Test that creating user with duplicate email fails."""
        password_hash = hash_password("password")

        # Create first user
        await create_user(
            db_session, username="user1", email="duplicate@example.com", password_hash=password_hash
        )

        # Try to create second user with same email
        with pytest.raises(IntegrityError):
            await create_user(
                db_session,
                username="user2",
                email="duplicate@example.com",  # Same email
                password_hash=password_hash,
            )

    @pytest.mark.asyncio
    async def test_create_user_with_admin_role(self, db_session: AsyncSession):
        """Test creating user with admin role."""
        password_hash = hash_password("admin_password")

        user = await create_user(
            db_session,
            username="adminuser",
            email="admin@example.com",
            password_hash=password_hash,
            role="admin",
        )

        assert user.role == "admin"

    @pytest.mark.asyncio
    async def test_create_user_auto_generates_uuid(self, db_session: AsyncSession):
        """Test that create_user auto-generates UUID for user_id."""
        password_hash = hash_password("password")

        user = await create_user(
            db_session, username="uuiduser", email="uuid@example.com", password_hash=password_hash
        )

        # user_id should be automatically generated
        assert user.user_id is not None
        assert isinstance(user.user_id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_create_user_sets_timestamps(self, db_session: AsyncSession):
        """Test that create_user sets created_at timestamp."""
        from datetime import datetime

        password_hash = hash_password("password")

        user = await create_user(
            db_session,
            username="timestampuser",
            email="timestamp@example.com",
            password_hash=password_hash,
        )

        # created_at should be set automatically
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)

        # created_at should be recent (within last minute)
        time_diff = datetime.utcnow() - user.created_at
        assert time_diff.total_seconds() < 60
