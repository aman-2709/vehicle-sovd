"""
WebSocket connection manager service.

Manages active WebSocket connections and handles broadcasting events
to multiple clients subscribed to the same command ID.
"""

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class WebSocketManager:
    """
    Manager for active WebSocket connections.

    Tracks connections by command_id and supports broadcasting events
    to all clients subscribed to a specific command.
    """

    def __init__(self) -> None:
        """Initialize the WebSocket manager with empty connections dict."""
        # Maps command_id to list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, command_id: str, websocket: WebSocket) -> None:
        """
        Register a new WebSocket connection for a command.

        Args:
            command_id: Command UUID (string) to subscribe to
            websocket: WebSocket connection instance
        """
        if command_id not in self.active_connections:
            self.active_connections[command_id] = []

        self.active_connections[command_id].append(websocket)

        logger.info(
            "websocket_connection_registered",
            command_id=command_id,
            total_connections=len(self.active_connections[command_id])
        )

    async def disconnect(self, command_id: str, websocket: WebSocket) -> None:
        """
        Unregister a WebSocket connection from a command.

        Args:
            command_id: Command UUID (string) to unsubscribe from
            websocket: WebSocket connection instance
        """
        if command_id in self.active_connections:
            try:
                self.active_connections[command_id].remove(websocket)

                # Clean up empty command entries
                if not self.active_connections[command_id]:
                    del self.active_connections[command_id]
                    logger.info(
                        "websocket_command_channel_closed",
                        command_id=command_id
                    )
                else:
                    logger.info(
                        "websocket_connection_unregistered",
                        command_id=command_id,
                        remaining_connections=len(self.active_connections[command_id])
                    )
            except ValueError:
                logger.warning(
                    "websocket_disconnect_failed",
                    command_id=command_id,
                    reason="connection_not_found"
                )

    async def broadcast(self, command_id: str, message: dict) -> None:
        """
        Broadcast a message to all WebSocket clients subscribed to a command.

        Args:
            command_id: Command UUID (string) to broadcast to
            message: JSON-serializable message dict to send
        """
        if command_id not in self.active_connections:
            logger.debug(
                "websocket_broadcast_skipped",
                command_id=command_id,
                reason="no_active_connections"
            )
            return

        # Track failed connections to remove them
        failed_connections: list[WebSocket] = []

        for connection in self.active_connections[command_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(
                    "websocket_broadcast_failed",
                    command_id=command_id,
                    error=str(e),
                    exc_info=True
                )
                failed_connections.append(connection)

        # Clean up failed connections
        for failed_connection in failed_connections:
            await self.disconnect(command_id, failed_connection)

        logger.debug(
            "websocket_broadcast_completed",
            command_id=command_id,
            successful_sends=len(self.active_connections.get(command_id, [])),
            failed_sends=len(failed_connections)
        )

    def get_connection_count(self, command_id: str) -> int:
        """
        Get the number of active connections for a command.

        Args:
            command_id: Command UUID (string)

        Returns:
            Number of active WebSocket connections
        """
        empty_list: list[WebSocket] = []
        return len(self.active_connections.get(command_id, empty_list))


# Global singleton instance
websocket_manager = WebSocketManager()
