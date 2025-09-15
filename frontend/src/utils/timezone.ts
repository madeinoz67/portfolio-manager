/**
 * Frontend Timezone Utilities
 *
 * Following FastAPI timezone best practices from:
 * https://medium.com/@rameshkannanyt0078/how-to-handle-timezones-properly-in-fastapi-and-database-68b1c019c1bc
 *
 * IMPORTANT FOR FUTURE DEVELOPERS:
 * ================================
 * Always use these utilities instead of raw Date operations to avoid timezone bugs.
 *
 * The backend sends all dates in UTC with proper timezone info (ISO 8601 format).
 * The frontend should display dates in the user's local timezone.
 */

/**
 * Get the current date in user's local timezone formatted as YYYY-MM-DD
 * This replaces the problematic: new Date().toISOString().split('T')[0]
 */
export const getCurrentDateInUserTimezone = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Convert a local date string (YYYY-MM-DD) to UTC for server submission
 * This ensures the server receives the correct date regardless of user timezone
 */
export const convertLocalDateToUTC = (localDateString: string): string => {
  if (!localDateString) return '';

  try {
    // Create date at midnight in user's timezone
    const localDate = new Date(localDateString + 'T00:00:00');

    // Convert to UTC date string for server
    const year = localDate.getUTCFullYear();
    const month = String(localDate.getUTCMonth() + 1).padStart(2, '0');
    const day = String(localDate.getUTCDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
  } catch {
    return localDateString; // Fallback to original
  }
};

/**
 * Safely parse a server datetime string (ISO 8601 format)
 * Returns null if parsing fails to prevent "Invalid Date" errors
 */
export const parseServerDate = (dateString: string): Date | null => {
  if (!dateString) return null;

  try {
    const date = new Date(dateString);
    return isNaN(date.getTime()) ? null : date;
  } catch {
    return null;
  }
};

/**
 * Format a server date string for display in user's local timezone
 * Handles server dates that may be in various formats
 */
export const formatDisplayDate = (
  dateString: string,
  options: Intl.DateTimeFormatOptions = {}
): string => {
  const date = parseServerDate(dateString);
  if (!date) return 'Invalid Date';

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    ...options
  };

  try {
    return date.toLocaleDateString('en-US', defaultOptions);
  } catch {
    return date.toLocaleDateString(); // Fallback to browser default
  }
};

/**
 * Format a server datetime string for display with time in user's local timezone
 */
export const formatDisplayDateTime = (
  dateString: string,
  options: Intl.DateTimeFormatOptions = {}
): string => {
  const date = parseServerDate(dateString);
  if (!date) return 'Invalid Date';


  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
    ...options
  };

  try {
    // Let JavaScript automatically convert UTC to user's local timezone
    return date.toLocaleString(navigator.language, defaultOptions);
  } catch {
    // Fallback to simple browser default
    return date.toLocaleString();
  }
};

/**
 * Get relative time string (e.g., "2 hours ago") with proper timezone handling
 * Used for market data timestamps and activity feeds
 */
export const getRelativeTime = (dateString: string): string => {
  const date = parseServerDate(dateString);
  if (!date) return 'Unknown time';

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;

  return formatDisplayDate(dateString);
};

/**
 * Compare dates properly handling timezone differences
 * Returns: -1 if date1 < date2, 0 if equal, 1 if date1 > date2
 */
export const compareDates = (date1String: string, date2String: string): number => {
  const date1 = parseServerDate(date1String);
  const date2 = parseServerDate(date2String);

  if (!date1 && !date2) return 0;
  if (!date1) return -1;
  if (!date2) return 1;

  const time1 = date1.getTime();
  const time2 = date2.getTime();

  if (time1 < time2) return -1;
  if (time1 > time2) return 1;
  return 0;
};

/**
 * Check if a date is in the future (accounting for timezone)
 */
export const isFutureDate = (dateString: string): boolean => {
  const date = parseServerDate(dateString);
  if (!date) return false;

  const now = new Date();
  return date.getTime() > now.getTime();
};

/**
 * Check if a date is within a certain range from now
 * Used for determining if market data is stale
 */
export const isWithinTimeRange = (dateString: string, maxAgeMinutes: number): boolean => {
  const date = parseServerDate(dateString);
  if (!date) return false;

  const now = new Date();
  const ageMs = now.getTime() - date.getTime();
  const ageMinutes = ageMs / (1000 * 60);

  return ageMinutes <= maxAgeMinutes;
};

/**
 * Validate that a date input string is valid for form submission
 */
