/**
 * Vehicles Page Component
 *
 * Placeholder for vehicle management interface.
 */

import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';

const VehiclesPage: React.FC = () => {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 4 }}>
      <Container maxWidth="lg">
        <Paper elevation={2} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Vehicles
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Vehicle management interface will be implemented in future iterations.
          </Typography>
        </Paper>
      </Container>
    </Box>
  );
};

export default VehiclesPage;
