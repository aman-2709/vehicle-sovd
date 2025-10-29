/**
 * History Page Component
 *
 * Placeholder for command history and audit log interface.
 */

import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';

const HistoryPage: React.FC = () => {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 4 }}>
      <Container maxWidth="lg">
        <Paper elevation={2} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            History
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Command history and audit log interface will be implemented in future iterations.
          </Typography>
        </Paper>
      </Container>
    </Box>
  );
};

export default HistoryPage;
