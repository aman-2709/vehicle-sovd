/**
 * Offline Banner Component
 *
 * Displays a non-dismissible banner at the top of the page when the browser
 * detects that it is offline. Automatically disappears when connection is restored.
 */

import React from 'react';
import { Alert, Collapse } from '@mui/material';
import { WifiOff as WifiOffIcon } from '@mui/icons-material';
import { useOnlineStatus } from '../../hooks/useOnlineStatus';

/**
 * OfflineBanner Component
 *
 * Shows a sticky warning banner when the browser is offline.
 */
const OfflineBanner: React.FC = () => {
  const isOnline = useOnlineStatus();

  return (
    <Collapse in={!isOnline}>
      <Alert
        severity="warning"
        icon={<WifiOffIcon />}
        sx={{
          borderRadius: 0,
          position: 'sticky',
          top: 0,
          zIndex: (theme) => theme.zIndex.appBar + 1,
          '& .MuiAlert-message': {
            width: '100%',
            textAlign: 'center',
            fontWeight: 500,
          },
        }}
        data-testid="offline-banner"
      >
        You are currently offline. Some features may be unavailable until your connection is
        restored.
      </Alert>
    </Collapse>
  );
};

export default OfflineBanner;
