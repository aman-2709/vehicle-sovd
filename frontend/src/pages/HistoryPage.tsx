/**
 * HistoryPage Component
 *
 * Displays command history with filtering and pagination.
 * Engineers see only their own commands. Admins see all commands with optional user filter.
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  TextField,
  MenuItem,
  Button,
  TablePagination,
} from '@mui/material';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import { commandAPI } from '../api/client';
import { vehicleAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';
import CommandHistory from '../components/commands/CommandHistory';
import type { CommandHistoryParams } from '../types/command';
import type { VehicleResponse } from '../types/vehicle';

const HistoryPage: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // Filter state
  const [vehicleId, setVehicleId] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [userId, setUserId] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Fetch vehicles for dropdown
  const { data: vehicles = [] } = useQuery<VehicleResponse[]>({
    queryKey: ['vehicles'],
    queryFn: () => vehicleAPI.getVehicles(),
  });

  // Build query parameters
  const queryParams: CommandHistoryParams = {
    limit: rowsPerPage,
    offset: page * rowsPerPage,
  };

  if (vehicleId) queryParams.vehicle_id = vehicleId;
  if (status) queryParams.status = status;
  if (userId && isAdmin) queryParams.user_id = userId;
  if (startDate) queryParams.start_date = new Date(startDate).toISOString();
  if (endDate) queryParams.end_date = new Date(endDate).toISOString();

  // Fetch command history
  const {
    data: commandHistoryData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['commandHistory', queryParams],
    queryFn: () => commandAPI.getCommandHistory(queryParams),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Create vehicle map for quick lookup
  const vehicleMap = new Map(
    vehicles.map((v) => [
      v.vehicle_id,
      { vin: v.vin, make: v.make, model: v.model },
    ])
  );

  // Handle filter changes
  const handleClearFilters = () => {
    setVehicleId('');
    setStatus('');
    setUserId('');
    setStartDate('');
    setEndDate('');
    setPage(0);
  };

  const handleApplyFilters = () => {
    setPage(0);
    void refetch();
  };

  // Handle pagination
  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Reset to first page when filters change
  useEffect(() => {
    setPage(0);
  }, [vehicleId, status, userId, startDate, endDate]);

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Command History
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {isAdmin
            ? 'View all commands from all users'
            : 'View your submitted commands'}
        </Typography>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <FilterListIcon color="action" />
          <Typography variant="h6">Filters</Typography>
        </Box>

        <Grid container spacing={2}>
          {/* Vehicle Filter */}
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              select
              fullWidth
              label="Vehicle"
              value={vehicleId}
              onChange={(e) => setVehicleId(e.target.value)}
              size="small"
            >
              <MenuItem value="">All Vehicles</MenuItem>
              {vehicles.map((vehicle) => (
                <MenuItem key={vehicle.vehicle_id} value={vehicle.vehicle_id}>
                  {vehicle.vin} - {vehicle.make} {vehicle.model}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          {/* Status Filter */}
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              select
              fullWidth
              label="Status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              size="small"
            >
              <MenuItem value="">All Statuses</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="in_progress">In Progress</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
            </TextField>
          </Grid>

          {/* User Filter (Admin only) */}
          {isAdmin && (
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="User ID"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                size="small"
                placeholder="Enter user ID"
                helperText="Filter by specific user"
              />
            </Grid>
          )}

          {/* Start Date Filter */}
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              type="date"
              label="Start Date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              size="small"
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* End Date Filter */}
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              type="date"
              label="End Date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              size="small"
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
        </Grid>

        <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<FilterListIcon />}
            onClick={handleApplyFilters}
          >
            Apply Filters
          </Button>
          <Button
            variant="outlined"
            startIcon={<ClearIcon />}
            onClick={handleClearFilters}
          >
            Clear Filters
          </Button>
        </Box>
      </Paper>

      {/* Command History Table */}
      <Paper>
        <CommandHistory
          commands={commandHistoryData?.commands || []}
          isLoading={isLoading}
          error={error instanceof Error ? error : null}
          showUserColumn={isAdmin}
          vehicleMap={vehicleMap}
        />

        {/* Pagination */}
        {commandHistoryData && commandHistoryData.commands.length > 0 && (
          <TablePagination
            component="div"
            count={-1} // Unknown total (backend doesn't return total count)
            page={page}
            onPageChange={handleChangePage}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            rowsPerPageOptions={[10, 25, 50, 100]}
            labelDisplayedRows={({ from, to }) =>
              `${from}-${to} (Page ${page + 1})`
            }
          />
        )}
      </Paper>
    </Container>
  );
};

export default HistoryPage;
