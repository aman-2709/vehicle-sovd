"""
Logging middleware for request correlation tracking.

Generates unique correlation IDs for each request and injects them into
the logging context for tracing requests through the application.
"""

import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate correlation IDs and inject into logging context.

    For each incoming request:
    1. Extracts or generates a correlation ID (X-Request-ID header)
    2. Binds correlation ID to structlog context variables
    3. Logs request start and completion
    4. Clears context after request completion

    The correlation ID appears in all logs generated during request processing,
    making it easy to trace a single request through the entire application.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process each request with correlation ID tracking.

        Args:
            request: Incoming FastAPI request
            call_next: Next middleware/endpoint in the chain

        Returns:
            Response from the endpoint
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Request-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Bind correlation ID to logging context
        bind_contextvars(correlation_id=correlation_id)

        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        try:
            # Process request
            response = await call_next(request)

            # Add correlation ID to response headers
            response.headers["X-Request-ID"] = correlation_id

            # Log request completion
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )

            return response

        except Exception as e:
            # Log request failure
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                exc_info=True,
            )
            raise

        finally:
            # Clear context variables after request
            clear_contextvars()
