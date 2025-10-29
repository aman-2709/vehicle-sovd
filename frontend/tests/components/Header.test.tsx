/**
 * Header Component Tests
 *
 * Tests for header component including navigation, user menu, and logout functionality.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Header from '../../src/components/common/Header';
import * as AuthContext from '../../src/context/AuthContext';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Header Component', () => {
  const mockLogout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock useAuth hook
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: {
        user_id: '1',
        username: 'testuser',
        role: 'engineer',
      },
      login: vi.fn(),
      logout: mockLogout,
      refreshToken: vi.fn(),
    });
  });

  it('renders app title', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    expect(screen.getByText('SOVD Command')).toBeInTheDocument();
  });

  it('displays username from auth context', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    // Username is visible in the header before opening menu
    expect(screen.getByText('testuser')).toBeInTheDocument();
  });

  it('renders all navigation links', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Vehicles')).toBeInTheDocument();
    expect(screen.getByText('Commands')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
  });

  it('navigates when clicking navigation links', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByText('Dashboard'));
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');

    fireEvent.click(screen.getByText('Vehicles'));
    expect(mockNavigate).toHaveBeenCalledWith('/vehicles');

    fireEvent.click(screen.getByText('Commands'));
    expect(mockNavigate).toHaveBeenCalledWith('/commands');

    fireEvent.click(screen.getByText('History'));
    expect(mockNavigate).toHaveBeenCalledWith('/history');
  });

  it('opens user menu when clicking account icon', () => {
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    const menuButton = screen.getByTestId('user-menu-button');
    fireEvent.click(menuButton);

    // Check menu items are visible
    expect(screen.getByText('Role: engineer')).toBeInTheDocument();
    expect(screen.getByTestId('logout-button')).toBeInTheDocument();
  });

  it('calls logout and navigates when clicking logout button', async () => {
    mockLogout.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    // Open user menu
    const menuButton = screen.getByTestId('user-menu-button');
    fireEvent.click(menuButton);

    // Click logout
    const logoutButton = screen.getByTestId('logout-button');
    fireEvent.click(logoutButton);

    // Wait for async logout to complete
    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledTimes(1);
      expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
    });
  });

  it('highlights active navigation link', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Header />
      </MemoryRouter>
    );

    const dashboardButton = screen.getByText('Dashboard').closest('button');
    expect(dashboardButton).toHaveStyle({ fontWeight: 600 });
  });
});
