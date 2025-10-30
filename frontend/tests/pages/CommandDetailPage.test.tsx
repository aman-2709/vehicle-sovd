/**
 * CommandDetailPage Component Tests
 *
 * Tests for the command detail page including loading, error, and data display.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CommandDetailPage from '../../src/pages/CommandDetailPage';

// Mock command data
const mockCommand = {
  command_id: '123e4567-e89b-12d3-a456-426614174000',
  user_id: 'user-123',
  vehicle_id: '789e4567-e89b-12d3-a456-426614174000',
  command_name: 'lockDoors',
  command_params: { duration: 3600, force: true },
  status: 'completed',
  error_message: null,
  submitted_at: new Date(Date.now() - 120000).toISOString(),
  completed_at: new Date(Date.now() - 60000).toISOString(),
};

const mockFailedCommand = {
  ...mockCommand,
  command_id: '223e4567-e89b-12d3-a456-426614174001',
  status: 'failed',
  error_message: 'Vehicle not responding',
};

const mockVehicle = {
  vehicle_id: '789e4567-e89b-12d3-a456-426614174000',
  vin: '1HGCM82633A123456',
  make: 'Honda',
  model: 'Accord',
  year: 2024,
  connection_status: 'connected',
  last_seen_at: new Date().toISOString(),
  metadata: null,
};

// Mock the API client
vi.mock('../../src/api/client', () => ({
  commandAPI: {
    getCommand: vi.fn(() => Promise.resolve(mockCommand)),
    getCommandResponses: vi.fn(() => Promise.resolve({ responses: [] })),
  },
  vehicleAPI: {
    getVehicle: vi.fn(() => Promise.resolve(mockVehicle)),
  },
}));

// Mock ResponseViewer component
vi.mock('../../src/components/commands/ResponseViewer', () => ({
  default: ({ commandId }: { commandId: string }) => (
    <div data-testid="response-viewer">Response Viewer for {commandId}</div>
  ),
}));

// Wrapper for Router and Query Client
const createWrapper = (initialPath = '/commands/123e4567-e89b-12d3-a456-426614174000') => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const Wrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return (
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <Routes>
            <Route path="/commands/:commandId" element={children} />
            <Route path="/history" element={<div>History Page</div>} />
          </Routes>
        </QueryClientProvider>
      </BrowserRouter>
    );
  };

  // Navigate to initial path
  window.history.pushState({}, '', initialPath);

  return Wrapper;
};

describe('CommandDetailPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should display loading spinner while fetching data', async () => {
      // Mock a delayed response
      const { commandAPI } = await import('../../src/api/client');
      vi.mocked(commandAPI.getCommand).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockCommand), 100))
      );

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error message when command fetch fails', async () => {
      const { commandAPI } = await import('../../src/api/client');
      vi.mocked(commandAPI.getCommand).mockRejectedValue(new Error('Network error'));

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText(/Error loading command details/i)).toBeInTheDocument();
        expect(screen.getByText(/Network error/i)).toBeInTheDocument();
      });
    });

    it('should show Back to History button on error', async () => {
      const { commandAPI } = await import('../../src/api/client');
      vi.mocked(commandAPI.getCommand).mockRejectedValue(new Error('Network error'));

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('Back to History')).toBeInTheDocument();
      });
    });

    it('should display warning when command is not found', async () => {
      const { commandAPI } = await import('../../src/api/client');
      // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-argument
      vi.mocked(commandAPI.getCommand).mockResolvedValue(null as any);

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('Command not found')).toBeInTheDocument();
      });
    });
  });

  describe('Page Rendering', () => {
    it('should render page title and description', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('Command Details')).toBeInTheDocument();
        expect(
          screen.getByText('View detailed information about this command and its responses')
        ).toBeInTheDocument();
      });
    });

    it('should render Back to History button', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const backButtons = screen.getAllByText('Back to History');
        expect(backButtons.length).toBeGreaterThan(0);
      });
    });

    it('should render Overview section', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });
    });

    it('should render Response Data section', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('Response Data')).toBeInTheDocument();
      });
    });
  });

  describe('Command Data Display', () => {
    it('should display command ID', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText(mockCommand.command_id)).toBeInTheDocument();
      });
    });

    it('should display command name', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('lockDoors')).toBeInTheDocument();
      });
    });

    it('should display command status chip', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const statusChip = screen.getByText('completed');
        expect(statusChip).toBeInTheDocument();
        expect(statusChip.closest('.MuiChip-root')).toHaveClass('MuiChip-colorSuccess');
      });
    });

    it('should display vehicle information when available', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('1HGCM82633A123456')).toBeInTheDocument();
        expect(screen.getByText(/Honda Accord \(2024\)/i)).toBeInTheDocument();
      });
    });

    it('should display vehicle ID when vehicle details are not available', async () => {
      const { vehicleAPI } = await import('../../src/api/client');
      vi.mocked(vehicleAPI.getVehicle).mockRejectedValue(new Error('Not found'));

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText(mockCommand.vehicle_id)).toBeInTheDocument();
      });
    });

    it('should display submitted at timestamp', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        // Check for relative time
        const relativeTimes = screen.getAllByText(/minutes ago|Just now/i);
        expect(relativeTimes.length).toBeGreaterThan(0);
      });
    });

    it('should display completed at timestamp when present', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('Completed At')).toBeInTheDocument();
      });
    });

    it('should display error message when present', async () => {
      const { commandAPI } = await import('../../src/api/client');
      vi.mocked(commandAPI.getCommand).mockResolvedValue(mockFailedCommand);

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('Error Message')).toBeInTheDocument();
        expect(screen.getByText('Vehicle not responding')).toBeInTheDocument();
      });
    });

    it('should not display error message section when error_message is null', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.queryByText('Error Message')).not.toBeInTheDocument();
      });
    });
  });

  describe('Command Parameters Display', () => {
    it('should display command parameters section when params exist', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByText('Command Parameters')).toBeInTheDocument();
      });
    });

    it('should display formatted JSON parameters', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const paramsText = screen.getByText(/duration.*3600/i);
        expect(paramsText).toBeInTheDocument();
      });
    });

    it('should not display parameters section when params are empty', async () => {
      const { commandAPI } = await import('../../src/api/client');
      vi.mocked(commandAPI.getCommand).mockResolvedValue({
        ...mockCommand,
        command_params: {},
      });

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.queryByText('Command Parameters')).not.toBeInTheDocument();
      });
    });
  });

  describe('ResponseViewer Integration', () => {
    it('should render ResponseViewer component', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(screen.getByTestId('response-viewer')).toBeInTheDocument();
      });
    });

    it('should pass correct command ID to ResponseViewer', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const responseViewer = screen.getByTestId('response-viewer');
        expect(responseViewer).toHaveTextContent(mockCommand.command_id);
      });
    });
  });

  describe('Navigation', () => {
    it('should navigate to history page when Back to History is clicked', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const backButtons = screen.getAllByText('Back to History');
        expect(backButtons[0]).toBeInTheDocument();
      });

      const backButton = screen.getAllByText('Back to History')[0];
      fireEvent.click(backButton);

      await waitFor(() => {
        expect(window.location.pathname).toBe('/history');
      });
    });
  });

  describe('Status Chip Colors', () => {
    it('should display success color for completed status', async () => {
      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const statusChip = screen.getByText('completed').closest('.MuiChip-root');
        expect(statusChip).toHaveClass('MuiChip-colorSuccess');
      });
    });

    it('should display error color for failed status', async () => {
      const { commandAPI } = await import('../../src/api/client');
      vi.mocked(commandAPI.getCommand).mockResolvedValue(mockFailedCommand);

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const statusChip = screen.getByText('failed').closest('.MuiChip-root');
        expect(statusChip).toHaveClass('MuiChip-colorError');
      });
    });

    it('should display primary color for in_progress status', async () => {
      const { commandAPI } = await import('../../src/api/client');
      vi.mocked(commandAPI.getCommand).mockResolvedValue({
        ...mockCommand,
        status: 'in_progress',
        completed_at: null,
      });

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const statusChip = screen.getByText('in_progress').closest('.MuiChip-root');
        expect(statusChip).toHaveClass('MuiChip-colorPrimary');
      });
    });

    it('should display warning color for pending status', async () => {
      const { commandAPI } = await import('../../src/api/client');
      vi.mocked(commandAPI.getCommand).mockResolvedValue({
        ...mockCommand,
        status: 'pending',
        completed_at: null,
      });

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        const statusChip = screen.getByText('pending').closest('.MuiChip-root');
        expect(statusChip).toHaveClass('MuiChip-colorWarning');
      });
    });
  });

  describe('Auto-refresh', () => {
    it('should enable query for command when commandId is present', async () => {
      const { commandAPI } = await import('../../src/api/client');

      const Wrapper = createWrapper();
      render(<CommandDetailPage />, { wrapper: Wrapper });

      await waitFor(() => {
        expect(commandAPI.getCommand).toHaveBeenCalled();
      });
    });
  });
});
