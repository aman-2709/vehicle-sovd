/**
 * Error Message Mapping Utility
 *
 * Maps backend error codes to user-friendly, actionable messages.
 * Extracts error information from standardized backend error responses.
 */

export interface BackendError {
  error: {
    code: string;
    message: string;
    correlation_id?: string;
    timestamp?: string;
    path?: string;
  };
}

/**
 * Error code to user-friendly message mapping.
 * Messages are actionable and guide users on what to do next.
 */
const ERROR_MESSAGES: Record<string, string> = {
  // Rate Limiting
  RATE_001: 'Too many requests. Please wait a moment before trying again.',

  // Authentication Errors
  AUTH_001: 'Invalid username or password. Please try again.',
  AUTH_002: 'Your session has expired. Please log in again.',
  AUTH_003: 'Invalid authentication token. Please log in again.',
  AUTH_004: 'You do not have permission to perform this action.',
  AUTH_005: 'Your account is inactive. Please contact support.',

  // Validation Errors
  VAL_001: 'Vehicle not found. Please check the vehicle ID and try again.',
  VAL_002: 'Invalid command. Please check the command name and parameters.',
  VAL_003: 'Required field is missing. Please fill in all required fields.',
  VAL_004: 'Invalid format. Please check your input and try again.',
  VAL_005: 'Resource not found. The requested item does not exist.',

  // Database Errors
  DB_001: 'Database connection failed. Please try again in a moment.',
  DB_002: 'Database query timed out. Please try again.',

  // Vehicle Communication Errors
  VEH_001: 'The vehicle is currently unreachable. Please check vehicle connectivity.',
  VEH_002: 'Vehicle command timed out. The vehicle may be offline or slow to respond.',
  VEH_003: 'Vehicle returned an invalid response. Please try again.',
  VEH_004: 'Command failed to execute on the vehicle. Please try again or check vehicle status.',

  // System Errors
  SYS_001: 'An internal error occurred. Please try again or contact support.',
  SYS_002: 'Service temporarily unavailable. Please try again in a moment.',
  SYS_003: 'Request timed out. Please try again.',
};

/**
 * Extract error information from backend error response.
 *
 * @param error - Axios error or backend error object
 * @returns Extracted error information
 */
export const extractErrorInfo = (error: unknown): {
  code: string | null;
  message: string;
  correlationId: string | null;
} => {
  // Check if it's a backend error response
  if (
    error &&
    typeof error === 'object' &&
    'response' in error &&
    error.response &&
    typeof error.response === 'object' &&
    'data' in error.response
  ) {
    const data = (error.response as { data: unknown }).data;

    if (data && typeof data === 'object' && 'error' in data) {
      const backendError = data as BackendError;
      return {
        code: backendError.error.code || null,
        message: backendError.error.message || 'An error occurred',
        correlationId: backendError.error.correlation_id || null,
      };
    }
  }

  // Fallback for non-backend errors
  if (error && typeof error === 'object' && 'message' in error) {
    return {
      code: null,
      message: (error as { message: string }).message,
      correlationId: null,
    };
  }

  return {
    code: null,
    message: 'An unexpected error occurred',
    correlationId: null,
  };
};

/**
 * Get user-friendly error message from error code.
 * Falls back to backend message if code is not mapped.
 *
 * @param code - Backend error code
 * @param fallbackMessage - Fallback message from backend
 * @returns User-friendly error message
 */
export const getErrorMessage = (code: string | null, fallbackMessage: string): string => {
  if (code && ERROR_MESSAGES[code]) {
    return ERROR_MESSAGES[code];
  }

  // For validation errors with field paths, extract just the message
  if (fallbackMessage && fallbackMessage.includes(' -> ') && fallbackMessage.includes(':')) {
    const parts = fallbackMessage.split(':');
    return parts.length > 1 ? parts.slice(1).join(':').trim() : fallbackMessage;
  }

  return fallbackMessage;
};

/**
 * Format error message with correlation ID for display.
 *
 * @param message - User-friendly error message
 * @param correlationId - Error correlation ID from backend
 * @returns Formatted error message
 */
export const formatErrorWithCorrelationId = (
  message: string,
  correlationId: string | null
): string => {
  if (correlationId) {
    return `${message}\n\nError ID: ${correlationId}`;
  }
  return message;
};

/**
 * Check if an error should trigger a retry.
 * Only network errors and 503/504 status codes should be retried.
 *
 * @param error - Error object
 * @returns True if error should be retried
 */
export const shouldRetryError = (error: unknown): boolean => {
  if (!error || typeof error !== 'object') {
    return false;
  }

  // Check if it's an Axios error
  if ('isAxiosError' in error && error.isAxiosError) {
    // Network errors (no response)
    if (!('response' in error) || !error.response) {
      return true;
    }

    // Only retry 503 (Service Unavailable) and 504 (Gateway Timeout)
    const response = error.response as { status?: number };
    return response.status === 503 || response.status === 504;
  }

  return false;
};
