"""Response schemas for API serialization."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_serializer


class ResponseDetail(BaseModel):
    """Schema for streaming command response details.

    Represents a single response chunk from a vehicle command execution.
    Multiple responses can be associated with one command for streaming data.
    """

    response_id: UUID
    command_id: UUID
    response_payload: dict[str, Any]
    sequence_number: int
    is_final: bool
    received_at: datetime

    @field_serializer("response_id", "command_id")
    def serialize_uuid(self, value: UUID) -> str:
        """Serialize UUIDs to strings for JSON compatibility."""
        return str(value)

    model_config = {"from_attributes": True}
