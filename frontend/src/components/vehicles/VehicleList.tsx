/**
 * VehicleList Component
 *
 * Displays a table of vehicles with connection status indicators and last seen timestamps.
 * Renders loading, error, and empty states appropriately.
 */

import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Box,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import type { VehicleResponse } from '../../types/vehicle';
import { formatRelativeTime } from '../../utils/dateUtils';

interface VehicleListProps {
  /** List of vehicles to display */
  vehicles: VehicleResponse[];
  /** Whether data is currently being fetched */
  isLoading: boolean;
  /** Error object if fetch failed */
  error: Error | null;
  /** Whether the list is filtered (affects empty state message) */
  isFiltered?: boolean;
}

/**
 * Gets the color for a connection status chip.
 */
const getStatusColor = (status: string): 'success' | 'error' | 'default' => {
  if (status === 'connected') return 'success';
  if (status === 'error') return 'error';
  return 'default';
};

/**
 * VehicleList component displays vehicles in a table format with status indicators.
 */
const VehicleList: React.FC<VehicleListProps> = ({
  vehicles,
  isLoading,
  error,
  isFiltered = false,
}) => {
  // Loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load vehicles. Please try again.
      </Alert>
    );
  }

  // Empty state
  if (vehicles.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No vehicles found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {isFiltered ? 'Try adjusting your filters' : 'No vehicles available'}
        </Typography>
      </Box>
    );
  }

  // Table view
  return (
    <TableContainer component={Paper} elevation={2}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 'bold' }}>VIN</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>Make</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>Model</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>Year</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>Status</TableCell>
            <TableCell sx={{ fontWeight: 'bold' }}>Last Seen</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {vehicles.map((vehicle) => (
            <TableRow
              key={vehicle.vehicle_id}
              hover
              sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
            >
              <TableCell>
                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                  {vehicle.vin}
                </Typography>
              </TableCell>
              <TableCell>{vehicle.make}</TableCell>
              <TableCell>{vehicle.model}</TableCell>
              <TableCell>{vehicle.year}</TableCell>
              <TableCell>
                <Chip
                  label={vehicle.connection_status}
                  color={getStatusColor(vehicle.connection_status)}
                  size="small"
                  sx={{ textTransform: 'capitalize' }}
                />
              </TableCell>
              <TableCell>
                <Typography variant="body2" color="text.secondary">
                  {formatRelativeTime(vehicle.last_seen_at)}
                </Typography>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default VehicleList;
