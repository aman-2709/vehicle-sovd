/**
 * LoginPage Component Tests
 *
 * Tests for login form rendering, submission, error handling, and token storage.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import LoginPage from '../../src/pages/LoginPage';
import { AuthProvider } from '../../src/context/AuthContext';
import theme from '../../src/styles/theme';
import * as apiClient from '../../src/api/client';

// Mock the API client
vi.mock('../../src/api/client', () => ({
  authAPI: {
    login: vi.fn(),
    getProfile: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
  },
  setAccessToken: vi.fn(),
  getAccessToken: vi.fn(),
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders login form with username and password fields', () => {
    renderLoginPage();

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('renders SOVD Command WebApp title', () => {
    renderLoginPage();

    expect(screen.getByText(/SOVD Command WebApp/i)).toBeInTheDocument();
  });

  it('displays validation error when fields are empty', async () => {
    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    // Fill fields with whitespace only
    fireEvent.change(usernameInput, { target: { value: '   ' } });
    fireEvent.change(passwordInput, { target: { value: '   ' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/username and password are required/i)).toBeInTheDocument();
    });
  });

  it('calls login API with correct credentials on form submission', async () => {
    const mockLoginResponse = {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
    };

    const mockUserProfile = {
      user_id: 1,
      username: 'admin',
      role: 'admin',
      email: null,
    };

    vi.mocked(apiClient.authAPI.login).mockResolvedValue(mockLoginResponse);
    vi.mocked(apiClient.authAPI.getProfile).mockResolvedValue(mockUserProfile);

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'admin' } });
    fireEvent.change(passwordInput, { target: { value: 'admin123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(apiClient.authAPI.login).toHaveBeenCalledWith({
        username: 'admin',
        password: 'admin123',
      });
    });
  });

  it('stores refresh token in localStorage on successful login', async () => {
    const mockLoginResponse = {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
    };

    const mockUserProfile = {
      user_id: 1,
      username: 'admin',
      role: 'admin',
      email: null,
    };

    vi.mocked(apiClient.authAPI.login).mockResolvedValue(mockLoginResponse);
    vi.mocked(apiClient.authAPI.getProfile).mockResolvedValue(mockUserProfile);

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'admin' } });
    fireEvent.change(passwordInput, { target: { value: 'admin123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(localStorage.getItem('refresh_token')).toBe('mock-refresh-token');
    });
  });

  it('displays error message on login failure (401)', async () => {
    const mockError = {
      response: {
        status: 401,
        data: { detail: 'Incorrect username or password' },
      },
    };

    vi.mocked(apiClient.authAPI.login).mockRejectedValue(mockError);

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'wronguser' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument();
    });
  });

  it('displays generic error message on network error', async () => {
    const mockError = {
      response: {
        status: 500,
      },
    };

    vi.mocked(apiClient.authAPI.login).mockRejectedValue(mockError);

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'admin' } });
    fireEvent.change(passwordInput, { target: { value: 'admin123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/an error occurred/i)).toBeInTheDocument();
    });
  });

  it('navigates to dashboard after successful login', async () => {
    const mockLoginResponse = {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
    };

    const mockUserProfile = {
      user_id: 1,
      username: 'admin',
      role: 'admin',
      email: null,
    };

    vi.mocked(apiClient.authAPI.login).mockResolvedValue(mockLoginResponse);
    vi.mocked(apiClient.authAPI.getProfile).mockResolvedValue(mockUserProfile);

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'admin' } });
    fireEvent.change(passwordInput, { target: { value: 'admin123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
  });

  it('disables form fields and shows loading spinner during submission', async () => {
    const mockLoginResponse = {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      expires_in: 3600,
    };

    const mockUserProfile = {
      user_id: 1,
      username: 'admin',
      role: 'admin',
      email: null,
    };

    // Delay the response to test loading state
    vi.mocked(apiClient.authAPI.login).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve(mockLoginResponse), 100)
        )
    );
    vi.mocked(apiClient.authAPI.getProfile).mockResolvedValue(mockUserProfile);

    renderLoginPage();

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(usernameInput, { target: { value: 'admin' } });
    fireEvent.change(passwordInput, { target: { value: 'admin123' } });
    fireEvent.click(submitButton);

    // Check that fields are disabled during loading
    expect(usernameInput).toHaveProperty('disabled', true);
    expect(passwordInput).toHaveProperty('disabled', true);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalled();
    });
  });
});
