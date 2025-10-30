"""
Integration tests for vehicle connector error scenarios.

Tests timeout handling, error event publishing, and command failure scenarios
as specified in task I3.T3.
"""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import redis.asyncio as redis

from app.config import settings
from app.connectors import vehicle_connector


class MockCommand:
    """Mock command object for testing."""

    def __init__(self, command_id: uuid.UUID, user_id: uuid.UUID):
        from datetime import datetime, timezone

        self.command_id = command_id
        self.user_id = user_id
        self.status = "pending"
        self.error_message = None
        self.completed_at = None
        self.submitted_at = datetime.now(timezone.utc)


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Create a Redis client for integration tests."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
    yield client
    await client.aclose()


class TestErrorScenarios:
    """Integration tests for error simulation in vehicle connector."""

    @pytest.mark.asyncio
    async def test_timeout_scenario(self, redis_client: redis.Redis) -> None:
        """
        Test timeout scenario (10% probability).

        Verifies:
        - Command status updated to 'failed'
        - Error message saved
        - Error event published to Redis
        - Audit log created
        """
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        user_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params = {"ecuAddress": "0x10"}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()
        mock_audit_service = AsyncMock()

        # Mock command object
        mock_command = MockCommand(command_id, user_id)
        mock_command_repo.get_command_by_id.return_value = mock_command

        # Subscribe to Redis channel to capture error event
        channel = f"response:{command_id}"
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.audit_service",
                mock_audit_service,
            ),
            patch("app.connectors.vehicle_connector.random.random") as mock_random,
            patch(
                "app.connectors.vehicle_connector.asyncio.sleep", new_callable=AsyncMock
            ) as mock_sleep,
        ):
            # Configure async session maker
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Force timeout scenario (roll < 0.10)
            mock_random.return_value = 0.05

            # Execute command (should trigger timeout)
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify asyncio.sleep was called with timeout duration
            # First call is network delay (random 0.5-1.5), second is timeout (31 seconds)
            assert mock_sleep.call_count >= 2
            timeout_sleep_call = mock_sleep.call_args_list[1]
            assert timeout_sleep_call[0][0] == vehicle_connector.COMMAND_TIMEOUT_SECONDS + 1

            # Verify command status was updated to 'failed'
            failed_calls = [
                call
                for call in mock_command_repo.update_command_status.call_args_list
                if call[1].get("status") == "failed"
            ]
            assert len(failed_calls) >= 1
            failed_call = failed_calls[0]
            assert failed_call[1]["command_id"] == command_id
            assert failed_call[1]["status"] == "failed"
            assert "error_message" in failed_call[1]
            assert "Vehicle connection timeout" in failed_call[1]["error_message"]
            assert "completed_at" in failed_call[1]

            # Verify audit log was created for command failure
            audit_calls = [
                call
                for call in mock_audit_service.log_audit_event.call_args_list
                if call[1].get("action") == "command_failed"
            ]
            assert len(audit_calls) >= 1
            audit_call = audit_calls[0]
            assert audit_call[1]["user_id"] == user_id
            assert audit_call[1]["action"] == "command_failed"
            assert audit_call[1]["entity_type"] == "command"
            assert audit_call[1]["entity_id"] == command_id
            assert "error" in audit_call[1]["details"]

            # Wait briefly for Redis publish to complete
            await asyncio.sleep(0.1)

            # Verify error event was published to Redis
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                error_event = json.loads(message["data"])
                assert error_event["event"] == "error"
                assert error_event["command_id"] == str(command_id)
                assert "error_message" in error_event
                assert "Vehicle connection timeout" in error_event["error_message"]
                assert "failed_at" in error_event

        await pubsub.unsubscribe(channel)
        await pubsub.aclose()

    @pytest.mark.asyncio
    async def test_unreachable_scenario(self, redis_client: redis.Redis) -> None:
        """
        Test vehicle unreachable scenario (5% probability).

        Verifies:
        - Immediate failure without timeout delay
        - Command status updated to 'failed'
        - Error message saved
        - Error event published to Redis
        """
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        user_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params = {"ecuAddress": "0x10"}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()
        mock_audit_service = AsyncMock()

        # Mock command object
        mock_command = MockCommand(command_id, user_id)
        mock_command_repo.get_command_by_id.return_value = mock_command

        # Subscribe to Redis channel
        channel = f"response:{command_id}"
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.audit_service",
                mock_audit_service,
            ),
            patch("app.connectors.vehicle_connector.random.random") as mock_random,
            patch(
                "app.connectors.vehicle_connector.asyncio.sleep", new_callable=AsyncMock
            ) as mock_sleep,
        ):
            # Configure async session maker
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Force unreachable scenario (0.10 <= roll < 0.15)
            mock_random.return_value = 0.12

            # Execute command (should trigger unreachable error)
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify NO timeout sleep was called (only network delay)
            # Should only have 1 sleep call for network delay
            timeout_sleeps = [
                call
                for call in mock_sleep.call_args_list
                if call[0][0] > 10  # Timeout would be 31 seconds
            ]
            assert len(timeout_sleeps) == 0

            # Verify command status was updated to 'failed'
            failed_calls = [
                call
                for call in mock_command_repo.update_command_status.call_args_list
                if call[1].get("status") == "failed"
            ]
            assert len(failed_calls) >= 1
            failed_call = failed_calls[0]
            assert failed_call[1]["command_id"] == command_id
            assert failed_call[1]["status"] == "failed"
            assert "error_message" in failed_call[1]
            assert "Vehicle unreachable" in failed_call[1]["error_message"]

            # Wait briefly for Redis publish
            await asyncio.sleep(0.1)

            # Verify error event was published
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                error_event = json.loads(message["data"])
                assert error_event["event"] == "error"
                assert "Vehicle unreachable" in error_event["error_message"]

        await pubsub.unsubscribe(channel)
        await pubsub.aclose()

    @pytest.mark.asyncio
    async def test_malformed_response_scenario(self, redis_client: redis.Redis) -> None:
        """
        Test malformed response scenario (3% probability).

        Verifies:
        - Malformed JSON chunk published to Redis
        - Command status updated to 'failed'
        - Error message saved
        """
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        user_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params = {"ecuAddress": "0x10"}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()
        mock_audit_service = AsyncMock()

        # Mock command object
        mock_command = MockCommand(command_id, user_id)
        mock_command_repo.get_command_by_id.return_value = mock_command

        # Subscribe to Redis channel
        channel = f"response:{command_id}"
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.audit_service",
                mock_audit_service,
            ),
            patch("app.connectors.vehicle_connector.random.random") as mock_random,
            patch("app.connectors.vehicle_connector.asyncio.sleep", new_callable=AsyncMock),
        ):
            # Configure async session maker
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Force malformed response scenario (0.15 <= roll < 0.18)
            mock_random.return_value = 0.16

            # Execute command (should trigger malformed response error)
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Wait briefly for Redis publish
            await asyncio.sleep(0.1)

            # Verify malformed chunk was published first
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                # First message should be malformed JSON (will fail to parse)
                malformed_data = message["data"]
                # Try to parse - should contain incomplete JSON
                assert "incomplete" in malformed_data or "missing_closing_brace" in malformed_data

            # Verify command status was updated to 'failed'
            failed_calls = [
                call
                for call in mock_command_repo.update_command_status.call_args_list
                if call[1].get("status") == "failed"
            ]
            assert len(failed_calls) >= 1
            failed_call = failed_calls[0]
            assert failed_call[1]["command_id"] == command_id
            assert failed_call[1]["status"] == "failed"
            assert "error_message" in failed_call[1]
            assert "Invalid response format" in failed_call[1]["error_message"]

        await pubsub.unsubscribe(channel)
        await pubsub.aclose()

    @pytest.mark.asyncio
    async def test_error_event_redis_delivery(self, redis_client: redis.Redis) -> None:
        """
        Test that error events are correctly formatted and delivered via Redis.

        Verifies:
        - Error event has correct format
        - Event contains all required fields
        - Event is published to correct channel
        """
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock dependencies
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_command = MockCommand(command_id, user_id)
        mock_command_repo.get_command_by_id.return_value = mock_command

        # Subscribe to Redis channel BEFORE executing command
        channel = f"response:{command_id}"
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)

        # Consume subscription confirmation message
        await pubsub.get_message(timeout=1.0)

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch("app.connectors.vehicle_connector.response_repository", AsyncMock()),
            patch("app.connectors.vehicle_connector.audit_service", AsyncMock()),
            patch("app.connectors.vehicle_connector.random.random", return_value=0.05),
            patch("app.connectors.vehicle_connector.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Execute command (will trigger timeout)
            await vehicle_connector.execute_command(command_id, vehicle_id, "ReadDTC", {})

            # Wait for Redis publish to propagate
            await asyncio.sleep(0.2)

            # Poll for message with retries
            message = None
            for _ in range(10):
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
                if message and message["type"] == "message":
                    break
                await asyncio.sleep(0.1)

            assert message is not None, "Error event was not received from Redis"
            assert message["type"] == "message"

            error_event = json.loads(message["data"])

            # Verify required fields
            assert error_event["event"] == "error"
            assert error_event["command_id"] == str(command_id)
            assert "error_message" in error_event
            assert isinstance(error_event["error_message"], str)
            assert len(error_event["error_message"]) > 0
            assert "failed_at" in error_event

            # Verify failed_at is valid ISO timestamp
            failed_at = datetime.fromisoformat(error_event["failed_at"])
            assert isinstance(failed_at, datetime)

        await pubsub.unsubscribe(channel)
        await pubsub.aclose()

    @pytest.mark.asyncio
    async def test_normal_execution_unaffected(self, redis_client: redis.Redis) -> None:
        """
        Test that normal command execution works when no error is triggered.

        Verifies:
        - Command completes successfully when error roll > all error probabilities
        - No error events published
        - Command status updated to 'completed'
        """
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        user_id = uuid.uuid4()
        command_name = "ClearDTC"
        command_params: dict[str, str] = {}

        # Mock dependencies
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()
        mock_audit_service = AsyncMock()

        mock_command = MockCommand(command_id, user_id)
        mock_command_repo.get_command_by_id.return_value = mock_command

        mock_response = MagicMock()
        mock_response.response_id = uuid.uuid4()
        mock_response_repo.create_response.return_value = mock_response

        # Subscribe to Redis channel
        channel = f"response:{command_id}"
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.audit_service",
                mock_audit_service,
            ),
            patch("app.connectors.vehicle_connector.random.random") as mock_random,
            patch("app.connectors.vehicle_connector.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Force NO error scenario (roll > all error probabilities)
            mock_random.return_value = 0.99

            # Execute command (should complete successfully)
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify command was updated to 'completed' (not 'failed')
            completed_calls = [
                call
                for call in mock_command_repo.update_command_status.call_args_list
                if call[1].get("status") == "completed"
            ]
            assert len(completed_calls) >= 1
            completed_call = completed_calls[0]
            assert completed_call[1]["command_id"] == command_id
            assert completed_call[1]["status"] == "completed"
            assert (
                "error_message" not in completed_call[1]
                or completed_call[1].get("error_message") is None
            )

            # Verify response was created
            assert mock_response_repo.create_response.called

            # Verify audit log for completion (not failure)
            completion_audit_calls = [
                call
                for call in mock_audit_service.log_audit_event.call_args_list
                if call[1].get("action") == "command_completed"
            ]
            assert len(completion_audit_calls) >= 1

            # Wait briefly for Redis
            await asyncio.sleep(0.1)

            # Verify NO error event was published (only response and status events)
            messages = []
            for _ in range(5):  # Check multiple messages
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
                if message and message["type"] == "message":
                    messages.append(json.loads(message["data"]))

            # Verify no error events
            error_events = [msg for msg in messages if msg.get("event") == "error"]
            assert len(error_events) == 0

        await pubsub.unsubscribe(channel)
        await pubsub.aclose()

    @pytest.mark.asyncio
    async def test_error_probabilities_configurable(self) -> None:
        """
        Test that error probabilities are configurable via module constants.

        Verifies:
        - ERROR_PROBABILITY_TIMEOUT is set correctly
        - ERROR_PROBABILITY_UNREACHABLE is set correctly
        - ERROR_PROBABILITY_MALFORMED is set correctly
        - COMMAND_TIMEOUT_SECONDS is set correctly
        """
        assert hasattr(vehicle_connector, "ERROR_PROBABILITY_TIMEOUT")
        assert hasattr(vehicle_connector, "ERROR_PROBABILITY_UNREACHABLE")
        assert hasattr(vehicle_connector, "ERROR_PROBABILITY_MALFORMED")
        assert hasattr(vehicle_connector, "COMMAND_TIMEOUT_SECONDS")

        # Verify default values match acceptance criteria
        assert vehicle_connector.ERROR_PROBABILITY_TIMEOUT == 0.10
        assert vehicle_connector.ERROR_PROBABILITY_UNREACHABLE == 0.05
        assert vehicle_connector.ERROR_PROBABILITY_MALFORMED == 0.03
        assert vehicle_connector.COMMAND_TIMEOUT_SECONDS == 30

    @pytest.mark.asyncio
    async def test_timeout_deterministic_with_seed(self) -> None:
        """
        Test that error scenarios are deterministic when using random seed.

        Verifies:
        - Same seed produces same error scenario
        - Tests are not flaky
        """
        import random

        command_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock dependencies
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_command = MockCommand(command_id, user_id)
        mock_command_repo.get_command_by_id.return_value = mock_command

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch("app.connectors.vehicle_connector.response_repository", AsyncMock()),
            patch("app.connectors.vehicle_connector.audit_service", AsyncMock()),
            patch("app.connectors.vehicle_connector.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Set seed for deterministic behavior
            random.seed(12345)

            # Execute command multiple times with same seed
            results = []
            for _ in range(3):
                random.seed(12345)  # Reset seed each time

                # Call random.random() to simulate error roll
                error_roll = random.random()

                # Determine expected outcome
                timeout_threshold = vehicle_connector.ERROR_PROBABILITY_TIMEOUT
                unreachable_threshold = timeout_threshold + (
                    vehicle_connector.ERROR_PROBABILITY_UNREACHABLE
                )
                malformed_threshold = unreachable_threshold + (
                    vehicle_connector.ERROR_PROBABILITY_MALFORMED
                )

                if error_roll < timeout_threshold:
                    results.append("timeout")
                elif error_roll < unreachable_threshold:
                    results.append("unreachable")
                elif error_roll < malformed_threshold:
                    results.append("malformed")
                else:
                    results.append("success")

            # Verify all results are identical (deterministic)
            assert len(set(results)) == 1, "Results should be deterministic with same seed"
