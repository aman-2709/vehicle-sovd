/**
 * Layout Component
 *
 * Main application layout that wraps pages with header, sidebar, and content area.
 * Provides consistent structure across all protected routes.
 */

import React, { ReactNode } from 'react';
import { Box, Toolbar } from '@mui/material';
import Header from './Header';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <>
      {/* Header - fixed at top */}
      <Header />

      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        {/* Sidebar - fixed on left */}
        <Sidebar />

        {/* Main content area */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            bgcolor: 'background.default',
            p: 3,
            marginLeft: { sm: `240px` }, // 240px = sidebar width
          }}
        >
          {/* Spacer to push content below fixed header */}
          <Toolbar />

          {/* Page content */}
          {children}
        </Box>
      </Box>
    </>
  );
};

export default Layout;
