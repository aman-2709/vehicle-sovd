/**
 * Dashboard Page Component
 *
 * Main dashboard view for authenticated users (placeholder for now).
 */

import React from 'react';
import { Box, Container, Typography, Button, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    void (async () => {
      await logout();
      navigate('/login', { replace: true });
    })();
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 4 }}>
      <Container maxWidth="lg">
        <Paper elevation={2} sx={{ p: 4 }}>
          <Box
            sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}
          >
            <Typography variant="h4" component="h1">
              Dashboard
            </Typography>
            <Button variant="outlined" color="secondary" onClick={handleLogout}>
              Logout
            </Button>
          </Box>

          <Typography variant="body1" color="text.secondary" paragraph>
            Welcome, {user?.username}!
          </Typography>

          <Typography variant="body2" color="text.secondary">
            Role: {user?.role}
          </Typography>

          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button variant="contained" onClick={() => navigate('/vehicles')}>
                Manage Vehicles
              </Button>
              <Button variant="contained" onClick={() => navigate('/commands')}>
                Execute Commands
              </Button>
              <Button variant="contained" onClick={() => navigate('/history')}>
                View History
              </Button>
            </Box>
          </Box>

          <Box sx={{ mt: 4, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
            <Typography variant="body2" color="white">
              This is a placeholder dashboard. Full functionality will be implemented in future
              iterations.
            </Typography>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default DashboardPage;
