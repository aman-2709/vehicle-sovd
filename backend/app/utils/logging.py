"""
Structured logging configuration using structlog.

Configures JSON-formatted structured logging with correlation IDs,
timestamps, and contextual information for all application logs.
"""

import logging
import sys

import structlog
from structlog.contextvars import merge_contextvars
from structlog.processors import JSONRenderer, TimeStamper
from structlog.stdlib import add_log_level, add_logger_name


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the application.

    Sets up structlog with JSON rendering, timestamp formatting, and
    context variable support for correlation IDs. All logs are output
    as parseable JSON with consistent field structure.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to INFO. Can be configured via LOG_LEVEL env var.

    Log fields included:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Logger name (module path)
    - event: Log message/event description
    - correlation_id: Request correlation ID (from context vars)
    - user_id: User ID if available (from context vars)
    - Additional contextual fields as provided
    """
    # Convert log level string to logging level constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Configure structlog processors
    structlog.configure(
        processors=[
            # Add context variables (correlation_id, user_id, etc.)
            merge_contextvars,
            # Add log level to output
            add_log_level,
            # Add logger name to output
            add_logger_name,
            # Add ISO 8601 timestamp
            TimeStamper(fmt="iso", utc=True),
            # Filter stack info for production
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.processors.format_exc_info,
            # Render as JSON
            JSONRenderer(),
        ],
        # Use LoggerFactory for standard logging integration
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Use BoundLogger for better typing support
        wrapper_class=structlog.stdlib.BoundLogger,
        # Cache logger instances
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured structlog logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured structlog BoundLogger instance
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]
