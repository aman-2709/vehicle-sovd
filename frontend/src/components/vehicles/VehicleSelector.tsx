/**
 * VehicleSelector Component
 *
 * Dropdown component for selecting a vehicle from connected vehicles only.
 * Fetches vehicles via React Query and filters to show only connected ones.
 */

import React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  CircularProgress,
  SelectChangeEvent,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { vehicleAPI } from '../../api/client';
import type { VehicleResponse } from '../../types/vehicle';

interface VehicleSelectorProps {
  value: string;
  onChange: (vehicleId: string) => void;
  error?: boolean;
  helperText?: string;
  disabled?: boolean;
}

export const VehicleSelector: React.FC<VehicleSelectorProps> = ({
  value,
  onChange,
  error = false,
  helperText,
  disabled = false,
}) => {
  // Fetch vehicles using React Query
  const {
    data: vehicles,
    isLoading,
    isError,
  } = useQuery<VehicleResponse[]>({
    queryKey: ['vehicles'],
    queryFn: () => vehicleAPI.getVehicles(),
    staleTime: 30000, // 30 seconds
  });

  // Filter to connected vehicles only
  const connectedVehicles = React.useMemo(() => {
    if (!vehicles) return [];
    return vehicles.filter((vehicle) => vehicle.connection_status === 'connected');
  }, [vehicles]);

  const handleChange = (event: SelectChangeEvent<string>) => {
    onChange(event.target.value);
  };

  return (
    <FormControl fullWidth error={error} disabled={disabled || isLoading}>
      <InputLabel id="vehicle-selector-label">Vehicle</InputLabel>
      <Select
        labelId="vehicle-selector-label"
        id="vehicle-selector"
        value={value}
        label="Vehicle"
        onChange={handleChange}
        startAdornment={isLoading ? <CircularProgress size={20} sx={{ mr: 1 }} /> : null}
      >
        <MenuItem value="">
          <em>Select a vehicle</em>
        </MenuItem>
        {isError && (
          <MenuItem disabled>
            <em>Error loading vehicles</em>
          </MenuItem>
        )}
        {!isLoading && connectedVehicles.length === 0 && (
          <MenuItem disabled>
            <em>No connected vehicles available</em>
          </MenuItem>
        )}
        {connectedVehicles.map((vehicle) => (
          <MenuItem key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
            {vehicle.vin} - {vehicle.make} {vehicle.model} ({vehicle.year})
          </MenuItem>
        ))}
      </Select>
      {helperText && <FormHelperText>{helperText}</FormHelperText>}
    </FormControl>
  );
};
