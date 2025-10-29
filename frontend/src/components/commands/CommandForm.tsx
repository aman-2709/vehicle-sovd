/**
 * CommandForm Component
 *
 * Dynamic form for submitting SOVD commands with validation.
 * Fields change based on selected command type.
 */

import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  FormHelperText,
} from '@mui/material';
import type { CommandFormData } from '../../types/command';

interface CommandFormProps {
  vehicleId: string;
  onSubmit: (data: CommandFormData) => Promise<void>;
  isSubmitting: boolean;
  submitError: string | null;
  submitSuccess: string | null;
}

export const CommandForm: React.FC<CommandFormProps> = ({
  vehicleId,
  onSubmit,
  isSubmitting,
  submitError,
  submitSuccess,
}) => {
  const {
    control,
    handleSubmit,
    watch,
    formState: { errors },
    reset,
  } = useForm<CommandFormData>({
    defaultValues: {
      vehicle_id: vehicleId,
      command_name: '',
      ecuAddress: '',
      dtcCode: '',
      dataId: '',
    },
  });

  // Watch command_name to show/hide fields dynamically
  const commandName = watch('command_name');

  // Update vehicle_id when prop changes
  React.useEffect(() => {
    reset({ vehicle_id: vehicleId, command_name: '', ecuAddress: '', dtcCode: '', dataId: '' });
  }, [vehicleId, reset]);

  const onFormSubmit = (data: CommandFormData) => {
    void onSubmit(data);
  };

  // Validation patterns
  const ecuAddressPattern = {
    value: /^0x[0-9A-Fa-f]{2}$/,
    message: 'ECU Address must be in format 0xXX (e.g., 0x10)',
  };

  const dtcCodePattern = {
    value: /^P[0-9A-F]{4}$/,
    message: 'DTC Code must be in format PXXXX (e.g., P0420)',
  };

  const dataIdPattern = {
    value: /^0x[0-9A-Fa-f]{4}$/,
    message: 'Data ID must be in format 0xXXXX (e.g., 0x1234)',
  };

  return (
    <Box
      component="form"
      onSubmit={(e) => {
        void handleSubmit(onFormSubmit)(e);
      }}
      noValidate
    >
      {/* Success Message */}
      {submitSuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {submitSuccess}
        </Alert>
      )}

      {/* Error Message */}
      {submitError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {submitError}
        </Alert>
      )}

      {/* Command Name Dropdown */}
      <Controller
        name="command_name"
        control={control}
        rules={{ required: 'Command name is required' }}
        render={({ field }) => (
          <FormControl fullWidth margin="normal" error={!!errors.command_name}>
            <InputLabel id="command-name-label">Command</InputLabel>
            <Select
              {...field}
              labelId="command-name-label"
              id="command-name"
              label="Command"
              disabled={isSubmitting}
            >
              <MenuItem value="">
                <em>Select a command</em>
              </MenuItem>
              <MenuItem value="ReadDTC">ReadDTC</MenuItem>
              <MenuItem value="ClearDTC">ClearDTC</MenuItem>
              <MenuItem value="ReadDataByID">ReadDataByID</MenuItem>
            </Select>
            {errors.command_name && <FormHelperText>{errors.command_name.message}</FormHelperText>}
          </FormControl>
        )}
      />

      {/* Dynamic Fields Based on Command Type */}

      {/* ECU Address - Required for all commands */}
      {commandName && (
        <Controller
          name="ecuAddress"
          control={control}
          rules={{
            required: 'ECU Address is required',
            pattern: ecuAddressPattern,
          }}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              margin="normal"
              label="ECU Address"
              placeholder="0x10"
              error={!!errors.ecuAddress}
              helperText={errors.ecuAddress?.message || 'Format: 0xXX (e.g., 0x10)'}
              disabled={isSubmitting}
            />
          )}
        />
      )}

      {/* DTC Code - Optional for ClearDTC */}
      {commandName === 'ClearDTC' && (
        <Controller
          name="dtcCode"
          control={control}
          rules={{
            pattern: dtcCodePattern,
          }}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              margin="normal"
              label="DTC Code (Optional)"
              placeholder="P0420"
              error={!!errors.dtcCode}
              helperText={errors.dtcCode?.message || 'Format: PXXXX (e.g., P0420)'}
              disabled={isSubmitting}
            />
          )}
        />
      )}

      {/* Data ID - Required for ReadDataByID */}
      {commandName === 'ReadDataByID' && (
        <Controller
          name="dataId"
          control={control}
          rules={{
            required: 'Data ID is required',
            pattern: dataIdPattern,
          }}
          render={({ field }) => (
            <TextField
              {...field}
              fullWidth
              margin="normal"
              label="Data ID"
              placeholder="0x1234"
              error={!!errors.dataId}
              helperText={errors.dataId?.message || 'Format: 0xXXXX (e.g., 0x1234)'}
              disabled={isSubmitting}
            />
          )}
        />
      )}

      {/* Submit Button */}
      <Button
        type="submit"
        variant="contained"
        color="primary"
        fullWidth
        disabled={isSubmitting || !commandName}
        sx={{ mt: 3, mb: 2 }}
        startIcon={isSubmitting ? <CircularProgress size={20} /> : null}
      >
        {isSubmitting ? 'Submitting...' : 'Submit Command'}
      </Button>
    </Box>
  );
};
