"""
Pydantic schemas for command-related API requests and responses.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class CommandSubmitRequest(BaseModel):
    """Request schema for submitting a new command."""

    command_name: str = Field(..., description="SOVD command identifier", max_length=100)
    vehicle_id: UUID = Field(..., description="Target vehicle UUID")
    command_params: dict[str, Any] = Field(
        default_factory=dict, description="Command-specific parameters"
    )


class CommandResponse(BaseModel):
    """Response schema for command details."""

    command_id: UUID
    user_id: UUID
    vehicle_id: UUID
    command_name: str
    command_params: dict[str, Any]
    status: str
    error_message: str | None
    submitted_at: datetime
    completed_at: datetime | None

    @field_serializer("command_id", "user_id", "vehicle_id")
    def serialize_uuid(self, value: UUID) -> str:
        """Serialize UUID fields to strings."""
        return str(value)

    model_config = {"from_attributes": True}


class CommandListResponse(BaseModel):
    """Response schema for paginated command list."""

    commands: list[CommandResponse]
    limit: int
    offset: int
