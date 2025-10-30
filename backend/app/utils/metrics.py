"""
Custom Prometheus metrics for SOVD Command WebApp.

This module defines application-specific metrics for monitoring:
- Command execution (count and duration)
- WebSocket connections
- Vehicle connections

Metrics are exposed via the /metrics endpoint and scraped by Prometheus.
"""

from prometheus_client import Counter, Gauge, Histogram

# Command execution metrics
commands_executed_total = Counter(
    'commands_executed_total',
    'Total number of SOVD commands executed',
    ['status']  # Labels: completed, failed, timeout
)

command_execution_duration_seconds = Histogram(
    'command_execution_duration_seconds',
    'Command execution duration in seconds (from submission to completion)',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]  # Bucket boundaries for histogram
)

# WebSocket connection metrics
websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Number of active WebSocket connections for real-time command updates'
)

# Vehicle connection metrics
vehicle_connections_active = Gauge(
    'vehicle_connections_active',
    'Number of vehicles currently connected to the system'
)


def increment_command_counter(status: str) -> None:
    """
    Increment the command execution counter with the given status.

    Args:
        status: Command status (completed, failed, timeout)
    """
    commands_executed_total.labels(status=status).inc()


def observe_command_duration(duration_seconds: float) -> None:
    """
    Record a command execution duration observation.

    Args:
        duration_seconds: Duration in seconds
    """
    command_execution_duration_seconds.observe(duration_seconds)


def increment_websocket_connections() -> None:
    """Increment the active WebSocket connections gauge."""
    websocket_connections_active.inc()


def decrement_websocket_connections() -> None:
    """Decrement the active WebSocket connections gauge."""
    websocket_connections_active.dec()


def set_vehicle_connections(count: int) -> None:
    """
    Set the number of active vehicle connections.

    Args:
        count: Number of connected vehicles
    """
    vehicle_connections_active.set(count)
