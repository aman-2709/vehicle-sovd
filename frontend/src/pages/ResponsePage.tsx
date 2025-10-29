/**
 * ResponsePage Component
 * Dedicated page for viewing real-time command responses
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Paper, Typography, Button, Box, Alert } from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { ResponseViewer } from '../components/commands/ResponseViewer';

/**
 * ResponsePage component for dedicated response viewing
 *
 * Route: /responses/:commandId
 *
 * Features:
 * - URL-based command ID routing
 * - Back navigation to command page
 * - Real-time response streaming via ResponseViewer
 */
export const ResponsePage: React.FC = () => {
  const { commandId } = useParams<{ commandId: string }>();
  const navigate = useNavigate();

  // Validate command ID
  if (!commandId) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          Invalid command ID. Please navigate from the command execution page.
        </Alert>
        <Button
          variant="outlined"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/commands')}
          sx={{ mt: 2 }}
        >
          Back to Commands
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Page header */}
      <Box sx={{ mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBack />}
          onClick={() => navigate(-1)}
          sx={{ mb: 2 }}
        >
          Back
        </Button>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h4" gutterBottom>
            Command Response Viewer
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Command ID: <code>{commandId}</code>
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Viewing real-time responses streamed from the vehicle via WebSocket connection.
          </Typography>
        </Paper>
      </Box>

      {/* Response viewer */}
      <ResponseViewer
        commandId={commandId}
        onStatusChange={(status) => {
          // Log status change for debugging
          // eslint-disable-next-line no-console
          console.log('[ResponsePage] Command status changed:', status);
        }}
        onError={(error) => {
          // eslint-disable-next-line no-console
          console.error('[ResponsePage] Error:', error);
        }}
      />
    </Container>
  );
};

export default ResponsePage;
