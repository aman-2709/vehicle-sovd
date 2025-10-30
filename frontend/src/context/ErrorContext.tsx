/**
 * Error Context
 *
 * Global error state management with toast notification queue.
 * Provides functions to display success, error, warning, and info messages.
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export type ToastSeverity = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  severity: ToastSeverity;
  correlationId?: string;
  autoDismiss: boolean;
  duration: number;
}

interface ErrorContextType {
  toasts: Toast[];
  showError: (message: string, options?: { code?: string; correlationId?: string }) => void;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showInfo: (message: string) => void;
  clearToast: (id: string) => void;
  clearAllToasts: () => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

interface ErrorProviderProps {
  children: ReactNode;
}

/**
 * Error Provider Component
 *
 * Wraps the application to provide global error handling and toast notifications.
 */
export const ErrorProvider: React.FC<ErrorProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  /**
   * Add a new toast to the queue.
   */
  const addToast = useCallback(
    (
      message: string,
      severity: ToastSeverity,
      options?: { correlationId?: string; duration?: number }
    ) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const duration = options?.duration || (severity === 'error' ? 6000 : 4000);

      const newToast: Toast = {
        id,
        message,
        severity,
        correlationId: options?.correlationId,
        autoDismiss: true,
        duration,
      };

      setToasts((prev) => [...prev, newToast]);

      // Auto-dismiss after duration
      if (newToast.autoDismiss) {
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id));
        }, duration);
      }
    },
    []
  );

  /**
   * Show an error toast.
   */
  const showError = useCallback(
    (message: string, options?: { code?: string; correlationId?: string }) => {
      // Don't append correlation ID to message - the ErrorToast component will handle it
      addToast(message, 'error', { correlationId: options?.correlationId });
    },
    [addToast]
  );

  /**
   * Show a success toast.
   */
  const showSuccess = useCallback(
    (message: string) => {
      addToast(message, 'success');
    },
    [addToast]
  );

  /**
   * Show a warning toast.
   */
  const showWarning = useCallback(
    (message: string) => {
      addToast(message, 'warning');
    },
    [addToast]
  );

  /**
   * Show an info toast.
   */
  const showInfo = useCallback(
    (message: string) => {
      addToast(message, 'info');
    },
    [addToast]
  );

  /**
   * Remove a specific toast by ID.
   */
  const clearToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  /**
   * Remove all toasts.
   */
  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const value: ErrorContextType = {
    toasts,
    showError,
    showSuccess,
    showWarning,
    showInfo,
    clearToast,
    clearAllToasts,
  };

  return <ErrorContext.Provider value={value}>{children}</ErrorContext.Provider>;
};

/**
 * Hook to use error context.
 *
 * @returns Error context value
 * @throws Error if used outside ErrorProvider
 */
export const useError = (): ErrorContextType => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};
