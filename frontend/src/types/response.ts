/**
 * WebSocket event types for real-time response streaming
 * Matches backend event format from backend/app/api/v1/websocket.py
 */

/**
 * Response Event - Streaming data chunks from vehicle
 */
export interface ResponseEvent {
  event: 'response';
  command_id: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  response: Record<string, any>; // Arbitrary JSON data from vehicle
  sequence_number: number;
}

/**
 * Status Event - Command completion notification
 */
export interface StatusEvent {
  event: 'status';
  command_id: string;
  status: string; // 'completed', 'failed', etc.
  completed_at?: string;
}

/**
 * Error Event - Command execution failure
 */
export interface ErrorEvent {
  event: 'error';
  command_id: string;
  error_message: string;
}

/**
 * Union type for all WebSocket events
 */
export type WebSocketEvent = ResponseEvent | StatusEvent | ErrorEvent;

/**
 * Connection status indicator
 */
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * Response item for display in viewer
 */
export interface ResponseItem {
  id: string;
  sequence_number: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  response: Record<string, any>;
  received_at: Date;
}
