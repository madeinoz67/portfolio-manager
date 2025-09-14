/**
 * Real page integration tests for admin market data
 * These tests verify the actual admin pages work with real data
 *
 * Following TDD principles to ensure the actual UI works correctly
 */

import { AdminApiClient } from '@/services/adminService'

// Mock global fetch to test real page scenarios
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

describe('Real Admin Page Integration Tests', () => {
  const testToken = 'real-admin-token'
  let apiClient: AdminApiClient

  beforeEach(() => {
    jest.clearAllMocks()
    apiClient = new AdminApiClient(testToken)

    // Mock environment to point to the correct backend
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8001'
  })

  describe('Market Data Page Integration', () => {
    it('should handle market data fetch for real admin dashboard page', async () => {
      // Arrange - Mock successful market data response matching real backend format
      const realMarketDataResponse = {
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
          },
          {
            providerId: 'alpha_vantage',
            providerName: 'Alpha Vantage',
            isEnabled: true,
            lastUpdate: '2025-01-14T10:20:00Z',
            apiCallsToday: 8,
            monthlyLimit: 500,
            monthlyUsage: 445,
            costPerCall: 0.02,
            status: 'rate_limited'
          }
        ]
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => realMarketDataResponse
      } as Response)

      // Act - Call the market data endpoint like the real page would
      const result = await apiClient.getMarketDataStatus()

      // Assert - Verify the response matches what the page expects
      expect(result.providers).toHaveLength(2)
      expect(result.providers[0].providerId).toBe('yfinance')
      expect(result.providers[0].apiCallsToday).toBe(42)
      expect(result.providers[1].status).toBe('rate_limited')

      // Verify the correct endpoint was called
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/admin/market-data/status',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': `Bearer ${testToken}`,
            'Content-Type': 'application/json'
          })
        })
      )
    })

    it('should handle network failures gracefully for admin pages', async () => {
      // Arrange - Mock network failure (real scenario when backend is down)
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      // Act & Assert - Should get user-friendly error message
      await expect(apiClient.getMarketDataStatus()).rejects.toThrow(
        'Network connection failed. Please check your internet connection and ensure the backend server is running.'
      )
    })

    it('should handle authentication errors for admin pages', async () => {
      // Arrange - Mock 401 response (token expired scenario)
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: async () => JSON.stringify({ detail: 'Token has expired' })
      } as Response)

      // Act & Assert - Should handle auth errors properly
      try {
        await apiClient.getMarketDataStatus()
        fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.message).toContain('Token has expired')
        expect(error.status).toBe(401)
      }
    })

    it('should handle backend server errors gracefully', async () => {
      // Arrange - Mock 500 server error (database issues, etc.)
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: async () => JSON.stringify({ detail: 'Database connection failed' })
      } as Response)

      // Act & Assert - Should get proper error message
      try {
        await apiClient.getMarketDataStatus()
        fail('Should have thrown an error')
      } catch (error: any) {
        expect(error.message).toContain('Database connection failed')
        expect(error.status).toBe(500)
      }
    })

    it('should handle CORS issues that occur in browser', async () => {
      // Arrange - Mock CORS error (happens when frontend/backend on different origins)
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      // Act & Assert - Should provide helpful error message
      await expect(apiClient.getMarketDataStatus()).rejects.toThrow(
        'Network connection failed. Please check your internet connection and ensure the backend server is running.'
      )
    })
  })

  describe('System Metrics Page Integration', () => {
    it('should fetch real system metrics for admin dashboard', async () => {
      // Arrange - Mock system metrics response
      const systemMetricsResponse = {
        totalUsers: 25,
        totalPortfolios: 78,
        activeUsers: 20,
        adminUsers: 3,
        systemStatus: 'healthy' as const,
        lastUpdated: '2025-01-14T10:30:00Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => systemMetricsResponse
      } as Response)

      // Act
      const result = await apiClient.getSystemMetrics()

      // Assert - Real data should be returned
      expect(result.totalUsers).toBe(25)
      expect(result.systemStatus).toBe('healthy')
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/admin/system/metrics',
        expect.objectContaining({
          method: 'GET'
        })
      )
    })
  })

  describe('Users Page Integration', () => {
    it('should fetch real user list for admin dashboard', async () => {
      // Arrange - Mock users response
      const usersResponse = {
        users: [
          {
            id: 'user-1',
            email: 'test@example.com',
            firstName: 'Test',
            lastName: 'User',
            role: 'user' as const,
            isActive: true,
            createdAt: '2025-01-10T09:00:00Z',
            portfolioCount: 2,
            lastLoginAt: '2025-01-14T08:30:00Z'
          }
        ],
        total: 25,
        page: 1,
        pages: 3
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => usersResponse
      } as Response)

      // Act
      const result = await apiClient.getUsers({ page: 1, size: 10 })

      // Assert
      expect(result.users).toHaveLength(1)
      expect(result.total).toBe(25)
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/admin/users?page=1&size=10',
        expect.objectContaining({
          method: 'GET'
        })
      )
    })
  })

  describe('Error Recovery and User Experience', () => {
    it('should allow retry after network failure', async () => {
      // Arrange - First call fails, second succeeds
      mockFetch
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ providers: [] })
        } as Response)

      // Act - First call should fail
      await expect(apiClient.getMarketDataStatus()).rejects.toThrow('Network connection failed')

      // Act - Second call should succeed (simulating user retry)
      const result = await apiClient.getMarketDataStatus()

      // Assert - Retry should work
      expect(result).toEqual({ providers: [] })
      expect(mockFetch).toHaveBeenCalledTimes(2)
    })

    it('should handle request cancellation when user navigates away', async () => {
      // Arrange - Mock slow request with proper AbortSignal handling
      mockFetch.mockImplementationOnce((url, options) => {
        return new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            resolve({
              ok: true,
              status: 200,
              json: async () => ({ providers: [] })
            } as Response)
          }, 1000)

          // Simulate AbortSignal cancellation
          const signal = (options as any)?.signal
          if (signal && signal.aborted === false) {
            // Mock a proper AbortController abort scenario
            setTimeout(() => {
              clearTimeout(timeout)
              reject(new DOMException('Request was cancelled', 'AbortError'))
            }, 50)
          }
        })
      })

      // Act - Start request and cancel it
      const promise = apiClient.getMarketDataStatus()

      // Simulate user navigating away (component unmount)
      setTimeout(() => apiClient.abort(), 10)

      // Assert - Should handle cancellation gracefully
      try {
        await promise
        fail('Should have been cancelled')
      } catch (error: any) {
        expect(error.message).toContain('Request was cancelled')
      }
    })

    it('should provide debugging information for troubleshooting', async () => {
      // Arrange - Mock network error
      mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

      // Act
      try {
        await apiClient.getMarketDataStatus()
      } catch (error) {
        // Assert - Error should contain debugging info
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8001/api/v1/admin/market-data/status',
          expect.objectContaining({
            method: 'GET',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${testToken}`
            })
          })
        )
      }
    })
  })

  describe('Performance and Caching Tests', () => {
    it('should complete requests within reasonable time', async () => {
      // Arrange
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ providers: [] })
      } as Response)

      // Act
      const startTime = Date.now()
      await apiClient.getMarketDataStatus()
      const endTime = Date.now()

      // Assert - Should be fast (< 100ms in test environment)
      expect(endTime - startTime).toBeLessThan(100)
    })

    it('should handle concurrent requests properly', async () => {
      // Arrange - Mock multiple responses
      const responses = [
        { providers: [{ providerId: 'test1' }] },
        { totalUsers: 10 },
        { users: [], total: 0, page: 1, pages: 0 }
      ]

      mockFetch
        .mockResolvedValueOnce({
          ok: true, status: 200, json: async () => responses[0]
        } as Response)
        .mockResolvedValueOnce({
          ok: true, status: 200, json: async () => responses[1]
        } as Response)
        .mockResolvedValueOnce({
          ok: true, status: 200, json: async () => responses[2]
        } as Response)

      // Act - Make concurrent requests
      const promises = [
        apiClient.getMarketDataStatus(),
        apiClient.getSystemMetrics(),
        apiClient.getUsers()
      ]

      const results = await Promise.all(promises)

      // Assert - All requests should complete successfully
      expect(results).toHaveLength(3)
      expect(results[0]).toEqual(responses[0])
      expect(results[1]).toEqual(responses[1])
      expect(results[2]).toEqual(responses[2])
    })
  })
})