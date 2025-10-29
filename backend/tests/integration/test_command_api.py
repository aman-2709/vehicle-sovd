"""
Integration tests for command API endpoints.

Tests all command endpoints with authentication, authorization, and error cases.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.command import Command
from app.models.response import Response
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


@pytest_asyncio.fixture
async def test_engineer(db_session: AsyncSession) -> User:
    """Create a test engineer user for authentication."""
    user = User(
        username="testengineer",
        email="engineer@example.com",
        password_hash=hash_password("testpassword"),
        role="engineer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_viewer(db_session: AsyncSession) -> User:
    """Create a test viewer user (should not have command submission permission)."""
    user = User(
        username="testviewer",
        email="viewer@example.com",
        password_hash=hash_password("testpassword"),
        role="viewer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def engineer_auth_headers(test_engineer: User) -> dict[str, str]:
    """Generate authentication headers for engineer user."""
    token = create_access_token(
        user_id=test_engineer.user_id,
        username=test_engineer.username,
        role=test_engineer.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def viewer_auth_headers(test_viewer: User) -> dict[str, str]:
    """Generate authentication headers for viewer user."""
    token = create_access_token(
        user_id=test_viewer.user_id,
        username=test_viewer.username,
        role=test_viewer.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_commands() -> list:
    """Create mock test commands."""

    class MockCommand:
        def __init__(
            self,
            command_id,
            user_id,
            vehicle_id,
            command_name,
            command_params,
            status,
            error_message,
            submitted_at,
            completed_at,
        ):
            self.command_id = command_id
            self.user_id = user_id
            self.vehicle_id = vehicle_id
            self.command_name = command_name
            self.command_params = command_params
            self.status = status
            self.error_message = error_message
            self.submitted_at = submitted_at
            self.completed_at = completed_at

    user_id = uuid.UUID("123e4567-e89b-12d3-a456-426614174001")
    vehicle_id = uuid.UUID("223e4567-e89b-12d3-a456-426614174001")

    commands = [
        MockCommand(
            command_id=uuid.UUID("323e4567-e89b-12d3-a456-426614174001"),
            user_id=user_id,
            vehicle_id=vehicle_id,
            command_name="lockDoors",
            command_params={"duration": 3600},
            status="completed",
            error_message=None,
            submitted_at=datetime(2025, 10, 28, 10, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2025, 10, 28, 10, 0, 5, tzinfo=timezone.utc),
        ),
        MockCommand(
            command_id=uuid.UUID("323e4567-e89b-12d3-a456-426614174002"),
            user_id=user_id,
            vehicle_id=vehicle_id,
            command_name="unlockDoors",
            command_params={},
            status="in_progress",
            error_message=None,
            submitted_at=datetime(2025, 10, 28, 11, 0, 0, tzinfo=timezone.utc),
            completed_at=None,
        ),
        MockCommand(
            command_id=uuid.UUID("323e4567-e89b-12d3-a456-426614174003"),
            user_id=user_id,
            vehicle_id=vehicle_id,
            command_name="startEngine",
            command_params={"warm_up": True},
            status="failed",
            error_message="Vehicle not responding",
            submitted_at=datetime(2025, 10, 28, 12, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2025, 10, 28, 12, 0, 10, tzinfo=timezone.utc),
        ),
    ]
    return commands


class TestSubmitCommandEndpoint:
    """Test POST /api/v1/commands endpoint."""

    @pytest.mark.asyncio
    async def test_submit_command_success(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        test_engineer: User,
    ):
        """Test successful command submission by engineer."""
        vehicle_id = uuid.UUID("223e4567-e89b-12d3-a456-426614174001")
        command_id = uuid.UUID("323e4567-e89b-12d3-a456-426614174999")

        mock_command = Command(
            command_id=command_id,
            user_id=test_engineer.user_id,
            vehicle_id=vehicle_id,
            command_name="lockDoors",
            command_params={"duration": 3600},
            status="in_progress",
            submitted_at=datetime.now(timezone.utc),
        )

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.submit_command = AsyncMock(return_value=mock_command)

            payload = {
                "command_name": "lockDoors",
                "vehicle_id": str(vehicle_id),
                "command_params": {"duration": 3600},
            }

            response = await async_client.post(
                "/api/v1/commands",
                json=payload,
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()

            assert data["command_id"] == str(command_id)
            assert data["command_name"] == "lockDoors"
            assert data["status"] == "in_progress"
            assert data["command_params"] == {"duration": 3600}

    @pytest.mark.asyncio
    async def test_submit_command_vehicle_not_found(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test command submission with invalid vehicle ID."""
        vehicle_id = uuid.uuid4()

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.submit_command = AsyncMock(return_value=None)

            payload = {
                "command_name": "lockDoors",
                "vehicle_id": str(vehicle_id),
                "command_params": {},
            }

            response = await async_client.post(
                "/api/v1/commands",
                json=payload,
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "vehicle not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_submit_command_unauthorized(self, async_client: AsyncClient):
        """Test that command submission requires authentication."""
        payload = {
            "command_name": "lockDoors",
            "vehicle_id": str(uuid.uuid4()),
            "command_params": {},
        }

        response = await async_client.post("/api/v1/commands", json=payload)

        # FastAPI returns 403 Forbidden when no credentials provided
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_submit_command_insufficient_permissions(
        self,
        async_client: AsyncClient,
        viewer_auth_headers: dict[str, str],
    ):
        """Test that command submission requires engineer or admin role."""
        payload = {
            "command_name": "lockDoors",
            "vehicle_id": str(uuid.uuid4()),
            "command_params": {},
        }

        response = await async_client.post(
            "/api/v1/commands",
            json=payload,
            headers=viewer_auth_headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_submit_command_empty_params(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        test_engineer: User,
    ):
        """Test command submission with empty parameters."""
        vehicle_id = uuid.UUID("223e4567-e89b-12d3-a456-426614174001")
        command_id = uuid.UUID("323e4567-e89b-12d3-a456-426614174998")

        mock_command = Command(
            command_id=command_id,
            user_id=test_engineer.user_id,
            vehicle_id=vehicle_id,
            command_name="getStatus",
            command_params={},
            status="in_progress",
            submitted_at=datetime.now(timezone.utc),
        )

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.submit_command = AsyncMock(return_value=mock_command)

            payload = {
                "command_name": "getStatus",
                "vehicle_id": str(vehicle_id),
            }

            response = await async_client.post(
                "/api/v1/commands",
                json=payload,
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["command_params"] == {}

    @pytest.mark.asyncio
    async def test_submit_command_invalid_payload(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test command submission with missing required fields."""
        payload = {
            "command_name": "lockDoors",
            # Missing vehicle_id
        }

        response = await async_client.post(
            "/api/v1/commands",
            json=payload,
            headers=engineer_auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetCommandEndpoint:
    """Test GET /api/v1/commands/{command_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_command_success(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        test_commands: list,
    ):
        """Test getting a command by ID."""
        command = test_commands[0]

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_by_id = AsyncMock(return_value=command)

            response = await async_client.get(
                f"/api/v1/commands/{command.command_id}",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["command_id"] == str(command.command_id)
            assert data["command_name"] == "lockDoors"
            assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_command_not_found(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test getting a non-existent command."""
        command_id = uuid.uuid4()

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_by_id = AsyncMock(return_value=None)

            response = await async_client.get(
                f"/api/v1/commands/{command_id}",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_command_unauthorized(self, async_client: AsyncClient):
        """Test that getting command requires authentication."""
        command_id = uuid.uuid4()

        response = await async_client.get(f"/api/v1/commands/{command_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_command_invalid_uuid(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test getting command with invalid UUID format."""
        response = await async_client.get(
            "/api/v1/commands/invalid-uuid",
            headers=engineer_auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListCommandsEndpoint:
    """Test GET /api/v1/commands endpoint."""

    @pytest.mark.asyncio
    async def test_list_commands_no_filters(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        test_commands: list,
    ):
        """Test listing all commands without filters."""
        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_history = AsyncMock(return_value=test_commands)

            response = await async_client.get(
                "/api/v1/commands",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data["commands"]) == 3
            assert data["limit"] == 50
            assert data["offset"] == 0

    @pytest.mark.asyncio
    async def test_list_commands_filter_by_vehicle(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        test_commands: list,
    ):
        """Test filtering commands by vehicle ID."""
        vehicle_id = test_commands[0].vehicle_id

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_history = AsyncMock(return_value=test_commands)

            response = await async_client.get(
                f"/api/v1/commands?vehicle_id={vehicle_id}",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data["commands"]) == 3
            assert all(c["vehicle_id"] == str(vehicle_id) for c in data["commands"])

    @pytest.mark.asyncio
    async def test_list_commands_filter_by_status(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        test_commands: list,
    ):
        """Test filtering commands by status."""
        completed_commands = [c for c in test_commands if c.status == "completed"]

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_history = AsyncMock(return_value=completed_commands)

            response = await async_client.get(
                "/api/v1/commands?status=completed",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data["commands"]) == 1
            assert all(c["status"] == "completed" for c in data["commands"])

    @pytest.mark.asyncio
    async def test_list_commands_pagination(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
        test_commands: list,
    ):
        """Test pagination with limit and offset."""
        paginated_commands = [test_commands[0]]

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_history = AsyncMock(return_value=paginated_commands)

            response = await async_client.get(
                "/api/v1/commands?limit=1&offset=0",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data["commands"]) == 1
            assert data["limit"] == 1
            assert data["offset"] == 0

    @pytest.mark.asyncio
    async def test_list_commands_unauthorized(self, async_client: AsyncClient):
        """Test that listing commands requires authentication."""
        response = await async_client.get("/api/v1/commands")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_list_commands_invalid_limit(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test that invalid limit parameter returns validation error."""
        response = await async_client.get(
            "/api/v1/commands?limit=0",  # limit must be >= 1
            headers=engineer_auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_list_commands_invalid_offset(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test that invalid offset parameter returns validation error."""
        response = await async_client.get(
            "/api/v1/commands?offset=-1",  # offset must be >= 0
            headers=engineer_auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_list_commands_empty_result(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test listing commands with no results."""
        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_history = AsyncMock(return_value=[])

            response = await async_client.get(
                "/api/v1/commands",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data["commands"]) == 0


class TestGetCommandResponsesEndpoint:
    """Test GET /api/v1/commands/{command_id}/responses endpoint."""

    @pytest.mark.asyncio
    async def test_get_responses_empty(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test getting responses for command with no responses."""
        command_id = uuid.uuid4()

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_responses = AsyncMock(return_value=[])

            response = await async_client.get(
                f"/api/v1/commands/{command_id}/responses",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data == []
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_responses_single_response(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test getting a single response for a command."""
        command_id = uuid.uuid4()
        response_id = uuid.uuid4()

        mock_response = Response(
            response_id=response_id,
            command_id=command_id,
            response_payload={"status": "success", "data": "test data"},
            sequence_number=1,
            is_final=True,
            received_at=datetime.now(timezone.utc),
        )

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_responses = AsyncMock(
                return_value=[mock_response]
            )

            response = await async_client.get(
                f"/api/v1/commands/{command_id}/responses",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["response_id"] == str(response_id)
            assert data[0]["command_id"] == str(command_id)
            assert data[0]["response_payload"] == {
                "status": "success",
                "data": "test data",
            }
            assert data[0]["sequence_number"] == 1
            assert data[0]["is_final"] is True
            assert "received_at" in data[0]

    @pytest.mark.asyncio
    async def test_get_responses_multiple_ordered(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test getting multiple responses ordered by sequence_number."""
        command_id = uuid.uuid4()

        mock_responses = [
            Response(
                response_id=uuid.uuid4(),
                command_id=command_id,
                response_payload={"chunk": 1},
                sequence_number=1,
                is_final=False,
                received_at=datetime.now(timezone.utc),
            ),
            Response(
                response_id=uuid.uuid4(),
                command_id=command_id,
                response_payload={"chunk": 2},
                sequence_number=2,
                is_final=False,
                received_at=datetime.now(timezone.utc),
            ),
            Response(
                response_id=uuid.uuid4(),
                command_id=command_id,
                response_payload={"chunk": 3, "final": True},
                sequence_number=3,
                is_final=True,
                received_at=datetime.now(timezone.utc),
            ),
        ]

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_responses = AsyncMock(
                return_value=mock_responses
            )

            response = await async_client.get(
                f"/api/v1/commands/{command_id}/responses",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 3

            # Verify ordering by sequence_number
            assert data[0]["sequence_number"] == 1
            assert data[1]["sequence_number"] == 2
            assert data[2]["sequence_number"] == 3

            # Verify response_payload JSONB serialization
            assert data[0]["response_payload"] == {"chunk": 1}
            assert data[1]["response_payload"] == {"chunk": 2}
            assert data[2]["response_payload"] == {"chunk": 3, "final": True}

            # Verify is_final flags
            assert data[0]["is_final"] is False
            assert data[1]["is_final"] is False
            assert data[2]["is_final"] is True

    @pytest.mark.asyncio
    async def test_get_responses_unauthorized(
        self,
        async_client: AsyncClient,
    ):
        """Test that unauthorized requests are rejected."""
        command_id = uuid.uuid4()

        response = await async_client.get(
            f"/api/v1/commands/{command_id}/responses"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_responses_complex_jsonb_payload(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test JSONB payload with complex nested structure serializes correctly."""
        command_id = uuid.uuid4()

        complex_payload = {
            "diagnostics": {
                "engine": {"temperature": 85.5, "rpm": 2500, "status": "ok"},
                "battery": {"voltage": 12.6, "charge_percent": 95},
            },
            "sensors": [
                {"id": "sensor1", "value": 42.0},
                {"id": "sensor2", "value": 17.3},
            ],
            "metadata": {"timestamp": "2024-01-15T10:30:00Z", "version": "1.0"},
        }

        mock_response = Response(
            response_id=uuid.uuid4(),
            command_id=command_id,
            response_payload=complex_payload,
            sequence_number=1,
            is_final=True,
            received_at=datetime.now(timezone.utc),
        )

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_responses = AsyncMock(
                return_value=[mock_response]
            )

            response = await async_client.get(
                f"/api/v1/commands/{command_id}/responses",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1

            # Verify complex JSONB structure is correctly serialized
            assert data[0]["response_payload"] == complex_payload
            assert data[0]["response_payload"]["diagnostics"]["engine"]["rpm"] == 2500
            assert len(data[0]["response_payload"]["sensors"]) == 2

    @pytest.mark.asyncio
    async def test_get_responses_invalid_uuid(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test that invalid UUID format returns validation error."""
        response = await async_client.get(
            "/api/v1/commands/not-a-uuid/responses",
            headers=engineer_auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
