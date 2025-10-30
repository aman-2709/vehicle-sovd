/**
 * Error Toast Component
 *
 * Displays toast notifications using MUI Snackbar and Alert components.
 * Supports multiple simultaneous toasts stacked vertically.
 */

import React from 'react';
import { Snackbar, Alert, AlertTitle, IconButton } from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { useError } from '../../context/ErrorContext';

/**
 * ErrorToast Component
 *
 * Renders all toasts from the error context as stacked Snackbars.
 */
const ErrorToast: React.FC = () => {
  const { toasts, clearToast } = useError();

  return (
    <>
      {toasts.map((toast, index) => (
        <Snackbar
          key={toast.id}
          open={true}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
          sx={{
            // Stack toasts vertically with spacing
            top: `${24 + index * 80}px !important`,
          }}
          data-testid={`toast-${toast.severity}`}
        >
          <Alert
            severity={toast.severity}
            variant="filled"
            onClose={() => clearToast(toast.id)}
            action={
              <IconButton
                aria-label="close"
                color="inherit"
                size="small"
                onClick={() => clearToast(toast.id)}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            }
            sx={{
              width: '100%',
              minWidth: '400px',
              maxWidth: '600px',
              boxShadow: 3,
              // Multi-line message support
              '& .MuiAlert-message': {
                whiteSpace: 'pre-line',
                wordBreak: 'break-word',
              },
            }}
          >
            {toast.correlationId ? (
              <>
                <AlertTitle>Error</AlertTitle>
                {toast.message.split('\n\n')[0]}
                <div
                  style={{
                    marginTop: '8px',
                    fontSize: '0.75rem',
                    opacity: 0.9,
                    fontFamily: 'monospace',
                  }}
                >
                  {toast.correlationId}
                </div>
              </>
            ) : (
              toast.message
            )}
          </Alert>
        </Snackbar>
      ))}
    </>
  );
};

export default ErrorToast;
