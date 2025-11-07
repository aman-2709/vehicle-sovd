/**
 * Date utility functions for formatting dates and times
 */

/**
 * Format a date as relative time (e.g., "2 minutes ago", "3 hours ago")
 */
export const formatRelativeTime = (dateString: string | null): string => {
  if (!dateString) {
    return 'Never';
  }

  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) {
      return 'Just now';
    } else if (diffMin < 60) {
      return diffMin + ' minute' + (diffMin !== 1 ? 's' : '') + ' ago';
    } else if (diffHour < 24) {
      return diffHour + ' hour' + (diffHour !== 1 ? 's' : '') + ' ago';
    } else if (diffDay < 30) {
      return diffDay + ' day' + (diffDay !== 1 ? 's' : '') + ' ago';
    } else {
      return date.toLocaleDateString();
    }
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Invalid date';
  }
};

export const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  } catch (error) {
    return 'Invalid date';
  }
};

export const formatDateTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString();
  } catch (error) {
    return 'Invalid date';
  }
};
