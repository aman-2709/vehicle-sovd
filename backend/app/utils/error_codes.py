"""
Error code definitions and utilities for standardized error handling.

Provides a hierarchical error code system for categorizing errors and
generating consistent error responses across the application.
"""

from enum import Enum


class ErrorCode(str, Enum):
    """
    Enumeration of application error codes organized by category.

    Error code format: CATEGORY_###
    - AUTH_xxx: Authentication and authorization errors (001-099)
    - VAL_xxx: Validation and business logic errors (100-199)
    - DB_xxx: Database and persistence errors (200-299)
    - VEH_xxx: Vehicle communication and SOVD errors (300-399)
    - SYS_xxx: System and internal errors (500-599)
    """

    # Authentication & Authorization Errors (001-099)
    AUTH_INVALID_CREDENTIALS = "AUTH_001"
    AUTH_TOKEN_EXPIRED = "AUTH_002"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_003"
    AUTH_TOKEN_INVALID = "AUTH_004"
    AUTH_USER_NOT_FOUND = "AUTH_005"
    AUTH_USER_INACTIVE = "AUTH_006"

    # Validation & Business Logic Errors (100-199)
    VAL_VEHICLE_NOT_FOUND = "VAL_101"
    VAL_INVALID_COMMAND = "VAL_102"
    VAL_MISSING_FIELD = "VAL_103"
    VAL_INVALID_FORMAT = "VAL_104"
    VAL_DUPLICATE_RESOURCE = "VAL_105"
    VAL_RESOURCE_NOT_FOUND = "VAL_106"
    VAL_INVALID_PARAMETER = "VAL_107"

    # Database & Persistence Errors (200-299)
    DB_CONNECTION_FAILED = "DB_201"
    DB_QUERY_TIMEOUT = "DB_202"
    DB_CONSTRAINT_VIOLATION = "DB_203"
    DB_TRANSACTION_FAILED = "DB_204"

    # Vehicle Communication & SOVD Errors (300-399)
    VEH_UNREACHABLE = "VEH_301"
    VEH_COMMAND_TIMEOUT = "VEH_302"
    VEH_INVALID_RESPONSE = "VEH_303"
    VEH_COMMAND_FAILED = "VEH_304"
    VEH_NOT_CONNECTED = "VEH_305"

    # System & Internal Errors (500-599)
    SYS_INTERNAL_ERROR = "SYS_501"
    SYS_SERVICE_UNAVAILABLE = "SYS_502"
    SYS_CONFIGURATION_ERROR = "SYS_503"
    SYS_TIMEOUT = "SYS_504"


# Error code to human-readable message mapping
ERROR_MESSAGES: dict[ErrorCode, str] = {
    # Authentication & Authorization
    ErrorCode.AUTH_INVALID_CREDENTIALS: "Invalid username or password",
    ErrorCode.AUTH_TOKEN_EXPIRED: "Authentication token has expired",
    ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: "Insufficient permissions to access this resource",
    ErrorCode.AUTH_TOKEN_INVALID: "Invalid authentication token",
    ErrorCode.AUTH_USER_NOT_FOUND: "User not found",
    ErrorCode.AUTH_USER_INACTIVE: "User account is inactive",
    # Validation & Business Logic
    ErrorCode.VAL_VEHICLE_NOT_FOUND: "Vehicle not found",
    ErrorCode.VAL_INVALID_COMMAND: "Invalid SOVD command format",
    ErrorCode.VAL_MISSING_FIELD: "Required field is missing",
    ErrorCode.VAL_INVALID_FORMAT: "Invalid data format",
    ErrorCode.VAL_DUPLICATE_RESOURCE: "Resource already exists",
    ErrorCode.VAL_RESOURCE_NOT_FOUND: "Requested resource not found",
    ErrorCode.VAL_INVALID_PARAMETER: "Invalid parameter value",
    # Database & Persistence
    ErrorCode.DB_CONNECTION_FAILED: "Database connection failed",
    ErrorCode.DB_QUERY_TIMEOUT: "Database query timed out",
    ErrorCode.DB_CONSTRAINT_VIOLATION: "Database constraint violation",
    ErrorCode.DB_TRANSACTION_FAILED: "Database transaction failed",
    # Vehicle Communication & SOVD
    ErrorCode.VEH_UNREACHABLE: "Vehicle is unreachable",
    ErrorCode.VEH_COMMAND_TIMEOUT: "Vehicle command timed out",
    ErrorCode.VEH_INVALID_RESPONSE: "Invalid response from vehicle",
    ErrorCode.VEH_COMMAND_FAILED: "Vehicle command execution failed",
    ErrorCode.VEH_NOT_CONNECTED: "Vehicle is not connected",
    # System & Internal
    ErrorCode.SYS_INTERNAL_ERROR: "Internal server error",
    ErrorCode.SYS_SERVICE_UNAVAILABLE: "Service temporarily unavailable",
    ErrorCode.SYS_CONFIGURATION_ERROR: "System configuration error",
    ErrorCode.SYS_TIMEOUT: "Request timeout",
}


