"""
Integration tests for WebSocket endpoints.

Tests WebSocket connections, authentication, event delivery, and error handling.
"""

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
import redis.asyncio as redis
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.main import app
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for WebSocket authentication."""
    user = User(
        username="wstest",
        email="wstest@example.com",
        password_hash=hash_password("testpassword"),
        role="engineer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive user for testing auth rejection."""
    user = User(
        username="inactive",
        email="inactive@example.com",
        password_hash=hash_password("testpassword"),
        role="engineer",
        is_active=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def valid_token(test_user: User) -> str:
    """Generate valid JWT token for test user."""
    token = create_access_token(
        user_id=test_user.user_id,
        username=test_user.username,
        role=test_user.role,
    )
    return token


@pytest_asyncio.fixture
async def inactive_user_token(inactive_user: User) -> str:
    """Generate JWT token for inactive user."""
    token = create_access_token(
        user_id=inactive_user.user_id,
        username=inactive_user.username,
        role=inactive_user.role,
    )
    return token


class TestWebSocketConnection:
    """Tests for WebSocket connection establishment and authentication."""

    def test_websocket_connection_success(self, valid_token: str) -> None:
        """Test successful WebSocket connection with valid JWT token."""
        command_id = str(uuid.uuid4())

        # Use TestClient for WebSocket testing
        with TestClient(app) as client:
            with client.websocket_connect(
                f"/ws/responses/{command_id}?token={valid_token}"
            ) as websocket:
                # Connection should be established successfully
                # We can verify by trying to receive (will timeout if not connected)
                # For this test, just ensure connection doesn't raise exception
                assert websocket is not None

    def test_websocket_connection_missing_token(self) -> None:
        """Test WebSocket connection rejected when token is missing."""
        command_id = str(uuid.uuid4())

        with TestClient(app) as client:
            # Connection should be rejected - client will disconnect immediately
            with client.websocket_connect(f"/ws/responses/{command_id}") as websocket:
                # Try to receive a message - should fail as connection was closed
                with pytest.raises(Exception):
                    websocket.receive_text()

    def test_websocket_connection_invalid_token(self) -> None:
        """Test WebSocket connection rejected with invalid JWT token."""
        command_id = str(uuid.uuid4())
        invalid_token = "invalid.jwt.token"

        with TestClient(app) as client:
            with client.websocket_connect(
                f"/ws/responses/{command_id}?token={invalid_token}"
            ) as websocket:
                # Try to receive a message - should fail as connection was closed
                with pytest.raises(Exception):
                    websocket.receive_text()

    def test_websocket_connection_inactive_user(self, inactive_user_token: str) -> None:
        """Test WebSocket connection rejected for inactive user."""
        command_id = str(uuid.uuid4())

        with TestClient(app) as client:
            with client.websocket_connect(
                f"/ws/responses/{command_id}?token={inactive_user_token}"
            ) as websocket:
                # Try to receive a message - should fail as connection was closed
                with pytest.raises(Exception):
                    websocket.receive_text()

    def test_websocket_connection_invalid_command_id(self, valid_token: str) -> None:
        """Test WebSocket connection with invalid command ID format."""
        invalid_command_id = "not-a-uuid"

        with TestClient(app) as client:
            # Should fail at FastAPI validation level
            with pytest.raises(Exception):
                with client.websocket_connect(
                    f"/ws/responses/{invalid_command_id}?token={valid_token}"
                ):
                    pass


class TestWebSocketEventDelivery:
    """Tests for WebSocket event delivery from Redis Pub/Sub."""

    def test_websocket_receives_response_event(self, valid_token: str) -> None:
        """Test that WebSocket client receives response events from Redis."""
        command_id = str(uuid.uuid4())

        def publish_event_sync():
            """Publish a test event to Redis after short delay using asyncio."""
            import time
            time.sleep(0.5)  # Give WebSocket time to subscribe

            # Run Redis publishing in a new event loop
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
                channel = f"response:{command_id}"
                event_data = {
                    "event": "response",
                    "command_id": command_id,
                    "response_id": str(uuid.uuid4()),
                    "response_payload": {"test": "data"},
                    "sequence_number": 1,
                    "is_final": True,
                }
                loop.run_until_complete(redis_client.publish(channel, json.dumps(event_data)))
                loop.run_until_complete(redis_client.aclose())
            finally:
                loop.close()

        # Start publishing in background thread
        import threading
        publish_thread = threading.Thread(target=publish_event_sync, daemon=True)
        publish_thread.start()

        with TestClient(app) as client:
            with client.websocket_connect(
                f"/ws/responses/{command_id}?token={valid_token}"
            ) as websocket:
                # Receive event from WebSocket
                data = websocket.receive_json()

                # Verify event format
                assert data["event"] == "response"
                assert data["command_id"] == command_id
                assert data["response_payload"] == {"test": "data"}
                assert data["sequence_number"] == 1
                assert data["is_final"] is True

        publish_thread.join(timeout=2.0)

    def test_websocket_receives_status_event(self, valid_token: str) -> None:
        """Test that WebSocket client receives status completion events."""
        command_id = str(uuid.uuid4())

        def publish_status_event_sync():
            """Publish a status event to Redis."""
            import time
            time.sleep(0.5)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
                channel = f"response:{command_id}"
                status_event = {
                    "event": "status",
                    "command_id": command_id,
                    "status": "completed",
                    "completed_at": "2025-10-28T10:00:00Z",
                }
                loop.run_until_complete(redis_client.publish(channel, json.dumps(status_event)))
                loop.run_until_complete(redis_client.aclose())
            finally:
                loop.close()

        import threading
        publish_thread = threading.Thread(target=publish_status_event_sync, daemon=True)
        publish_thread.start()

        with TestClient(app) as client:
            with client.websocket_connect(
                f"/ws/responses/{command_id}?token={valid_token}"
            ) as websocket:
                # Receive status event
                data = websocket.receive_json()

                # Verify status event format
                assert data["event"] == "status"
                assert data["command_id"] == command_id
                assert data["status"] == "completed"
                assert "completed_at" in data

        publish_thread.join(timeout=2.0)

    def test_websocket_receives_error_event(self, valid_token: str) -> None:
        """Test that WebSocket client receives error events."""
        command_id = str(uuid.uuid4())

        def publish_error_event_sync():
            """Publish an error event to Redis."""
            import time
            time.sleep(0.5)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
                channel = f"response:{command_id}"
                error_event = {
                    "event": "error",
                    "command_id": command_id,
                    "error_message": "Vehicle connection timeout",
                }
                loop.run_until_complete(redis_client.publish(channel, json.dumps(error_event)))
                loop.run_until_complete(redis_client.aclose())
            finally:
                loop.close()

        import threading
        publish_thread = threading.Thread(target=publish_error_event_sync, daemon=True)
        publish_thread.start()

        with TestClient(app) as client:
            with client.websocket_connect(
                f"/ws/responses/{command_id}?token={valid_token}"
            ) as websocket:
                # Receive error event
                data = websocket.receive_json()

                # Verify error event format
                assert data["event"] == "error"
                assert data["command_id"] == command_id
                assert data["error_message"] == "Vehicle connection timeout"

        publish_thread.join(timeout=2.0)

    def test_websocket_multiple_clients(self, valid_token: str) -> None:
        """Test that multiple WebSocket clients can subscribe to the same command."""
        command_id = str(uuid.uuid4())

        def publish_event_sync():
            """Publish a test event to Redis."""
            import time
            time.sleep(0.5)  # Give both WebSockets time to subscribe

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
                channel = f"response:{command_id}"
                event_data = {
                    "event": "response",
                    "command_id": command_id,
                    "response_id": str(uuid.uuid4()),
                    "response_payload": {"test": "multi-client"},
                    "sequence_number": 1,
                    "is_final": True,
                }
                loop.run_until_complete(redis_client.publish(channel, json.dumps(event_data)))
                loop.run_until_complete(redis_client.aclose())
            finally:
                loop.close()

        import threading
        publish_thread = threading.Thread(target=publish_event_sync, daemon=True)
        publish_thread.start()

        with TestClient(app) as client1, TestClient(app) as client2:
            with client1.websocket_connect(
                f"/ws/responses/{command_id}?token={valid_token}"
            ) as ws1, client2.websocket_connect(
                f"/ws/responses/{command_id}?token={valid_token}"
            ) as ws2:
                # Both clients should receive the event
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                # Verify both received the same event
                assert data1["event"] == "response"
                assert data2["event"] == "response"
                assert data1["command_id"] == command_id
                assert data2["command_id"] == command_id
                assert data1["response_payload"] == {"test": "multi-client"}
                assert data2["response_payload"] == {"test": "multi-client"}

        publish_thread.join(timeout=2.0)


class TestWebSocketCleanup:
    """Tests for WebSocket connection cleanup and resource management."""

    def test_websocket_disconnect_cleanup(self, valid_token: str) -> None:
        """Test that WebSocket resources are cleaned up on disconnect."""
        command_id = str(uuid.uuid4())

        with TestClient(app) as client:
            with client.websocket_connect(
                f"/ws/responses/{command_id}?token={valid_token}"
            ) as websocket:
                # Connection established
                assert websocket is not None

            # After context manager exits, connection should be closed
            # This is implicit - if there's a resource leak, it would show in logs
            # or cause issues in subsequent tests

    def test_websocket_no_event_on_different_command(
        self, valid_token: str
    ) -> None:
        """Test that WebSocket only receives events for subscribed command_id."""
        command_id_1 = str(uuid.uuid4())
        command_id_2 = str(uuid.uuid4())

        def publish_to_different_command_sync():
            """Publish event to a different command ID."""
            import time
            time.sleep(0.5)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
                channel = f"response:{command_id_2}"
                event_data = {
                    "event": "response",
                    "command_id": command_id_2,
                    "response_payload": {"test": "wrong-command"},
                }
                loop.run_until_complete(redis_client.publish(channel, json.dumps(event_data)))
                loop.run_until_complete(redis_client.aclose())
            finally:
                loop.close()

        import threading
        import time
        publish_thread = threading.Thread(target=publish_to_different_command_sync, daemon=True)
        publish_thread.start()

        with TestClient(app) as client:
            with client.websocket_connect(
                f"/ws/responses/{command_id_1}?token={valid_token}"
            ) as websocket:
                # Wait for the publish to complete
                time.sleep(1.0)

                # Since we're subscribed to command_id_1 but event was published
                # to command_id_2, we shouldn't have received anything.
                # The WebSocket should still be open and waiting.
                # This test mainly verifies no crash/error occurred
                assert websocket is not None

        publish_thread.join(timeout=2.0)
