#!/usr/bin/env python3
"""Test script to verify protobuf generated code imports successfully."""

import sys

try:
    from app.generated import sovd_vehicle_service_pb2
    from app.generated import sovd_vehicle_service_pb2_grpc

    print("✓ Import successful: sovd_vehicle_service_pb2")
    print("✓ Import successful: sovd_vehicle_service_pb2_grpc")
    print()

    # Verify message classes exist
    print("Message classes:")
    print(f"  ✓ CommandRequest: {sovd_vehicle_service_pb2.CommandRequest}")
    print(f"  ✓ CommandResponse: {sovd_vehicle_service_pb2.CommandResponse}")
    print()

    # Verify service classes exist
    print("Service classes:")
    print(f"  ✓ VehicleServiceStub: {sovd_vehicle_service_pb2_grpc.VehicleServiceStub}")
    print(f"  ✓ VehicleServiceServicer: {sovd_vehicle_service_pb2_grpc.VehicleServiceServicer}")
    print()

    # Test creating a message instance
    request = sovd_vehicle_service_pb2.CommandRequest(
        command_id="550e8400-e29b-41d4-a716-446655440000",
        vehicle_id="123e4567-e89b-12d3-a456-426614174000",
        command_name="ReadDTC",
        command_params={"ecuAddress": "0x10"}
    )
    print("✓ Successfully created CommandRequest instance:")
    print(f"  command_id: {request.command_id}")
    print(f"  vehicle_id: {request.vehicle_id}")
    print(f"  command_name: {request.command_name}")
    print(f"  command_params: {dict(request.command_params)}")
    print()

    print("✅ All imports and tests passed!")
    sys.exit(0)

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
