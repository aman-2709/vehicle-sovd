/**
 * Command Page Component
 *
 * Main page for submitting SOVD commands to vehicles.
 * Includes vehicle selector and dynamic command form.
 */

import React, { useState } from 'react';
import { Box, Container, Typography, Paper, Grid } from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { VehicleSelector } from '../components/vehicles/VehicleSelector';
import { CommandForm } from '../components/commands/CommandForm';
import { ResponseViewer } from '../components/commands/ResponseViewer';
import { commandAPI } from '../api/client';
import type {
  CommandFormData,
  CommandSubmitRequest,
  CommandResponse,
  CommandParams,
} from '../types/command';

const CommandPage: React.FC = () => {
  const [selectedVehicleId, setSelectedVehicleId] = useState<string>('');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<string | null>(null);
  const [activeCommandId, setActiveCommandId] = useState<string | null>(null);

  // Mutation for submitting commands
  const submitCommandMutation = useMutation<CommandResponse, AxiosError, CommandSubmitRequest>({
    mutationFn: (request: CommandSubmitRequest) => commandAPI.submitCommand(request),
    onSuccess: (data: CommandResponse) => {
      setSubmitError(null);
      setSubmitSuccess(
        `Command submitted successfully! Command ID: ${data.command_id}. Status: ${data.status}`
      );
      // Set active command ID to show ResponseViewer
      setActiveCommandId(data.command_id);
    },
    onError: (error: AxiosError) => {
      setSubmitSuccess(null);
      if (error.response?.status === 400) {
        const errorData = error.response.data as { detail?: string };
        setSubmitError(
          errorData.detail || 'Validation error: Please check your command parameters.'
        );
      } else if (error.response?.status === 404) {
        setSubmitError('Vehicle not found. Please select a valid vehicle.');
      } else if (error.response?.status === 401) {
        setSubmitError('Unauthorized. Please log in again.');
      } else {
        setSubmitError(
          error.message || 'An error occurred while submitting the command. Please try again.'
        );
      }
    },
  });

  const handleVehicleChange = (vehicleId: string) => {
    setSelectedVehicleId(vehicleId);
    setSubmitError(null);
    setSubmitSuccess(null);
    setActiveCommandId(null); // Clear active command when changing vehicle
  };

  const handleCommandSubmit = async (data: CommandFormData): Promise<void> => {
    // Build command_params based on command type
    const commandParams: CommandParams = {};

    if (data.command_name === 'ReadDTC') {
      commandParams.ecuAddress = data.ecuAddress;
    } else if (data.command_name === 'ClearDTC') {
      commandParams.ecuAddress = data.ecuAddress;
      if (data.dtcCode) {
        commandParams.dtcCode = data.dtcCode;
      }
    } else if (data.command_name === 'ReadDataByID') {
      commandParams.ecuAddress = data.ecuAddress;
      commandParams.dataId = data.dataId;
    }

    const request: CommandSubmitRequest = {
      vehicle_id: selectedVehicleId,
      command_name: data.command_name as 'ReadDTC' | 'ClearDTC' | 'ReadDataByID',
      command_params: commandParams,
    };

    await submitCommandMutation.mutateAsync(request);
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 4 }}>
      <Container maxWidth="md">
        <Paper elevation={2} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Command Execution
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Select a connected vehicle and submit a SOVD command.
          </Typography>

          <Grid container spacing={3}>
            {/* Vehicle Selector Section */}
            <Grid item xs={12}>
              <VehicleSelector
                value={selectedVehicleId}
                onChange={handleVehicleChange}
                error={false}
                helperText="Select a connected vehicle to enable command submission"
              />
            </Grid>

            {/* Command Form Section */}
            <Grid item xs={12}>
              {!selectedVehicleId ? (
                <Box
                  sx={{
                    p: 3,
                    bgcolor: 'grey.50',
                    borderRadius: 1,
                    textAlign: 'center',
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Please select a vehicle to start submitting commands
                  </Typography>
                </Box>
              ) : (
                <CommandForm
                  vehicleId={selectedVehicleId}
                  onSubmit={handleCommandSubmit}
                  isSubmitting={submitCommandMutation.isPending}
                  submitError={submitError}
                  submitSuccess={submitSuccess}
                />
              )}
            </Grid>

            {/* Response Viewer Section - Show after successful command submission */}
            {activeCommandId && (
              <Grid item xs={12}>
                <ResponseViewer
                  commandId={activeCommandId}
                  onStatusChange={(status) => {
                    // Log status change for debugging
                    // eslint-disable-next-line no-console
                    console.log('[CommandPage] Command status changed:', status);
                  }}
                  onError={(error) => {
                    // eslint-disable-next-line no-console
                    console.error('[CommandPage] ResponseViewer error:', error);
                  }}
                />
              </Grid>
            )}
          </Grid>
        </Paper>
      </Container>
    </Box>
  );
};

export default CommandPage;
