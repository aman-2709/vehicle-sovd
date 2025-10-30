/**
 * ErrorToast Component Tests
 *
 * Tests for error toast notification display, stacking, and auto-dismiss behavior.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { ErrorProvider, useError } from '../../src/context/ErrorContext';
import ErrorToast from '../../src/components/common/ErrorToast';

// Test component to trigger errors
const ErrorTrigger = () => {
  const { showError, showSuccess, showWarning, showInfo, clearToast } = useError();

  return (
    <div>
      <button onClick={() => showError('Test error message')}>Trigger Error</button>
      <button onClick={() => showError('Error with ID', { correlationId: 'test-123' })}>
        Trigger Error with ID
      </button>
      <button onClick={() => showSuccess('Success message')}>Trigger Success</button>
      <button onClick={() => showWarning('Warning message')}>Trigger Warning</button>
      <button onClick={() => showInfo('Info message')}>Trigger Info</button>
      <button onClick={() => clearToast('test-id')}>Clear Toast</button>
    </div>
  );
};

describe('ErrorToast Component', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('renders no toasts when there are no errors', () => {
    render(
      <ErrorProvider>
        <ErrorToast />
      </ErrorProvider>
    );

    // Should not find any toast elements
    expect(screen.queryByTestId('toast-error')).not.toBeInTheDocument();
    expect(screen.queryByTestId('toast-success')).not.toBeInTheDocument();
  });

  it('displays error toast when error is triggered', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const errorButton = screen.getByText('Trigger Error');
    fireEvent.click(errorButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast-error')).toBeInTheDocument();
    });
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('displays error with correlation ID', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const errorButton = screen.getByText('Trigger Error with ID');
    fireEvent.click(errorButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast-error')).toBeInTheDocument();
    });
    expect(screen.getByText(/Error with ID/)).toBeInTheDocument();
    expect(screen.getByText('test-123')).toBeInTheDocument();
  });

  it('displays success toast when success is triggered', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const successButton = screen.getByText('Trigger Success');
    fireEvent.click(successButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast-success')).toBeInTheDocument();
    });
    expect(screen.getByText('Success message')).toBeInTheDocument();
  });

  it('displays warning toast when warning is triggered', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const warningButton = screen.getByText('Trigger Warning');
    fireEvent.click(warningButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast-warning')).toBeInTheDocument();
    });
    expect(screen.getByText('Warning message')).toBeInTheDocument();
  });

  it('displays info toast when info is triggered', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const infoButton = screen.getByText('Trigger Info');
    fireEvent.click(infoButton);

    await waitFor(() => {
      expect(screen.getByTestId('toast-info')).toBeInTheDocument();
    });
    expect(screen.getByText('Info message')).toBeInTheDocument();
  });

  it('stacks multiple toasts vertically', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    // Trigger multiple toasts
    fireEvent.click(screen.getByText('Trigger Error'));
    fireEvent.click(screen.getByText('Trigger Success'));
    fireEvent.click(screen.getByText('Trigger Warning'));

    // All three toasts should be visible
    await waitFor(() => {
      expect(screen.getByTestId('toast-error')).toBeInTheDocument();
      expect(screen.getByTestId('toast-success')).toBeInTheDocument();
      expect(screen.getByTestId('toast-warning')).toBeInTheDocument();
    });
  });

  it('auto-dismisses error toast after 6 seconds', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const errorButton = screen.getByText('Trigger Error');
    fireEvent.click(errorButton);

    // Toast should be visible initially
    await waitFor(() => {
      expect(screen.getByTestId('toast-error')).toBeInTheDocument();
    });

    // Fast-forward 6 seconds
    vi.advanceTimersByTime(6000);

    // Wait for toast to be removed
    await waitFor(() => {
      expect(screen.queryByTestId('toast-error')).not.toBeInTheDocument();
    });
  });

  it('auto-dismisses success toast after 4 seconds', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const successButton = screen.getByText('Trigger Success');
    fireEvent.click(successButton);

    // Toast should be visible initially
    await waitFor(() => {
      expect(screen.getByTestId('toast-success')).toBeInTheDocument();
    });

    // Fast-forward 4 seconds
    vi.advanceTimersByTime(4000);

    // Wait for toast to be removed
    await waitFor(() => {
      expect(screen.queryByTestId('toast-success')).not.toBeInTheDocument();
    });
  });

  it('allows manual dismissal of toast via close button', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const errorButton = screen.getByText('Trigger Error');
    fireEvent.click(errorButton);

    // Toast should be visible
    await waitFor(() => {
      expect(screen.getByTestId('toast-error')).toBeInTheDocument();
    });

    // Find and click the close button
    const closeButton = screen.getByLabelText('close');
    fireEvent.click(closeButton);

    // Toast should be removed
    await waitFor(() => {
      expect(screen.queryByTestId('toast-error')).not.toBeInTheDocument();
    });
  });

  it('displays correlation ID in separate section', async () => {
    render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const errorButton = screen.getByText('Trigger Error with ID');
    fireEvent.click(errorButton);

    // Check that toast appears first
    await waitFor(() => {
      expect(screen.getByTestId('toast-error')).toBeInTheDocument();
    });

    // Check that correlation ID is displayed
    const correlationIdElement = screen.getByText('test-123');
    expect(correlationIdElement).toBeInTheDocument();

    // Check that it's in a monospace font
    expect(correlationIdElement).toHaveStyle({ fontFamily: 'monospace' });
  });

  it('handles multiple simultaneous errors with different correlation IDs', async () => {
    const MultiErrorTrigger = () => {
      const { showError } = useError();

      return (
        <div>
          <button onClick={() => showError('Error 1', { correlationId: 'id-1' })}>
            Error 1
          </button>
          <button onClick={() => showError('Error 2', { correlationId: 'id-2' })}>
            Error 2
          </button>
        </div>
      );
    };

    render(
      <ErrorProvider>
        <MultiErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    fireEvent.click(screen.getByText('Error 1'));
    fireEvent.click(screen.getByText('Error 2'));

    // Both errors should be visible with their respective IDs
    await waitFor(() => {
      expect(screen.getByText('Error 1')).toBeInTheDocument();
      expect(screen.getByText('Error 2')).toBeInTheDocument();
      expect(screen.getByText('id-1')).toBeInTheDocument();
      expect(screen.getByText('id-2')).toBeInTheDocument();
    });
  });
});
