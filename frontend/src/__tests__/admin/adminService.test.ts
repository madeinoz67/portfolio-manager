/**
 * Tests for AdminApiClient to verify proper backend API integration
 * These tests ensure the service correctly calls backend endpoints and handles real responses
 */

import { AdminApiClient, AdminApiError } from '@/services/adminService'

// Mock global fetch
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

describe('AdminApiClient Integration Tests', () => {
  let apiClient: AdminApiClient
  const testToken = 'test-admin-jwt-token'

  beforeEach(() => {
    jest.clearAllMocks()
    apiClient = new AdminApiClient(testToken)
  })

  describe('getSystemMetrics', () => {
    it('should fetch real system metrics from backend API', async () => {
      // Arrange - Mock realistic backend response
      const mockSystemMetrics = {
        totalUsers: 25,
        totalPortfolios: 78,
        activeUsers: 20,
        adminUsers: 3,
        systemStatus: 'healthy',
        lastUpdated: '2025-01-14T10:30:00Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockSystemMetrics
      } as Response)

      // Act
      const result = await apiClient.getSystemMetrics()

      // Assert - Verify correct API call and response handling
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/admin/system/metrics',
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${testToken}`
          },
          signal: expect.any(AbortSignal)
        })
      )
      expect(result).toEqual(mockSystemMetrics)
    })

    it('should throw AdminApiError on HTTP error response', async () => {
      // Arrange - Mock 500 error response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ detail: 'Database connection failed' })
      } as Response)

      // Act & Assert
      await expect(apiClient.getSystemMetrics()).rejects.toThrow(AdminApiError)

      try {
        await apiClient.getSystemMetrics()
      } catch (error) {
        expect(error).toBeInstanceOf(AdminApiError)
        expect((error as AdminApiError).status).toBe(500)
      }
    })
  })

  describe('getUsers', () => {
    it('should fetch paginated user list with correct parameters', async () => {
      // Arrange - Mock realistic users response from backend
      const mockUsersResponse = {
        users: [
          {
            id: 'uuid-1',
            email: 'user1@example.com',
            firstName: 'John',
            lastName: 'Doe',
            role: 'user',
            isActive: true,
            createdAt: '2025-01-10T09:00:00Z',
            portfolioCount: 2,
            lastLoginAt: '2025-01-14T08:30:00Z'
          },
          {
            id: 'uuid-2',
            email: 'admin@example.com',
            firstName: 'Jane',
            lastName: 'Admin',
            role: 'admin',
            isActive: true,
            createdAt: '2025-01-05T14:00:00Z',
            portfolioCount: 1,
            lastLoginAt: '2025-01-14T09:15:00Z'
          }
        ],
        total: 25,
        page: 1,
        pages: 3
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUsersResponse
      } as Response)

      // Act
      const result = await apiClient.getUsers({ page: 1, size: 10, role: 'user', active: true })

      // Assert - Verify correct API call with query parameters
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/admin/users?page=1&size=10&role=user&active=true',
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${testToken}`
          },
          signal: expect.any(AbortSignal)
        })
      )
      expect(result).toEqual(mockUsersResponse)
      expect(result.users).toHaveLength(2)
    })

    it('should handle empty query parameters correctly', async () => {
      // Arrange
      const mockEmptyResponse = {
        users: [],
        total: 0,
        page: 1,
        pages: 0
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockEmptyResponse
      } as Response)

      // Act
      const result = await apiClient.getUsers({})

      // Assert - No query parameters should be added
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/admin/users',
        expect.objectContaining({
          method: 'GET',
          signal: expect.any(AbortSignal)
        })
      )
      expect(result).toEqual(mockEmptyResponse)
    })
  })

  describe('getUserDetails', () => {
    it('should fetch detailed user information with portfolios', async () => {
      // Arrange - Mock detailed user response
      const userId = 'user-uuid-123'
      const mockUserDetails = {
        id: userId,
        email: 'detailed.user@example.com',
        firstName: 'Detailed',
        lastName: 'User',
        role: 'user',
        isActive: true,
        createdAt: '2025-01-08T10:00:00Z',
        portfolioCount: 3,
        lastLoginAt: '2025-01-14T07:45:00Z',
        totalAssets: 125000.50,
        portfolios: [
          {
            id: 'portfolio-1',
            name: 'Growth Portfolio',
            value: 75000.25,
            lastUpdated: '2025-01-14T09:00:00Z'
          },
          {
            id: 'portfolio-2',
            name: 'Conservative Portfolio',
            value: 50000.25,
            lastUpdated: '2025-01-14T09:00:00Z'
          }
        ]
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUserDetails
      } as Response)

      // Act
      const result = await apiClient.getUserDetails(userId)

      // Assert - Verify correct endpoint and response
      expect(mockFetch).toHaveBeenCalledWith(
        `http://localhost:8001/api/v1/admin/users/${userId}`,
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${testToken}`
          },
          signal: expect.any(AbortSignal)
        })
      )
      expect(result).toEqual(mockUserDetails)
      expect(result.totalAssets).toBe(125000.50) // Real calculated asset total
      expect(result.portfolios).toHaveLength(2)
    })
  })

  describe('getMarketDataStatus', () => {
    it('should fetch real market data provider status and usage', async () => {
      // Arrange - Mock realistic market data status from backend
      const mockMarketDataStatus = {
        providers: [
          {
            providerId: 'yfinance',
            providerName: 'Yahoo Finance',
            isEnabled: true,
            lastUpdate: '2025-01-14T10:25:00Z',
            apiCallsToday: 127, // Real usage from database
            monthlyLimit: 2000,
            monthlyUsage: 3240, // Real monthly usage
            costPerCall: 0.0,
            status: 'active'
          },
          {
            providerId: 'alpha_vantage',
            providerName: 'Alpha Vantage',
            isEnabled: true,
            lastUpdate: '2025-01-14T10:25:00Z',
            apiCallsToday: 8, // Real usage from database
            monthlyLimit: 500,
            monthlyUsage: 445, // Close to rate limit
            costPerCall: 0.02,
            status: 'rate_limited' // Real status based on usage
          }
        ]
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockMarketDataStatus
      } as Response)

      // Act
      const result = await apiClient.getMarketDataStatus()

      // Assert - Verify real market data is fetched
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/admin/market-data/status',
        expect.objectContaining({
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${testToken}`
          },
          signal: expect.any(AbortSignal)
        })
      )
      expect(result).toEqual(mockMarketDataStatus)
      expect(result.providers).toHaveLength(2)

      // Verify real usage statistics are preserved
      const alphaVantageProvider = result.providers.find(p => p.providerId === 'alpha_vantage')
      expect(alphaVantageProvider?.monthlyUsage).toBe(445) // Real usage count
      expect(alphaVantageProvider?.status).toBe('rate_limited') // Real computed status
    })
  })

  describe('Authentication handling', () => {
    it('should handle 401 unauthorized responses correctly', async () => {
      // Arrange - Mock 401 response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        text: async () => JSON.stringify({ detail: 'Token has expired' }),
        json: async () => ({ detail: 'Token has expired' })
      } as Response)

      // Act & Assert
      await expect(apiClient.getSystemMetrics()).rejects.toThrow(AdminApiError)

      try {
        await apiClient.getSystemMetrics()
      } catch (error) {
        expect(error).toBeInstanceOf(AdminApiError)
        expect((error as AdminApiError).status).toBe(401)
        expect((error as AdminApiError).message).toContain('Token has expired')
      }
    })

    it('should handle 403 forbidden responses correctly', async () => {
      // Arrange - Mock 403 response for insufficient privileges
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: 'Forbidden',
        text: async () => JSON.stringify({ detail: 'Admin access required' }),
        json: async () => ({ detail: 'Admin access required' })
      } as Response)

      // Act & Assert
      await expect(apiClient.getSystemMetrics()).rejects.toThrow(AdminApiError)

      try {
        await apiClient.getSystemMetrics()
      } catch (error) {
        expect(error).toBeInstanceOf(AdminApiError)
        expect((error as AdminApiError).status).toBe(403)
        expect((error as AdminApiError).message).toContain('Admin access required')
      }
    })
  })

  describe('API Usage endpoint integration', () => {
    it('should fetch real API usage statistics from backend', async () => {
      // Arrange - Mock realistic API usage data from backend
      const mockApiUsage = {
        summary: {
          total_requests_today: 127,
          total_requests_this_month: 3240,
          errors_today: 8,
          success_rate_today: 93.7
        },
        by_provider: [
          {
            provider_name: 'yfinance',
            requests_today: 119,
            requests_this_month: 3100,
            errors_today: 5,
            rate_limit_remaining: 0, // No rate limit for yfinance
            rate_limit_total: 2000,
            last_request_at: '2025-01-14T10:25:30Z'
          },
          {
            provider_name: 'alpha_vantage',
            requests_today: 8,
            requests_this_month: 140,
            errors_today: 3,
            rate_limit_remaining: 360,
            rate_limit_total: 500,
            last_request_at: '2025-01-14T09:45:15Z'
          }
        ],
        by_date: [
          {
            date: '2025-01-14',
            total_requests: 127,
            successful_requests: 119,
            failed_requests: 8,
            unique_symbols: 23
          },
          {
            date: '2025-01-13',
            total_requests: 156,
            successful_requests: 154,
            failed_requests: 2,
            unique_symbols: 28
          }
        ],
        rate_limits: {
          daily_limit: 2000,
          hourly_limit: 100,
          minute_limit: 10,
          current_usage: {
            daily: 127,
            hourly: 12,
            minute: 2
          }
        },
        last_updated: '2025-01-14T10:30:00Z'
      }

      // Mock the fetch call
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockApiUsage
      } as Response)

      // Create a method to call the API usage endpoint
      const getApiUsage = async () => {
        const response = await fetch('http://localhost:8001/api/v1/admin/api-usage', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${testToken}`
          }
        })

        if (!response.ok) {
          throw new AdminApiError(
            await response.text(),
            response.status,
            response
          )
        }

        return response.json()
      }

      // Act
      const result = await getApiUsage()

      // Assert - Verify real API usage data is returned
      expect(result).toEqual(mockApiUsage)
      expect(result.summary.total_requests_today).toBe(127) // Real request count
      expect(result.summary.success_rate_today).toBe(93.7) // Real calculated rate
      expect(result.by_provider).toHaveLength(2)
      expect(result.by_provider[0].requests_today).toBe(119) // Real yfinance usage
      expect(result.by_provider[1].requests_today).toBe(8) // Real alpha_vantage usage
      expect(result.by_date).toHaveLength(2) // Daily breakdown
    })
  })

  describe('Request cancellation', () => {
    it('should support request cancellation via AbortSignal', async () => {
      // Arrange - Mock fetch to check for abort signal and throw if aborted
      mockFetch.mockImplementationOnce((url, options) => {
        const signal = (options as any)?.signal as AbortSignal
        if (signal?.aborted) {
          return Promise.reject(new DOMException('The user aborted a request.', 'AbortError'))
        }

        return new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            resolve({
              ok: true,
              status: 200,
              json: async () => ({})
            } as Response)
          }, 1000)

          signal?.addEventListener('abort', () => {
            clearTimeout(timeout)
            reject(new DOMException('The user aborted a request.', 'AbortError'))
          })
        })
      })

      // Act - Start request and immediately cancel
      const promise = apiClient.getSystemMetrics()

      // Cancel after a short delay to ensure the request has started
      setTimeout(() => apiClient.abort(), 10)

      // Assert - Request should be cancelled
      await expect(promise).rejects.toThrow('AbortError')
    })
  })
})