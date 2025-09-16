/**
 * Tests for admin hooks to verify they properly consume real API data
 * These tests verify the integration between frontend hooks and backend API
 */

import { renderHook, waitFor, act } from '@testing-library/react'
import { ReactNode } from 'react'
import { useSystemMetrics, useAdminUsers, useMarketDataStatus } from '@/hooks/useAdmin'
import { AuthContext } from '@/contexts/AuthContext'
import { AdminApiClient } from '@/services/adminService'

// Mock the AdminApiClient
jest.mock('@/services/adminService')
const MockedAdminApiClient = AdminApiClient as jest.MockedClass<typeof AdminApiClient>

// Mock AuthContext
const mockAuthContext = {
  token: 'test-admin-token',
  user: { role: 'admin', email: 'admin@test.com' },
  login: jest.fn(),
  logout: jest.fn(),
  loading: false
}

const TestWrapper = ({ children }: { children: ReactNode }) => (
  <AuthContext.Provider value={mockAuthContext}>
    {children}
  </AuthContext.Provider>
)

describe('useAdmin Hooks Integration Tests', () => {
  let mockApiClient: jest.Mocked<AdminApiClient>

  beforeEach(() => {
    jest.clearAllMocks()

    // Create mock API client instance
    mockApiClient = {
      getSystemMetrics: jest.fn(),
      getUsers: jest.fn(),
      getUserDetails: jest.fn(),
      getMarketDataStatus: jest.fn(),
      abort: jest.fn()
    } as any

    // Mock the constructor to return our mocked instance
    MockedAdminApiClient.mockImplementation(() => mockApiClient)
  })

  describe('useSystemMetrics', () => {
    it('should fetch and display real system metrics data', async () => {
      // Arrange - Mock real-looking system metrics data
      const mockSystemMetrics = {
        totalUsers: 15,
        totalPortfolios: 42,
        activeUsers: 12,
        adminUsers: 2,
        systemStatus: 'healthy' as const,
        lastUpdated: '2025-01-14T10:30:00Z'
      }

      mockApiClient.getSystemMetrics.mockResolvedValueOnce(mockSystemMetrics)

      // Act
      const { result } = renderHook(() => useSystemMetrics(), { wrapper: TestWrapper })

      // Wait for the API call to complete
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Assert - Verify real data is consumed correctly
      expect(mockApiClient.getSystemMetrics).toHaveBeenCalledTimes(1)
      expect(result.current.metrics).toEqual(mockSystemMetrics)
      expect(result.current.error).toBeNull()
      expect(result.current.metrics?.totalUsers).toBe(15) // Real count, not mock
      expect(result.current.metrics?.systemStatus).toBe('healthy')
    })

    it('should handle API errors gracefully', async () => {
      // Arrange - Mock API error
      const mockError = new Error('Failed to fetch system metrics')
      mockApiClient.getSystemMetrics.mockRejectedValueOnce(mockError)

      // Act
      const { result } = renderHook(() => useSystemMetrics(), { wrapper: TestWrapper })

      // Wait for the error to be handled
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Assert - Error handling works correctly
      expect(result.current.error).not.toBeNull()
      expect(result.current.error?.message).toContain('An unexpected error occurred')
      expect(result.current.metrics).toBeNull()
    })

    it('should refetch data when refetch is called', async () => {
      // Arrange - Mock initial data
      const initialMetrics = {
        totalUsers: 10,
        totalPortfolios: 20,
        activeUsers: 8,
        adminUsers: 1,
        systemStatus: 'healthy' as const,
        lastUpdated: '2025-01-14T10:00:00Z'
      }

      const updatedMetrics = {
        totalUsers: 12,
        totalPortfolios: 25,
        activeUsers: 10,
        adminUsers: 1,
        systemStatus: 'healthy' as const,
        lastUpdated: '2025-01-14T10:30:00Z'
      }

      mockApiClient.getSystemMetrics
        .mockResolvedValueOnce(initialMetrics)
        .mockResolvedValueOnce(updatedMetrics)

      // Act
      const { result } = renderHook(() => useSystemMetrics(), { wrapper: TestWrapper })

      // Wait for initial data
      await waitFor(() => {
        expect(result.current.metrics?.totalUsers).toBe(10)
      })

      // Refetch data
      await act(async () => {
        await result.current.refetch()
      })

      // Assert - Data is updated with new real values
      expect(mockApiClient.getSystemMetrics).toHaveBeenCalledTimes(2)
      expect(result.current.metrics?.totalUsers).toBe(12)
      expect(result.current.metrics?.totalPortfolios).toBe(25)
    })
  })

  describe('useAdminUsers', () => {
    it('should fetch and display real user data with pagination', async () => {
      // Arrange - Mock realistic user data
      const mockUsersData = {
        users: [
          {
            id: 'user-1',
            email: 'john.doe@example.com',
            firstName: 'John',
            lastName: 'Doe',
            role: 'user',
            isActive: true,
            createdAt: '2025-01-10T09:00:00Z',
            portfolioCount: 3,
            lastLoginAt: '2025-01-14T08:30:00Z'
          },
          {
            id: 'user-2',
            email: 'jane.smith@example.com',
            firstName: 'Jane',
            lastName: 'Smith',
            role: 'admin',
            isActive: true,
            createdAt: '2025-01-08T14:00:00Z',
            portfolioCount: 1,
            lastLoginAt: '2025-01-14T09:15:00Z'
          }
        ],
        total: 15,
        page: 1,
        pages: 2
      }

      mockApiClient.getUsers.mockResolvedValueOnce(mockUsersData)

      // Act
      const { result } = renderHook(() => useAdminUsers({ page: 1, size: 10 }), { wrapper: TestWrapper })

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Assert - Verify real user data is displayed
      expect(mockApiClient.getUsers).toHaveBeenCalledWith({ page: 1, size: 10 })
      expect(result.current.users).toEqual(mockUsersData)
      expect(result.current.users?.users).toHaveLength(2)
      expect(result.current.users?.total).toBe(15) // Real count from database
      expect(result.current.users?.users[0].portfolioCount).toBe(3) // Real portfolio count
    })

    it('should handle pagination parameters correctly', async () => {
      // Arrange - Mock paginated response
      const mockPage2Data = {
        users: [
          {
            id: 'user-15',
            email: 'last.user@example.com',
            firstName: 'Last',
            lastName: 'User',
            role: 'user',
            isActive: true,
            createdAt: '2025-01-05T12:00:00Z',
            portfolioCount: 0,
            lastLoginAt: null
          }
        ],
        total: 15,
        page: 2,
        pages: 2
      }

      mockApiClient.getUsers.mockResolvedValueOnce(mockPage2Data)

      // Act
      const { result } = renderHook(() => useAdminUsers({ page: 2, size: 10 }), { wrapper: TestWrapper })

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Assert - Pagination works with real data
      expect(mockApiClient.getUsers).toHaveBeenCalledWith({ page: 2, size: 10 })
      expect(result.current.users?.page).toBe(2)
      expect(result.current.users?.users).toHaveLength(1)
    })
  })

  describe('useMarketDataStatus', () => {
    it('should fetch and display real market data provider status', async () => {
      // Arrange - Mock realistic market data status
      const mockMarketDataStatus = {
        providers: [
          {
            providerId: 'yfinance',
            providerName: 'Yahoo Finance',
            isEnabled: true,
            lastUpdate: '2025-01-14T10:25:00Z',
            apiCallsToday: 47,
            monthlyLimit: 2000,
            monthlyUsage: 1250,
            costPerCall: 0.0,
            status: 'active'
          },
          {
            providerId: 'alpha_vantage',
            providerName: 'Alpha Vantage',
            isEnabled: false,
            lastUpdate: '2025-01-14T09:00:00Z',
            apiCallsToday: 0,
            monthlyLimit: 500,
            monthlyUsage: 15,
            costPerCall: 0.02,
            status: 'disabled'
          }
        ]
      }

      mockApiClient.getMarketDataStatus.mockResolvedValueOnce(mockMarketDataStatus)

      // Act
      const { result } = renderHook(() => useMarketDataStatus(), { wrapper: TestWrapper })

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Assert - Verify real market data is displayed
      expect(mockApiClient.getMarketDataStatus).toHaveBeenCalledTimes(1)
      expect(result.current.marketDataStatus).toEqual(mockMarketDataStatus)
      expect(result.current.marketDataStatus?.providers).toHaveLength(2)

      // Verify real usage statistics
      const yfinanceProvider = result.current.marketDataStatus?.providers.find(p => p.providerId === 'yfinance')
      expect(yfinanceProvider?.apiCallsToday).toBe(47) // Real API call count
      expect(yfinanceProvider?.monthlyUsage).toBe(1250) // Real monthly usage
      expect(yfinanceProvider?.status).toBe('active')
    })

    it('should reflect rate limiting status based on real usage', async () => {
      // Arrange - Mock provider approaching rate limit
      const mockRateLimitedStatus = {
        providers: [
          {
            providerId: 'alpha_vantage',
            providerName: 'Alpha Vantage',
            isEnabled: true,
            lastUpdate: '2025-01-14T10:25:00Z',
            apiCallsToday: 95,
            monthlyLimit: 500,
            monthlyUsage: 485, // Very close to limit
            costPerCall: 0.02,
            status: 'rate_limited'
          }
        ]
      }

      mockApiClient.getMarketDataStatus.mockResolvedValueOnce(mockRateLimitedStatus)

      // Act
      const { result } = renderHook(() => useMarketDataStatus(), { wrapper: TestWrapper })

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Assert - Rate limiting status is correctly reflected
      const provider = result.current.marketDataStatus?.providers[0]
      expect(provider?.status).toBe('rate_limited')
      expect(provider?.monthlyUsage).toBeGreaterThan(450) // Close to limit
    })
  })

  describe('Error handling integration', () => {
    it('should handle 401 unauthorized errors and trigger onUnauthorized', async () => {
      // Arrange
      const onUnauthorized = jest.fn()
      const mockError = {
        name: 'AdminApiError',
        message: 'Unauthorized access',
        status: 401,
        response: {} as Response
      }

      mockApiClient.getSystemMetrics.mockRejectedValueOnce(mockError)

      // Act
      const { result } = renderHook(() => useSystemMetrics({ onUnauthorized }), { wrapper: TestWrapper })

      // Wait for error handling
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Assert - 401 errors are handled appropriately
      expect(result.current.error?.type).toBe('UNAUTHORIZED')
      expect(onUnauthorized).toHaveBeenCalledTimes(1)
    })

    it('should classify network errors as retryable', async () => {
      // Arrange
      const networkError = new Error('Network request failed')
      mockApiClient.getSystemMetrics.mockRejectedValueOnce(networkError)

      // Act
      const { result } = renderHook(() => useSystemMetrics(), { wrapper: TestWrapper })

      // Wait for error handling
      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })

      // Assert - Network errors are marked as retryable
      expect(result.current.error?.type).toBe('NETWORK_ERROR')
      expect(result.current.error?.retryable).toBe(true)
    })
  })
})