# HTTP status code mapping for error codes
ERROR_STATUS_CODES: dict[ErrorCode, int] = {
    # Authentication & Authorization (401, 403)
    ErrorCode.AUTH_INVALID_CREDENTIALS: 401,
    ErrorCode.AUTH_TOKEN_EXPIRED: 401,
    ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: 403,
    ErrorCode.AUTH_TOKEN_INVALID: 401,
    ErrorCode.AUTH_USER_NOT_FOUND: 401,
    ErrorCode.AUTH_USER_INACTIVE: 403,
    # Validation & Business Logic (400, 404, 409)
    ErrorCode.VAL_VEHICLE_NOT_FOUND: 404,
    ErrorCode.VAL_INVALID_COMMAND: 400,
    ErrorCode.VAL_MISSING_FIELD: 400,
    ErrorCode.VAL_INVALID_FORMAT: 400,
    ErrorCode.VAL_DUPLICATE_RESOURCE: 409,
    ErrorCode.VAL_RESOURCE_NOT_FOUND: 404,
    ErrorCode.VAL_INVALID_PARAMETER: 400,
    # Database & Persistence (500, 503, 504)
    ErrorCode.DB_CONNECTION_FAILED: 503,
    ErrorCode.DB_QUERY_TIMEOUT: 504,
    ErrorCode.DB_CONSTRAINT_VIOLATION: 400,
    ErrorCode.DB_TRANSACTION_FAILED: 500,
    # Vehicle Communication & SOVD (503, 504)
    ErrorCode.VEH_UNREACHABLE: 503,
    ErrorCode.VEH_COMMAND_TIMEOUT: 504,
    ErrorCode.VEH_INVALID_RESPONSE: 500,
    ErrorCode.VEH_COMMAND_FAILED: 500,
    ErrorCode.VEH_NOT_CONNECTED: 503,
    # System & Internal (500, 503, 504)
    ErrorCode.SYS_INTERNAL_ERROR: 500,
    ErrorCode.SYS_SERVICE_UNAVAILABLE: 503,
    ErrorCode.SYS_CONFIGURATION_ERROR: 500,
    ErrorCode.SYS_TIMEOUT: 504,
}


def get_error_message(error_code: ErrorCode) -> str:
    """
    Get the human-readable message for an error code.

    Args:
        error_code: The error code enum value

    Returns:
        Human-readable error message
    """
    return ERROR_MESSAGES.get(error_code, "An error occurred")


def get_status_code(error_code: ErrorCode) -> int:
    """
    Get the HTTP status code for an error code.

    Args:
        error_code: The error code enum value

    Returns:
        HTTP status code (400, 401, 403, 404, 500, 503, 504)
    """
    return ERROR_STATUS_CODES.get(error_code, 500)


def http_exception_to_error_code(status_code: int, detail: str) -> ErrorCode:
    """
    Map an HTTPException to an appropriate error code.

    Analyzes the HTTP status code and error detail message to determine
    the most appropriate error code from our hierarchy.

    Args:
        status_code: HTTP status code from the exception
        detail: Error detail message from the exception

    Returns:
        Appropriate ErrorCode enum value
    """
    # Authentication errors (401)
    if status_code == 401:
        detail_lower = detail.lower()
        if "expired" in detail_lower:
            return ErrorCode.AUTH_TOKEN_EXPIRED
        elif "invalid" in detail_lower and "token" in detail_lower:
            return ErrorCode.AUTH_TOKEN_INVALID
        elif "password" in detail_lower or "credentials" in detail_lower:
            return ErrorCode.AUTH_INVALID_CREDENTIALS
        elif "user" in detail_lower and "not found" in detail_lower:
            return ErrorCode.AUTH_USER_NOT_FOUND
        else:
            return ErrorCode.AUTH_INVALID_CREDENTIALS

    # Authorization errors (403)
    elif status_code == 403:
        detail_lower = detail.lower()
        if "inactive" in detail_lower:
            return ErrorCode.AUTH_USER_INACTIVE
        else:
            return ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS

    # Not found errors (404)
    elif status_code == 404:
        detail_lower = detail.lower()
        if "vehicle" in detail_lower:
            return ErrorCode.VAL_VEHICLE_NOT_FOUND
        else:
            return ErrorCode.VAL_RESOURCE_NOT_FOUND

    # Bad request errors (400)
    elif status_code == 400:
        detail_lower = detail.lower()
        if "command" in detail_lower:
            return ErrorCode.VAL_INVALID_COMMAND
        elif "missing" in detail_lower or "required" in detail_lower:
            return ErrorCode.VAL_MISSING_FIELD
        elif "format" in detail_lower:
            return ErrorCode.VAL_INVALID_FORMAT
        elif "parameter" in detail_lower:
            return ErrorCode.VAL_INVALID_PARAMETER
        else:
            return ErrorCode.VAL_INVALID_FORMAT

    # Conflict errors (409)
    elif status_code == 409:
        return ErrorCode.VAL_DUPLICATE_RESOURCE

    # Service unavailable (503)
    elif status_code == 503:
        detail_lower = detail.lower()
        if "vehicle" in detail_lower:
            return ErrorCode.VEH_UNREACHABLE
        elif "database" in detail_lower:
            return ErrorCode.DB_CONNECTION_FAILED
        else:
            return ErrorCode.SYS_SERVICE_UNAVAILABLE

    # Gateway timeout (504)
    elif status_code == 504:
        detail_lower = detail.lower()
        if "vehicle" in detail_lower or "command" in detail_lower:
            return ErrorCode.VEH_COMMAND_TIMEOUT
        elif "database" in detail_lower:
            return ErrorCode.DB_QUERY_TIMEOUT
        else:
            return ErrorCode.SYS_TIMEOUT

    # Internal server error (500) or unknown
    else:
        return ErrorCode.SYS_INTERNAL_ERROR
