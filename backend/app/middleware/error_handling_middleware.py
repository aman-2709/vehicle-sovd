"""
Global error handling for standardized error responses.

Provides exception handlers that catch all exceptions (HTTPException, validation
errors, and unhandled exceptions) and format them into a consistent error response
structure with error codes, correlation IDs, and appropriate logging.
"""

from datetime import datetime, timezone

import structlog
from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from structlog.contextvars import get_contextvars

from app.utils.error_codes import (
    ErrorCode,
    get_error_message,
    http_exception_to_error_code,
)

logger = structlog.get_logger(__name__)

# Sensitive fields that should never appear in logs or error responses
SENSITIVE_FIELDS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "jwt",
    "secret",
    "api_key",
    "authorization",
}


def format_error_response(
    error_code: ErrorCode,
    message: str,
    correlation_id: str,
    path: str,
) -> dict:
    """
    Format a standardized error response.

    Error Response Format:
    {
        "error": {
            "code": "AUTH_001",
            "message": "Invalid username or password",
            "correlation_id": "uuid-here",
            "timestamp": "2025-10-30T14:48:00Z",
            "path": "/api/v1/auth/login"
        }
    }

    Args:
        error_code: The error code enum value
        message: Human-readable error message
        correlation_id: Request correlation ID
        path: Request path

    Returns:
        Dictionary containing the standardized error response
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "error": {
            "code": error_code.value,
            "message": message,
            "correlation_id": correlation_id,
            "timestamp": timestamp,
            "path": path,
        }
    }


async def handle_http_exception(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """
    Handle FastAPI HTTPException and format with error codes.

    Args:
        request: The incoming request
        exc: The HTTPException that was raised

    Returns:
        Formatted JSON error response with error code and correlation ID
    """
    # Get correlation ID from context (set by LoggingMiddleware)
    context_vars = get_contextvars()
    correlation_id = context_vars.get("correlation_id", "unknown")

    # Check if detail is a dict (e.g., health check responses)
    if isinstance(exc.detail, dict):
        # For dict details (like health checks), preserve the original structure
        # but add correlation_id and timestamp
        error_response = {
            **exc.detail,  # Preserve original dict structure
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Log the error with context
        logger.warning(
            "http_exception_dict_detail",
            status_code=exc.status_code,
            detail=exc.detail,
            path=str(request.url.path),
            method=request.method,
            client_host=request.client.host if request.client else None,
        )
    else:
        # For string details, use standard error code mapping
        detail_str = str(exc.detail)
        error_code = http_exception_to_error_code(exc.status_code, detail_str)

        # Create standardized error response
        error_response = format_error_response(
            error_code=error_code,
            message=detail_str,
            correlation_id=correlation_id,
            path=str(request.url.path),
        )

        # Log the error with context
        logger.warning(
            "http_exception",
            status_code=exc.status_code,
            error_code=error_code.value,
            message=detail_str,
            path=str(request.url.path),
            method=request.method,
            client_host=request.client.host if request.client else None,
        )

    # Create response with any custom headers from the exception
    response = JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )

    # Add any custom headers (e.g., WWW-Authenticate for 401 errors)
    if exc.headers:
        for key, value in exc.headers.items():
            response.headers[key] = value

    return response


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors (422).

    Args:
        request: The incoming request
        exc: The validation error that was raised

    Returns:
        Formatted JSON error response for validation errors
    """
    # Get correlation ID from context (set by LoggingMiddleware)
    context_vars = get_contextvars()
    correlation_id = context_vars.get("correlation_id", "unknown")

    # Extract error details
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(x) for x in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{loc}: {msg}")

    combined_message = "; ".join(error_messages)

    # Use validation error code
    error_code = ErrorCode.VAL_INVALID_FORMAT

    # Create standardized error response
    error_response = format_error_response(
        error_code=error_code,
        message=f"Validation error: {combined_message}",
        correlation_id=correlation_id,
        path=str(request.url.path),
    )

    # Log the validation error
    logger.warning(
        "validation_error",
        error_code=error_code.value,
        errors=errors,
        path=str(request.url.path),
        method=request.method,
        client_host=request.client.host if request.client else None,
    )

    return JSONResponse(
        status_code=422,
        content=error_response,
    )


async def handle_unexpected_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions and return safe 500 error.

    Logs the full exception with stack trace but returns a generic
    error message to the client to avoid exposing internal details.

    Args:
        request: The incoming request
        exc: The unexpected exception that was raised

    Returns:
        Generic 500 error response with correlation ID for troubleshooting
    """
    # Get correlation ID from context (set by LoggingMiddleware)
    context_vars = get_contextvars()
    correlation_id = context_vars.get("correlation_id", "unknown")

    # Use generic system error code
    error_code = ErrorCode.SYS_INTERNAL_ERROR

    # Create standardized error response (generic message for security)
    error_response = format_error_response(
        error_code=error_code,
        message=get_error_message(error_code),
        correlation_id=correlation_id,
        path=str(request.url.path),
    )

    # Log the error with full stack trace
    logger.error(
        "unhandled_exception",
        error_code=error_code.value,
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        path=str(request.url.path),
        method=request.method,
        client_host=request.client.host if request.client else None,
        exc_info=True,  # This triggers stack trace logging
    )

    # Return 500 Internal Server Error
    return JSONResponse(
        status_code=500,
        content=error_response,
    )


def filter_sensitive_data(data: dict) -> dict:
    """
    Filter sensitive fields from data before logging.

    Args:
        data: Dictionary that may contain sensitive fields

    Returns:
        Dictionary with sensitive fields replaced with "[REDACTED]"
    """
    filtered = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            filtered[key] = "[REDACTED]"
        elif isinstance(value, dict):
            filtered[key] = filter_sensitive_data(value)
        else:
            filtered[key] = value
    return filtered
