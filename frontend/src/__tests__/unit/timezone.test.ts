/**
 * TDD Test for Transaction Date Timezone Display Issue
 *
 * Problem: UTC date "2025-09-14" should display as "Sep 15, 2025" for UTC+8 timezone
 * Current behavior: Still showing as "Sep 14, 2025"
 */

import { formatDisplayDate, parseServerDate, formatUTCDateForLocalDisplay } from '@/utils/timezone'

describe('Transaction Date Timezone Display', () => {
  // Mock the timezone to simulate UTC+8 (Australia/Perth, Asia/Singapore, etc)
  const originalTimezoneOffset = Date.prototype.getTimezoneOffset
  const originalIntl = global.Intl

  beforeEach(() => {
    // Mock timezone offset for UTC+8 (offset = -480 minutes)
    Date.prototype.getTimezoneOffset = jest.fn(() => -480)

    // Mock Intl.DateTimeFormat for consistent formatting
    global.Intl = {
      ...originalIntl,
      DateTimeFormat: jest.fn((locale, options) => ({
        resolvedOptions: () => ({ timeZone: 'Asia/Singapore' }),
        format: (date: Date) => {
          // For UTC+8, simulate what the browser would do:
          // Convert UTC time to UTC+8 local time (add 8 hours)
          const utc8Time = new Date(date.getTime() + (8 * 60 * 60 * 1000))
          return utc8Time.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            timeZone: 'UTC' // Use UTC since we already adjusted the time
          })
        }
      })) as any
    }
  })

  afterEach(() => {
    Date.prototype.getTimezoneOffset = originalTimezoneOffset
    global.Intl = originalIntl
  })

  test('formatDisplayDate is not suitable for UTC date-only strings', () => {
    // This test shows the current behavior - formatDisplayDate is for datetime strings
    const utcDateFromBackend = '2025-09-14'
    const displayDate = formatDisplayDate(utcDateFromBackend)

    // formatDisplayDate treats date-only strings as local dates, not UTC
    console.log('formatDisplayDate result:', displayDate)
    expect(displayDate).toBe('Sep 14, 2025') // Current behavior
  })

  test('formatUTCDateForLocalDisplay should convert UTC date-only strings correctly', () => {
    // Given: A UTC date string from the backend (when user entered Sep 15 in UTC+8)
    const utcDateFromBackend = '2025-09-14'  // Backend stores as UTC when user enters Sep 15

    // When: We format it for display using the proper UTC date formatter
    const displayDate = formatUTCDateForLocalDisplay(utcDateFromBackend)

    // Then: It should show the original local date (Sep 15) for UTC+8 users
    console.log('UTC date from backend:', utcDateFromBackend)
    console.log('Local display result:', displayDate)
    console.log('Timezone offset:', new Date().getTimezoneOffset())

    // This should pass for UTC+8 users
    expect(displayDate).toBe('Sep 15, 2025')
  })

  test('parseServerDate should parse date string correctly', () => {
    const dateString = '2025-09-14'
    const parsedDate = parseServerDate(dateString)

    expect(parsedDate).not.toBeNull()
    expect(parsedDate?.getFullYear()).toBe(2025)
    expect(parsedDate?.getMonth()).toBe(8) // September is month 8 (0-indexed)
    expect(parsedDate?.getDate()).toBe(14)
  })

  test('formatDisplayDate handles various date formats', () => {
    const testCases = [
      '2025-09-14',           // YYYY-MM-DD
      '2025-09-14T00:00:00Z', // ISO format
      '2025-09-14T00:00:00',  // Without timezone
    ]

    testCases.forEach(dateString => {
      const result = formatDisplayDate(dateString)
      console.log(`Input: ${dateString} -> Output: ${result}`)
      expect(result).not.toBe('Invalid Date')
    })
  })
})