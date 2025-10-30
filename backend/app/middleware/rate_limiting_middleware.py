"""
Rate limiting middleware using slowapi with Redis backend.

Provides configurable rate limits for different endpoint types:
- Authentication endpoints: 5 requests/minute (IP-based)
- Command execution: 10 requests/minute (user-based)
- General API: 100 requests/minute (user-based)
- Admin users: Effectively unlimited (10000/minute)
"""

import structlog
from fastapi import Request
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.utils.request_utils import get_client_ip

logger = structlog.get_logger(__name__)

# Rate limit constants
RATE_LIMIT_AUTH = "5/minute"
RATE_LIMIT_COMMANDS = "10/minute"
RATE_LIMIT_GENERAL = "100/minute"
RATE_LIMIT_ADMIN = "10000/minute"  # Effectively unlimited for admins


def get_client_ip_key(request: Request) -> str:
    """
    Get rate limit key based on client IP address.

    Used for unauthenticated endpoints (e.g., login) where we can only
    identify clients by their IP address.

    Args:
        request: FastAPI Request object

    Returns:
        Rate limit key in format "ip:<ip_address>"
    """
    ip = get_client_ip(request)
    if ip:
        logger.debug("rate_limit_key_generated", key_type="ip", ip=ip)
        return f"ip:{ip}"

    # Fallback to slowapi's default remote address getter
    fallback_ip = get_remote_address(request)
    logger.debug("rate_limit_key_generated", key_type="ip_fallback", ip=fallback_ip)
    return f"ip:{fallback_ip}"


def get_user_id_key(request: Request) -> str:
    """
    Get rate limit key based on user ID from JWT token.

    For authenticated endpoints, we rate limit by user ID to prevent
    a single user from overwhelming the system. Admin users get a much
    higher limit (effectively unlimited).

    Args:
        request: FastAPI Request object

    Returns:
        Rate limit key in format:
        - "admin:<user_id>" for admin users (high limit)
        - "user:<user_id>" for regular users
        - "ip:<ip_address>" for unauthenticated requests (fallback)
    """
    # Try to extract user info from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # No token, fall back to IP-based limiting
        ip = get_client_ip(request)
        if ip:
            logger.debug("rate_limit_key_generated", key_type="ip_no_token", ip=ip)
            return f"ip:{ip}"
        fallback_ip = get_remote_address(request)
        logger.debug("rate_limit_key_generated", key_type="ip_fallback_no_token", ip=fallback_ip)
        return f"ip:{fallback_ip}"

    # Extract token
    token = auth_header.split(" ")[1]

    try:
        # Decode JWT token (without verification for performance)
        # The actual verification happens in the authentication dependency
        # We just need user_id and role for rate limiting
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": True, "verify_exp": False}  # Don't fail on expired tokens
        )

        user_id = payload.get("user_id")
        role = payload.get("role")

        if not user_id:
            # Invalid token structure, fall back to IP
            ip = get_client_ip(request)
            if ip:
                logger.debug("rate_limit_key_generated", key_type="ip_invalid_token", ip=ip)
                return f"ip:{ip}"
            fallback_ip = get_remote_address(request)
            logger.debug(
                "rate_limit_key_generated", key_type="ip_fallback_invalid_token", ip=fallback_ip
            )
            return f"ip:{fallback_ip}"

        # Admin users get high limit (admin prefix triggers different limit)
        if role == "admin":
            logger.debug("rate_limit_key_generated", key_type="admin", user_id=user_id)
            return f"admin:{user_id}"

        # Regular users get standard limit
        logger.debug("rate_limit_key_generated", key_type="user", user_id=user_id)
        return f"user:{user_id}"

    except JWTError as e:
        # Token decode failed, fall back to IP-based limiting
        logger.debug("rate_limit_jwt_decode_failed", error=str(e))
        ip = get_client_ip(request)
        if ip:
            logger.debug("rate_limit_key_generated", key_type="ip_jwt_error", ip=ip)
            return f"ip:{ip}"
        fallback_ip = get_remote_address(request)
        logger.debug("rate_limit_key_generated", key_type="ip_fallback_jwt_error", ip=fallback_ip)
        return f"ip:{fallback_ip}"


def get_admin_key(request: Request) -> str:
    """
    Get rate limit key for admin users with high limit.

    This is a special key function that always returns an admin-prefixed key
    for endpoints that should have high limits for all users.

    Args:
        request: FastAPI Request object

    Returns:
        Rate limit key with admin prefix
    """
    user_key = get_user_id_key(request)
    if user_key.startswith("admin:"):
        return user_key
    # For non-admin users, still apply admin-level limit
    # This is useful for endpoints that need high throughput
    return f"admin:{user_key}"


# Create limiter instance with Redis backend
try:
    limiter = Limiter(
        key_func=get_remote_address,  # Default key function
        storage_uri=settings.REDIS_URL,
        strategy="fixed-window",
        # Disable automatic header injection (we add manually in exception handler)
        headers_enabled=False,
    )
    logger.info("rate_limiter_initialized", storage_uri=settings.REDIS_URL, strategy="fixed-window")
except Exception as e:
    # If Redis connection fails, create limiter without storage (in-memory fallback)
    logger.warning("rate_limiter_redis_connection_failed", error=str(e), fallback="in-memory")
    limiter = Limiter(
        key_func=get_remote_address,
        strategy="fixed-window",
        headers_enabled=False,  # Disable automatic header injection
    )
