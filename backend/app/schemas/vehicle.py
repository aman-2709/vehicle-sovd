"""Pydantic schemas for vehicle API requests and responses.

These models define the structure of data sent to and received from vehicle endpoints.
Uses Pydantic v2 syntax with proper type hints and validation.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class VehicleResponse(BaseModel):
    """Vehicle details response schema.

    Returned by GET /api/v1/vehicles and GET /api/v1/vehicles/{vehicle_id} endpoints.

    Attributes:
        vehicle_id: UUID string identifier
        vin: Vehicle Identification Number (17 characters)
        make: Vehicle manufacturer name
        model: Vehicle model name
        year: Vehicle manufacturing year
        connection_status: Current connection status (connected, disconnected, error)
        last_seen_at: Timestamp when vehicle was last seen (nullable)
        metadata: Additional vehicle-specific attributes stored in JSONB (nullable)
    """

    vehicle_id: UUID
    vin: str
    make: str
    model: str
    year: int
    connection_status: str
    last_seen_at: datetime | None
    metadata: dict[str, Any] | None = Field(default=None, serialization_alias="metadata", validation_alias="vehicle_metadata")

    @field_serializer("vehicle_id")
    def serialize_vehicle_id(self, value: UUID) -> str:
        """Serialize UUID to string for JSON response."""
        return str(value)

    model_config = {"from_attributes": True, "populate_by_name": True}


class VehicleStatusResponse(BaseModel):
    """Vehicle status response schema.

    Returned by GET /api/v1/vehicles/{vehicle_id}/status endpoint.
    This endpoint is optimized with Redis caching (TTL=30s).

    Attributes:
        connection_status: Current connection status (connected, disconnected, error)
        last_seen_at: Timestamp when vehicle was last seen (nullable)
        health: Health metrics like signal strength, battery voltage (nullable)
    """

    connection_status: str
    last_seen_at: datetime | None
    health: dict[str, Any] | None = Field(default=None)

    model_config = {"from_attributes": True}


class VehicleListResponse(BaseModel):
    """List of vehicles with pagination metadata.

    Used for paginated vehicle list responses with metadata about the result set.

    Attributes:
        vehicles: List of vehicle response objects
        total: Total number of vehicles matching the filters
        limit: Maximum number of results returned in this response
        offset: Number of results skipped (pagination offset)
    """

    vehicles: list[VehicleResponse]
    total: int
    limit: int
    offset: int
