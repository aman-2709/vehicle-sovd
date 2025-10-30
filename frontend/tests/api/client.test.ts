/**
 * Tests for API Client
 *
 * Comprehensive test suite covering token management, interceptors,
 * token refresh logic, and all API methods.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import type {
  LoginRequest,
  TokenResponse,
  RefreshResponse,
  UserProfile,
  LogoutResponse,
} from '../../src/types/auth';
import type { VehicleResponse, VehicleStatusResponse } from '../../src/types/vehicle';
import type { CommandSubmitRequest, CommandResponse } from '../../src/types/command';

// We'll use dynamic import to ensure fresh module state
let setAccessToken: (token: string | null) => void;
let getAccessToken: () => string | null;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let authAPI: any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let vehicleAPI: any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let commandAPI: any;

// Create mock adapter that will mock the actual axios used by client.ts
const mock = new MockAdapter(axios, { onNoMatch: 'throwException' });

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Save original window.location
const originalLocation = window.location;

describe('API Client', () => {
  beforeEach(async () => {
    mock.reset();
    localStorageMock.clear();

    // Mock window.location
    delete (window as any).location;
    window.location = { href: '' } as Location;

    // Dynamically import the client module to get fresh state
    const clientModule = await import('../../src/api/client');
    setAccessToken = clientModule.setAccessToken;
    getAccessToken = clientModule.getAccessToken;
    authAPI = clientModule.authAPI;
    vehicleAPI = clientModule.vehicleAPI;
    commandAPI = clientModule.commandAPI;

    // Reset token state
    setAccessToken(null);
  });

  afterEach(() => {
    mock.reset();
    window.location = originalLocation;
  });

  describe('Token Management', () => {
    it('should set and get access token', () => {
      const token = 'test-token-123';
      setAccessToken(token);
      expect(getAccessToken()).toBe(token);
    });

    it('should return null when no token is set', () => {
      expect(getAccessToken()).toBeNull();
    });

    it('should clear token when set to null', () => {
      setAccessToken('test-token');
      expect(getAccessToken()).toBe('test-token');
      setAccessToken(null);
      expect(getAccessToken()).toBeNull();
    });
  });

  describe('Auth API Methods', () => {
    describe('login', () => {
      it('should make POST request to /api/v1/auth/login and return token response', async () => {
        const credentials: LoginRequest = {
          username: 'testuser',
          password: 'testpassword',
        };

        const mockResponse: TokenResponse = {
          access_token: 'access-token-123',
          refresh_token: 'refresh-token-456',
          token_type: 'bearer',
          expires_in: 3600,
        };

        mock.onPost('/api/v1/auth/login', credentials).reply(200, mockResponse);

        const result = await authAPI.login(credentials);

        expect(result).toEqual(mockResponse);
        expect(mock.history.post.length).toBe(1);
        expect(mock.history.post[0].url).toBe('/api/v1/auth/login');
      });

      it('should handle login failure', async () => {
        const credentials: LoginRequest = {
          username: 'wronguser',
          password: 'wrongpassword',
        };

        mock.onPost('/api/v1/auth/login').reply(401, {
          detail: 'Invalid credentials',
        });

        await expect(authAPI.login(credentials)).rejects.toThrow();
      });
    });

    describe('refresh', () => {
      it('should make POST request to /api/v1/auth/refresh with refresh token', async () => {
        const refreshToken = 'refresh-token-123';
        const mockResponse: RefreshResponse = {
          access_token: 'new-access-token',
          token_type: 'bearer',
          expires_in: 3600,
        };

        mock.onPost('/api/v1/auth/refresh').reply(200, mockResponse);

        const result = await authAPI.refresh(refreshToken);

        expect(result).toEqual(mockResponse);
        expect(mock.history.post.length).toBe(1);
        expect(JSON.parse(mock.history.post[0].data as string)).toEqual({
          refresh_token: refreshToken,
        });
      });
    });

    describe('logout', () => {
      it('should make POST request to /api/v1/auth/logout', async () => {
        setAccessToken('test-token');

        const mockResponse: LogoutResponse = {
          message: 'Successfully logged out',
        };

        mock.onPost('/api/v1/auth/logout').reply(200, mockResponse);

        const result = await authAPI.logout();

        expect(result).toEqual(mockResponse);
        expect(mock.history.post.length).toBe(1);
        expect(mock.history.post[0].url).toBe('/api/v1/auth/logout');
      });
    });

    describe('getProfile', () => {
      it('should make GET request to /api/v1/auth/me', async () => {
        setAccessToken('test-token');

        const mockProfile: UserProfile = {
          user_id: 'user-123',
          username: 'testuser',
          role: 'admin',
          email: 'test@example.com',
        };

        mock.onGet('/api/v1/auth/me').reply(200, mockProfile);

        const result = await authAPI.getProfile();

        expect(result).toEqual(mockProfile);
        expect(mock.history.get.length).toBe(1);
        expect(mock.history.get[0].url).toBe('/api/v1/auth/me');
      });
    });
  });

  describe('Vehicle API Methods', () => {
    describe('getVehicles', () => {
      it('should make GET request to /api/v1/vehicles without params', async () => {
        setAccessToken('test-token');

        const mockVehicles: VehicleResponse[] = [
          {
            vehicle_id: 'vehicle-1',
            vin: 'VIN123',
            model: 'Model X',
            connection_status: 'connected',
            last_seen_at: '2024-01-01T00:00:00Z',
          },
        ];

        mock.onGet('/api/v1/vehicles').reply(200, mockVehicles);

        const result = await vehicleAPI.getVehicles();

        expect(result).toEqual(mockVehicles);
        expect(mock.history.get.length).toBe(1);
        expect(mock.history.get[0].url).toBe('/api/v1/vehicles');
      });

      it('should make GET request to /api/v1/vehicles with query params', async () => {
        setAccessToken('test-token');

        const mockVehicles: VehicleResponse[] = [];
        const params = { status: 'connected', limit: 10 };

        mock.onGet('/api/v1/vehicles').reply(200, mockVehicles);

        const result = await vehicleAPI.getVehicles(params);

        expect(result).toEqual(mockVehicles);
        expect(mock.history.get[0].params).toEqual(params);
      });
    });

    describe('getVehicle', () => {
      it('should make GET request to /api/v1/vehicles/{id}', async () => {
        setAccessToken('test-token');

        const vehicleId = 'vehicle-123';
        const mockVehicle: VehicleResponse = {
          vehicle_id: vehicleId,
          vin: 'VIN123',
          model: 'Model X',
          connection_status: 'connected',
          last_seen_at: '2024-01-01T00:00:00Z',
        };

        mock.onGet(`/api/v1/vehicles/${vehicleId}`).reply(200, mockVehicle);

        const result = await vehicleAPI.getVehicle(vehicleId);

        expect(result).toEqual(mockVehicle);
        expect(mock.history.get.length).toBe(1);
        expect(mock.history.get[0].url).toBe(`/api/v1/vehicles/${vehicleId}`);
      });
    });

    describe('getVehicleStatus', () => {
      it('should make GET request to /api/v1/vehicles/{id}/status', async () => {
        setAccessToken('test-token');

        const vehicleId = 'vehicle-123';
        const mockStatus: VehicleStatusResponse = {
          vehicle_id: vehicleId,
          connection_status: 'connected',
          last_seen_at: '2024-01-01T00:00:00Z',
        };

        mock.onGet(`/api/v1/vehicles/${vehicleId}/status`).reply(200, mockStatus);

        const result = await vehicleAPI.getVehicleStatus(vehicleId);

        expect(result).toEqual(mockStatus);
        expect(mock.history.get.length).toBe(1);
        expect(mock.history.get[0].url).toBe(`/api/v1/vehicles/${vehicleId}/status`);
      });
    });
  });

  describe('Command API Methods', () => {
    describe('submitCommand', () => {
      it('should make POST request to /api/v1/commands', async () => {
        setAccessToken('test-token');

        const commandRequest: CommandSubmitRequest = {
          vehicle_id: 'vehicle-123',
          command_name: 'GetVehicleData',
          command_params: { data_id: 'VIN' },
        };

        const mockResponse: CommandResponse = {
          command_id: 'command-123',
          vehicle_id: 'vehicle-123',
          command_name: 'GetVehicleData',
          status: 'pending',
          created_at: '2024-01-01T00:00:00Z',
        };

        mock.onPost('/api/v1/commands', commandRequest).reply(200, mockResponse);

        const result = await commandAPI.submitCommand(commandRequest);

        expect(result).toEqual(mockResponse);
        expect(mock.history.post.length).toBe(1);
        expect(mock.history.post[0].url).toBe('/api/v1/commands');
        expect(JSON.parse(mock.history.post[0].data as string)).toEqual(commandRequest);
      });
    });
  });

  describe('Request Interceptor - JWT Token Injection', () => {
    it('should inject token into Authorization header for authenticated requests', async () => {
      const token = 'test-token-123';
      setAccessToken(token);

      mock.onGet('/api/v1/vehicles').reply(200, []);

      await vehicleAPI.getVehicles();

      expect(mock.history.get.length).toBe(1);
      expect(mock.history.get[0].headers?.Authorization).toBe(`Bearer ${token}`);
    });

    it('should NOT inject token for /auth/login endpoint', async () => {
      setAccessToken('test-token');

      const credentials: LoginRequest = {
        username: 'test',
        password: 'test',
      };

      mock.onPost('/api/v1/auth/login').reply(200, {
        access_token: 'new-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
        expires_in: 3600,
      });

      await authAPI.login(credentials);

      expect(mock.history.post.length).toBe(1);
      expect(mock.history.post[0].headers?.Authorization).toBeUndefined();
    });

    it('should NOT inject token for /auth/refresh endpoint', async () => {
      setAccessToken('test-token');

      mock.onPost('/api/v1/auth/refresh').reply(200, {
        access_token: 'new-token',
        token_type: 'bearer',
        expires_in: 3600,
      });

      await authAPI.refresh('refresh-token');

      expect(mock.history.post.length).toBe(1);
      expect(mock.history.post[0].headers?.Authorization).toBeUndefined();
    });

    it('should NOT inject token when no token is set', async () => {
      setAccessToken(null);

      mock.onGet('/api/v1/vehicles').reply(200, []);

      await vehicleAPI.getVehicles();

      expect(mock.history.get.length).toBe(1);
      expect(mock.history.get[0].headers?.Authorization).toBeUndefined();
    });
  });

  describe('Response Interceptor - Token Refresh Logic', () => {
    it('should NOT trigger refresh for 401 errors on /auth/login endpoint', async () => {
      const credentials: LoginRequest = {
        username: 'wrong',
        password: 'wrong',
      };

      mock.onPost('/api/v1/auth/login').reply(401, {
        detail: 'Invalid credentials',
      });

      await expect(authAPI.login(credentials)).rejects.toThrow();

      // Should only have the login request, no refresh request
      expect(mock.history.post.length).toBe(1);
      expect(mock.history.post[0].url).toBe('/api/v1/auth/login');
    });

    it('should redirect to /login when refresh token is missing', async () => {
      setAccessToken('expired-token');
      localStorage.removeItem('refresh_token');

      mock.onGet('/api/v1/vehicles').reply(401);

      await expect(vehicleAPI.getVehicles()).rejects.toThrow();

      expect(window.location.href).toBe('/login');
      expect(getAccessToken()).toBeNull();
    });

    it('should successfully refresh token and retry original request on 401', async () => {
      setAccessToken('expired-token');
      localStorage.setItem('refresh_token', 'valid-refresh-token');

      const mockVehicles: VehicleResponse[] = [
        {
          vehicle_id: 'vehicle-1',
          vin: 'VIN123',
          model: 'Model X',
          connection_status: 'connected',
          last_seen_at: '2024-01-01T00:00:00Z',
        },
      ];

      // First request fails with 401
      mock.onGet('/api/v1/vehicles').replyOnce(401);

      // Refresh succeeds (must match the full URL including base)
      mock
        .onPost('http://localhost:8000/api/v1/auth/refresh')
        .reply(200, {
          access_token: 'new-access-token',
          token_type: 'bearer',
          expires_in: 3600,
        });

      // Retry succeeds
      mock.onGet('/api/v1/vehicles').reply(200, mockVehicles);

      const result = await vehicleAPI.getVehicles();

      expect(result).toEqual(mockVehicles);
      expect(getAccessToken()).toBe('new-access-token');

      // Should have: 1 failed GET, 1 refresh POST, 1 successful GET
      expect(mock.history.get.length).toBe(2);
      expect(mock.history.post.length).toBe(1);
    });

    it('should redirect to /login when token refresh fails', async () => {
      setAccessToken('expired-token');
      localStorage.setItem('refresh_token', 'invalid-refresh-token');

      // First request fails with 401
      mock.onGet('/api/v1/vehicles').reply(401);

      // Refresh fails (must match the full URL including base)
      mock.onPost('http://localhost:8000/api/v1/auth/refresh').reply(401, {
        detail: 'Invalid refresh token',
      });

      await expect(vehicleAPI.getVehicles()).rejects.toThrow();

      expect(window.location.href).toBe('/login');
      expect(getAccessToken()).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });

    it('should handle concurrent requests during token refresh (queue mechanism)', async () => {
      setAccessToken('expired-token');
      localStorage.setItem('refresh_token', 'valid-refresh-token');

      const mockVehicles: VehicleResponse[] = [
        {
          vehicle_id: 'vehicle-1',
          vin: 'VIN123',
          model: 'Model X',
          connection_status: 'connected',
          last_seen_at: '2024-01-01T00:00:00Z',
        },
      ];

      const mockProfile: UserProfile = {
        user_id: 'user-123',
        username: 'testuser',
        role: 'admin',
        email: 'test@example.com',
      };

      // Both initial requests fail with 401
      mock.onGet('/api/v1/vehicles').replyOnce(401);
      mock.onGet('/api/v1/auth/me').replyOnce(401);

      // Refresh succeeds (should only be called once) - must match full URL
      mock.onPost('http://localhost:8000/api/v1/auth/refresh').reply(200, {
        access_token: 'new-access-token',
        token_type: 'bearer',
        expires_in: 3600,
      });

      // Retries succeed
      mock.onGet('/api/v1/vehicles').reply(200, mockVehicles);
      mock.onGet('/api/v1/auth/me').reply(200, mockProfile);

      // Make concurrent requests
      const [vehiclesResult, profileResult] = await Promise.all([
        vehicleAPI.getVehicles(),
        authAPI.getProfile(),
      ]);

      expect(vehiclesResult).toEqual(mockVehicles);
      expect(profileResult).toEqual(mockProfile);
      expect(getAccessToken()).toBe('new-access-token');

      // Should have: 1 refresh POST, 2 failed GETs, 2 successful GETs
      expect(mock.history.post.length).toBe(1);
      expect(mock.history.get.length).toBe(4); // 2 failed + 2 retried
    });

    it('should reject all queued requests when token refresh fails', async () => {
      setAccessToken('expired-token');
      localStorage.setItem('refresh_token', 'invalid-refresh-token');

      // Both initial requests fail with 401
      mock.onGet('/api/v1/vehicles').reply(401);
      mock.onGet('/api/v1/auth/me').reply(401);

      // Refresh fails - must match full URL
      mock.onPost('http://localhost:8000/api/v1/auth/refresh').reply(401, {
        detail: 'Invalid refresh token',
      });

      // Both requests should fail
      await expect(
        Promise.all([vehicleAPI.getVehicles(), authAPI.getProfile()])
      ).rejects.toThrow();

      expect(window.location.href).toBe('/login');
      expect(getAccessToken()).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });

    it('should handle non-401 errors without triggering refresh', async () => {
      setAccessToken('valid-token');

      mock.onGet('/api/v1/vehicles').reply(500, {
        detail: 'Internal server error',
      });

      await expect(vehicleAPI.getVehicles()).rejects.toThrow();

      // Should not attempt refresh
      expect(mock.history.post.length).toBe(0);
      expect(getAccessToken()).toBe('valid-token');
    });

    it('should handle errors without config object', async () => {
      setAccessToken('valid-token');

      // Create an axios error without config
      const errorWithoutConfig = new Error('Network Error') as any;
      errorWithoutConfig.isAxiosError = true;
      errorWithoutConfig.response = undefined;
      errorWithoutConfig.config = undefined;

      mock.onGet('/api/v1/vehicles').reply(() => {
        throw errorWithoutConfig;
      });

      await expect(vehicleAPI.getVehicles()).rejects.toThrow();
    });
  });
});
