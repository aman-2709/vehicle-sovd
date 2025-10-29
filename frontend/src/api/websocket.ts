/**
 * WebSocket client for real-time response streaming
 * Connects to backend WebSocket endpoint: /ws/responses/{command_id}
 */

import { WebSocketEvent, ConnectionStatus } from '../types/response';

/**
 * WebSocket connection configuration
 */
export interface WebSocketConfig {
  commandId: string;
  token: string;
  onMessage: (event: WebSocketEvent) => void;
  onStatusChange: (status: ConnectionStatus) => void;
  onError?: (error: string) => void;
}

/**
 * Get WebSocket base URL from environment
 */
const getWebSocketBaseUrl = (): string => {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  return apiBaseUrl.replace(/^http/, 'ws');
};

/**
 * Create WebSocket connection to response streaming endpoint
 *
 * @param config - WebSocket configuration
 * @returns WebSocket instance
 *
 * @example
 * ```typescript
 * const ws = createWebSocketConnection({
 *   commandId: '123e4567-e89b-12d3-a456-426614174000',
 *   token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
 *   onMessage: (event) => console.log('Event:', event),
 *   onStatusChange: (status) => console.log('Status:', status)
 * });
 * ```
 */
export const createWebSocketConnection = (config: WebSocketConfig): WebSocket => {
  const { commandId, token, onMessage, onStatusChange, onError } = config;

  const wsBaseUrl = getWebSocketBaseUrl();
  const url = `${wsBaseUrl}/ws/responses/${commandId}?token=${token}`;

  // eslint-disable-next-line no-console
  console.log('[WebSocket] Connecting to:', url);
  onStatusChange('connecting');

  const ws = new WebSocket(url);

  ws.onopen = () => {
    // eslint-disable-next-line no-console
    console.log('[WebSocket] Connected to command:', commandId);
    onStatusChange('connected');
  };

  ws.onmessage = (event) => {
    try {
      // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
      const data: WebSocketEvent = JSON.parse(event.data as string);
      // eslint-disable-next-line no-console
      console.log('[WebSocket] Message received:', data);
      onMessage(data);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('[WebSocket] Failed to parse message:', error);
      onError?.('Failed to parse server message');
    }
  };

  ws.onerror = (error) => {
    // eslint-disable-next-line no-console
    console.error('[WebSocket] Error:', error);
    onStatusChange('error');
    onError?.('WebSocket connection error');
  };

  ws.onclose = (event) => {
    // eslint-disable-next-line no-console
    console.log('[WebSocket] Closed:', event.code, event.reason);

    // Normal closure (1000) or server-initiated closure after completion is expected
    if (event.code === 1000 || event.code === 1001) {
      // eslint-disable-next-line no-console
      console.log('[WebSocket] Connection closed normally');
    } else if (event.code === 1008) {
      // Policy violation - authentication failure
      // eslint-disable-next-line no-console
      console.error('[WebSocket] Authentication failed (policy violation)');
      onError?.('Authentication failed. Please log in again.');
    } else {
      // eslint-disable-next-line no-console
      console.warn('[WebSocket] Unexpected close code:', event.code);
      onError?.(`Connection closed unexpectedly (code: ${event.code})`);
    }

    onStatusChange('disconnected');
  };

  return ws;
};

/**
 * Reconnection manager with exponential backoff
 */
export class WebSocketReconnectionManager {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private retryCount: number = 0;
  private maxRetries: number = 5;
  private retryTimeout: ReturnType<typeof setTimeout> | null = null;
  private isManualClose: boolean = false;

  constructor(config: WebSocketConfig, maxRetries: number = 5) {
    this.config = config;
    this.maxRetries = maxRetries;
  }

  /**
   * Connect to WebSocket with automatic retry on failure
   */
  connect(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // eslint-disable-next-line no-console
      console.log('[WebSocket] Already connected');
      return;
    }

    this.isManualClose = false;
    this.ws = createWebSocketConnection({
      ...this.config,
      onStatusChange: (status) => {
        this.config.onStatusChange(status);

        // Attempt reconnection on error if retries remaining
        if (status === 'error' && !this.isManualClose && this.retryCount < this.maxRetries) {
          this.scheduleReconnect();
        }
      },
      onError: (error) => {
        this.config.onError?.(error);
      },
    });
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
    }

    this.retryCount++;
    const delay = Math.min(1000 * Math.pow(2, this.retryCount - 1), 30000); // Max 30s

    // eslint-disable-next-line no-console
    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.retryCount}/${this.maxRetries})`
    );

    this.retryTimeout = setTimeout(() => {
      // eslint-disable-next-line no-console
      console.log('[WebSocket] Attempting reconnection...');
      this.connect();
    }, delay);
  }

  /**
   * Close WebSocket connection and cancel any pending reconnections
   */
  close(): void {
    this.isManualClose = true;

    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
      this.retryTimeout = null;
    }

    if (this.ws) {
      // eslint-disable-next-line no-console
      console.log('[WebSocket] Closing connection');
      this.ws.close(1000, 'Client initiated close');
      this.ws = null;
    }

    this.retryCount = 0;
  }

  /**
   * Reset retry count (useful after successful connection)
   */
  resetRetryCount(): void {
    this.retryCount = 0;
  }
}
