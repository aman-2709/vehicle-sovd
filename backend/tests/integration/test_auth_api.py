"""
Integration tests for authentication API endpoints.

Tests all auth endpoints with success and error cases.
"""

from datetime import datetime, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.user import User
from app.services.auth_service import create_access_token, create_refresh_token, hash_password


class TestLoginEndpoint:
    """Test POST /api/v1/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test successful login with valid credentials."""
        # Create test user
        password = "test_password_123"
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password(password),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Login
        response = await async_client.post(
            "/api/v1/auth/login", json={"username": "testuser", "password": password}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] > 0

        # Verify refresh token is stored in database
        result = await db_session.execute(select(Session).where(Session.user_id == user.user_id))
        session = result.scalar_one_or_none()
        assert session is not None
        assert session.refresh_token == data["refresh_token"]

    @pytest.mark.asyncio
    async def test_login_invalid_username(self, async_client: AsyncClient):
        """Test login with non-existent username."""
        response = await async_client.post(
            "/api/v1/auth/login", json={"username": "nonexistent", "password": "password"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid username or password" in response.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_login_invalid_password(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test login with incorrect password."""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("correct_password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Try to login with wrong password
        response = await async_client.post(
            "/api/v1/auth/login", json={"username": "testuser", "password": "wrong_password"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test login with inactive user account."""
        # Create inactive user
        password = "test_password"
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=hash_password(password),
            role="engineer",
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/login", json={"username": "inactiveuser", "password": password}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, async_client: AsyncClient):
        """Test login with missing required fields."""
        # Missing password
        response = await async_client.post("/api/v1/auth/login", json={"username": "testuser"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing username
        response = await async_client.post("/api/v1/auth/login", json={"password": "password"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRefreshEndpoint:
    """Test POST /api/v1/auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test successful token refresh with valid refresh token."""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.flush()

        # Create refresh token
        refresh_token = create_refresh_token(user.user_id, user.username)

        # Store refresh token in database
        session = Session(
            user_id=user.user_id,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(session)
        await db_session.commit()

        # Refresh access token
        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, async_client: AsyncClient):
        """Test refresh with invalid JWT token."""
        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid.jwt.token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_token_not_in_database(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test refresh with valid JWT but not stored in database."""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Create valid refresh token but don't store in database
        refresh_token = create_refresh_token(user.user_id, user.username)

        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_expired_token(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test refresh with expired token in database."""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.flush()

        # Create refresh token
        refresh_token = create_refresh_token(user.user_id, user.username)

        # Store with expired timestamp
        session = Session(
            user_id=user.user_id,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
        )
        db_session.add(session)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_inactive_user(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test refresh when user becomes inactive."""
        # Create user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.flush()

        # Create refresh token
        refresh_token = create_refresh_token(user.user_id, user.username)
        session = Session(
            user_id=user.user_id,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(session)
        await db_session.commit()

        # Deactivate user
        user.is_active = False
        await db_session.commit()

        # Try to refresh
        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestLogoutEndpoint:
    """Test POST /api/v1/auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test successful logout invalidates all refresh tokens."""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.flush()

        # Create multiple sessions
        for _ in range(3):
            refresh_token = create_refresh_token(user.user_id, user.username)
            session = Session(
                user_id=user.user_id,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            db_session.add(session)
        await db_session.commit()

        # Create access token
        access_token = create_access_token(user.user_id, user.username, user.role)

        # Logout
        response = await async_client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Logged out successfully" in response.json()["message"]

        # Verify all sessions are deleted
        result = await db_session.execute(select(Session).where(Session.user_id == user.user_id))
        sessions = result.scalars().all()
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_logout_missing_token(self, async_client: AsyncClient):
        """Test logout without authentication token."""
        response = await async_client.post("/api/v1/auth/logout")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, async_client: AsyncClient):
        """Test logout with invalid token."""
        response = await async_client.post(
            "/api/v1/auth/logout", headers={"Authorization": "Bearer invalid.jwt.token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUserProfileEndpoint:
    """Test GET /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test successful retrieval of current user profile."""
        # Create test user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="admin",
        )
        db_session.add(user)
        await db_session.commit()

        # Create access token
        access_token = create_access_token(user.user_id, user.username, user.role)

        # Get profile
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["user_id"] == str(user.user_id)
        assert data["username"] == "testuser"
        assert data["role"] == "admin"
        assert data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_me_missing_token(self, async_client: AsyncClient):
        """Test /me without authentication token."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, async_client: AsyncClient):
        """Test /me with invalid token."""
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_me_user_deleted(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test /me when user is deleted after token was issued."""
        # Create user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Create access token
        access_token = create_access_token(user.user_id, user.username, user.role)

        # Delete user using SQL delete (bypasses ORM cascade)
        user_id = user.user_id
        from sqlalchemy import delete as sql_delete

        await db_session.execute(sql_delete(User).where(User.user_id == user_id))
        await db_session.commit()

        # Try to get profile
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRoleBasedAccessControl:
    """Test RBAC with require_role dependency."""

    @pytest.mark.asyncio
    async def test_require_role_admin_success(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that admin user can access admin-only endpoint."""
        # Note: This will be tested when we create endpoints that use require_role
        # For now, we test the dependency directly in unit tests
        pass

    @pytest.mark.asyncio
    async def test_require_role_engineer_blocked(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that engineer user is blocked from admin-only endpoint."""
        # Note: This will be tested when we create endpoints that use require_role
        pass


class TestAuthEndpointEdgeCases:
    """Test edge cases and error paths for auth endpoints."""

    @pytest.mark.asyncio
    async def test_login_with_invalid_json(self, async_client: AsyncClient):
        """Test login with malformed JSON payload."""
        response = await async_client.post(
            "/api/v1/auth/login",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        # FastAPI returns 422 for invalid JSON
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_login_with_empty_username(self, async_client: AsyncClient):
        """Test login with empty username."""
        response = await async_client.post(
            "/api/v1/auth/login", json={"username": "", "password": "password"}
        )
        # Should either fail validation or authentication
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    @pytest.mark.asyncio
    async def test_login_with_empty_password(self, async_client: AsyncClient):
        """Test login with empty password."""
        response = await async_client.post(
            "/api/v1/auth/login", json={"username": "testuser", "password": ""}
        )
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    @pytest.mark.asyncio
    async def test_refresh_with_missing_field(self, async_client: AsyncClient):
        """Test refresh endpoint with missing refresh_token field."""
        response = await async_client.post("/api/v1/auth/refresh", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_refresh_with_empty_token(self, async_client: AsyncClient):
        """Test refresh endpoint with empty refresh token."""
        response = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": ""})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_instead(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test refresh endpoint with access token (wrong token type)."""
        # Create user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Create access token (not refresh token)
        access_token = create_access_token(user.user_id, user.username, user.role)

        # Try to refresh with access token
        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": access_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_logout_with_malformed_header(self, async_client: AsyncClient):
        """Test logout with malformed Authorization header."""
        # Missing "Bearer " prefix
        response = await async_client.post(
            "/api/v1/auth/logout", headers={"Authorization": "not-a-bearer-token"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_logout_with_empty_token(self, async_client: AsyncClient):
        """Test logout with empty Bearer token."""
        response = await async_client.post(
            "/api/v1/auth/logout", headers={"Authorization": "Bearer "}
        )
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @pytest.mark.asyncio
    async def test_get_me_with_malformed_header(self, async_client: AsyncClient):
        """Test /me with malformed Authorization header."""
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": "InvalidFormat"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_me_with_expired_token(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test /me with expired access token."""
        from datetime import datetime, timedelta

        from jose import jwt

        from app.config import settings

        # Create user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Create expired token
        past_time = datetime.utcnow() - timedelta(hours=1)
        claims = {
            "user_id": str(user.user_id),
            "username": user.username,
            "role": user.role,
            "type": "access",
            "exp": past_time,
            "iat": past_time - timedelta(hours=2),
        }
        expired_token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_me_with_token_missing_claims(self, async_client: AsyncClient):
        """Test /me with token missing required claims."""
        from datetime import datetime, timedelta

        from jose import jwt

        from app.config import settings

        # Create token without user_id claim
        claims = {
            "username": "testuser",
            "role": "engineer",
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "iat": datetime.utcnow(),
        }
        invalid_token = jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {invalid_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_me_inactive_user_with_valid_token(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test /me when user becomes inactive after token was issued."""
        # Create active user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Create valid token
        access_token = create_access_token(user.user_id, user.username, user.role)

        # Deactivate user
        user.is_active = False
        await db_session.commit()

        # Try to access with valid token
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_user_not_found_cleanup(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that refresh endpoint cleans up session when user not found."""
        # Create user
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.flush()

        user_id = user.user_id

        # Create valid refresh token and session
        refresh_token = create_refresh_token(user.user_id, user.username)
        session = Session(
            user_id=user.user_id,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(session)
        await db_session.commit()

        # Delete user (simulating user deletion)
        from sqlalchemy import delete as sql_delete

        await db_session.execute(sql_delete(User).where(User.user_id == user_id))
        await db_session.commit()

        # Try to refresh - should fail and cleanup session
        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify session was cleaned up
        result = await db_session.execute(
            select(Session).where(Session.refresh_token == refresh_token)
        )
        cleaned_session = result.scalar_one_or_none()
        assert cleaned_session is None


class TestEndToEndAuthFlow:
    """Test complete authentication flow."""

    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test login -> access protected endpoint -> refresh -> logout flow."""
        # 1. Create user
        password = "test_password"
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password(password),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # 2. Login
        login_response = await async_client.post(
            "/api/v1/auth/login", json={"username": "testuser", "password": password}
        )
        assert login_response.status_code == status.HTTP_200_OK
        tokens = login_response.json()

        # 3. Access protected endpoint with access token
        me_response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_response.status_code == status.HTTP_200_OK
        profile = me_response.json()
        assert profile["username"] == "testuser"

        # 4. Refresh token
        refresh_response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == status.HTTP_200_OK
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens

        # 5. Use new access token
        me_response2 = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
        )
        assert me_response2.status_code == status.HTTP_200_OK

        # 6. Logout
        logout_response = await async_client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {new_tokens['access_token']}"}
        )
        assert logout_response.status_code == status.HTTP_200_OK

        # 7. Verify refresh token no longer works
        refresh_after_logout = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_after_logout.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthAPISpecificCoverage:
    """Additional tests to ensure full coverage of auth API endpoints."""

    @pytest.mark.asyncio
    async def test_login_success_with_all_fields(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test login success path to cover token generation and session creation."""
        # Create active user
        password = "ValidPassword123"
        user = User(
            username="coverageuser",
            email="coverage@example.com",
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Login to trigger full success path
        response = await async_client.post(
            "/api/v1/auth/login", json={"username": "coverageuser", "password": password}
        )

        # Verify full response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

        # Verify session was created in database
        result = await db_session.execute(select(Session).where(Session.user_id == user.user_id))
        session = result.scalar_one_or_none()
        assert session is not None

    @pytest.mark.asyncio
    async def test_refresh_success_full_path(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test refresh endpoint success to cover user lookup and token generation."""
        # Create user
        user = User(
            username="refreshuser",
            email="refresh@example.com",
            password_hash=hash_password("password"),
            role="engineer",
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        # Create valid refresh token and session
        refresh_token = create_refresh_token(user.user_id, user.username)
        session = Session(
            user_id=user.user_id,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db_session.add(session)
        await db_session.commit()

        # Refresh to trigger full success path
        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    @pytest.mark.asyncio
    async def test_logout_success_full_path(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test logout endpoint to cover session deletion."""
        # Create user
        user = User(
            username="logoutuser",
            email="logout@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.flush()

        # Create sessions
        for i in range(2):
            refresh_token = create_refresh_token(user.user_id, user.username)
            session = Session(
                user_id=user.user_id,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            db_session.add(session)
        await db_session.commit()

        # Create access token
        access_token = create_access_token(user.user_id, user.username, user.role)

        # Logout
        response = await async_client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Logged out successfully"

    @pytest.mark.asyncio
    async def test_get_me_success_full_path(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test /me endpoint to cover user profile retrieval."""
        # Create user
        user = User(
            username="profileuser",
            email="profile@example.com",
            password_hash=hash_password("password"),
            role="engineer",
        )
        db_session.add(user)
        await db_session.commit()

        # Create access token
        access_token = create_access_token(user.user_id, user.username, user.role)

        # Get profile
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == str(user.user_id)
        assert data["username"] == "profileuser"
        assert data["email"] == "profile@example.com"
        assert data["role"] == "engineer"
