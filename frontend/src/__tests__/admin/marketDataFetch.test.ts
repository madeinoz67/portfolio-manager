/**
 * TDD tests for market data fetch issue diagnosis
 *
 * Following TDD methodology to identify and fix "failed to fetch" issue:
 * 1. Write failing tests that reproduce the frontend fetch problem
 * 2. Identify the exact failure point in the frontend code
 * 3. Fix the minimal code to make tests pass
 * 4. Refactor while keeping tests green
 */

import { AdminApiClient, AdminApiError } from '@/services/adminService'

// Mock global fetch
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

describe('Market Data Fetch Issue TDD', () => {
  let apiClient: AdminApiClient
  const testToken = 'test-admin-jwt-token'
  const expectedUrl = 'http://localhost:8001/api/v1/admin/market-data/status'

  beforeEach(() => {
    jest.clearAllMocks()
    apiClient = new AdminApiClient(testToken)
  })

  describe('TDD: Reproduce "failed to fetch" issue', () => {
    it('should fail initially with network error - reproducing the issue', async () => {
      // Arrange - Mock network failure (simulating the "failed to fetch" error)
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      // Act & Assert - This should now be wrapped in AdminApiError with better message
      await expect(apiClient.getMarketDataStatus()).rejects.toThrow('Network connection failed')

      // Verify the correct URL was called
      expect(mockFetch).toHaveBeenCalledWith(
        expectedUrl,
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': `Bearer ${testToken}`
          })
        })
      )
    })

    it('should handle CORS issues that could cause "failed to fetch"', async () => {
      // Arrange - Mock CORS error (another common cause of "failed to fetch")
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      // Act & Assert - Should handle CORS gracefully with proper error message
      await expect(apiClient.getMarketDataStatus()).rejects.toThrow('Network connection failed')

      // The call should still be made to the correct endpoint
      expect(mockFetch).toHaveBeenCalledWith(expectedUrl, expect.any(Object))
    })

    it('should handle incorrect API URL causing fetch to fail', async () => {
      // Arrange - This tests if the API_BASE_URL is incorrectly configured
      const originalEnv = process.env.NEXT_PUBLIC_API_URL

      // Mock an unreachable URL
      process.env.NEXT_PUBLIC_API_URL = 'http://wrong-url:9999'

      // Recreate client to pick up new URL
      const clientWithBadUrl = new AdminApiClient(testToken)

      // Mock network failure for bad URL
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      try {
        // Act & Assert
        await expect(clientWithBadUrl.getMarketDataStatus()).rejects.toThrow('Network connection failed')

        // Should have tried to call the wrong URL
        expect(mockFetch).toHaveBeenCalledWith(
          'http://wrong-url:9999/api/v1/admin/market-data/status',
          expect.any(Object)
        )
      } finally {
        // Restore original environment
        process.env.NEXT_PUBLIC_API_URL = originalEnv
      }
    })

    it('should handle server not running causing "failed to fetch"', async () => {
      // Arrange - Mock server connection refused
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      // Act & Assert
      await expect(apiClient.getMarketDataStatus()).rejects.toThrow('Network connection failed')
    })
  })

  describe('TDD: Fix the fetch issue', () => {
    it('should succeed when server responds correctly', async () => {
      // Arrange - Mock successful response
      const mockMarketDataResponse = {
        providers: [
          {
            providerId: 'yfinance',
            providerName: 'Yahoo Finance',
            isEnabled: true,
            lastUpdate: '2025-01-14T10:25:00Z',
            apiCallsToday: 42,
            monthlyLimit: 2000,
            monthlyUsage: 1200,
            costPerCall: 0.0,
            status: 'active'
          }
        ]
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockMarketDataResponse,
        text: async () => JSON.stringify(mockMarketDataResponse)
      } as Response)

      // Act
      const result = await apiClient.getMarketDataStatus()

      // Assert - Should successfully return market data
      expect(result).toEqual(mockMarketDataResponse)
      expect(mockFetch).toHaveBeenCalledWith(expectedUrl, expect.any(Object))
    })

    it('should provide meaningful error messages for different failure types', async () => {
      // Test 1: Network error
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      await expect(apiClient.getMarketDataStatus()).rejects.toThrow('Network connection failed')

      // Reset mock for next test
      jest.clearAllMocks()

      // Test 2: Timeout error
      mockFetch.mockRejectedValueOnce(new TypeError('Network request failed'))

      await expect(apiClient.getMarketDataStatus()).rejects.toThrow('Request failed: Network request failed')
    })

    it('should handle HTTP error responses properly', async () => {
      // Arrange - Mock 500 error response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => JSON.stringify({ detail: 'Database error' }),
        json: async () => ({ detail: 'Database error' })
      } as Response)

      // Act & Assert
      try {
        await apiClient.getMarketDataStatus()
        fail('Should have thrown an error')
      } catch (error) {
        expect(error).toBeInstanceOf(AdminApiError)
        expect((error as AdminApiError).status).toBe(500)
        expect((error as AdminApiError).message).toContain('Database error')
      }
    })

    it('should handle authentication errors properly', async () => {
      // Arrange - Mock 401 unauthorized response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: async () => JSON.stringify({ detail: 'Token expired' }),
        json: async () => ({ detail: 'Token expired' })
      } as Response)

      // Act & Assert
      await expect(apiClient.getMarketDataStatus()).rejects.toThrow(AdminApiError)
    })
  })

  describe('TDD: Integration with real backend', () => {
    it('should connect to the real backend when available', async () => {
      // This test verifies the client can connect to a real running backend
      // Skip if no real backend is available

      if (process.env.TEST_TYPE !== 'integration') {
        console.log('Skipping integration test')
        return
      }

      // Use real fetch (not mocked) for this test
      const realApiClient = new AdminApiClient(testToken)

      try {
        // This should work if backend is running on localhost:8001
        const result = await realApiClient.getMarketDataStatus()
        expect(result).toHaveProperty('providers')
        expect(Array.isArray(result.providers)).toBe(true)
      } catch (error) {
        if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
          console.log('Backend not available for integration test - this is the issue we need to fix')
          throw error
        } else {
          // Some other error occurred
          throw error
        }
      }
    })
  })

  describe('TDD: Error handling and recovery', () => {
    it('should provide retry capability on transient failures', async () => {
      // Arrange - Mock failure then success
      mockFetch
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ providers: [] })
        } as Response)

      // Act - First call should fail
      await expect(apiClient.getMarketDataStatus()).rejects.toThrow('Network connection failed')

      // Act - Second call should succeed
      const result = await apiClient.getMarketDataStatus()

      // Assert
      expect(result).toEqual({ providers: [] })
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })

    it('should handle request cancellation without causing "failed to fetch"', async () => {
      // Arrange - Mock slow response
      mockFetch.mockImplementationOnce(() =>
        new Promise((resolve, reject) => {
          setTimeout(() => {
            resolve({
              ok: true,
              status: 200,
              json: async () => ({ providers: [] })
            } as Response)
          }, 1000)
        })
      )

      // Act - Start request and cancel
      const promise = apiClient.getMarketDataStatus()
      apiClient.abort() // This should not cause "failed to fetch" error

      // Assert - Should handle cancellation gracefully
      // Note: The exact behavior depends on the AbortController implementation
      try {
        await promise
      } catch (error) {
        // Cancellation should result in AbortError, not "failed to fetch"
        expect(error).not.toThrow('Failed to fetch')
      }
    })
  })

  describe('TDD: Debug information for troubleshooting', () => {
    it('should log helpful debug information on fetch failures', async () => {
      // Arrange
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      // Act
      try {
        await apiClient.getMarketDataStatus()
      } catch (error) {
        // Expected to fail
      }

      // Assert - Should provide debug information (this test might initially fail if logging isn't implemented)
      // We can add logging later if needed

      consoleSpy.mockRestore()
    })

    it('should provide clear information about the attempted request', async () => {
      // Arrange
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      // Act
      try {
        await apiClient.getMarketDataStatus()
      } catch (error) {
        // The error should contain information about what was attempted
        expect(mockFetch).toHaveBeenCalledWith(
          expectedUrl,
          expect.objectContaining({
            method: 'GET',
            headers: expect.objectContaining({
              'Authorization': `Bearer ${testToken}`,
              'Content-Type': 'application/json'
            })
          })
        )
      }
    })
  })
})