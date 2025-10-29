"""
Request utility functions.

Provides helper functions for extracting information from FastAPI Request objects.
"""

from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    """
    Extract client IP address from request.

    Checks for X-Forwarded-For header first (for proxied requests),
    then falls back to direct client IP. Supports both IPv4 and IPv6.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address as string, or None if not available
    """
    # Check X-Forwarded-For header (for requests through proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first (client IP)
        return forwarded_for.split(",")[0].strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return None


def get_user_agent(request: Request) -> str | None:
    """
    Extract user agent string from request.

    Args:
        request: FastAPI Request object

    Returns:
        User agent string, or None if not present
    """
    return request.headers.get("User-Agent")
