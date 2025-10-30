/**
 * CommandHistory Component Tests
 *
 * Tests for command history display, loading states, error states, and empty states.
 */

import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import CommandHistory from '../../src/components/commands/CommandHistory';
import type { CommandResponse } from '../../src/types/command';

// Wrapper for Router context
const RouterWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <BrowserRouter>{children}</BrowserRouter>;
};

// Mock command data
const mockCommands: CommandResponse[] = [
  {
    command_id: '123e4567-e89b-12d3-a456-426614174000',
    user_id: '456e4567-e89b-12d3-a456-426614174000',
    vehicle_id: '789e4567-e89b-12d3-a456-426614174000',
    command_name: 'lockDoors',
    command_params: { duration: 3600 },
    status: 'completed',
    error_message: null,
    submitted_at: new Date(Date.now() - 120000).toISOString(), // 2 minutes ago
    completed_at: new Date(Date.now() - 60000).toISOString(),
  },
  {
    command_id: '223e4567-e89b-12d3-a456-426614174001',
    user_id: '556e4567-e89b-12d3-a456-426614174001',
    vehicle_id: '889e4567-e89b-12d3-a456-426614174001',
    command_name: 'startEngine',
    command_params: { warm_up: true },
    status: 'failed',
    error_message: 'Vehicle not responding',
    submitted_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    completed_at: new Date(Date.now() - 3590000).toISOString(),
  },
  {
    command_id: '323e4567-e89b-12d3-a456-426614174002',
    user_id: '656e4567-e89b-12d3-a456-426614174002',
    vehicle_id: '989e4567-e89b-12d3-a456-426614174002',
    command_name: 'getStatus',
    command_params: {},
    status: 'in_progress',
    error_message: null,
    submitted_at: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
    completed_at: null,
  },
  {
    command_id: '423e4567-e89b-12d3-a456-426614174003',
    user_id: '756e4567-e89b-12d3-a456-426614174003',
    vehicle_id: 'a89e4567-e89b-12d3-a456-426614174003',
    command_name: 'unlockDoors',
    command_params: {},
    status: 'pending',
    error_message: null,
    submitted_at: new Date(Date.now() - 30000).toISOString(), // 30 seconds ago
    completed_at: null,
  },
];

// Mock vehicle map
const mockVehicleMap = new Map([
  [
    '789e4567-e89b-12d3-a456-426614174000',
    { vin: '1HGCM82633A123456', make: 'Honda', model: 'Accord' },
  ],
  [
    '889e4567-e89b-12d3-a456-426614174001',
    { vin: '1FTFW1E50KFA12345', make: 'Ford', model: 'F-150' },
  ],
]);

// Mock user map
const mockUserMap = new Map([
  ['456e4567-e89b-12d3-a456-426614174000', 'engineer1'],
  ['556e4567-e89b-12d3-a456-426614174001', 'engineer2'],
]);

