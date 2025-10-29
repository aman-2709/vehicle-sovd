"""
WebSocket API endpoints for real-time command response streaming.

Provides WebSocket connections for clients to receive command execution
updates in real-time via Redis Pub/Sub.
"""

import asyncio
import json
import uuid

import redis.asyncio as redis
import structlog
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import get_user_by_id
from app.services.auth_service import verify_access_token
from app.services.websocket_manager import websocket_manager

logger = structlog.get_logger(__name__)

router = APIRouter()


async def authenticate_websocket(
    websocket: WebSocket,
    token: str | None,
    db: AsyncSession
) -> User | None:
    """
    Authenticate WebSocket connection using JWT from query parameter.

    Args:
        websocket: WebSocket connection instance
        token: JWT token from query parameter
        db: Database session

    Returns:
        Authenticated User object, or None if authentication failed

    Note:
        On authentication failure, this function closes the WebSocket
        with WS_1008_POLICY_VIOLATION status code.
    """
    if not token:
        logger.warning("websocket_auth_failed", reason="missing_token")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Missing authentication token"
        )
        return None

    # Verify JWT token
    payload = verify_access_token(token)
    if not payload:
        logger.warning("websocket_auth_failed", reason="invalid_token")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid authentication token"
        )
        return None

    # Extract user_id from token
    user_id_str = payload.get("user_id")
    if not user_id_str:
        logger.warning("websocket_auth_failed", reason="missing_user_id")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
        return None

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        logger.warning(
            "websocket_auth_failed",
            reason="invalid_user_id_format",
            user_id=user_id_str
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid user ID format")
        return None

    # Fetch user from database
    user = await get_user_by_id(db, user_id)
    if not user:
        logger.warning("websocket_auth_failed", reason="user_not_found", user_id=user_id_str)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        return None

    # Verify user is active
    if not user.is_active:
        logger.warning("websocket_auth_failed", reason="user_inactive", user_id=user_id_str)
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="User account is inactive"
        )
        return None

    logger.info(
        "websocket_auth_success",
        user_id=str(user.user_id),
        username=user.username,
        role=user.role
    )
    return user


async def redis_listener(
    command_id: str,
    websocket: WebSocket,
    redis_client: redis.Redis,
    stop_event: asyncio.Event
) -> None:
    """
    Listen for Redis Pub/Sub messages and forward to WebSocket client.

    Args:
        command_id: Command UUID to subscribe to
        websocket: WebSocket connection to send messages to
        redis_client: Redis client instance
        stop_event: Asyncio event to signal when to stop listening

    Note:
        This coroutine runs until stop_event is set or an error occurs.
    """
    pubsub = redis_client.pubsub()
    channel = f"response:{command_id}"

    try:
        await pubsub.subscribe(channel)
        logger.info("redis_pubsub_subscribed", command_id=command_id, channel=channel)

        async for message in pubsub.listen():
            # Check if we should stop
            if stop_event.is_set():
                logger.debug("redis_listener_stopping", command_id=command_id)
                break

            # Only process actual messages (not subscribe confirmations)
            if message["type"] == "message":
                try:
                    # Parse event data from Redis
                    event_data = json.loads(message["data"])

                    logger.debug(
                        "redis_event_received",
                        command_id=command_id,
                        event_type=event_data.get("event")
                    )

                    # Forward event to WebSocket client
                    await websocket.send_json(event_data)

                    logger.debug(
                        "websocket_event_sent",
                        command_id=command_id,
                        event_type=event_data.get("event")
                    )

                    # Stop listening if we received a final status or error event
                    event_type = event_data.get("event")
                    if event_type == "status" and event_data.get("status") == "completed":
                        logger.info("redis_listener_command_completed", command_id=command_id)
                        break
                    elif event_type == "error":
                        logger.info("redis_listener_command_error", command_id=command_id)
                        break

                except json.JSONDecodeError as e:
                    logger.error(
                        "redis_event_parse_failed",
                        command_id=command_id,
                        error=str(e),
                        exc_info=True
                    )
                except Exception as e:
                    logger.error(
                        "websocket_send_failed",
                        command_id=command_id,
                        error=str(e),
                        exc_info=True
                    )
                    # If WebSocket send fails, stop listening
                    break

    except asyncio.CancelledError:
        logger.info("redis_listener_cancelled", command_id=command_id)
        raise
    except Exception as e:
        logger.error(
            "redis_listener_error",
            command_id=command_id,
            error=str(e),
            exc_info=True
        )
    finally:
        # Cleanup: unsubscribe from Redis channel
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info("redis_pubsub_unsubscribed", command_id=command_id, channel=channel)
        except Exception as e:
            logger.error(
                "redis_pubsub_cleanup_failed",
                command_id=command_id,
                error=str(e),
                exc_info=True
            )


