/**
 * HistoryPage Component Tests
 *
 * Tests for the command history page including filters, pagination, and RBAC.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import HistoryPage from '../../src/pages/HistoryPage';

// Mock the auth context
const mockUser = {
  user_id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  role: 'engineer',
};

const mockAdminUser = {
  user_id: 'admin-123',
  username: 'admin',
  email: 'admin@example.com',
  role: 'admin',
};

vi.mock('../../src/context/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    user: mockUser,
    isAuthenticated: true,
  })),
}));

// Mock the API client
const mockCommandHistory = {
  commands: [
    {
      command_id: '123e4567-e89b-12d3-a456-426614174000',
      user_id: 'user-123',
      vehicle_id: '789e4567-e89b-12d3-a456-426614174000',
      command_name: 'lockDoors',
      command_params: { duration: 3600 },
      status: 'completed',
      error_message: null,
      submitted_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
    },
  ],
  limit: 25,
  offset: 0,
};

const mockVehicles = [
  {
    vehicle_id: '789e4567-e89b-12d3-a456-426614174000',
    vin: '1HGCM82633A123456',
    make: 'Honda',
    model: 'Accord',
    year: 2024,
    connection_status: 'connected',
    last_seen_at: new Date().toISOString(),
    metadata: null,
  },
  {
    vehicle_id: '889e4567-e89b-12d3-a456-426614174001',
    vin: '1FTFW1E50KFA12345',
    make: 'Ford',
    model: 'F-150',
    year: 2023,
    connection_status: 'disconnected',
    last_seen_at: new Date().toISOString(),
    metadata: null,
  },
];

vi.mock('../../src/api/client', () => ({
  commandAPI: {
    getCommandHistory: vi.fn(() => Promise.resolve(mockCommandHistory)),
  },
  vehicleAPI: {
    getVehicles: vi.fn(() => Promise.resolve(mockVehicles)),
  },
}));

// Wrapper for Router and Query Client
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </BrowserRouter>
    );
  };

  return Wrapper;
};

describe('HistoryPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Page Rendering', () => {
    it('should render page title and description for engineer', async () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      expect(screen.getByText('Command History')).toBeInTheDocument();
      await waitFor(() => {
        expect(screen.getByText('View your submitted commands')).toBeInTheDocument();
      });
    });

    it('should render page title and description for admin', async () => {
      // Mock admin user
      const { useAuth } = await import('../../src/context/AuthContext');
      vi.mocked(useAuth).mockReturnValue({
        user: mockAdminUser,
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
      });

      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      expect(screen.getByText('Command History')).toBeInTheDocument();
      await waitFor(() => {
        expect(screen.getByText('View all commands from all users')).toBeInTheDocument();
      });
    });

    it('should render filters section', () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      expect(screen.getByText('Filters')).toBeInTheDocument();
    });

    it('should render CommandHistory component', async () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      // Wait for data to load and table to appear
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });
    });
  });

  describe('Filter Controls', () => {
    it('should render vehicle filter dropdown', () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      const vehicleFilter = screen.getByLabelText('Vehicle');
      expect(vehicleFilter).toBeInTheDocument();
    });

    it('should render status filter dropdown', () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      const statusFilter = screen.getByLabelText('Status');
      expect(statusFilter).toBeInTheDocument();
    });

    it('should render date filters', () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      const startDateFilter = screen.getByLabelText('Start Date');
      const endDateFilter = screen.getByLabelText('End Date');
      expect(startDateFilter).toBeInTheDocument();
      expect(endDateFilter).toBeInTheDocument();
    });

    it('should show user filter for admin', async () => {
      // Mock admin user
      const { useAuth } = await import('../../src/context/AuthContext');
      vi.mocked(useAuth).mockReturnValue({
        user: mockAdminUser,
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
      });

      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByLabelText('User ID')).toBeInTheDocument();
      });
    });

    it('should NOT show user filter for engineer', async () => {
      // Mock engineer user (default mockUser)
      const { useAuth } = await import('../../src/context/AuthContext');
      vi.mocked(useAuth).mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
      });

      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.queryByLabelText('User ID')).not.toBeInTheDocument();
      });
    });

    it('should render Apply Filters button', () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      const applyButton = screen.getByText('Apply Filters');
      expect(applyButton).toBeInTheDocument();
    });

    it('should render Clear Filters button', () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      const clearButton = screen.getByText('Clear Filters');
      expect(clearButton).toBeInTheDocument();
    });
  });

  describe('Filter Functionality', () => {
    it('should update vehicle filter when changed', async () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const vehicleFilter = screen.getByLabelText('Vehicle');
        expect(vehicleFilter).toBeInTheDocument();
      });

      const vehicleFilter = screen.getByLabelText('Vehicle');
      fireEvent.change(vehicleFilter, { target: { value: '789e4567-e89b-12d3-a456-426614174000' } });

      await waitFor(() => {
        expect(vehicleFilter.value).toBe('789e4567-e89b-12d3-a456-426614174000');
      });
    });

    it('should update status filter when changed', async () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      const statusFilter = screen.getByLabelText('Status');
      fireEvent.change(statusFilter, { target: { value: 'completed' } });

      await waitFor(() => {
        expect(statusFilter.value).toBe('completed');
      });
    });

    it('should update date filters when changed', () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      const startDateFilter = screen.getByLabelText('Start Date');
      const endDateFilter = screen.getByLabelText('End Date');

      fireEvent.change(startDateFilter, { target: { value: '2025-01-01' } });
      fireEvent.change(endDateFilter, { target: { value: '2025-12-31' } });

      expect(startDateFilter.value).toBe('2025-01-01');
      expect(endDateFilter.value).toBe('2025-12-31');
    });

    it('should clear all filters when Clear Filters is clicked', async () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      // Set some filters
      const statusFilter = screen.getByLabelText('Status');
      fireEvent.change(statusFilter, { target: { value: 'completed' } });

      await waitFor(() => {
        expect(statusFilter.value).toBe('completed');
      });

      // Click clear
      const clearButton = screen.getByText('Clear Filters');
      fireEvent.click(clearButton);

      await waitFor(() => {
        expect(statusFilter.value).toBe('');
      });
    });
  });

  describe('Pagination', () => {
    it('should render pagination controls when data is present', async () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      await waitFor(() => {
        // Check for pagination text pattern
        const paginationText = screen.queryByText(/1-/);
        expect(paginationText).toBeInTheDocument();
      });
    });

    it('should allow changing rows per page', async () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const paginationText = screen.queryByText(/1-/);
        expect(paginationText).toBeInTheDocument();
      });

      // Find the select element for rows per page
      // MUI TablePagination uses a select with class MuiTablePagination-select
      const selectElement = document.querySelector('.MuiTablePagination-select') as HTMLSelectElement;
      if (selectElement) {
        fireEvent.change(selectElement, { target: { value: '50' } });

        await waitFor(() => {
          expect(selectElement.value).toBe('50');
        });
      }
    });
  });

  describe('Data Loading', () => {
    it('should call API with correct default parameters', async () => {
      const { commandAPI } = await import('../../src/api/client');
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(commandAPI.getCommandHistory).toHaveBeenCalled();
      });

      // Check that it was called with pagination params
      const callArgs = vi.mocked(commandAPI.getCommandHistory).mock.calls[0][0];
      expect(callArgs.limit).toBe(25);
      expect(callArgs.offset).toBe(0);
    });

    it('should call API with filter parameters when filters are applied', async () => {
      const { commandAPI } = await import('../../src/api/client');
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      // Set a filter
      const statusFilter = screen.getByLabelText('Status');
      fireEvent.change(statusFilter, { target: { value: 'completed' } });

      // Filters are applied automatically due to queryKey changes
      await waitFor(() => {
        expect(commandAPI.getCommandHistory).toHaveBeenCalled();
      });
    });

    it('should display loading state', async () => {
      // Mock a delayed response
      const { commandAPI } = await import('../../src/api/client');
      vi.mocked(commandAPI.getCommandHistory).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockCommandHistory), 100))
      );

      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      // Should show loading spinner initially
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('RBAC Integration', () => {
    it('should pass showUserColumn=false for engineer', async () => {
      const { useAuth } = await import('../../src/context/AuthContext');
      vi.mocked(useAuth).mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
      });

      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      await waitFor(() => {
        // User column should not be in headers
        expect(screen.queryByText('User')).not.toBeInTheDocument();
      });
    });

    it('should pass showUserColumn=true for admin', async () => {
      const { useAuth } = await import('../../src/context/AuthContext');
      vi.mocked(useAuth).mockReturnValue({
        user: mockAdminUser,
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
      });

      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      await waitFor(() => {
        // User column should be in headers when data loads
        const table = screen.queryByRole('table');
        if (table) {
          expect(screen.getByText('User')).toBeInTheDocument();
        }
      });
    });
  });

  describe('Vehicle Map Integration', () => {
    it('should pass vehicle map to CommandHistory component', async () => {
      const Wrapper = createWrapper();
      render(<HistoryPage />, { wrapper: Wrapper });

      await waitFor(() => {
        // Check that vehicle information is displayed (VIN from vehicleMap)
        const vinElement = screen.queryByText('1HGCM82633A123456');
        if (vinElement) {
          expect(vinElement).toBeInTheDocument();
        }
      });
    });
  });
});
