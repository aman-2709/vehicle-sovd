"""
Integration tests for Prometheus metrics endpoint and custom metrics.

Tests verify that:
1. /metrics endpoint is accessible and returns Prometheus format
2. HTTP metrics are automatically collected
3. Custom application metrics are registered and updated
"""

import asyncio
import re
import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.vehicle import Vehicle
from app.services.auth_service import create_access_token, hash_password


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for authentication."""
    user = User(
        username="metricsuser",
        email="metrics@example.com",
        password_hash=hash_password("testpassword"),
        role="engineer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_token(test_user: User) -> str:
    """Generate authentication token for test user."""
    token = create_access_token(
        user_id=test_user.user_id,
        username=test_user.username,
        role=test_user.role,
    )
    return token


@pytest.fixture
def mock_vehicle() -> Vehicle:
    """Create a mock vehicle object."""
    vehicle = Vehicle(
        vehicle_id=uuid.UUID("a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"),
        vin="TESTMETRICS00001",
        make="Tesla",
        model="Model Y",
        year=2024,
        connection_status="connected",
        vehicle_metadata={}
    )
    return vehicle


@pytest.fixture
def test_vehicle_id(mock_vehicle: Vehicle) -> str:
    """Get test vehicle ID as string."""
    return str(mock_vehicle.vehicle_id)


@pytest.mark.asyncio
async def test_metrics_endpoint_accessible(async_client: AsyncClient) -> None:
    """
    Test that the /metrics endpoint is accessible.

    Verifies:
    - Returns 200 status code
    - Returns text/plain content type
    - Response is not empty
    """
    response = await async_client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert len(response.text) > 0


@pytest.mark.asyncio
async def test_metrics_prometheus_format(async_client: AsyncClient) -> None:
    """
    Test that metrics are returned in Prometheus exposition format.

    Verifies:
    - Contains HELP and TYPE comments
    - Contains metric names with valid Prometheus syntax
    """
    response = await async_client.get("/metrics")

    metrics_text = response.text

    # Check for Prometheus format indicators
    assert "# HELP" in metrics_text
    assert "# TYPE" in metrics_text

    # Verify basic Prometheus metric syntax (metric_name{labels} value timestamp)
    # Should have lines with metric names (alphanumeric + underscores)
    metric_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*(\{.*\})?\s+[\d\.e\+\-]+', re.MULTILINE)
    assert metric_pattern.search(metrics_text) is not None


@pytest.mark.asyncio
async def test_http_metrics_present(async_client: AsyncClient) -> None:
    """
    Test that automatic HTTP metrics are collected by the instrumentator.

    Verifies presence of:
    - http_requests_total: Counter of HTTP requests
    - http_request_duration_seconds: Histogram of request latency
    """
    # Make a request to generate HTTP metrics
    await async_client.get("/health")

    # Fetch metrics
    response = await async_client.get("/metrics")
    metrics_text = response.text

    # Verify HTTP metrics are present
    assert "http_requests_total" in metrics_text or "http_request_duration_seconds" in metrics_text


@pytest.mark.asyncio
async def test_custom_metrics_registered(async_client: AsyncClient) -> None:
    """
    Test that custom application metrics are registered in /metrics output.

    Verifies presence of:
    - commands_executed_total
    - command_execution_duration_seconds
    - websocket_connections_active
    - vehicle_connections_active
    """
    response = await async_client.get("/metrics")
    metrics_text = response.text

    # Verify all custom metrics are registered
    assert "commands_executed_total" in metrics_text
    assert "command_execution_duration_seconds" in metrics_text
    assert "websocket_connections_active" in metrics_text
    assert "vehicle_connections_active" in metrics_text


@pytest.mark.asyncio
@patch("app.repositories.vehicle_repository.get_vehicle_by_id")
async def test_command_metrics_update(
    mock_get_vehicle,
    async_client: AsyncClient,
    test_user_token: str,
    test_vehicle_id: str,
    mock_vehicle: Vehicle,
) -> None:
    """
    Test that command execution metrics are updated correctly.

    Verifies:
    - commands_executed_total increments after command completion
    - command_execution_duration_seconds records observations
    """
    # Mock vehicle repository to return mock vehicle
    mock_get_vehicle.return_value = mock_vehicle

    # Get initial metrics
    response = await async_client.get("/metrics")
    initial_metrics = response.text

    # Extract initial command count (if any)
    initial_count = 0
    for line in initial_metrics.split("\n"):
        if line.startswith("commands_executed_total") and 'status="completed"' in line:
            # Extract the value (last token on the line)
            initial_count = int(float(line.split()[-1]))
            break

    # Submit a command
    command_response = await async_client.post(
        "/api/v1/commands",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "vehicle_id": test_vehicle_id,
            "command_name": "ReadDTC",
            "command_params": {},
        },
    )

    assert command_response.status_code == 201
    command_id = command_response.json()["command_id"]

    # Wait for command to complete (mock connector completes quickly)
    # Poll command status until it's completed
    max_attempts = 20
    for _ in range(max_attempts):
        status_response = await async_client.get(
            f"/api/v1/commands/{command_id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        command_data = status_response.json()
        if command_data["status"] == "completed":
            break
        await asyncio.sleep(0.1)

    # Verify command completed
    assert command_data["status"] == "completed"

    # Get updated metrics
    response = await async_client.get("/metrics")
    updated_metrics = response.text

    # Verify commands_executed_total incremented
    updated_count = 0
    for line in updated_metrics.split("\n"):
        if line.startswith("commands_executed_total") and 'status="completed"' in line:
            updated_count = int(float(line.split()[-1]))
            break

    assert updated_count > initial_count, "Command counter should have incremented"

    # Verify command_execution_duration_seconds has observations
    # Check for histogram buckets or sum/count metrics
    assert "command_execution_duration_seconds_bucket" in updated_metrics or \
           "command_execution_duration_seconds_sum" in updated_metrics


@pytest.mark.asyncio
@patch("app.repositories.vehicle_repository.get_vehicle_by_id")
async def test_websocket_metrics_gauge(
    mock_get_vehicle,
    async_client: AsyncClient,
    test_user_token: str,
    test_vehicle_id: str,
    mock_vehicle: Vehicle,
) -> None:
    """
    Test that WebSocket connection gauge metric updates correctly.

    Verifies:
    - websocket_connections_active increments when connection is established
    - websocket_connections_active decrements when connection is closed
    """
    # Mock vehicle repository to return mock vehicle
    mock_get_vehicle.return_value = mock_vehicle

    # Get initial metrics
    response = await async_client.get("/metrics")
    initial_metrics = response.text

    # Extract initial WebSocket count
    initial_ws_count = 0
    for line in initial_metrics.split("\n"):
        if line.startswith("websocket_connections_active"):
            initial_ws_count = int(float(line.split()[-1]))
            break

    # Create a command first (needed for WebSocket endpoint)
    command_response = await async_client.post(
        "/api/v1/commands",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "vehicle_id": test_vehicle_id,
            "command_name": "ReadDTC",
            "command_params": {},
        },
    )
    command_id = command_response.json()["command_id"]

    # Connect to WebSocket
    async with async_client.websocket_connect(
        f"/ws/responses/{command_id}?token={test_user_token}"
    ) as websocket:
        # Wait a bit for metrics to update
        await asyncio.sleep(0.2)

        # Get metrics while WebSocket is connected
        response = await async_client.get("/metrics")
        connected_metrics = response.text

        # Extract WebSocket count while connected
        connected_ws_count = 0
        for line in connected_metrics.split("\n"):
            if line.startswith("websocket_connections_active"):
                connected_ws_count = int(float(line.split()[-1]))
                break

        # Verify count incremented
        assert connected_ws_count == initial_ws_count + 1, \
            "WebSocket gauge should increment when connection established"

        # Receive any pending messages (to prevent warnings)
        try:
            while True:
                await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
        except asyncio.TimeoutError:
            pass

    # WebSocket closed - wait for cleanup
    await asyncio.sleep(0.2)

    # Get final metrics
    response = await async_client.get("/metrics")
    final_metrics = response.text

    # Extract final WebSocket count
    final_ws_count = 0
    for line in final_metrics.split("\n"):
        if line.startswith("websocket_connections_active"):
            final_ws_count = int(float(line.split()[-1]))
            break

    # Verify count decremented back to initial value
    assert final_ws_count == initial_ws_count, \
        "WebSocket gauge should decrement when connection closed"


@pytest.mark.asyncio
async def test_metrics_help_text(async_client: AsyncClient) -> None:
    """
    Test that custom metrics have proper HELP text documentation.

    Verifies:
    - Each custom metric has a HELP comment explaining its purpose
    """
    response = await async_client.get("/metrics")
    metrics_text = response.text

    # Extract HELP lines
    help_lines = [line for line in metrics_text.split("\n") if line.startswith("# HELP")]

    # Verify our custom metrics have HELP text
    metric_names = [
        "commands_executed_total",
        "command_execution_duration_seconds",
        "websocket_connections_active",
        "vehicle_connections_active",
    ]

    for metric_name in metric_names:
        help_exists = any(metric_name in line for line in help_lines)
        assert help_exists, f"Metric {metric_name} should have HELP documentation"


@pytest.mark.asyncio
async def test_metrics_type_declarations(async_client: AsyncClient) -> None:
    """
    Test that custom metrics have proper TYPE declarations.

    Verifies:
    - commands_executed_total is declared as counter
    - command_execution_duration_seconds is declared as histogram
    - websocket_connections_active is declared as gauge
    - vehicle_connections_active is declared as gauge
    """
    response = await async_client.get("/metrics")
    metrics_text = response.text

    # Extract TYPE lines
    type_lines = {
        line.split()[2]: line.split()[3]
        for line in metrics_text.split("\n")
        if line.startswith("# TYPE")
    }

    # Verify metric types
    assert type_lines.get("commands_executed_total") == "counter"
    assert type_lines.get("command_execution_duration_seconds") == "histogram"
    assert type_lines.get("websocket_connections_active") == "gauge"
    assert type_lines.get("vehicle_connections_active") == "gauge"
