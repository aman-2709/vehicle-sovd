/**
 * Error Message Mapping Tests
 *
 * Tests for error code to user-friendly message mapping.
 */

import { describe, it, expect } from 'vitest';
import {
  extractErrorInfo,
  getErrorMessage,
  formatErrorWithCorrelationId,
  shouldRetryError,
} from '../../src/utils/errorMessages';

describe('extractErrorInfo', () => {
  it('extracts error info from backend error response', () => {
    const error = {
      response: {
        data: {
          error: {
            code: 'AUTH_001',
            message: 'Invalid credentials',
            correlation_id: 'test-123',
          },
        },
      },
    };

    const result = extractErrorInfo(error);

    expect(result).toEqual({
      code: 'AUTH_001',
      message: 'Invalid credentials',
      correlationId: 'test-123',
    });
  });

  it('handles backend error without correlation ID', () => {
    const error = {
      response: {
        data: {
          error: {
            code: 'VAL_001',
            message: 'Vehicle not found',
          },
        },
      },
    };

    const result = extractErrorInfo(error);

    expect(result).toEqual({
      code: 'VAL_001',
      message: 'Vehicle not found',
      correlationId: null,
    });
  });

  it('handles error with message property but no backend format', () => {
    const error = {
      message: 'Network error',
    };

    const result = extractErrorInfo(error);

    expect(result).toEqual({
      code: null,
      message: 'Network error',
      correlationId: null,
    });
  });

  it('handles unknown error format', () => {
    const error = { something: 'unknown' };

    const result = extractErrorInfo(error);

    expect(result).toEqual({
      code: null,
      message: 'An unexpected error occurred',
      correlationId: null,
    });
  });

  it('handles null error', () => {
    const result = extractErrorInfo(null);

    expect(result).toEqual({
      code: null,
      message: 'An unexpected error occurred',
      correlationId: null,
    });
  });
});

describe('getErrorMessage', () => {
  it('returns mapped message for known error code', () => {
    const message = getErrorMessage('AUTH_001', 'Backend message');

    expect(message).toBe('Invalid username or password. Please try again.');
  });

  it('returns mapped message for rate limit error', () => {
    const message = getErrorMessage('RATE_001', 'Backend message');

    expect(message).toBe('Too many requests. Please wait a moment before trying again.');
  });

  it('returns mapped message for vehicle unreachable error', () => {
    const message = getErrorMessage('VEH_001', 'Backend message');

    expect(message).toBe('The vehicle is currently unreachable. Please check vehicle connectivity.');
  });

  it('returns fallback message for unknown error code', () => {
    const message = getErrorMessage('UNKNOWN_CODE', 'Fallback message');

    expect(message).toBe('Fallback message');
  });

  it('returns fallback message when code is null', () => {
    const message = getErrorMessage(null, 'Fallback message');

    expect(message).toBe('Fallback message');
  });

  it('extracts validation error message from field path when code is not mapped', () => {
    const message = getErrorMessage(
      null,
      'vehicle_id -> field: This field is required'
    );

    expect(message).toBe('This field is required');
  });

  it('handles validation error with multiple arrows when code is not mapped', () => {
    const message = getErrorMessage(
      null,
      'command_params -> nested -> field: Invalid format'
    );

    expect(message).toBe('Invalid format');
  });

  it('returns original message if no colon in validation error', () => {
    const message = getErrorMessage(null, 'vehicle_id -> field');

    expect(message).toBe('vehicle_id -> field');
  });

  it('maps all authentication error codes', () => {
    expect(getErrorMessage('AUTH_001', '')).toContain('Invalid username or password');
    expect(getErrorMessage('AUTH_002', '')).toContain('session has expired');
    expect(getErrorMessage('AUTH_003', '')).toContain('Invalid authentication token');
    expect(getErrorMessage('AUTH_004', '')).toContain('do not have permission');
    expect(getErrorMessage('AUTH_005', '')).toContain('account is inactive');
  });

  it('maps all validation error codes', () => {
    expect(getErrorMessage('VAL_001', '')).toContain('Vehicle not found');
    expect(getErrorMessage('VAL_002', '')).toContain('Invalid command');
    expect(getErrorMessage('VAL_003', '')).toContain('Required field is missing');
    expect(getErrorMessage('VAL_004', '')).toContain('Invalid format');
    expect(getErrorMessage('VAL_005', '')).toContain('Resource not found');
  });

  it('maps all database error codes', () => {
    expect(getErrorMessage('DB_001', '')).toContain('Database connection failed');
    expect(getErrorMessage('DB_002', '')).toContain('Database query timed out');
  });

  it('maps all vehicle communication error codes', () => {
    expect(getErrorMessage('VEH_001', '')).toContain('vehicle is currently unreachable');
    expect(getErrorMessage('VEH_002', '')).toContain('Vehicle command timed out');
    expect(getErrorMessage('VEH_003', '')).toContain('invalid response');
    expect(getErrorMessage('VEH_004', '')).toContain('Command failed to execute');
  });

  it('maps all system error codes', () => {
    expect(getErrorMessage('SYS_001', '')).toContain('internal error occurred');
    expect(getErrorMessage('SYS_002', '')).toContain('Service temporarily unavailable');
    expect(getErrorMessage('SYS_003', '')).toContain('Request timed out');
  });
});

