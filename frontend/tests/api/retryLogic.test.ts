/**
 * API Client Retry Logic Tests
 *
 * Tests for exponential backoff retry logic on 503/504 errors.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import apiClient, { vehicleAPI } from '../../src/api/client';
import { shouldRetryError } from '../../src/utils/errorMessages';

describe('API Client Retry Logic', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(apiClient, { delayResponse: 0 });
    vi.useFakeTimers();
  });

  afterEach(() => {
    mock.reset();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('retries 503 errors up to 3 times with exponential backoff', async () => {
    let attemptCount = 0;

    mock.onGet('/api/v1/vehicles').reply(() => {
      attemptCount++;
      if (attemptCount < 4) {
        return [503, { error: { code: 'SYS_002', message: 'Service unavailable' } }];
      }
      return [200, []];
    });

    const promise = vehicleAPI.getVehicles();

    // Wait for first attempt
    await vi.advanceTimersByTimeAsync(0);

    // Wait for 1st retry (1s backoff)
    await vi.advanceTimersByTimeAsync(1000);

    // Wait for 2nd retry (2s backoff)
    await vi.advanceTimersByTimeAsync(2000);

    // Wait for 3rd retry (4s backoff)
    await vi.advanceTimersByTimeAsync(4000);

    const result = await promise;

    expect(attemptCount).toBe(4); // Initial + 3 retries
    expect(result).toEqual([]);
  });

  it('retries 504 errors up to 3 times', async () => {
    let attemptCount = 0;

    mock.onGet('/api/v1/vehicles').reply(() => {
      attemptCount++;
      if (attemptCount < 4) {
        return [504, { error: { code: 'SYS_003', message: 'Gateway timeout' } }];
      }
      return [200, []];
    });

    const promise = vehicleAPI.getVehicles();

    await vi.advanceTimersByTimeAsync(0);
    await vi.advanceTimersByTimeAsync(1000);
    await vi.advanceTimersByTimeAsync(2000);
    await vi.advanceTimersByTimeAsync(4000);

    const result = await promise;

    expect(attemptCount).toBe(4);
    expect(result).toEqual([]);
  });

  it('fails after 3 retry attempts if still getting 503', async () => {
    let attemptCount = 0;

    mock.onGet('/api/v1/vehicles').reply(() => {
      attemptCount++;
      return [503, { error: { code: 'SYS_002', message: 'Service unavailable' } }];
    });

    const promise = vehicleAPI.getVehicles();

    await vi.advanceTimersByTimeAsync(0);
    await vi.advanceTimersByTimeAsync(1000);
    await vi.advanceTimersByTimeAsync(2000);
    await vi.advanceTimersByTimeAsync(4000);

    await expect(promise).rejects.toThrow();
    expect(attemptCount).toBe(4); // Initial + 3 retries
  });

  it('does not retry 400 errors', async () => {
    let attemptCount = 0;

    mock.onGet('/api/v1/vehicles').reply(() => {
      attemptCount++;
      return [400, { error: { code: 'VAL_003', message: 'Missing field' } }];
    });

    await expect(vehicleAPI.getVehicles()).rejects.toThrow();
    expect(attemptCount).toBe(1); // No retries
  });

  it('does not retry 401 errors', async () => {
    let attemptCount = 0;

    mock.onGet('/api/v1/vehicles').reply(() => {
      attemptCount++;
      return [401, { error: { code: 'AUTH_002', message: 'Token expired' } }];
    });

    await expect(vehicleAPI.getVehicles()).rejects.toThrow();
    expect(attemptCount).toBe(1); // No retries (handled by token refresh interceptor)
  });

  it('does not retry 403 errors', async () => {
    let attemptCount = 0;

    mock.onGet('/api/v1/vehicles').reply(() => {
      attemptCount++;
      return [403, { error: { code: 'AUTH_004', message: 'Insufficient permissions' } }];
    });

    await expect(vehicleAPI.getVehicles()).rejects.toThrow();
    expect(attemptCount).toBe(1); // No retries
  });

  it('does not retry 404 errors', async () => {
    let attemptCount = 0;

    mock.onGet('/api/v1/vehicles/123').reply(() => {
      attemptCount++;
      return [404, { error: { code: 'VAL_001', message: 'Vehicle not found' } }];
    });

    await expect(vehicleAPI.getVehicle('123')).rejects.toThrow();
    expect(attemptCount).toBe(1); // No retries
  });

  it('uses exponential backoff: 1s, 2s, 4s', async () => {
    const delays: number[] = [];
    let lastTime = Date.now();

    mock.onGet('/api/v1/vehicles').reply(() => {
      const now = Date.now();
      if (delays.length > 0) {
        delays.push(now - lastTime);
      }
      lastTime = now;
      return [503, { error: { code: 'SYS_002', message: 'Service unavailable' } }];
    });

    const promise = vehicleAPI.getVehicles();

    await vi.advanceTimersByTimeAsync(0);
    delays.push(0); // Start tracking

    await vi.advanceTimersByTimeAsync(1000);
    await vi.advanceTimersByTimeAsync(2000);
    await vi.advanceTimersByTimeAsync(4000);

    await expect(promise).rejects.toThrow();

    // Verify delays are approximately 1s, 2s, 4s
    expect(delays[0]).toBeGreaterThanOrEqual(0);
    expect(delays[1]).toBeGreaterThanOrEqual(1000);
    expect(delays[2]).toBeGreaterThanOrEqual(2000);
  });
});

describe('shouldRetryError utility', () => {
  it('returns true for 503 errors', () => {
    const error = {
      isAxiosError: true,
      response: { status: 503 },
    };
    expect(shouldRetryError(error)).toBe(true);
  });

  it('returns true for 504 errors', () => {
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

  it('returns false for 400 errors', () => {
    const error = {
      isAxiosError: true,
      response: { status: 400 },
    };
    expect(shouldRetryError(error)).toBe(false);
  });

  it('returns false for 401 errors', () => {
    const error = {
      isAxiosError: true,
      response: { status: 401 },
    };
    expect(shouldRetryError(error)).toBe(false);
  });

  it('returns false for 404 errors', () => {
    const error = {
      isAxiosError: true,
      response: { status: 404 },
    };
    expect(shouldRetryError(error)).toBe(false);
  });

  it('returns false for 500 errors', () => {
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
});
