/**
 * Date utility functions for formatting timestamps.
 */

/**
 * Formats an ISO 8601 timestamp as relative time (e.g., "2 minutes ago", "5 hours ago").
 *
 * @param dateString - ISO 8601 timestamp string or null
 * @returns Formatted relative time string
 *
 * @example
 * formatRelativeTime("2025-10-28T10:00:00Z") // "2 minutes ago" (if current time is 10:02:00)
 * formatRelativeTime(null) // "Never"
 */
export const formatRelativeTime = (dateString: string | null): string => {
  if (!dateString) return 'Never';

  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  // Handle future dates (clock skew)
  if (diffInSeconds < 0) return 'Just now';

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
  }
  if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
  }

  const days = Math.floor(diffInSeconds / 86400);
  return `${days} ${days === 1 ? 'day' : 'days'} ago`;
};