describe('CommandHistory Component', () => {
  describe('Loading State', () => {
    it('should display loading spinner when isLoading is true', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={[]} isLoading={true} error={null} />
        </RouterWrapper>
      );

      const spinner = screen.getByRole('progressbar');
      expect(spinner).toBeInTheDocument();
    });

    it('should not display table when loading', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={[]} isLoading={true} error={null} />
        </RouterWrapper>
      );

      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error message when error is present', () => {
      const error = new Error('Network error');
      render(
        <RouterWrapper>
          <CommandHistory commands={[]} isLoading={false} error={error} />
        </RouterWrapper>
      );

      expect(screen.getByText(/Error loading command history/i)).toBeInTheDocument();
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });

    it('should not display table when error occurs', () => {
      const error = new Error('Network error');
      render(
        <RouterWrapper>
          <CommandHistory commands={[]} isLoading={false} error={error} />
        </RouterWrapper>
      );

      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no commands', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={[]} isLoading={false} error={null} />
        </RouterWrapper>
      );

      expect(screen.getByText(/No commands found/i)).toBeInTheDocument();
    });

    it('should not display table when no commands', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={[]} isLoading={false} error={null} />
        </RouterWrapper>
      );

      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });
  });

  describe('Command List Display', () => {
    it('should render command list table with headers', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      // Check table headers (without User column by default)
      expect(screen.getByText('Command Name')).toBeInTheDocument();
      expect(screen.getByText('Vehicle (VIN)')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Submitted At')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('should include User column when showUserColumn is true', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} showUserColumn={true} />
        </RouterWrapper>
      );

      expect(screen.getByText('User')).toBeInTheDocument();
    });

    it('should not include User column when showUserColumn is false', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} showUserColumn={false} />
        </RouterWrapper>
      );

      expect(screen.queryByText('User')).not.toBeInTheDocument();
    });

    it('should display all command names correctly', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      expect(screen.getByText('lockDoors')).toBeInTheDocument();
      expect(screen.getByText('startEngine')).toBeInTheDocument();
      expect(screen.getByText('getStatus')).toBeInTheDocument();
      expect(screen.getByText('unlockDoors')).toBeInTheDocument();
    });

    it('should display vehicle information when vehicleMap is provided', () => {
      render(
        <RouterWrapper>
          <CommandHistory
            commands={mockCommands}
            isLoading={false}
            error={null}
            vehicleMap={mockVehicleMap}
          />
        </RouterWrapper>
      );

      expect(screen.getByText('1HGCM82633A123456')).toBeInTheDocument();
      expect(screen.getByText('Honda Accord')).toBeInTheDocument();
      expect(screen.getByText('1FTFW1E50KFA12345')).toBeInTheDocument();
      expect(screen.getByText('Ford F-150')).toBeInTheDocument();
    });

    it('should display vehicle ID substring when vehicleMap is not provided', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      // Check that truncated IDs are shown (first 8 chars + "...")
      const vehicleIdCells = screen.getAllByText(/[a-f0-9]{8}\.\.\./i);
      expect(vehicleIdCells.length).toBeGreaterThan(0);
    });

    it('should display username when userMap is provided and showUserColumn is true', () => {
      render(
        <RouterWrapper>
          <CommandHistory
            commands={mockCommands}
            isLoading={false}
            error={null}
            showUserColumn={true}
            userMap={mockUserMap}
          />
        </RouterWrapper>
      );

      expect(screen.getByText('engineer1')).toBeInTheDocument();
      expect(screen.getByText('engineer2')).toBeInTheDocument();
    });

    it('should display user ID substring when userMap is not provided and showUserColumn is true', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} showUserColumn={true} />
        </RouterWrapper>
      );

      // Check that truncated user IDs are shown (first 8 chars + "...")
      const userIdCells = screen.getAllByText(/[a-f0-9]{8}\.\.\./i);
      expect(userIdCells.length).toBeGreaterThan(0);
    });

    it('should render correct number of command rows', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      const rows = screen.getAllByRole('row');
      // +1 for header row
      expect(rows).toHaveLength(mockCommands.length + 1);
    });
  });

  describe('Status Chips', () => {
    it('should display status chips with correct labels', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('failed')).toBeInTheDocument();
      expect(screen.getByText('in_progress')).toBeInTheDocument();
      expect(screen.getByText('pending')).toBeInTheDocument();
    });

    it('should apply correct color classes to status chips', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      const completedChip = screen.getByText('completed').closest('.MuiChip-root');
      const failedChip = screen.getByText('failed').closest('.MuiChip-root');
      const inProgressChip = screen.getByText('in_progress').closest('.MuiChip-root');
      const pendingChip = screen.getByText('pending').closest('.MuiChip-root');

      expect(completedChip).toHaveClass('MuiChip-colorSuccess');
      expect(failedChip).toHaveClass('MuiChip-colorError');
      expect(inProgressChip).toHaveClass('MuiChip-colorPrimary');
      expect(pendingChip).toHaveClass('MuiChip-colorWarning');
    });
  });

  describe('Actions', () => {
    it('should display View Details button for each command', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      const viewButtons = screen.getAllByText('View Details');
      expect(viewButtons).toHaveLength(mockCommands.length);
    });

    it('should navigate to command detail page when View Details is clicked', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      const viewButtons = screen.getAllByText('View Details');
      fireEvent.click(viewButtons[0]);

      // Check that the URL contains the command ID
      expect(window.location.pathname).toContain('/commands/');
    });
  });

  describe('Timestamp Display', () => {
    it('should display relative time for submitted_at', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      // Check that relative times are displayed
      const relativeTimes = screen.getAllByText(
        /minutes ago|hour ago|seconds ago|Just now/i
      );
      expect(relativeTimes.length).toBeGreaterThan(0);
    });

    it('should display absolute time in locale format', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={mockCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      // Check that absolute times are displayed (locale format will vary)
      // Just verify that date/time strings exist
      const timestamps = screen.getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}|AM|PM/i);
      expect(timestamps.length).toBeGreaterThan(0);
    });
  });

  describe('Filtering', () => {
    it('should only display filtered commands when provided', () => {
      const filteredCommands = [mockCommands[0]]; // Only lockDoors
      render(
        <RouterWrapper>
          <CommandHistory commands={filteredCommands} isLoading={false} error={null} />
        </RouterWrapper>
      );

      expect(screen.getByText('lockDoors')).toBeInTheDocument();
      expect(screen.queryByText('startEngine')).not.toBeInTheDocument();
      expect(screen.queryByText('getStatus')).not.toBeInTheDocument();
      expect(screen.queryByText('unlockDoors')).not.toBeInTheDocument();
    });

    it('should handle empty filtered results', () => {
      render(
        <RouterWrapper>
          <CommandHistory commands={[]} isLoading={false} error={null} />
        </RouterWrapper>
      );

      expect(screen.getByText(/No commands found/i)).toBeInTheDocument();
    });
  });
});
