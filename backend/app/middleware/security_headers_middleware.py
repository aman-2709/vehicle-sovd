"""
Security Headers Middleware for SOVD Command WebApp.

Adds security-related HTTP headers to all responses to enhance application security.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    Headers added:
    - Content-Security-Policy (CSP): Restricts sources for scripts, styles, images
    - X-Frame-Options: Prevents clickjacking by restricting iframe embedding
    - X-Content-Type-Options: Prevents MIME type sniffing
    - Strict-Transport-Security (HSTS): Enforces HTTPS connections
    - Referrer-Policy: Controls referrer information leakage
    - Permissions-Policy: Restricts browser features
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # Content Security Policy (CSP)
        # Allow same-origin resources and inline scripts/styles (required for React/MUI)
        # Note: 'unsafe-inline' is needed for React and MUI but documented as accepted risk
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Prevent clickjacking - allow same-origin iframes only
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enforce HTTPS (HSTS) - 1 year max-age, include subdomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features (Permissions Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response