describe('formatErrorWithCorrelationId', () => {
  it('appends correlation ID to message', () => {
    const formatted = formatErrorWithCorrelationId('Error occurred', 'test-123');

    expect(formatted).toBe('Error occurred\n\nError ID: test-123');
  });

  it('returns message without ID when correlation ID is null', () => {
    const formatted = formatErrorWithCorrelationId('Error occurred', null);

    expect(formatted).toBe('Error occurred');
  });

  it('handles empty string correlation ID', () => {
    const formatted = formatErrorWithCorrelationId('Error occurred', '');

    expect(formatted).toBe('Error occurred');
  });

  it('formats multi-line messages correctly', () => {
    const formatted = formatErrorWithCorrelationId('Error occurred.\nPlease try again.', 'id-456');

    expect(formatted).toBe('Error occurred.\nPlease try again.\n\nError ID: id-456');
  });
});

describe('shouldRetryError', () => {
  it('returns true for 503 Service Unavailable', () => {
    const error = {
      isAxiosError: true,
      response: { status: 503 },
    };

    expect(shouldRetryError(error)).toBe(true);
  });

  it('returns true for 504 Gateway Timeout', () => {
    const error = {
      isAxiosError: true,
      response: { status: 504 },
    };

    expect(shouldRetryError(error)).toBe(true);
  });

  it('returns true for network errors (no response)', () => {
    const error = {
      isAxiosError: true,
    };

    expect(shouldRetryError(error)).toBe(true);
  });

  it('returns false for 400 Bad Request', () => {
    const error = {
      isAxiosError: true,
      response: { status: 400 },
    };

    expect(shouldRetryError(error)).toBe(false);
  });

  it('returns false for 401 Unauthorized', () => {
    const error = {
      isAxiosError: true,
      response: { status: 401 },
    };

    expect(shouldRetryError(error)).toBe(false);
  });

  it('returns false for 403 Forbidden', () => {
    const error = {
      isAxiosError: true,
      response: { status: 403 },
    };

    expect(shouldRetryError(error)).toBe(false);
  });

  it('returns false for 404 Not Found', () => {
    const error = {
      isAxiosError: true,
      response: { status: 404 },
    };

    expect(shouldRetryError(error)).toBe(false);
  });

  it('returns false for 500 Internal Server Error', () => {
    const error = {
      isAxiosError: true,
      response: { status: 500 },
    };

    expect(shouldRetryError(error)).toBe(false);
  });

  it('returns false for non-Axios errors', () => {
    const error = new Error('Regular error');

    expect(shouldRetryError(error)).toBe(false);
  });

  it('returns false for null error', () => {
    expect(shouldRetryError(null)).toBe(false);
  });

  it('returns false for undefined error', () => {
    expect(shouldRetryError(undefined)).toBe(false);
  });
});
