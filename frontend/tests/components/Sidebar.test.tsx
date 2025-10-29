/**
 * Sidebar Component Tests
 *
 * Tests for navigation sidebar component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Sidebar from '../../src/components/common/Sidebar';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Sidebar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders all navigation items', () => {
      render(
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      );

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Vehicles')).toBeInTheDocument();
      expect(screen.getByText('Commands')).toBeInTheDocument();
      expect(screen.getByText('History')).toBeInTheDocument();
    });

    it('renders navigation icons', () => {
      const { container } = render(
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      );

      // Check that icons are rendered (MUI renders them as SVGs)
      const icons = container.querySelectorAll('.MuiListItemIcon-root svg');
      expect(icons.length).toBe(4);
    });

    it('renders as permanent drawer', () => {
      const { container } = render(
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      );

      const drawer = container.querySelector('.MuiDrawer-root');
      expect(drawer).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('navigates to dashboard when dashboard item is clicked', () => {
      render(
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      );

      fireEvent.click(screen.getByText('Dashboard'));
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });

    it('navigates to vehicles when vehicles item is clicked', () => {
      render(
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      );

      fireEvent.click(screen.getByText('Vehicles'));
      expect(mockNavigate).toHaveBeenCalledWith('/vehicles');
    });

    it('navigates to commands when commands item is clicked', () => {
      render(
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      );

      fireEvent.click(screen.getByText('Commands'));
      expect(mockNavigate).toHaveBeenCalledWith('/commands');
    });

    it('navigates to history when history item is clicked', () => {
      render(
        <MemoryRouter>
          <Sidebar />
        </MemoryRouter>
      );

      fireEvent.click(screen.getByText('History'));
      expect(mockNavigate).toHaveBeenCalledWith('/history');
    });
  });

  describe('Route Handling', () => {
    it('renders sidebar consistently across all routes', () => {
      const routes = ['/dashboard', '/vehicles', '/commands', '/history', '/other'];

      routes.forEach((route) => {
        const { unmount } = render(
          <MemoryRouter initialEntries={[route]}>
            <Sidebar />
          </MemoryRouter>
        );

        // All navigation items should be rendered
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Vehicles')).toBeInTheDocument();
        expect(screen.getByText('Commands')).toBeInTheDocument();
        expect(screen.getByText('History')).toBeInTheDocument();

        unmount();
      });
    });
  });
});
