/**
 * LoadingSpinner Component Tests
 *
 * Tests for reusable loading spinner component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../../src/components/common/LoadingSpinner';

describe('LoadingSpinner Component', () => {
  describe('Rendering', () => {
    it('renders loading spinner with default props', () => {
      render(<LoadingSpinner />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders with custom message', () => {
      render(<LoadingSpinner message="Fetching vehicles..." />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.getByText('Fetching vehicles...')).toBeInTheDocument();
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    it('renders with custom size', () => {
      const { container } = render(<LoadingSpinner size={60} />);

      const progressbar = container.querySelector('.MuiCircularProgress-root');
      expect(progressbar).toBeInTheDocument();
    });

    it('renders without message when message is empty string', () => {
      render(<LoadingSpinner message="" />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });

    it('renders with both custom size and message', () => {
      render(<LoadingSpinner size={80} message="Processing request..." />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.getByText('Processing request...')).toBeInTheDocument();
    });
  });

  describe('Different Loading Messages', () => {
    it('renders with vehicle-specific loading message', () => {
      render(<LoadingSpinner message="Loading vehicle details..." />);

      expect(screen.getByText('Loading vehicle details...')).toBeInTheDocument();
    });

    it('renders with command-specific loading message', () => {
      render(<LoadingSpinner message="Sending command..." />);

      expect(screen.getByText('Sending command...')).toBeInTheDocument();
    });

    it('renders with data-specific loading message', () => {
      render(<LoadingSpinner message="Fetching data..." />);

      expect(screen.getByText('Fetching data...')).toBeInTheDocument();
    });
  });
});
