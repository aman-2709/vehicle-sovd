/**
 * ResponseViewer Component Tests
 * Tests WebSocket connection, event handling, and UI updates
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ResponseViewer } from '../../src/components/commands/ResponseViewer';
import type { WebSocketEvent } from '../../src/types/response';

// Mock the WebSocket API
// eslint-disable-next-line @typescript-eslint/no-explicit-any
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  public readyState: number = MockWebSocket.CONNECTING;
  public onopen: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public url: string;

  constructor(url: string) {
    this.url = url;
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(data: string): void {
    // Mock send - no-op
    void data;
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close', { code: code || 1000, reason: reason || '' }));
    }
  }

  // Helper to simulate receiving a message
  simulateMessage(data: WebSocketEvent): void {
    if (this.onmessage) {
      const event = new MessageEvent('message', {
        data: JSON.stringify(data),
      });
      this.onmessage(event);
    }
  }

  // Helper to simulate error
  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Store reference to mock instance for test assertions
let mockWebSocketInstance: MockWebSocket | null = null;

// Mock the client module
vi.mock('../../src/api/client', () => ({
  getAccessToken: vi.fn(() => 'mock-jwt-token'),
}));

// Mock react-json-view
vi.mock('@microlink/react-json-view', () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  default: ({ src }: { src: any }) => (
    <div data-testid="json-viewer">{JSON.stringify(src)}</div>
  ),
}));

describe('ResponseViewer', () => {
  beforeEach(() => {
    // Set up WebSocket mock
    mockWebSocketInstance = null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access
    (global as any).WebSocket = vi.fn((url: string) => {
      mockWebSocketInstance = new MockWebSocket(url);
      return mockWebSocketInstance;
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    mockWebSocketInstance = null;
  });

  it('should render component with connection status', () => {
    render(<ResponseViewer commandId="test-command-123" />);

    // Check for main heading
    expect(screen.getByText('Real-Time Responses')).toBeInTheDocument();
  });

  it('should establish WebSocket connection on mount with JWT token', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-member-access
      expect((global as any).WebSocket).toHaveBeenCalledWith(
        expect.stringContaining('ws://localhost:8000/ws/responses/test-command-123?token=mock-jwt-token')
      );
    });
  });

  it('should display "Connecting..." status initially', () => {
    render(<ResponseViewer commandId="test-command-123" />);

    // The component should show connecting initially
    expect(screen.getByText(/Connecting|Waiting/i)).toBeInTheDocument();
  });

  it('should update to "Connected" status when connection opens', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('should display response events in real-time', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    // Wait for connection
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    // Simulate receiving a response event
    const responseEvent: WebSocketEvent = {
      event: 'response',
      command_id: 'test-command-123',
      response: { dtcCode: 'P0420', description: 'Catalyst System Efficiency Below Threshold' },
      sequence_number: 1,
    };

    act(() => {
      mockWebSocketInstance?.simulateMessage(responseEvent);
    });

    // Check that response is displayed
    await waitFor(() => {
      expect(screen.getByText('Response #1')).toBeInTheDocument();
      expect(screen.getByText(/P0420/)).toBeInTheDocument();
    });
  });

  it('should handle multiple response events in sequence', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    // Send multiple response events
    act(() => {
      mockWebSocketInstance?.simulateMessage({
        event: 'response',
        command_id: 'test-command-123',
        response: { dtcCode: 'P0420', description: 'Error 1' },
        sequence_number: 1,
      });

      mockWebSocketInstance?.simulateMessage({
        event: 'response',
        command_id: 'test-command-123',
        response: { dtcCode: 'P0171', description: 'Error 2' },
        sequence_number: 2,
      });

      mockWebSocketInstance?.simulateMessage({
        event: 'response',
        command_id: 'test-command-123',
        response: { dtcCode: 'P0301', description: 'Error 3' },
        sequence_number: 3,
      });
    });

    // Check that all responses are displayed
    await waitFor(() => {
      expect(screen.getByText('Response #1')).toBeInTheDocument();
      expect(screen.getByText('Response #2')).toBeInTheDocument();
      expect(screen.getByText('Response #3')).toBeInTheDocument();
      expect(screen.getByText('3 responses received')).toBeInTheDocument();
    });
  });

  it('should update command status when status event received', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    // Send status event
    const statusEvent: WebSocketEvent = {
      event: 'status',
      command_id: 'test-command-123',
      status: 'completed',
      completed_at: '2025-10-28T12:34:56Z',
    };

    act(() => {
      mockWebSocketInstance?.simulateMessage(statusEvent);
    });

    // Check that command status is displayed
    await waitFor(() => {
      expect(screen.getByText('Status: completed')).toBeInTheDocument();
    });
  });

  it('should display error events prominently', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    // Send error event
    const errorEvent: WebSocketEvent = {
      event: 'error',
      command_id: 'test-command-123',
      error_message: 'Vehicle connection timeout',
    };

    act(() => {
      mockWebSocketInstance?.simulateMessage(errorEvent);
    });

    // Check that error is displayed
    await waitFor(() => {
      expect(screen.getByText('Vehicle connection timeout')).toBeInTheDocument();
    });
  });

  it('should call onStatusChange callback when status updates', async () => {
    const onStatusChange = vi.fn();
    render(<ResponseViewer commandId="test-command-123" onStatusChange={onStatusChange} />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    // Send status event
    act(() => {
      mockWebSocketInstance?.simulateMessage({
        event: 'status',
        command_id: 'test-command-123',
        status: 'completed',
      });
    });

    await waitFor(() => {
      expect(onStatusChange).toHaveBeenCalledWith('completed');
    });
  });

  it('should call onError callback when error occurs', async () => {
    const onError = vi.fn();
    render(<ResponseViewer commandId="test-command-123" onError={onError} />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    // Send error event
    act(() => {
      mockWebSocketInstance?.simulateMessage({
        event: 'error',
        command_id: 'test-command-123',
        error_message: 'Test error',
      });
    });

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Test error');
    });
  });

  it('should handle WebSocket connection errors', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(mockWebSocketInstance).not.toBeNull();
    });

    // Simulate connection error
    act(() => {
      mockWebSocketInstance?.simulateError();
    });

    await waitFor(() => {
      expect(screen.getByText('Connection Error')).toBeInTheDocument();
    });
  });

  it('should display error when no authentication token available', async () => {
    // Mock getAccessToken to return null
    const clientModule = await import('../../src/api/client');
    vi.spyOn(clientModule, 'getAccessToken').mockReturnValueOnce(null);

    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(screen.getByText(/Authentication required/i)).toBeInTheDocument();
    });
  });

  it('should clean up WebSocket connection on unmount', async () => {
    const { unmount } = render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(mockWebSocketInstance).not.toBeNull();
    });

    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const closeSpy = vi.spyOn(mockWebSocketInstance!, 'close');

    // Unmount component
    unmount();

    // Verify WebSocket was closed
    expect(closeSpy).toHaveBeenCalled();
  });

  it('should format response payload as JSON', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    // Send response with complex JSON
    act(() => {
      mockWebSocketInstance?.simulateMessage({
        event: 'response',
        command_id: 'test-command-123',
        response: {
          dtcCode: 'P0420',
          description: 'Catalyst System Efficiency Below Threshold',
          metadata: { severity: 'high', timestamp: '2025-10-28T12:00:00Z' },
        },
        sequence_number: 1,
      });
    });

    // Check that JSON viewer is rendered
    await waitFor(() => {
      expect(screen.getByTestId('json-viewer')).toBeInTheDocument();
      expect(screen.getByText(/P0420/)).toBeInTheDocument();
    });
  });

  it('should show "Waiting for responses..." when connected but no responses yet', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.getByText('Waiting for responses...')).toBeInTheDocument();
    });
  });

  it('should display response count in footer', async () => {
    render(<ResponseViewer commandId="test-command-123" />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    // Send multiple responses
    act(() => {
      mockWebSocketInstance?.simulateMessage({
        event: 'response',
        command_id: 'test-command-123',
        response: { data: 'response1' },
        sequence_number: 1,
      });

      mockWebSocketInstance?.simulateMessage({
        event: 'response',
        command_id: 'test-command-123',
        response: { data: 'response2' },
        sequence_number: 2,
      });
    });

    await waitFor(() => {
      expect(screen.getByText('2 responses received')).toBeInTheDocument();
    });
  });
});
