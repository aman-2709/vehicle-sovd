#!/usr/bin/env python3
"""
OpenAPI Specification Generator for SOVD Command WebApp

This script extracts the OpenAPI 3.1 specification from the running FastAPI
backend and converts it to YAML format for documentation purposes.

Usage:
    python scripts/generate_openapi.py [--url URL] [--output PATH] [--validate]

Arguments:
    --url URL           Base URL of the running backend (default: http://localhost:8000)
    --output PATH       Output path for the YAML file (default: docs/api/openapi.yaml)
    --validate          Validate the generated spec using openapi-spec-validator

Requirements:
    - Backend must be running and accessible
    - pip install pyyaml requests openapi-spec-validator (for validation)
"""

import argparse
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: pyyaml library not found. Install with: pip install pyyaml")
    sys.exit(1)


def fetch_openapi_spec(base_url: str) -> dict:
    """
    Fetch the OpenAPI specification from the running FastAPI backend.

    Args:
        base_url: Base URL of the backend (e.g., http://localhost:8000)

    Returns:
        dict: The OpenAPI specification as a Python dictionary

    Raises:
        requests.exceptions.RequestException: If the backend is not reachable
    """
    openapi_url = f"{base_url.rstrip('/')}/openapi.json"
    print(f"Fetching OpenAPI spec from: {openapi_url}")

    try:
        response = requests.get(openapi_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to backend at {base_url}")
        print("Make sure the backend is running (try: make up)")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"Error: Request to {openapi_url} timed out")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching OpenAPI spec: {e}")
        sys.exit(1)


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


def validate_spec(spec_dict: dict) -> bool:
    """
    Validate the OpenAPI specification using openapi-spec-validator.

    Args:
        spec_dict: OpenAPI spec as a dictionary

    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        from openapi_spec_validator import validate_spec
        from openapi_spec_validator.validation.exceptions import OpenAPIValidationError
    except ImportError:
        print("Warning: openapi-spec-validator not installed. Skipping validation.")
        print("Install with: pip install openapi-spec-validator")
        return True

    try:
        validate_spec(spec_dict)
        print("✓ OpenAPI spec validation passed")
        return True
    except OpenAPIValidationError as e:
        print(f"✗ OpenAPI spec validation failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI YAML specification from running FastAPI backend"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the running backend (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--output",
        default="docs/api/openapi.yaml",
        help="Output path for YAML file (default: docs/api/openapi.yaml)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the generated spec using openapi-spec-validator",
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
    print("SOVD OpenAPI Specification Generator")
    print("=" * 60)

    # Step 1: Fetch OpenAPI spec from running backend
    spec_dict = fetch_openapi_spec(args.url)
    print(f"✓ Fetched OpenAPI spec (version: {spec_dict.get('openapi', 'unknown')})")
    print(f"  Title: {spec_dict.get('info', {}).get('title', 'N/A')}")
    print(f"  Version: {spec_dict.get('info', {}).get('version', 'N/A')}")
    print(f"  Endpoints: {len(spec_dict.get('paths', {}))}")

    # Step 2: Validate if requested
    if args.validate:
        if not validate_spec(spec_dict):
            print("\nWarning: Validation failed, but continuing with file generation...")

    # Step 3: Convert to YAML
    yaml_content = convert_to_yaml(spec_dict)

    # Step 4: Save to file
    save_spec(yaml_content, output_path)

    print("\n" + "=" * 60)
    print("Next steps:")
    print("  1. Review and enhance the spec manually (add examples, descriptions)")
    print("  2. Validate online: https://editor.swagger.io/")
    print("  3. View in browser: http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()
