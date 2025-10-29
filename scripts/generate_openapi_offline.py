#!/usr/bin/env python3
"""
Offline OpenAPI Specification Generator for SOVD Command WebApp

This script generates the OpenAPI 3.1 specification directly from the FastAPI
application code without requiring the backend to be running.

Usage:
    python scripts/generate_openapi_offline.py [--output PATH]

Arguments:
    --output PATH       Output path for the YAML file (default: docs/api/openapi.yaml)
"""

import argparse
import os
import sys
from pathlib import Path

# Set minimal environment variables required by the FastAPI app
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "dummy-secret-for-openapi-generation")

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    import yaml
except ImportError:
    print("Error: pyyaml library not found. Install with: pip install pyyaml")
    sys.exit(1)

try:
    # Import the FastAPI app
    from app.main import app
except ImportError as e:
    print(f"Error importing FastAPI app: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def generate_openapi_spec() -> dict:
    """
    Generate the OpenAPI specification from the FastAPI app instance.

    Returns:
        dict: The OpenAPI specification as a Python dictionary
    """
    return app.openapi()


def enhance_spec(spec_dict: dict) -> dict:
    """
    Enhance the auto-generated OpenAPI spec with additional details.

    Adds:
    - Security schemes (JWT Bearer)
    - Security requirements for protected endpoints
    - Additional response codes
    - Enhanced descriptions

    Args:
        spec_dict: Base OpenAPI spec from FastAPI

    Returns:
        dict: Enhanced OpenAPI spec
    """
    # Add security schemes
    if "components" not in spec_dict:
        spec_dict["components"] = {}

    spec_dict["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token obtained from /api/v1/auth/login"
        }
    }

    # Add security requirements to all /api/v1/ endpoints except login and refresh
    public_endpoints = {"/api/v1/auth/login", "/api/v1/auth/refresh"}

    for path, path_item in spec_dict.get("paths", {}).items():
        # Skip root and health endpoints
        if path in ["/", "/health"]:
            continue

        # Add security to all API endpoints except public auth endpoints
        if path.startswith("/api/v1/") and path not in public_endpoints:
            for method, operation in path_item.items():
                if method.lower() in ["get", "post", "put", "delete", "patch"]:
                    operation["security"] = [{"bearerAuth": []}]

                    # Add common error responses
                    if "responses" not in operation:
                        operation["responses"] = {}

                    operation["responses"]["401"] = {
                        "description": "Unauthorized - Missing or invalid access token"
                    }
                    operation["responses"]["403"] = {
                        "description": "Forbidden - Insufficient permissions"
                    }
                    operation["responses"]["422"] = {
                        "description": "Validation Error"
                    }

    # Enhance metadata
    spec_dict["info"]["description"] = (
        "Cloud-based SOVD 2.0 command execution platform. "
        "This API enables remote diagnostic operations on vehicles using the SOVD protocol. "
        "Features include user authentication, vehicle management, and command execution with real-time response streaming."
    )

    return spec_dict


def add_examples(spec_dict: dict) -> dict:
    """
    Add request/response examples to key endpoints.

    Args:
        spec_dict: OpenAPI spec

    Returns:
        dict: Spec with examples added
    """
    paths = spec_dict.get("paths", {})

    # Add example for login endpoint
    if "/api/v1/auth/login" in paths:
        login_op = paths["/api/v1/auth/login"].get("post", {})
        if "requestBody" in login_op:
            login_op["requestBody"]["content"]["application/json"]["example"] = {
                "username": "engineer1",
                "password": "securePassword123"
            }

    # Add example for submit command endpoint
    if "/api/v1/commands" in paths:
        submit_op = paths["/api/v1/commands"].get("post", {})
        if "requestBody" in submit_op:
            submit_op["requestBody"]["content"]["application/json"]["example"] = {
                "vehicle_id": "123e4567-e89b-12d3-a456-426614174000",
                "command_name": "ReadDTC",
                "command_params": {
                    "ecuAddress": "0x10",
                    "format": "UDS"
                }
            }

    # Add example for get vehicles endpoint
    if "/api/v1/vehicles" in paths:
        vehicles_op = paths["/api/v1/vehicles"].get("get", {})
        if "responses" in vehicles_op and "200" in vehicles_op["responses"]:
            vehicles_op["responses"]["200"]["content"] = {
                "application/json": {
                    "example": {
                        "vehicles": [
                            {
                                "vehicle_id": "123e4567-e89b-12d3-a456-426614174000",
                                "vin": "1HGCM82633A123456",
                                "make": "Honda",
                                "model": "Accord",
                                "year": 2024,
                                "connection_status": "connected",
                                "last_seen_at": "2025-10-28T10:00:00Z"
                            }
                        ],
                        "total": 1,
                        "limit": 20,
                        "offset": 0
                    }
                }
            }

    return spec_dict


def convert_to_yaml(spec_dict: dict) -> str:
    """
    Convert OpenAPI specification dictionary to YAML format.

    Args:
        spec_dict: OpenAPI spec as a dictionary

    Returns:
        str: YAML formatted string
    """
    return yaml.dump(
        spec_dict,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )


def save_spec(yaml_content: str, output_path: Path) -> None:
    """
    Save the YAML specification to a file.

    Args:
        yaml_content: YAML formatted OpenAPI spec
        output_path: Path where the file should be saved
    """
    # Create parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print(f"✓ OpenAPI spec saved to: {output_path}")
    print(f"  File size: {output_path.stat().st_size} bytes")


def main():
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI YAML specification from FastAPI app (offline mode)"
    )
    parser.add_argument(
        "--output",
        default="docs/api/openapi.yaml",
        help="Output path for YAML file (default: docs/api/openapi.yaml)",
    )

    args = parser.parse_args()

    # Convert output path to absolute Path object
    output_path = Path(args.output)
    if not output_path.is_absolute():
        # Make it relative to the project root (parent of scripts/)
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        output_path = project_root / args.output

    print("=" * 60)
    print("SOVD OpenAPI Specification Generator (Offline Mode)")
    print("=" * 60)

    # Step 1: Generate OpenAPI spec from app
    print("Generating OpenAPI spec from FastAPI app...")
    spec_dict = generate_openapi_spec()
    print(f"✓ Generated OpenAPI spec (version: {spec_dict.get('openapi', 'unknown')})")
    print(f"  Title: {spec_dict.get('info', {}).get('title', 'N/A')}")
    print(f"  Version: {spec_dict.get('info', {}).get('version', 'N/A')}")
    print(f"  Endpoints: {len(spec_dict.get('paths', {}))}")

    # Step 2: Enhance spec with security schemes and additional details
    print("\nEnhancing spec with security schemes and metadata...")
    spec_dict = enhance_spec(spec_dict)
    print("✓ Added JWT bearer authentication scheme")
    print("✓ Added security requirements to protected endpoints")
    print("✓ Added common error responses")

    # Step 3: Add examples
    print("\nAdding request/response examples...")
    spec_dict = add_examples(spec_dict)
    print("✓ Added examples for key endpoints")

    # Step 4: Convert to YAML
    print("\nConverting to YAML format...")
    yaml_content = convert_to_yaml(spec_dict)

    # Step 5: Save to file
    save_spec(yaml_content, output_path)

    print("\n" + "=" * 60)
    print("OpenAPI spec generation complete!")
    print("\nNext steps:")
    print("  1. Review the spec at:", output_path)
    print("  2. Validate online: https://editor.swagger.io/")
    print("  3. Start backend and test: http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()