async def websocket_receiver(websocket: WebSocket, stop_event: asyncio.Event) -> None:
    """
    Receive messages from WebSocket client and handle disconnection.

    Args:
        websocket: WebSocket connection
        stop_event: Asyncio event to signal when client disconnects

    Note:
        This coroutine runs until the client disconnects or an error occurs.
        It sets the stop_event to signal other tasks to stop.
    """
    try:
        while True:
            # Wait for messages from client (or disconnection)
            # We don't expect any messages, but this allows us to detect disconnection
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("websocket_client_disconnected")
        stop_event.set()
    except Exception as e:
        logger.error("websocket_receiver_error", error=str(e), exc_info=True)
        stop_event.set()


@router.websocket("/ws/responses/{command_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    command_id: uuid.UUID,
    token: str | None = None,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    WebSocket endpoint for receiving real-time command response updates.

    Connection: ws://localhost:8000/ws/responses/{command_id}?token={jwt}

    Protocol:
        - Client connects with JWT token in query parameter
        - Server validates token and accepts connection
        - Server subscribes to Redis Pub/Sub channel: response:{command_id}
        - Server forwards all events from Redis to WebSocket client
        - Connection closes when command completes or client disconnects

    Event types sent to client:
        - response: {"event": "response", "command_id": "...",
                     "response": {...}, "sequence_number": 1}
        - status: {"event": "status", "command_id": "...",
                   "status": "completed", "completed_at": "..."}
        - error: {"event": "error", "command_id": "...",
                  "error_message": "..."}

    Args:
        websocket: WebSocket connection
        command_id: UUID of the command to subscribe to
        token: JWT authentication token from query parameter
        db: Database session dependency

    Raises:
        WebSocketDisconnect: When client disconnects
    """
    command_id_str = str(command_id)

    # Accept WebSocket connection first (required before any other operations)
    await websocket.accept()

    logger.info(
        "websocket_connection_attempt",
        command_id=command_id_str,
        has_token=bool(token)
    )

    # Authenticate user
    user = await authenticate_websocket(websocket, token, db)
    if not user:
        # authenticate_websocket already closed the connection
        return

    logger.info(
        "websocket_connection_established",
        command_id=command_id_str,
        user_id=str(user.user_id),
        username=user.username
    )

    # Register connection with manager
    await websocket_manager.connect(command_id_str, websocket)

    # Create Redis client
    redis_client: redis.Redis = redis.from_url(  # type: ignore[no-untyped-call]
        settings.REDIS_URL, decode_responses=True
    )

    # Create stop event for coordinating tasks
    stop_event = asyncio.Event()

    # Create tasks for Redis listener and WebSocket receiver
    redis_task = asyncio.create_task(
        redis_listener(command_id_str, websocket, redis_client, stop_event)
    )
    receiver_task = asyncio.create_task(
        websocket_receiver(websocket, stop_event)
    )

    try:
        # Wait for either task to complete (disconnection or Redis completion)
        done, pending = await asyncio.wait(
            [redis_task, receiver_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel any remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        logger.error(
            "websocket_handler_error",
            command_id=command_id_str,
            user_id=str(user.user_id),
            error=str(e),
            exc_info=True
        )
    finally:
        # Cleanup: unregister connection and close Redis
        await websocket_manager.disconnect(command_id_str, websocket)

        try:
            await redis_client.aclose()
            logger.debug("redis_client_closed", command_id=command_id_str)
        except Exception as e:
            logger.error(
                "redis_client_close_failed",
                command_id=command_id_str,
                error=str(e),
                exc_info=True
            )

        # Close WebSocket if not already closed
        try:
            await websocket.close()
        except Exception:
            # Already closed or in invalid state
            pass

        logger.info(
            "websocket_connection_closed",
            command_id=command_id_str,
            user_id=str(user.user_id)
        )
