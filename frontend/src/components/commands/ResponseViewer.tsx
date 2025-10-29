/**
 * ResponseViewer Component
 * Real-time WebSocket-based command response viewer with streaming updates
 */

import React, { useEffect, useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import ReactJson from '@microlink/react-json-view';
import { getAccessToken } from '../../api/client';
import { WebSocketReconnectionManager } from '../../api/websocket';
import {
  WebSocketEvent,
  ConnectionStatus,
  ResponseItem,
} from '../../types/response';

/**
 * Component props
 */
export interface ResponseViewerProps {
  commandId: string;
  onStatusChange?: (status: string) => void;
  onError?: (error: string) => void;
}

/**
 * Get status chip color based on connection status
 */
const getStatusColor = (
  status: ConnectionStatus
): 'default' | 'primary' | 'success' | 'error' => {
  switch (status) {
    case 'connecting':
      return 'default';
    case 'connected':
      return 'success';
    case 'disconnected':
      return 'default';
    case 'error':
      return 'error';
    default:
      return 'default';
  }
};

/**
 * Get status label for display
 */
const getStatusLabel = (status: ConnectionStatus): string => {
  switch (status) {
    case 'connecting':
      return 'Connecting...';
    case 'connected':
      return 'Connected';
    case 'disconnected':
      return 'Disconnected';
    case 'error':
      return 'Connection Error';
    default:
      return 'Unknown';
  }
};

/**
 * ResponseViewer component for real-time command response streaming
 *
 * Features:
 * - WebSocket connection with JWT authentication
 * - Real-time response streaming
 * - JSON syntax highlighting
 * - Auto-scroll to newest response
 * - Connection status indicator
 * - Error handling with retry logic
 * - Automatic cleanup on unmount
 */
export const ResponseViewer: React.FC<ResponseViewerProps> = ({
  commandId,
  onStatusChange,
  onError,
}) => {
  // State management
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [responses, setResponses] = useState<ResponseItem[]>([]);
  const [commandStatus, setCommandStatus] = useState<string>('pending');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Refs
  const wsManagerRef = useRef<WebSocketReconnectionManager | null>(null);
  const responseEndRef = useRef<HTMLDivElement>(null);

  /**
   * Auto-scroll to bottom when new responses arrive
   */
  useEffect(() => {
    // Check if scrollIntoView is available (may not be in test environment)
    if (responseEndRef.current && typeof responseEndRef.current.scrollIntoView === 'function') {
      responseEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [responses]);

  /**
   * Initialize WebSocket connection on mount
   */
  useEffect(() => {
    const token = getAccessToken();

    if (!token) {
      const error = 'Authentication required. Please log in.';
      setErrorMessage(error);
      setConnectionStatus('error');
      onError?.(error);
      return;
    }

    // Handle WebSocket messages
    const handleMessage = (event: WebSocketEvent) => {
      if (event.event === 'response') {
        // Add response to list
        const newResponse: ResponseItem = {
          id: `${event.command_id}-${event.sequence_number}`,
          sequence_number: event.sequence_number,
          response: event.response,
          received_at: new Date(),
        };

        setResponses((prev) => [...prev, newResponse]);
        setErrorMessage(null); // Clear any previous errors
      } else if (event.event === 'status') {
        // Update command status
        setCommandStatus(event.status);
        onStatusChange?.(event.status);

        // eslint-disable-next-line no-console
        console.log('[ResponseViewer] Command completed with status:', event.status);
      } else if (event.event === 'error') {
        // Display error message
        const error = event.error_message || 'Unknown error occurred';
        setErrorMessage(error);
        onError?.(error);
        setCommandStatus('failed');
      }
    };

    // Handle connection status changes
    const handleStatusChange = (status: ConnectionStatus) => {
      setConnectionStatus(status);

      // Reset retry count on successful connection
      if (status === 'connected' && wsManagerRef.current) {
        wsManagerRef.current.resetRetryCount();
      }
    };

    // Handle connection errors
    const handleError = (error: string) => {
      setErrorMessage(error);
      onError?.(error);
    };

    // Create WebSocket connection manager with retry logic
    wsManagerRef.current = new WebSocketReconnectionManager(
      {
        commandId,
        token,
        onMessage: handleMessage,
        onStatusChange: handleStatusChange,
        onError: handleError,
      },
      5 // Max 5 retry attempts
    );

    // Connect
    wsManagerRef.current.connect();

    // Cleanup on unmount
    return () => {
      // eslint-disable-next-line no-console
      console.log('[ResponseViewer] Cleaning up WebSocket connection');
      wsManagerRef.current?.close();
      wsManagerRef.current = null;
    };
  }, [commandId, onStatusChange, onError]);

  return (
    <Paper sx={{ p: 3 }}>
      {/* Header with connection status */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Real-Time Responses</Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {/* Connection status indicator */}
          <Chip
            label={getStatusLabel(connectionStatus)}
            color={getStatusColor(connectionStatus)}
            size="small"
            icon={
              connectionStatus === 'connecting' ? (
                <CircularProgress size={16} color="inherit" />
              ) : undefined
            }
          />

          {/* Command status indicator */}
          {commandStatus !== 'pending' && (
            <Chip
              label={`Status: ${commandStatus}`}
              color={commandStatus === 'completed' ? 'success' : commandStatus === 'failed' ? 'error' : 'default'}
              size="small"
            />
          )}
        </Box>
      </Box>

      <Divider sx={{ mb: 2 }} />

      {/* Error message display */}
      {errorMessage && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setErrorMessage(null)}>
          {errorMessage}
        </Alert>
      )}

      {/* Response list */}
      <Box
        sx={{
          maxHeight: '600px',
          overflowY: 'auto',
          bgcolor: 'background.default',
          borderRadius: 1,
          p: 2,
        }}
      >
        {responses.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            {connectionStatus === 'connected' ? (
              <>
                <CircularProgress size={40} sx={{ mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  Waiting for responses...
                </Typography>
              </>
            ) : (
              <Typography variant="body2" color="text.secondary">
                {connectionStatus === 'connecting'
                  ? 'Establishing connection...'
                  : 'No responses yet'}
              </Typography>
            )}
          </Box>
        ) : (
          responses.map((item, index) => (
            <Box key={item.id} sx={{ mb: 2 }}>
              {/* Response header */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Response #{item.sequence_number}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {item.received_at.toLocaleTimeString()}
                </Typography>
              </Box>

              {/* JSON payload with syntax highlighting */}
              <Paper
                variant="outlined"
                sx={{
                  p: 1,
                  bgcolor: 'grey.900',
                  '& .react-json-view': { fontSize: '0.875rem' },
                }}
              >
                <ReactJson
                  src={item.response}
                  theme="monokai"
                  collapsed={false}
                  displayDataTypes={false}
                  displayObjectSize={false}
                  enableClipboard={true}
                  name={null}
                  style={{
                    backgroundColor: 'transparent',
                    fontSize: '0.875rem',
                  }}
                />
              </Paper>

              {/* Divider between responses (except last) */}
              {index < responses.length - 1 && <Divider sx={{ mt: 2 }} />}
            </Box>
          ))
        )}

        {/* Auto-scroll anchor */}
        <div ref={responseEndRef} />
      </Box>

      {/* Footer info */}
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          {responses.length > 0
            ? `${responses.length} response${responses.length > 1 ? 's' : ''} received`
            : 'Streaming responses in real-time'}
        </Typography>
      </Box>
    </Paper>
  );
};

export default ResponseViewer;
