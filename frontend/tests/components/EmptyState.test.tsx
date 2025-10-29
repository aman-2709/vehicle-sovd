/**
 * EmptyState Component Tests
 *
 * Tests for empty state display component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Search as SearchIcon, Warning as WarningIcon } from '@mui/icons-material';
import EmptyState from '../../src/components/common/EmptyState';

describe('EmptyState Component', () => {
  describe('Basic Rendering', () => {
    it('renders with required title prop', () => {
      render(<EmptyState title="No vehicles found" />);

      expect(screen.getByText('No vehicles found')).toBeInTheDocument();
    });

    it('renders with title and message', () => {
      render(
        <EmptyState
          title="No vehicles found"
          message="Try adjusting your search or filters."
        />
      );

      expect(screen.getByText('No vehicles found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search or filters.')).toBeInTheDocument();
    });

    it('renders without message when not provided', () => {
      render(<EmptyState title="No data available" />);

      expect(screen.getByText('No data available')).toBeInTheDocument();
      expect(screen.queryByText('Try adjusting')).not.toBeInTheDocument();
    });

    it('renders with default inbox icon', () => {
      const { container } = render(<EmptyState title="Empty" />);

      const iconElement = container.querySelector('svg');
      expect(iconElement).toBeInTheDocument();
    });
  });

  describe('Custom Icons', () => {
    it('renders with custom search icon', () => {
      render(
        <EmptyState
          icon={<SearchIcon data-testid="search-icon" sx={{ fontSize: 64 }} />}
          title="No results"
          message="No search results found."
        />
      );

      expect(screen.getByTestId('search-icon')).toBeInTheDocument();
      expect(screen.getByText('No results')).toBeInTheDocument();
    });

    it('renders with custom warning icon', () => {
      render(
        <EmptyState
          icon={<WarningIcon data-testid="warning-icon" sx={{ fontSize: 64 }} />}
          title="No commands available"
          message="There are no commands to display."
        />
      );

      expect(screen.getByTestId('warning-icon')).toBeInTheDocument();
      expect(screen.getByText('No commands available')).toBeInTheDocument();
    });
  });

  describe('Different Use Cases', () => {
    it('renders empty vehicle list state', () => {
      render(
        <EmptyState
          title="No vehicles"
          message="No vehicles are currently available. Add a vehicle to get started."
        />
      );

      expect(screen.getByText('No vehicles')).toBeInTheDocument();
      expect(
        screen.getByText('No vehicles are currently available. Add a vehicle to get started.')
      ).toBeInTheDocument();
    });

    it('renders empty command history state', () => {
      render(
        <EmptyState
          title="No command history"
          message="Execute a command to see it in your history."
        />
      );

      expect(screen.getByText('No command history')).toBeInTheDocument();
      expect(screen.getByText('Execute a command to see it in your history.')).toBeInTheDocument();
    });

    it('renders empty search results state', () => {
      render(
        <EmptyState
          title="No matching results"
          message="Try using different search terms or filters."
        />
      );

      expect(screen.getByText('No matching results')).toBeInTheDocument();
      expect(screen.getByText('Try using different search terms or filters.')).toBeInTheDocument();
    });

    it('renders empty response state', () => {
      render(
        <EmptyState
          title="No responses yet"
          message="Responses will appear here once the command is executed."
        />
      );

      expect(screen.getByText('No responses yet')).toBeInTheDocument();
      expect(
        screen.getByText('Responses will appear here once the command is executed.')
      ).toBeInTheDocument();
    });
  });

  describe('Long Text Handling', () => {
    it('renders with long title text', () => {
      const longTitle =
        'This is a very long title that should still be displayed correctly without breaking the layout';

      render(<EmptyState title={longTitle} />);

      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('renders with long message text', () => {
      const longMessage =
        'This is a very long message that provides detailed information about why the state is empty and what the user should do next to see content here.';

      render(<EmptyState title="Empty State" message={longMessage} />);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });
  });
});
