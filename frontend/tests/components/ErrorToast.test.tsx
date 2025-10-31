/**
 * ErrorToast Component Tests
 *
 * Tests for error toast notification display, stacking, and auto-dismiss behavior.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
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
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('renders no toasts when there are no errors', async () => {
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

    // The toast should contain both the message and the correlation ID
    const toast = screen.getByTestId('toast-error');
    expect(toast).toHaveTextContent('Error with ID');
    expect(toast).toHaveTextContent('test-123');
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
    vi.useFakeTimers();

    const { container } = render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const errorButton = screen.getByText('Trigger Error');

    act(() => {
      fireEvent.click(errorButton);
    });

    // Toast should be visible initially
    expect(screen.getByTestId('toast-error')).toBeInTheDocument();

    // Fast-forward past the auto-dismiss timer (6 seconds) and run all timers
    act(() => {
      vi.runAllTimers();
    });

    // Toast should be removed
    expect(screen.queryByTestId('toast-error')).not.toBeInTheDocument();

    vi.useRealTimers();
  });

  it('auto-dismisses success toast after 4 seconds', async () => {
    vi.useFakeTimers();

    const { container } = render(
      <ErrorProvider>
        <ErrorTrigger />
        <ErrorToast />
      </ErrorProvider>
    );

    const successButton = screen.getByText('Trigger Success');

    act(() => {
      fireEvent.click(successButton);
    });

    // Toast should be visible initially
    expect(screen.getByTestId('toast-success')).toBeInTheDocument();

    // Fast-forward past the auto-dismiss timer (4 seconds) and run all timers
    act(() => {
      vi.runAllTimers();
    });

    // Toast should be removed
    expect(screen.queryByTestId('toast-success')).not.toBeInTheDocument();

    vi.useRealTimers();
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

    fireEvent.click(screen.getByRole('button', { name: 'Error 1' }));
    fireEvent.click(screen.getByRole('button', { name: 'Error 2' }));

    // Both errors should be visible with their respective IDs
    await waitFor(() => {
      const toasts = screen.getAllByTestId('toast-error');
      expect(toasts).toHaveLength(2);
    });

    // Check that both correlation IDs are present
    expect(screen.getByText('id-1')).toBeInTheDocument();
    expect(screen.getByText('id-2')).toBeInTheDocument();
  });
});