export const isValidDateString = (dateString: string): boolean => {
  if (!dateString) return false;

  // Check format YYYY-MM-DD
  const datePattern = /^\d{4}-\d{2}-\d{2}$/;
  if (!datePattern.test(dateString)) return false;

  // Check that it's actually a valid date
  const date = new Date(dateString + 'T00:00:00');
  return !isNaN(date.getTime());
};

/**
 * Get the maximum date string for date inputs (today in user timezone)
 * Prevents users from selecting future dates
 */
export const getMaxDateForInput = (): string => {
  return getCurrentDateInUserTimezone();
};

/**
 * Convert server date to input-ready format (YYYY-MM-DD)
 * Used when editing forms with existing dates
 */
export const serverDateToInputFormat = (serverDateString: string): string => {
  const date = parseServerDate(serverDateString);
  if (!date) return '';

  // Convert to local date components to avoid timezone shift
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
};

/**
 * Convert a local date string (YYYY-MM-DD) to UTC timestamp for server submission
 * This replaces convertLocalDateToUTC for the new timestamp-based approach
 *
 * Creates a timestamp representing midnight in the user's local timezone,
 * which when converted to UTC maintains the user's intended date relationship.
 */
export const convertLocalDateToTimestamp = (localDateString: string): string => {
  if (!localDateString) return '';

  try {
    // Create date at midnight in user's timezone
    const localMidnight = new Date(localDateString + 'T00:00:00');

    if (isNaN(localMidnight.getTime())) {
      return localDateString; // Fallback to original for invalid input
    }

    // Convert to UTC timestamp (ISO 8601 format)
    return localMidnight.toISOString();
  } catch {
    return localDateString; // Fallback to original
  }
};

/**
 * Format a UTC timestamp for display in user's local timezone
 * This replaces formatUTCDateForLocalDisplay for the new timestamp-based approach
 *
 * Uses standard JavaScript Date handling - much simpler than date-only conversion.
 */
export const formatTimestampForLocalDisplay = (utcTimestamp: string): string => {
  if (!utcTimestamp) return 'Invalid Date';

  try {
    const date = new Date(utcTimestamp);

    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }

    // Use browser's built-in timezone handling - this is the clean approach
    return date.toLocaleDateString(navigator.language || 'en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch {
    return 'Invalid Date';
  }
};

/**
 * @deprecated Use formatTimestampForLocalDisplay for new timestamp-based approach
 * Format a UTC date string (YYYY-MM-DD) for display in user's local timezone
 * Used specifically for transaction dates that are stored as UTC dates
 * This properly converts UTC date-only strings back to the original local date the user entered
 *
 * Uses Intl.DateTimeFormat to properly handle timezone conversion without hardcoded offsets.
 */
export const formatUTCDateForLocalDisplay = (utcDateString: string): string => {
  if (!utcDateString) return 'Invalid Date';

  try {
    // Parse the UTC date string as a proper UTC date
    // Adding 'T00:00:00Z' ensures it's treated as UTC midnight, not local midnight
    const utcDate = new Date(utcDateString + 'T00:00:00Z');

    if (isNaN(utcDate.getTime())) {
      return 'Invalid Date';
    }

    // Use Intl.DateTimeFormat - this is the standard, correct approach
    // It automatically handles timezone conversion from UTC to user's local timezone
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };

    return new Intl.DateTimeFormat(navigator.language || 'en-US', options).format(utcDate);
  } catch {
    // Fallback for very old browsers or broken test environments
    try {
      const utcDate = new Date(utcDateString + 'T00:00:00Z');
      return utcDate.toLocaleDateString(navigator.language || 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return 'Invalid Date';
    }
  }
};

/**
 * @deprecated Use formatUTCDateForLocalDisplay for transaction dates
 * Format a UTC date string (YYYY-MM-DD) for display in user's local timezone
 * Used specifically for transaction dates that are stored as UTC dates
 * This converts the UTC date to the equivalent local date that the user originally intended
 */
export const formatUTCDateForDisplay = (utcDateString: string): string => {
  if (!utcDateString) return 'Invalid Date';

  try {
    // Parse the UTC date as a simple date (no time component)
    const utcDate = new Date(utcDateString);

    // Get timezone offset in hours (negative for timezones ahead of UTC)
    const offsetHours = new Date().getTimezoneOffset() / 60;

    // If timezone is ahead of UTC (negative offset), add a day to display the local equivalent
    if (offsetHours < 0) {
      utcDate.setDate(utcDate.getDate() + 1);
    }

    return utcDate.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch {
    return 'Invalid Date';
  }
};