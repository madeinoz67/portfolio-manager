/**
 * Tests for enhanced error handling in portfolio management
 * RED phase - These tests will fail initially as the features don't exist yet
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import { usePortfolios } from '../usePortfolios'

// Mock fetch globally
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

// Mock auth context
const mockUseAuth = {
  token: 'test-token',
  user: { id: '1', email: 'test@example.com' }
}

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth
}))

describe('usePortfolios Enhanced Error Handling', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    jest.clearAllTimers()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  describe('Network Error Handling', () => {
    it('should implement exponential backoff retry for network failures', async () => {
      // Simulate network failures followed by success
      mockFetch
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [{ id: '1', name: 'Test Portfolio' }]
        } as Response)

      const { result } = renderHook(() => usePortfolios())

      // Initial state
      expect(result.current.loading).toBe(true)
      expect(result.current.retryCount).toBe(0)
      expect(result.current.isRetrying).toBe(false)

      // Wait for first retry attempt
      await act(async () => {
        jest.advanceTimersByTime(1000) // First retry after 1s
      })

      expect(result.current.retryCount).toBe(1)
      expect(result.current.isRetrying).toBe(true)

      // Wait for second retry attempt  
      await act(async () => {
        jest.advanceTimersByTime(2000) // Second retry after 2s (exponential backoff)
      })

      expect(result.current.retryCount).toBe(2)

      // Wait for successful attempt
      await act(async () => {
        jest.advanceTimersByTime(4000) // Third attempt after 4s
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
        expect(result.current.portfolios).toHaveLength(1)
        expect(result.current.error).toBe(null)
        expect(result.current.retryCount).toBe(0) // Reset after success
      })

      expect(mockFetch).toHaveBeenCalledTimes(3)
    })

    it('should stop retrying after maximum attempts and show appropriate error', async () => {
      mockFetch.mockRejectedValue(new Error('Persistent Network Error'))

      const { result } = renderHook(() => usePortfolios())

      // Fast-forward through all retry attempts
      await act(async () => {
        jest.advanceTimersByTime(15000) // Should cover all retry attempts
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
        expect(result.current.error).toBe('Unable to connect after multiple attempts. Please check your internet connection.')
        expect(result.current.retryCount).toBe(0) // Reset after max attempts
        expect(result.current.canRetry).toBe(true) // Allow manual retry
      })

      expect(mockFetch).toHaveBeenCalledTimes(3) // Initial + 2 retries = 3 total
    })
  })

  describe('HTTP Error Handling', () => {
    it('should handle 500 server errors with retry', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({ detail: 'Internal Server Error' })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [{ id: '1', name: 'Test Portfolio' }]
        } as Response)

      const { result } = renderHook(() => usePortfolios())

      await act(async () => {
        jest.advanceTimersByTime(1000) // First retry
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
        expect(result.current.portfolios).toHaveLength(1)
        expect(result.current.error).toBe(null)
      })

      expect(mockFetch).toHaveBeenCalledTimes(2)
    })

    it('should not retry 4xx client errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Bad Request' })
      } as Response)

      const { result } = renderHook(() => usePortfolios())

      await act(async () => {
        jest.advanceTimersByTime(5000) // Should not trigger any retries
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
        expect(result.current.error).toBe('Bad Request')
        expect(result.current.retryCount).toBe(0)
      })

      expect(mockFetch).toHaveBeenCalledTimes(1) // No retries for 4xx
    })

    it('should handle 401 errors by redirecting to login', async () => {
      const mockRedirect = jest.fn()
      
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' })
      } as Response)

      const { result } = renderHook(() => usePortfolios({ onUnauthorized: mockRedirect }))

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
        expect(mockRedirect).toHaveBeenCalledWith('/login')
      })
    })
  })

  describe('Manual Retry Functionality', () => {
    it('should provide manual retry capability', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [{ id: '1', name: 'Test Portfolio' }]
        } as Response)

      const { result } = renderHook(() => usePortfolios())

      // Wait for initial failure
      await act(async () => {
        jest.advanceTimersByTime(15000) // Let auto-retry exhaust
      })

      await waitFor(() => {
        expect(result.current.error).toBeTruthy()
        expect(result.current.canRetry).toBe(true)
      })

      // Manual retry
      await act(async () => {
        result.current.manualRetry()
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
        expect(result.current.portfolios).toHaveLength(1)
        expect(result.current.error).toBe(null)
      })
    })
  })

  describe('Error Classification', () => {
    it('should classify errors by type', async () => {
      const networkError = new Error('Network Error')
      mockFetch.mockRejectedValueOnce(networkError)

      const { result } = renderHook(() => usePortfolios())

      await waitFor(() => {
        expect(result.current.errorType).toBe('NETWORK_ERROR')
        expect(result.current.errorDetails).toEqual({
          message: 'Network Error',
          type: 'NETWORK_ERROR',
          retryable: true,
          timestamp: expect.any(Date)
        })
      })
    })

    it('should provide user-friendly error messages', async () => {
      const testCases = [
        { status: 429, expectedMessage: 'Too many requests. Please wait a moment and try again.' },
        { status: 503, expectedMessage: 'Service temporarily unavailable. Please try again later.' },
        { status: 404, expectedMessage: 'The requested resource was not found.' }
      ]

      for (const testCase of testCases) {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: testCase.status,
          json: async () => ({ detail: `HTTP ${testCase.status}` })
        } as Response)

        const { result } = renderHook(() => usePortfolios())

        await waitFor(() => {
          expect(result.current.userFriendlyError).toBe(testCase.expectedMessage)
        })

        mockFetch.mockClear()
      }
    })
  })

  describe('Recovery Strategies', () => {
    it('should suggest recovery actions based on error type', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network Error'))

      const { result } = renderHook(() => usePortfolios())

      await waitFor(() => {
        expect(result.current.recoveryActions).toEqual([
          { type: 'retry', label: 'Try Again', action: expect.any(Function) },
          { type: 'refresh', label: 'Refresh Page', action: expect.any(Function) },
          { type: 'contact', label: 'Contact Support', action: expect.any(Function) }
        ])
      })
    })

    it('should handle offline/online state changes', async () => {
      // Simulate going offline
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      })

      const { result } = renderHook(() => usePortfolios())

      expect(result.current.isOffline).toBe(true)
      expect(result.current.error).toBe('You appear to be offline. Please check your internet connection.')

      // Simulate coming back online
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: true
      })

      // Trigger online event
      window.dispatchEvent(new Event('online'))

      await waitFor(() => {
        expect(result.current.isOffline).toBe(false)
        // Should automatically retry when coming back online
        expect(mockFetch).toHaveBeenCalled()
      })
    })
  })
})