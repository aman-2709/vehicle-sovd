/**
 * useOnlineStatus Hook
 *
 * React hook that detects online/offline status using the browser's
 * navigator.onLine API and online/offline events.
 */

import { useState, useEffect } from 'react';

/**
 * Hook to detect browser online/offline status.
 *
 * @returns Boolean indicating whether the browser is online
 */
export const useOnlineStatus = (): boolean => {
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Cleanup listeners on unmount
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
};
