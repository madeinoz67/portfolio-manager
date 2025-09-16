# Frontend Date Handling Guide

This guide covers best practices for handling dates and timestamps in the Portfolio Manager frontend application.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core Functions](#core-functions)
- [Usage Examples](#usage-examples)
- [Migration from Legacy Approach](#migration-from-legacy-approach)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)

## Overview

The Portfolio Manager application uses a **timestamp-based approach** for handling transaction dates and other date fields. This approach leverages JavaScript's built-in timezone handling to provide accurate date display across different timezones without hardcoded offsets.

### Key Principles

1. **Store as UTC timestamps**: All dates are stored in the database as UTC timestamps (ISO 8601 format)
2. **Display in local timezone**: Frontend displays dates in the user's browser timezone
3. **Browser handles conversion**: Use native JavaScript Date operations for timezone conversion
4. **Maintain user intent**: Preserve the date the user originally intended to enter

## Architecture

```
User Input (Local Date) -> Frontend Conversion -> Server Storage (UTC Timestamp) -> Display (Local Date)
     "2025-09-15"      ->  "2025-09-14T16:00:00.000Z"  ->    "Sep 15, 2025"
                            (UTC+8 user example)
```

## Core Functions

### Location: `frontend/src/utils/timezone.ts`

#### Input/Submission Functions

##### `convertLocalDateToTimestamp(localDateString: string): string`

Converts a local date input (YYYY-MM-DD) to a UTC timestamp for server submission.

```typescript
// User enters "2025-09-15" in UTC+8 timezone
const timestamp = convertLocalDateToTimestamp("2025-09-15");
// Returns: "2025-09-14T16:00:00.000Z"
```

**When to use:**
- Form submissions (TransactionForm, etc.)
- Any time sending date data to the server
- Date validation before submission

##### `getCurrentDateInUserTimezone(): string`

Gets the current date in the user's local timezone as YYYY-MM-DD format.

```typescript
const today = getCurrentDateInUserTimezone();
// Returns: "2025-09-15" (for a user in UTC+8 on Sep 15)
```

**When to use:**
- Default values for date inputs
- Setting maximum date for date inputs
- Current date comparisons

#### Display Functions

##### `formatTimestampForLocalDisplay(utcTimestamp: string): string`

Formats a UTC timestamp for display in the user's local timezone.

```typescript
// Server returns: "2025-09-14T16:00:00.000Z"
const displayDate = formatTimestampForLocalDisplay("2025-09-14T16:00:00.000Z");
// Returns: "Sep 15, 2025" (for UTC+8 user)
```

**When to use:**
- Displaying transaction dates
- Any timestamp from the server that needs local display
- Transaction lists, details, reports

##### `formatDisplayDateTime(dateString: string, options?: Intl.DateTimeFormatOptions): string`

Formats a server datetime string with time component for display.

```typescript
const displayDateTime = formatDisplayDateTime("2025-09-14T16:00:00.000Z");
// Returns: "Sep 15, 2025, 12:00 AM" (for UTC+8 user)
```

#### Utility Functions

##### `serverDateToInputFormat(serverDateString: string): string`

Converts server timestamp back to input format (YYYY-MM-DD) for editing forms.

```typescript
// For editing existing transactions
const inputValue = serverDateToInputFormat("2025-09-14T16:00:00.000Z");
// Returns: "2025-09-15" (user's original intended date)
```

##### `parseServerDate(dateString: string): Date | null`

Safely parses server date strings with error handling.

```typescript
const date = parseServerDate("2025-09-14T16:00:00.000Z");
// Returns: Date object or null if parsing fails
```

## Usage Examples

### Form Input Component

```typescript
import {
  getCurrentDateInUserTimezone,
  convertLocalDateToTimestamp,
  serverDateToInputFormat
} from '@/utils/timezone';

function TransactionForm({ initialData }: { initialData?: Transaction }) {
  const [formData, setFormData] = useState({
    transaction_date: initialData?.transaction_date
      ? serverDateToInputFormat(initialData.transaction_date)
      : getCurrentDateInUserTimezone()
  });

  const handleSubmit = async () => {
    const submissionData = {
      ...formData,
      transaction_date: convertLocalDateToTimestamp(formData.transaction_date)
    };

    await api.createTransaction(submissionData);
  };

  return (
    <input
      type="date"
      value={formData.transaction_date}
      max={getCurrentDateInUserTimezone()}
      onChange={(e) => setFormData(prev => ({
        ...prev,
        transaction_date: e.target.value
      }))}
    />
  );
}
```

### Display Component

```typescript
import { formatTimestampForLocalDisplay } from '@/utils/timezone';

function TransactionList({ transactions }: { transactions: Transaction[] }) {
  return (
    <table>
      {transactions.map(transaction => (
        <tr key={transaction.id}>
          <td>{formatTimestampForLocalDisplay(transaction.transaction_date)}</td>
          <td>{transaction.stock_symbol}</td>
        </tr>
      ))}
    </table>
  );
}
```

### Date Validation

```typescript
import { convertLocalDateToTimestamp } from '@/utils/timezone';

function validateTransactionDate(dateString: string): string | null {
  if (!dateString) {
    return 'Transaction date is required';
  }

  const timestamp = convertLocalDateToTimestamp(dateString);
  const transactionDate = new Date(timestamp);
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);

  if (transactionDate > today) {
    return 'Transaction date cannot be in the future';
  }

  return null; // No error
}
```

## Migration from Legacy Approach

### Before (Date-only with hardcoded offsets)

```typescript
// ❌ Old approach - avoid
const utcDate = new Date(localDateString + 'T00:00:00Z');
if (offsetHours < 0) {
  utcDate.setDate(utcDate.getDate() + 1); // Hardcoded offset
}
```

### After (Timestamp-based)

```typescript
// ✅ New approach - use this
const timestamp = convertLocalDateToTimestamp(localDateString);
const displayDate = formatTimestampForLocalDisplay(timestamp);
```

### Migration Checklist

When updating components:

1. **Replace import statements:**
   ```typescript
   // Old
   import { convertLocalDateToUTC, formatUTCDateForLocalDisplay } from '@/utils/timezone';

   // New
   import { convertLocalDateToTimestamp, formatTimestampForLocalDisplay } from '@/utils/timezone';
   ```

2. **Update form submissions:**
   ```typescript
   // Old
   transaction_date: convertLocalDateToUTC(formData.transaction_date)

   // New
   transaction_date: convertLocalDateToTimestamp(formData.transaction_date)
   ```

3. **Update display logic:**
   ```typescript
   // Old
   {formatUTCDateForLocalDisplay(transaction.transaction_date)}

   // New
   {formatTimestampForLocalDisplay(transaction.transaction_date)}
   ```

## Best Practices

### ✅ Do's

1. **Always use the provided utility functions** instead of raw Date operations
2. **Use `convertLocalDateToTimestamp`** for all form submissions
3. **Use `formatTimestampForLocalDisplay`** for displaying server timestamps
4. **Use `getCurrentDateInUserTimezone`** for default and maximum date values
5. **Validate dates using the converted timestamp** for consistency with backend
6. **Test across different timezones** to ensure correct behavior

### ❌ Don'ts

1. **Don't use hardcoded timezone offsets** (e.g., `+ 1 day`, `- 8 hours`)
2. **Don't use `new Date().toISOString().split('T')[0]`** for local dates
3. **Don't assume UTC dates without timezone info** represent local dates
4. **Don't mix date-only and timestamp approaches** in the same component
5. **Don't use deprecated functions** like `convertLocalDateToUTC`

### Code Examples

#### ✅ Correct Implementation

```typescript
// Form submission
const handleSubmit = async (formData: FormData) => {
  const transactionData = {
    ...formData,
    transaction_date: convertLocalDateToTimestamp(formData.transaction_date)
  };
  await api.createTransaction(transactionData);
};

// Display
const TransactionRow = ({ transaction }: { transaction: Transaction }) => (
  <tr>
    <td>{formatTimestampForLocalDisplay(transaction.transaction_date)}</td>
  </tr>
);

// Default value
const [date, setDate] = useState(getCurrentDateInUserTimezone());
```

#### ❌ Incorrect Implementation

```typescript
// Don't do this - hardcoded offset
const localDate = new Date(utcDateString);
if (timezoneOffset < 0) {
  localDate.setDate(localDate.getDate() + 1);
}

// Don't do this - incorrect local date
const today = new Date().toISOString().split('T')[0];

// Don't do this - mixing approaches
transaction_date: convertLocalDateToUTC(formData.transaction_date) // Old function
```

## Troubleshooting

### Common Issues

#### Issue: Dates showing one day off

**Symptoms:** User enters "Sep 15" but sees "Sep 14" in the transaction list

**Cause:** Using wrong display function or timezone handling

**Solution:**
```typescript
// Ensure you're using the correct display function
formatTimestampForLocalDisplay(transaction.transaction_date)

// Not formatDisplayDate or formatUTCDateForLocalDisplay
```

#### Issue: "Date cannot be in the future" error for today's date

**Symptoms:** User can't enter today's date in forms

**Cause:** Timezone conversion mismatch between frontend and backend validation

**Solution:**
```typescript
// Use the same conversion for validation as submission
const timestamp = convertLocalDateToTimestamp(formData.transaction_date);
const transactionDate = new Date(timestamp);
```

#### Issue: Wrong timezone display

**Symptoms:** Dates showing in UTC instead of local timezone

**Cause:** Server sending wrong format or frontend not converting properly

**Solution:**
1. Verify server sends ISO 8601 timestamps: `"2025-09-14T16:00:00.000Z"`
2. Use `formatTimestampForLocalDisplay` for display
3. Check browser timezone detection: `Intl.DateTimeFormat().resolvedOptions().timeZone`

### Debugging Tools

#### Check browser timezone

```typescript
console.log('Browser timezone:', Intl.DateTimeFormat().resolvedOptions().timeZone);
console.log('Timezone offset:', new Date().getTimezoneOffset()); // Minutes from UTC
```

#### Test conversion functions

```typescript
const testDate = "2025-09-15";
console.log('Input:', testDate);
console.log('Timestamp:', convertLocalDateToTimestamp(testDate));
console.log('Display:', formatTimestampForLocalDisplay(convertLocalDateToTimestamp(testDate)));
```

#### Verify round-trip consistency

```typescript
const originalDate = "2025-09-15";
const timestamp = convertLocalDateToTimestamp(originalDate);
const displayDate = formatTimestampForLocalDisplay(timestamp);
console.log('Round-trip consistent:', displayDate.includes('15')); // Should be true
```

## Testing

### Unit Tests Location

- **Timestamp tests:** `frontend/src/__tests__/unit/timezone-timestamps.test.ts`
- **Legacy tests:** `frontend/src/__tests__/unit/timezone.test.ts`

### Key Test Scenarios

1. **Round-trip consistency:** Local date → timestamp → display should maintain user intent
2. **Timezone edge cases:** New Year's Day, daylight saving time transitions
3. **Error handling:** Invalid date strings, empty inputs
4. **Cross-timezone compatibility:** UTC+8, UTC-5, UTC+0 scenarios

### Running Tests

```bash
# Run all timezone tests
npm test -- __tests__/unit/timezone

# Run only timestamp tests
npm test -- __tests__/unit/timezone-timestamps.test.ts
```

### Example Test

```typescript
test('should maintain user intent through complete round-trip', () => {
  // Given: User enters a date in their local timezone
  const userIntendedDate = '2025-09-15';

  // When: We convert to timestamp for storage and back for display
  const serverTimestamp = convertLocalDateToTimestamp(userIntendedDate);
  const displayedDate = formatTimestampForLocalDisplay(serverTimestamp);

  // Then: User should see their original intended date
  expect(displayedDate).toBe('Sep 15, 2025');
});
```

## Advanced Usage

### Custom Date Formatting

```typescript
import { formatTimestampForLocalDisplay } from '@/utils/timezone';

// Custom format options
const customFormat = formatDisplayDateTime(timestamp, {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric'
});
// Returns: "Monday, September 15, 2025"
```

### Relative Time Display

```typescript
import { getRelativeTime } from '@/utils/timezone';

const relativeTime = getRelativeTime("2025-09-14T16:00:00.000Z");
// Returns: "2 hours ago" or "Just now"
```

### Date Comparison

```typescript
import { compareDates } from '@/utils/timezone';

const comparison = compareDates(date1, date2);
// Returns: -1, 0, or 1 for less than, equal, or greater than
```

## Migration History

- **September 2025:** Migrated from date-only storage to timestamp-based storage
- **Database:** Updated `transaction_date` column from `DATE` to `DATETIME`
- **Frontend:** Replaced `convertLocalDateToUTC` with `convertLocalDateToTimestamp`
- **Display:** Replaced `formatUTCDateForLocalDisplay` with `formatTimestampForLocalDisplay`

## Related Files

- **Utilities:** `frontend/src/utils/timezone.ts`
- **Components:** `frontend/src/components/Transaction/TransactionForm.tsx`
- **Components:** `frontend/src/components/Transaction/TransactionList.tsx`
- **Tests:** `frontend/src/__tests__/unit/timezone-timestamps.test.ts`
- **Migration:** `backend/alembic/versions/9b3bfca83bef_convert_transaction_date_from_date_to_.py`

For questions or issues with date handling, refer to the test files for comprehensive examples or consult the timezone utility functions.