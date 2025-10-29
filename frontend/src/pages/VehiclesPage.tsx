/**
 * Vehicles Page Component
 *
 * Displays list of vehicles with search and filter capabilities.
 * Integrates with React Query for data fetching, caching, and auto-refresh.
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  MenuItem,
  Grid,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { vehicleAPI } from '../api/client';
import VehicleList from '../components/vehicles/VehicleList';

/**
 * VehiclesPage component manages vehicle list display with filtering and search.
 */
const VehiclesPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');

  // Fetch vehicles with React Query (auto-refresh every 30 seconds)
  const {
    data: vehicles,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['vehicles'],
    queryFn: () => vehicleAPI.getVehicles(),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Client-side filtering by VIN and status
  const filteredVehicles = useMemo(() => {
    if (!vehicles) return [];

    return vehicles.filter((vehicle) => {
      const matchesSearch =
        searchTerm === '' ||
        vehicle.vin.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus =
        statusFilter === 'All' ||
        vehicle.connection_status === statusFilter.toLowerCase();

      return matchesSearch && matchesStatus;
    });
  }, [vehicles, searchTerm, statusFilter]);

  const isFiltered = searchTerm !== '' || statusFilter !== 'All';

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 4 }}>
      <Container maxWidth="lg">
        {/* Page Header */}
        <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 4 }}>
          Vehicles
        </Typography>

        {/* Search and Filter Controls */}
        <Box sx={{ mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                label="Search by VIN"
                variant="outlined"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Enter VIN to filter..."
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                label="Status Filter"
                variant="outlined"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="All">All</MenuItem>
                <MenuItem value="Connected">Connected</MenuItem>
                <MenuItem value="Disconnected">Disconnected</MenuItem>
                <MenuItem value="Error">Error</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </Box>

        {/* Vehicle List */}
        <VehicleList
          vehicles={filteredVehicles}
          isLoading={isLoading}
          error={error}
          isFiltered={isFiltered}
        />
      </Container>
    </Box>
  );
};

export default VehiclesPage;
