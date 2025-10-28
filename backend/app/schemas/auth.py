"""
Authentication schema definitions.

Pydantic models for authentication-related API requests and responses.
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request schema for user login."""

    username: str = Field(..., min_length=1, max_length=100, description="Username")
    password: str = Field(..., min_length=1, description="Password")


class TokenResponse(BaseModel):
    """Response schema for token generation."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class RefreshRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str = Field(..., description="JWT refresh token")


class RefreshResponse(BaseModel):
    """Response schema for token refresh."""

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")


class UserResponse(BaseModel):
    """Response schema for user profile information."""

    user_id: str = Field(..., description="User unique identifier (UUID)")
    username: str = Field(..., description="Username")
    role: str = Field(..., description="User role (e.g., 'engineer', 'admin')")
    email: str = Field(..., description="User email address")

    class Config:
        """Pydantic config."""
        from_attributes = True


class LogoutResponse(BaseModel):
    """Response schema for logout."""

    message: str = Field(..., description="Logout confirmation message")
