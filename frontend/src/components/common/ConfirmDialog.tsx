/**
 * Confirm Dialog Component
 *
 * Reusable confirmation dialog for critical actions like logout, delete, etc.
 * Uses Material-UI Dialog components for consistent styling.
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
} from '@mui/material';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmColor?: 'primary' | 'error' | 'warning' | 'success' | 'info';
}

/**
 * ConfirmDialog Component
 *
 * Displays a confirmation dialog with customizable title, message, and button labels.
 *
 * @param open - Whether the dialog is open
 * @param title - Dialog title
 * @param message - Dialog message/description
 * @param confirmText - Text for the confirm button (default: "Confirm")
 * @param cancelText - Text for the cancel button (default: "Cancel")
 * @param onConfirm - Callback when confirm button is clicked
 * @param onCancel - Callback when cancel button is clicked or dialog is closed
 * @param confirmColor - Color of the confirm button (default: "primary")
 */
const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  confirmColor = 'primary',
}) => {
  return (
    <Dialog
      open={open}
      onClose={onCancel}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
      data-testid="confirm-dialog"
    >
      <DialogTitle id="confirm-dialog-title">{title}</DialogTitle>
      <DialogContent>
        <DialogContentText id="confirm-dialog-description">{message}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} color="inherit" data-testid="confirm-dialog-cancel">
          {cancelText}
        </Button>
        <Button
          onClick={onConfirm}
          color={confirmColor}
          variant="contained"
          autoFocus
          data-testid="confirm-dialog-confirm"
        >
          {confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;
