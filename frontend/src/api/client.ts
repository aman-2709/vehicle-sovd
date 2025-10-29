/**
 * API Client Configuration
 *
 * Axios instance with automatic JWT injection and token refresh logic.
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  LoginRequest,
  TokenResponse,
  RefreshRequest,
  RefreshResponse,
  UserProfile,
  LogoutResponse,
} from '../types/auth';
import type { VehicleResponse, VehicleStatusResponse, VehicleListParams } from '../types/vehicle';
import type { CommandSubmitRequest, CommandResponse } from '../types/command';

// Get API base URL from environment variable or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Token management
let accessToken: string | null = null;
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string) => void;
  reject: (error: Error) => void;
}> = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

export const getAccessToken = (): string | null => {
  return accessToken;
};

// Request interceptor: Inject JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Skip token injection for login and refresh endpoints
    const isAuthEndpoint =
      config.url?.includes('/auth/login') || config.url?.includes('/auth/refresh');

    if (!isAuthEndpoint && accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Handle 401 and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    const requestWithRetry = originalRequest as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !requestWithRetry._retry) {
      // Skip refresh for login endpoint errors
      if (requestWithRetry.url?.includes('/auth/login')) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token: string) => {
            requestWithRetry.headers.Authorization = `Bearer ${token}`;
            return apiClient(requestWithRetry);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      requestWithRetry._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');

      if (!refreshToken) {
        // No refresh token available, redirect to login
        processQueue(new Error('No refresh token available'), null);
        isRefreshing = false;
        // Clear tokens and redirect
        setAccessToken(null);
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        // Attempt to refresh the token
        const response = await axios.post<RefreshResponse>(
          `${API_BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken } as RefreshRequest,
          {
            headers: { 'Content-Type': 'application/json' },
          }
        );

        const newAccessToken = response.data.access_token;
        setAccessToken(newAccessToken);

        // Process queued requests with new token
        processQueue(null, newAccessToken);

        // Retry original request with new token
        requestWithRetry.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(requestWithRetry);
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        processQueue(refreshError as Error, null);
        setAccessToken(null);
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// API methods
export const authAPI = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', credentials);
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<RefreshResponse> => {
    const response = await apiClient.post<RefreshResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    } as RefreshRequest);
    return response.data;
  },

  logout: async (): Promise<LogoutResponse> => {
    const response = await apiClient.post<LogoutResponse>('/api/v1/auth/logout');
    return response.data;
  },

  getProfile: async (): Promise<UserProfile> => {
    const response = await apiClient.get<UserProfile>('/api/v1/auth/me');
    return response.data;
  },
};

// Vehicle API methods
export const vehicleAPI = {
  /**
   * Get list of vehicles with optional filtering and pagination.
   *
   * @param params - Query parameters for filtering and pagination
   * @returns Array of vehicle objects
   */
  getVehicles: async (params?: VehicleListParams): Promise<VehicleResponse[]> => {
    const response = await apiClient.get<VehicleResponse[]>('/api/v1/vehicles', { params });
    return response.data;
  },

  /**
   * Get a single vehicle by ID.
   *
   * @param vehicleId - UUID of the vehicle to retrieve
   * @returns Vehicle object with full details
   */
  getVehicle: async (vehicleId: string): Promise<VehicleResponse> => {
    const response = await apiClient.get<VehicleResponse>(`/api/v1/vehicles/${vehicleId}`);
    return response.data;
  },

  /**
   * Get vehicle connection status (cached in Redis for 30 seconds).
   *
   * @param vehicleId - UUID of the vehicle
   * @returns Vehicle status object with connection_status, last_seen_at, and health metrics
   */
  getVehicleStatus: async (vehicleId: string): Promise<VehicleStatusResponse> => {
    const response = await apiClient.get<VehicleStatusResponse>(
      `/api/v1/vehicles/${vehicleId}/status`
    );
    return response.data;
  },
};

// Command API methods
export const commandAPI = {
  /**
   * Submit a new command to a vehicle.
   *
   * @param request - Command submission request with vehicle_id, command_name, and command_params
   * @returns Command response object with command_id and status
   */
  submitCommand: async (request: CommandSubmitRequest): Promise<CommandResponse> => {
    const response = await apiClient.post<CommandResponse>('/api/v1/commands', request);
    return response.data;
  },
};

export default apiClient;
