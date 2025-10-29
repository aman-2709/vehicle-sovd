/**
 * Authentication Type Definitions
 *
 * TypeScript interfaces matching backend Pydantic schemas.
 */

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  user_id: number;
  username: string;
  role: string;
  email: string | null;
}

export interface LogoutResponse {
  message: string;
}
