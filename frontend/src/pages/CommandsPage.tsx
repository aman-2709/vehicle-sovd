/**
 * Commands Page Component
 *
 * Placeholder for command execution interface.
 */

import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';

const CommandsPage: React.FC = () => {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 4 }}>
      <Container maxWidth="lg">
        <Paper elevation={2} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Commands
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Command execution interface will be implemented in future iterations.
          </Typography>
        </Paper>
      </Container>
    </Box>
  );
};

export default CommandsPage;
