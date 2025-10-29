/**
 * Authentication Context
 *
 * Manages JWT tokens and authentication state:
 * - Access token stored in memory (state)
 * - Refresh token stored in localStorage
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI, setAccessToken as setApiAccessToken } from '../api/client';
import type { LoginRequest, UserProfile } from '../types/auth';

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserProfile | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [user, setUser] = useState<UserProfile | null>(null);

  // Check for existing refresh token on mount
  useEffect(() => {
    void (async () => {
      const storedRefreshToken = localStorage.getItem('refresh_token');

      if (storedRefreshToken) {
        try {
          // Try to refresh the access token
          const response = await authAPI.refresh(storedRefreshToken);
          setApiAccessToken(response.access_token);

          // Fetch user profile
          const profile = await authAPI.getProfile();
          setUser(profile);
          setIsAuthenticated(true);
        } catch (error) {
          // Refresh token is invalid or expired
          localStorage.removeItem('refresh_token');
          setApiAccessToken(null);
          setIsAuthenticated(false);
          setUser(null);
        }
      }

      setIsLoading(false);
    })();
  }, []);

  const login = async (credentials: LoginRequest): Promise<void> => {
    try {
      // Call login API
      const response = await authAPI.login(credentials);

      // Store tokens
      setApiAccessToken(response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);

      // Fetch user profile
      const profile = await authAPI.getProfile();
      setUser(profile);
      setIsAuthenticated(true);
    } catch (error) {
      // Clear any existing tokens on login failure
      setApiAccessToken(null);
      localStorage.removeItem('refresh_token');
      setIsAuthenticated(false);
      setUser(null);
      throw error;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      // Call logout API (if authenticated)
      if (isAuthenticated) {
        await authAPI.logout();
      }
    } catch (error) {
      // Ignore logout API errors, continue with local cleanup
      console.error('Logout API error:', error);
    } finally {
      // Clear tokens and state
      setApiAccessToken(null);
      localStorage.removeItem('refresh_token');
      setIsAuthenticated(false);
      setUser(null);
    }
  };

  const refreshToken = async (): Promise<void> => {
    const storedRefreshToken = localStorage.getItem('refresh_token');

    if (!storedRefreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await authAPI.refresh(storedRefreshToken);
      setApiAccessToken(response.access_token);
    } catch (error) {
      // Refresh failed, clear tokens
      setApiAccessToken(null);
      localStorage.removeItem('refresh_token');
      setIsAuthenticated(false);
      setUser(null);
      throw error;
    }
  };

  const value: AuthContextType = {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    refreshToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
