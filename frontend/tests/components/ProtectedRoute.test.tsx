/**
 * ProtectedRoute Component Tests
 *
 * Tests for protected route wrapper including authentication states and redirects.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '../../src/components/auth/ProtectedRoute';
import * as AuthContext from '../../src/context/AuthContext';

describe('ProtectedRoute Component', () => {
  const TestComponent = () => <div>Protected Content</div>;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('displays loading spinner when authentication is being checked', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Authenticated State', () => {
    it('renders children when user is authenticated', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: {
          user_id: '1',
          username: 'testuser',
          role: 'engineer',
        },
        login: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('renders complex children components when authenticated', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: {
          user_id: '1',
          username: 'testuser',
          role: 'engineer',
        },
        login: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      const ComplexComponent = () => (
        <div>
          <h1>Dashboard</h1>
          <p>Welcome back</p>
        </div>
      );

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <ComplexComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Welcome back')).toBeInTheDocument();
    });
  });

  describe('Unauthenticated State', () => {
    it('redirects to login when user is not authenticated', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route
              path="/protected"
              element={
                <ProtectedRoute>
                  <TestComponent />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div>Login Page</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('Login Page')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('does not render children when not authenticated', () => {
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      render(
        <MemoryRouter>
          <Routes>
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <TestComponent />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div>Login Page</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('State Transitions', () => {
    it('transitions from loading to authenticated state', () => {
      const { rerender } = render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      // Initial loading state
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      rerender(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();

      // Transition to authenticated
      vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: {
          user_id: '1',
          username: 'testuser',
          role: 'engineer',
        },
        login: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
      });

      rerender(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });
});
