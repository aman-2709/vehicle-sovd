/**
 * OfflineBanner Component Tests
 *
 * Tests for offline detection banner display and online/offline state transitions.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import OfflineBanner from '../../src/components/common/OfflineBanner';

describe('OfflineBanner Component', () => {
  let onlineGetter: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Mock navigator.onLine
    onlineGetter = vi.fn(() => true);
    Object.defineProperty(navigator, 'onLine', {
      configurable: true,
      get: onlineGetter,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('does not display banner when online', () => {
    onlineGetter.mockReturnValue(true);

    render(<OfflineBanner />);

    // Banner should not be visible
    expect(screen.queryByTestId('offline-banner')).not.toBeVisible();
  });

  it('displays banner when offline', () => {
    onlineGetter.mockReturnValue(false);

    render(<OfflineBanner />);

    // Banner should be visible
    const banner = screen.getByTestId('offline-banner');
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent(
      /You are currently offline.*Some features may be unavailable/i
    );
  });

  it('shows banner when going offline', async () => {
    onlineGetter.mockReturnValue(true);

    render(<OfflineBanner />);

    // Initially online, banner not visible
    expect(screen.queryByTestId('offline-banner')).not.toBeVisible();

    // Simulate going offline
    onlineGetter.mockReturnValue(false);
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });

    // Banner should now be visible
    await waitFor(() => {
      expect(screen.getByTestId('offline-banner')).toBeVisible();
    });
  });

  it('hides banner when coming back online', async () => {
    onlineGetter.mockReturnValue(false);

    render(<OfflineBanner />);

    // Initially offline, banner visible
    expect(screen.getByTestId('offline-banner')).toBeVisible();

    // Simulate coming back online
    onlineGetter.mockReturnValue(true);
    act(() => {
      window.dispatchEvent(new Event('online'));
    });

    // Banner should be hidden
    await waitFor(() => {
      expect(screen.queryByTestId('offline-banner')).not.toBeVisible();
    });
  });

  it('displays warning icon', () => {
    onlineGetter.mockReturnValue(false);

    render(<OfflineBanner />);

    // Check for WiFi off icon
    const icon = document.querySelector('[data-testid="WifiOffIcon"]');
    expect(icon).toBeInTheDocument();
  });

  it('has warning severity styling', () => {
    onlineGetter.mockReturnValue(false);

    render(<OfflineBanner />);

    const banner = screen.getByTestId('offline-banner');
    // MUI Alert with warning severity has specific classes
    expect(banner.className).toContain('MuiAlert-standardWarning');
  });

  it('is non-dismissible (no close button)', () => {
    onlineGetter.mockReturnValue(false);

    render(<OfflineBanner />);

    // Should not have a close button
    const closeButton = screen.queryByLabelText('close');
    expect(closeButton).not.toBeInTheDocument();
  });

  it('is sticky at the top of the page', () => {
    onlineGetter.mockReturnValue(false);

    render(<OfflineBanner />);

    const banner = screen.getByTestId('offline-banner');
    // Check for sticky positioning
    expect(banner).toHaveStyle({ position: 'sticky' });
  });

  it('handles multiple online/offline transitions', async () => {
    onlineGetter.mockReturnValue(true);

    render(<OfflineBanner />);

    // Initially online
    expect(screen.queryByTestId('offline-banner')).not.toBeVisible();

    // Go offline
    onlineGetter.mockReturnValue(false);
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('offline-banner')).toBeVisible();
    });

    // Go back online
    onlineGetter.mockReturnValue(true);
    act(() => {
      window.dispatchEvent(new Event('online'));
    });

    await waitFor(() => {
      expect(screen.queryByTestId('offline-banner')).not.toBeVisible();
    });

    // Go offline again
    onlineGetter.mockReturnValue(false);
    act(() => {
      window.dispatchEvent(new Event('offline'));
    });

    await waitFor(() => {
      expect(screen.getByTestId('offline-banner')).toBeVisible();
    });
  });
});
