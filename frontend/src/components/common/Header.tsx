/**
 * Header Component
 *
 * Application header with app title, navigation links, and user profile menu.
 * Displays username and provides logout functionality.
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Divider,
} from '@mui/material';
import { AccountCircle } from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import ConfirmDialog from './ConfirmDialog';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogoutClick = () => {
    handleMenuClose();
    setShowLogoutConfirm(true);
  };

  const handleLogoutConfirm = () => {
    setShowLogoutConfirm(false);
    void (async () => {
      await logout();
      navigate('/login', { replace: true });
    })();
  };

  const handleLogoutCancel = () => {
    setShowLogoutConfirm(false);
  };

  const navigationLinks = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Vehicles', path: '/vehicles' },
    { label: 'Commands', path: '/commands' },
    { label: 'History', path: '/history' },
  ];

  return (
    <AppBar position="fixed" elevation={1} sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        {/* App Title */}
        <Typography variant="h6" component="div" sx={{ fontWeight: 600, letterSpacing: 0.5 }}>
          SOVD Command
        </Typography>

        {/* Navigation Links */}
        <Box sx={{ flexGrow: 1, display: 'flex', ml: 4 }}>
          {navigationLinks.map((link) => (
            <Button
              key={link.path}
              color="inherit"
              onClick={() => navigate(link.path)}
              sx={{
                mx: 0.5,
                fontWeight: location.pathname === link.path ? 600 : 400,
                borderBottom: location.pathname === link.path ? '2px solid white' : 'none',
                borderRadius: 0,
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              {link.label}
            </Button>
          ))}
        </Box>

        {/* User Profile Menu */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="body2" sx={{ mr: 1 }}>
            {user?.username}
          </Typography>
          <IconButton
            aria-label="User menu"
            color="inherit"
            onClick={handleMenuOpen}
            data-testid="user-menu-button"
          >
            <AccountCircle />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
          >
            <MenuItem disabled>
              <Typography variant="body2" color="text.secondary">
                {user?.username}
              </Typography>
            </MenuItem>
            <MenuItem disabled>
              <Typography variant="body2" color="text.secondary">
                Role: {user?.role}
              </Typography>
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogoutClick} data-testid="logout-button">
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>

      {/* Logout Confirmation Dialog */}
      <ConfirmDialog
        open={showLogoutConfirm}
        title="Confirm Logout"
        message="Are you sure you want to log out? You will need to sign in again to access the application."
        confirmText="Log Out"
        cancelText="Cancel"
        confirmColor="primary"
        onConfirm={handleLogoutConfirm}
        onCancel={handleLogoutCancel}
      />
    </AppBar>
  );
};

export default Header;
