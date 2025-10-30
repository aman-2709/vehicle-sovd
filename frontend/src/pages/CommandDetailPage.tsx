/**
 * CommandDetailPage Component
 *
 * Displays detailed information about a single command including its status,
 * parameters, and response data.
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { commandAPI } from '../api/client';
import { vehicleAPI } from '../api/client';
import ResponseViewer from '../components/commands/ResponseViewer';
import { formatRelativeTime } from '../utils/dateUtils';
import type { CommandResponse } from '../types/command';

/**
 * Get color for command status chip
 */
const getStatusColor = (
  status: string
): 'default' | 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success' => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    case 'in_progress':
      return 'primary';
    case 'pending':
      return 'warning';
    default:
      return 'default';
  }
};

const CommandDetailPage: React.FC = () => {
  const { commandId } = useParams<{ commandId: string }>();
  const navigate = useNavigate();

  // Fetch command details
  const {
    data: command,
    isLoading: isLoadingCommand,
    error: commandError,
  } = useQuery<CommandResponse>({
    queryKey: ['command', commandId],
    queryFn: () => {
      if (!commandId) throw new Error('Command ID is required');
      return commandAPI.getCommand(commandId);
    },
    enabled: !!commandId,
    refetchInterval: 5000, // Auto-refresh every 5 seconds for status updates
  });

  // Fetch vehicle details if command is loaded
  const { data: vehicle } = useQuery({
    queryKey: ['vehicle', command?.vehicle_id],
    queryFn: () => {
      if (!command?.vehicle_id) throw new Error('Vehicle ID is required');
      return vehicleAPI.getVehicle(command.vehicle_id);
    },
    enabled: !!command?.vehicle_id,
  });

  const handleBack = () => {
    navigate('/history');
  };

  if (isLoadingCommand) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (commandError) {
    const errorMessage = commandError instanceof Error ? commandError.message : 'Unknown error';
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">Error loading command details: {errorMessage}</Alert>
        <Box sx={{ mt: 2 }}>
          <Button variant="outlined" startIcon={<ArrowBackIcon />} onClick={handleBack}>
            Back to History
          </Button>
        </Box>
      </Container>
    );
  }

  if (!command) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="warning">Command not found</Alert>
        <Box sx={{ mt: 2 }}>
          <Button variant="outlined" startIcon={<ArrowBackIcon />} onClick={handleBack}>
            Back to History
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={handleBack}
          sx={{ mb: 2 }}
        >
          Back to History
        </Button>
        <Typography variant="h4" component="h1" gutterBottom>
          Command Details
        </Typography>
        <Typography variant="body2" color="text.secondary">
          View detailed information about this command and its responses
        </Typography>
      </Box>

      {/* Command Overview */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Overview</Typography>
          <Chip label={command.status} color={getStatusColor(command.status)} />
        </Box>
        <Divider sx={{ mb: 2 }} />

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Command ID
            </Typography>
            <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
              {command.command_id}
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Command Name
            </Typography>
            <Typography variant="body1" fontWeight="medium">
              {command.command_name}
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Vehicle
            </Typography>
            {vehicle ? (
              <Box>
                <Typography variant="body1">{vehicle.vin}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {vehicle.make} {vehicle.model} ({vehicle.year})
                </Typography>
              </Box>
            ) : (
              <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
                {command.vehicle_id}
              </Typography>
            )}
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Submitted At
            </Typography>
            <Typography variant="body1">{formatRelativeTime(command.submitted_at)}</Typography>
            <Typography variant="caption" color="text.secondary">
              {new Date(command.submitted_at).toLocaleString()}
            </Typography>
          </Grid>

          {command.completed_at && (
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Completed At
              </Typography>
              <Typography variant="body1">{formatRelativeTime(command.completed_at)}</Typography>
              <Typography variant="caption" color="text.secondary">
                {new Date(command.completed_at).toLocaleString()}
              </Typography>
            </Grid>
          )}

          {command.error_message && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Error Message
              </Typography>
              <Alert severity="error">{command.error_message}</Alert>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Command Parameters */}
      {command.command_params && Object.keys(command.command_params).length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Command Parameters
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box
              component="pre"
              sx={{
                backgroundColor: 'grey.100',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
              }}
            >
              {JSON.stringify(command.command_params, null, 2)}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Response Data */}
      {commandId && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Response Data
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <ResponseViewer commandId={commandId} />
          </CardContent>
        </Card>
      )}
    </Container>
  );
};

export default CommandDetailPage;
