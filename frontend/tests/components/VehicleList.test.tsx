/**
 * VehicleList Component Tests
 *
 * Tests for vehicle list display, loading states, error states, and empty states.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import VehicleList from '../../src/components/vehicles/VehicleList';
import type { VehicleResponse } from '../../src/types/vehicle';

// Mock vehicle data
const mockVehicles: VehicleResponse[] = [
  {
    vehicle_id: '123e4567-e89b-12d3-a456-426614174000',
    vin: '1HGCM82633A123456',
    make: 'Honda',
    model: 'Accord',
    year: 2024,
    connection_status: 'connected',
    last_seen_at: new Date(Date.now() - 120000).toISOString(), // 2 minutes ago
    metadata: null,
  },
  {
    vehicle_id: '223e4567-e89b-12d3-a456-426614174001',
    vin: '1FTFW1E50KFA12345',
    make: 'Ford',
    model: 'F-150',
    year: 2023,
    connection_status: 'disconnected',
    last_seen_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
    metadata: null,
  },
  {
    vehicle_id: '323e4567-e89b-12d3-a456-426614174002',
    vin: '5YJSA1E14HF123456',
    make: 'Tesla',
    model: 'Model S',
    year: 2022,
    connection_status: 'error',
    last_seen_at: null,
    metadata: null,
  },
];

describe('VehicleList Component', () => {
  describe('Loading State', () => {
    it('should display loading spinner when isLoading is true', () => {
      render(<VehicleList vehicles={[]} isLoading={true} error={null} />);

      const spinner = screen.getByRole('progressbar');
      expect(spinner).toBeInTheDocument();
    });

    it('should not display table when loading', () => {
      render(<VehicleList vehicles={[]} isLoading={true} error={null} />);

      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error message when error is present', () => {
      const error = new Error('Network error');
      render(<VehicleList vehicles={[]} isLoading={false} error={error} />);

      expect(screen.getByText(/Failed to load vehicles/i)).toBeInTheDocument();
      expect(screen.getByText(/Please try again/i)).toBeInTheDocument();
    });

    it('should not display table when error occurs', () => {
      const error = new Error('Network error');
      render(<VehicleList vehicles={[]} isLoading={false} error={error} />);

      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no vehicles and not filtered', () => {
      render(
        <VehicleList
          vehicles={[]}
          isLoading={false}
          error={null}
          isFiltered={false}
        />
      );

      expect(screen.getByText(/No vehicles found/i)).toBeInTheDocument();
      expect(screen.getByText(/No vehicles available/i)).toBeInTheDocument();
    });

    it('should display filtered empty state when no vehicles and filtered', () => {
      render(
        <VehicleList
          vehicles={[]}
          isLoading={false}
          error={null}
          isFiltered={true}
        />
      );

      expect(screen.getByText(/No vehicles found/i)).toBeInTheDocument();
      expect(screen.getByText(/Try adjusting your filters/i)).toBeInTheDocument();
    });

    it('should not display table when no vehicles', () => {
      render(<VehicleList vehicles={[]} isLoading={false} error={null} />);

      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });
  });

  describe('Vehicle List Display', () => {
    it('should render vehicle list table with headers', () => {
      render(
        <VehicleList vehicles={mockVehicles} isLoading={false} error={null} />
      );

      // Check table headers
      expect(screen.getByText('VIN')).toBeInTheDocument();
      expect(screen.getByText('Make')).toBeInTheDocument();
      expect(screen.getByText('Model')).toBeInTheDocument();
      expect(screen.getByText('Year')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Last Seen')).toBeInTheDocument();
    });

    it('should display all vehicle data correctly', () => {
      render(
        <VehicleList vehicles={mockVehicles} isLoading={false} error={null} />
      );

      // Check first vehicle data
      expect(screen.getByText('1HGCM82633A123456')).toBeInTheDocument();
      expect(screen.getByText('Honda')).toBeInTheDocument();
      expect(screen.getByText('Accord')).toBeInTheDocument();
      expect(screen.getByText('2024')).toBeInTheDocument();

      // Check second vehicle data
      expect(screen.getByText('1FTFW1E50KFA12345')).toBeInTheDocument();
      expect(screen.getByText('Ford')).toBeInTheDocument();
      expect(screen.getByText('F-150')).toBeInTheDocument();
      expect(screen.getByText('2023')).toBeInTheDocument();

      // Check third vehicle data
      expect(screen.getByText('5YJSA1E14HF123456')).toBeInTheDocument();
      expect(screen.getByText('Tesla')).toBeInTheDocument();
      expect(screen.getByText('Model S')).toBeInTheDocument();
      expect(screen.getByText('2022')).toBeInTheDocument();
    });

    it('should display connection status chips with correct labels', () => {
      render(
        <VehicleList vehicles={mockVehicles} isLoading={false} error={null} />
      );

      expect(screen.getByText('connected')).toBeInTheDocument();
      expect(screen.getByText('disconnected')).toBeInTheDocument();
      expect(screen.getByText('error')).toBeInTheDocument();
    });

    it('should display relative time for last_seen_at', () => {
      render(
        <VehicleList vehicles={mockVehicles} isLoading={false} error={null} />
      );

      // Check that relative times are displayed (specific text may vary based on current time)
      const relativeTimes = screen.getAllByText(/minutes ago|hour ago|Just now/i);
      expect(relativeTimes.length).toBeGreaterThan(0);
    });

    it('should display "Never" for null last_seen_at', () => {
      render(
        <VehicleList vehicles={mockVehicles} isLoading={false} error={null} />
      );

      expect(screen.getByText('Never')).toBeInTheDocument();
    });

    it('should render correct number of vehicle rows', () => {
      render(
        <VehicleList vehicles={mockVehicles} isLoading={false} error={null} />
      );

      const rows = screen.getAllByRole('row');
      // +1 for header row
      expect(rows).toHaveLength(mockVehicles.length + 1);
    });
  });

  describe('Vehicle Filtering', () => {
    it('should only display filtered vehicles when provided', () => {
      const filteredVehicles = [mockVehicles[0]]; // Only Honda
      render(
        <VehicleList
          vehicles={filteredVehicles}
          isLoading={false}
          error={null}
        />
      );

      expect(screen.getByText('Honda')).toBeInTheDocument();
      expect(screen.queryByText('Ford')).not.toBeInTheDocument();
      expect(screen.queryByText('Tesla')).not.toBeInTheDocument();
    });

    it('should handle empty filtered results', () => {
      render(
        <VehicleList
          vehicles={[]}
          isLoading={false}
          error={null}
          isFiltered={true}
        />
      );

      expect(screen.getByText(/Try adjusting your filters/i)).toBeInTheDocument();
    });
  });
});
