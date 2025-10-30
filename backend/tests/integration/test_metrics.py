"""
Integration tests for Prometheus metrics endpoint and custom metrics.

Tests verify that:
1. /metrics endpoint is accessible and returns Prometheus format
2. HTTP metrics are automatically collected
3. Custom application metrics are registered and updated

Note: These tests use direct metric manipulation and mocking to avoid
database dependencies, as the test database (SQLite) does not support
all tables (only auth-related tables) due to PostgreSQL-specific types.
"""

import re

import pytest
from httpx import AsyncClient


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
async def test_command_metrics_update(
    async_client: AsyncClient,
) -> None:
    """
    Test that command execution metrics are updated correctly.

    This is a unit test that directly calls metric helper functions to verify
    the metrics system is working correctly, without requiring database operations.

    Verifies:
    - commands_executed_total increments after calling increment_command_counter
    - command_execution_duration_seconds records observations after calling observe_command_duration
    """
    from app.utils.metrics import increment_command_counter, observe_command_duration

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

    # Simulate command execution by directly updating metrics
    increment_command_counter("completed")
    observe_command_duration(2.5)  # Simulate 2.5 second execution

    # Get updated metrics
    response = await async_client.get("/metrics")
    updated_metrics = response.text

    # Verify commands_executed_total incremented
    updated_count = 0
    for line in updated_metrics.split("\n"):
        if line.startswith("commands_executed_total") and 'status="completed"' in line:
            updated_count = int(float(line.split()[-1]))
            break

    assert updated_count == initial_count + 1, "Command counter should have incremented by 1"

    # Verify command_execution_duration_seconds has observations
    # Check for histogram buckets or sum/count metrics
    assert "command_execution_duration_seconds_bucket" in updated_metrics or \
           "command_execution_duration_seconds_sum" in updated_metrics


@pytest.mark.asyncio
async def test_websocket_metrics_gauge(
    async_client: AsyncClient,
) -> None:
    """
    Test that WebSocket connection gauge metric updates correctly.

    This is a unit test that directly calls the WebSocket manager's
    connect/disconnect methods to verify the metrics system is working
    correctly, without requiring database operations.

    Verifies:
    - websocket_connections_active increments when connection is established
    - websocket_connections_active decrements when connection is closed
    """
    from unittest.mock import AsyncMock, MagicMock

    from fastapi import WebSocket

    from app.services.websocket_manager import websocket_manager

    # Get initial metrics
    response = await async_client.get("/metrics")
    initial_metrics = response.text

    # Extract initial WebSocket count
    initial_ws_count = 0
    for line in initial_metrics.split("\n"):
        if line.startswith("websocket_connections_active"):
            initial_ws_count = int(float(line.split()[-1]))
            break

    # Create mock WebSocket
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.close = AsyncMock()

    # Simulate WebSocket connection
    test_command_id = "test-command-123"
    await websocket_manager.connect(test_command_id, mock_ws)

    # Get metrics while connected and verify increment
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

    # Simulate disconnect
    await websocket_manager.disconnect(test_command_id, mock_ws)

    # Get metrics after disconnect and verify decrement
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
