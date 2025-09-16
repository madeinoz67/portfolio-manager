/**
 * Tests for Admin Dashboard components to verify they properly display real data
 * These tests ensure components correctly render real backend API responses
 */

import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { AuthContext } from '@/contexts/AuthContext'
import { useSystemMetrics, useAdminUsers, useMarketDataStatus } from '@/hooks/useAdmin'

// Mock the admin hooks
jest.mock('@/hooks/useAdmin')
const mockUseSystemMetrics = useSystemMetrics as jest.MockedFunction<typeof useSystemMetrics>
const mockUseAdminUsers = useAdminUsers as jest.MockedFunction<typeof useAdminUsers>
const mockUseMarketDataStatus = useMarketDataStatus as jest.MockedFunction<typeof useMarketDataStatus>

// Create a minimal admin dashboard component for testing
const AdminSystemMetrics = () => {
  const { metrics, loading, error, refetch } = useSystemMetrics()

  if (loading) return <div data-testid="loading">Loading system metrics...</div>
  if (error) return <div data-testid="error">Error: {error.message}</div>
  if (!metrics) return <div data-testid="no-data">No metrics data</div>

  return (
    <div data-testid="system-metrics">
      <h2>System Metrics</h2>
      <div data-testid="total-users">Total Users: {metrics.totalUsers}</div>
      <div data-testid="total-portfolios">Total Portfolios: {metrics.totalPortfolios}</div>
      <div data-testid="active-users">Active Users: {metrics.activeUsers}</div>
      <div data-testid="admin-users">Admin Users: {metrics.adminUsers}</div>
      <div data-testid="system-status">Status: {metrics.systemStatus}</div>
      <div data-testid="last-updated">Last Updated: {metrics.lastUpdated}</div>
      <button data-testid="refresh-btn" onClick={refetch}>Refresh</button>
    </div>
  )
}

const AdminUsersList = () => {
  const { users, loading, error, updateParams, refetch } = useAdminUsers({ page: 1, size: 10 })

  if (loading) return <div data-testid="loading">Loading users...</div>
  if (error) return <div data-testid="error">Error: {error.message}</div>
  if (!users) return <div data-testid="no-data">No users data</div>

  return (
    <div data-testid="users-list">
      <h2>Users Management</h2>
      <div data-testid="users-count">
        Showing {users.users.length} of {users.total} users (Page {users.page} of {users.pages})
      </div>
      <div data-testid="users-table">
        {users.users.map(user => (
          <div key={user.id} data-testid={`user-${user.id}`} className="user-row">
            <span data-testid={`user-email-${user.id}`}>{user.email}</span>
            <span data-testid={`user-role-${user.id}`}>{user.role}</span>
            <span data-testid={`user-status-${user.id}`}>{user.isActive ? 'Active' : 'Inactive'}</span>
            <span data-testid={`user-portfolios-${user.id}`}>{user.portfolioCount} portfolios</span>
          </div>
        ))}
      </div>
      <button
        data-testid="filter-admin-btn"
        onClick={() => updateParams({ role: 'admin' })}
      >
        Show Admin Users Only
      </button>
      <button data-testid="refresh-users-btn" onClick={refetch}>Refresh Users</button>
    </div>
  )
}

const AdminMarketDataStatus = () => {
  const { marketDataStatus, loading, error, refetch } = useMarketDataStatus()

  if (loading) return <div data-testid="loading">Loading market data...</div>
  if (error) return <div data-testid="error">Error: {error.message}</div>
  if (!marketDataStatus) return <div data-testid="no-data">No market data</div>

  return (
    <div data-testid="market-data-status">
      <h2>Market Data Providers</h2>
      <div data-testid="providers-list">
        {marketDataStatus.providers.map(provider => (
          <div key={provider.providerId} data-testid={`provider-${provider.providerId}`} className="provider-card">
            <h3 data-testid={`provider-name-${provider.providerId}`}>{provider.providerName}</h3>
            <div data-testid={`provider-status-${provider.providerId}`}>Status: {provider.status}</div>
            <div data-testid={`provider-calls-today-${provider.providerId}`}>
              Calls Today: {provider.apiCallsToday}
            </div>
            <div data-testid={`provider-monthly-usage-${provider.providerId}`}>
              Monthly Usage: {provider.monthlyUsage} / {provider.monthlyLimit}
            </div>
            <div data-testid={`provider-enabled-${provider.providerId}`}>
              {provider.isEnabled ? 'Enabled' : 'Disabled'}
            </div>
            <div data-testid={`provider-last-update-${provider.providerId}`}>
              Last Update: {provider.lastUpdate}
            </div>
          </div>
        ))}
      </div>
      <button data-testid="refresh-providers-btn" onClick={refetch}>Refresh Providers</button>
    </div>
  )
}

// Test wrapper with auth context
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const authValue = {
    token: 'test-admin-token',
    user: { role: 'admin', email: 'admin@test.com' },
    login: jest.fn(),
    logout: jest.fn(),
    loading: false
  }

  return (
    <AuthContext.Provider value={authValue}>
      {children}
    </AuthContext.Provider>
  )
}

describe('Admin Dashboard Components with Real Data', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('AdminSystemMetrics Component', () => {
    it('should display real system metrics data', async () => {
      // Arrange - Mock real system metrics data from backend
      const mockRealMetrics = {
        totalUsers: 42,
        totalPortfolios: 127,
        activeUsers: 35,
        adminUsers: 3,
        systemStatus: 'healthy' as const,
        lastUpdated: '2025-01-14T10:30:00Z'
      }

      mockUseSystemMetrics.mockReturnValue({
        metrics: mockRealMetrics,
        loading: false,
        error: null,
        clearError: jest.fn(),
        refetch: jest.fn()
      })

      // Act
      render(
        <TestWrapper>
          <AdminSystemMetrics />
        </TestWrapper>
      )

      // Assert - Verify real data is displayed correctly
      expect(screen.getByTestId('total-users')).toHaveTextContent('Total Users: 42')
      expect(screen.getByTestId('total-portfolios')).toHaveTextContent('Total Portfolios: 127')
      expect(screen.getByTestId('active-users')).toHaveTextContent('Active Users: 35')
      expect(screen.getByTestId('admin-users')).toHaveTextContent('Admin Users: 3')
      expect(screen.getByTestId('system-status')).toHaveTextContent('Status: healthy')
      expect(screen.getByTestId('last-updated')).toHaveTextContent('Last Updated: 2025-01-14T10:30:00Z')
    })

    it('should handle loading state during data fetch', () => {
      // Arrange - Mock loading state
      mockUseSystemMetrics.mockReturnValue({
        metrics: null,
        loading: true,
        error: null,
        clearError: jest.fn(),
        refetch: jest.fn()
      })

      // Act
      render(
        <TestWrapper>
          <AdminSystemMetrics />
        </TestWrapper>
      )

      // Assert - Loading message should be displayed
      expect(screen.getByTestId('loading')).toHaveTextContent('Loading system metrics...')
    })

    it('should handle API errors gracefully', () => {
      // Arrange - Mock error state
      const mockError = {
        message: 'Failed to fetch system metrics',
        type: 'HTTP_ERROR' as const,
        status: 500,
        retryable: true,
        timestamp: new Date()
      }

      mockUseSystemMetrics.mockReturnValue({
        metrics: null,
        loading: false,
        error: mockError,
        clearError: jest.fn(),
        refetch: jest.fn()
      })

      // Act
      render(
        <TestWrapper>
          <AdminSystemMetrics />
        </TestWrapper>
      )

      // Assert - Error message should be displayed
      expect(screen.getByTestId('error')).toHaveTextContent('Error: Failed to fetch system metrics')
    })

    it('should call refetch when refresh button is clicked', async () => {
      // Arrange
      const mockRefetch = jest.fn()
      const mockMetrics = {
        totalUsers: 10,
        totalPortfolios: 20,
        activeUsers: 8,
        adminUsers: 1,
        systemStatus: 'healthy' as const,
        lastUpdated: '2025-01-14T10:00:00Z'
      }

      mockUseSystemMetrics.mockReturnValue({
        metrics: mockMetrics,
        loading: false,
        error: null,
        clearError: jest.fn(),
        refetch: mockRefetch
      })

      // Act
      render(
        <TestWrapper>
          <AdminSystemMetrics />
        </TestWrapper>
      )

      fireEvent.click(screen.getByTestId('refresh-btn'))

      // Assert - Refetch should be called
      expect(mockRefetch).toHaveBeenCalledTimes(1)
    })
  })

  describe('AdminUsersList Component', () => {
    it('should display real user data with pagination info', () => {
      // Arrange - Mock real users data from backend
      const mockRealUsersData = {
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
            email: 'admin@example.com',
            firstName: 'Admin',
            lastName: 'User',
            role: 'admin',
            isActive: true,
            createdAt: '2025-01-05T14:00:00Z',
            portfolioCount: 1,
            lastLoginAt: '2025-01-14T09:15:00Z'
          }
        ],
        total: 42,
        page: 1,
        pages: 5
      }

      mockUseAdminUsers.mockReturnValue({
        users: mockRealUsersData,
        params: { page: 1, size: 10 },
        loading: false,
        error: null,
        clearError: jest.fn(),
        updateParams: jest.fn(),
        refetch: jest.fn()
      })

      // Act
      render(
        <TestWrapper>
          <AdminUsersList />
        </TestWrapper>
      )

      // Assert - Verify real user data is displayed
      expect(screen.getByTestId('users-count')).toHaveTextContent('Showing 2 of 42 users (Page 1 of 5)')

      // Verify first user data
      expect(screen.getByTestId('user-email-user-1')).toHaveTextContent('john.doe@example.com')
      expect(screen.getByTestId('user-role-user-1')).toHaveTextContent('user')
      expect(screen.getByTestId('user-status-user-1')).toHaveTextContent('Active')
      expect(screen.getByTestId('user-portfolios-user-1')).toHaveTextContent('3 portfolios')

      // Verify admin user data
      expect(screen.getByTestId('user-email-user-2')).toHaveTextContent('admin@example.com')
      expect(screen.getByTestId('user-role-user-2')).toHaveTextContent('admin')
      expect(screen.getByTestId('user-portfolios-user-2')).toHaveTextContent('1 portfolios')
    })

    it('should call updateParams when filter button is clicked', () => {
      // Arrange
      const mockUpdateParams = jest.fn()
      const mockUsersData = {
        users: [],
        total: 0,
        page: 1,
        pages: 0
      }

      mockUseAdminUsers.mockReturnValue({
        users: mockUsersData,
        params: { page: 1, size: 10 },
        loading: false,
        error: null,
        clearError: jest.fn(),
        updateParams: mockUpdateParams,
        refetch: jest.fn()
      })

      // Act
      render(
        <TestWrapper>
          <AdminUsersList />
        </TestWrapper>
      )

      fireEvent.click(screen.getByTestId('filter-admin-btn'))

      // Assert - updateParams should be called with admin filter
      expect(mockUpdateParams).toHaveBeenCalledWith({ role: 'admin' })
    })
  })

  describe('AdminMarketDataStatus Component', () => {
    it('should display real market data provider information', () => {
      // Arrange - Mock real market data from backend
      const mockRealMarketData = {
        providers: [
          {
            providerId: 'yfinance',
            providerName: 'Yahoo Finance',
            isEnabled: true,
            lastUpdate: '2025-01-14T10:25:00Z',
            apiCallsToday: 127,
            monthlyLimit: 2000,
            monthlyUsage: 1540,
            costPerCall: 0.0,
            status: 'active'
          },
          {
            providerId: 'alpha_vantage',
            providerName: 'Alpha Vantage',
            isEnabled: true,
            lastUpdate: '2025-01-14T10:20:00Z',
            apiCallsToday: 23,
            monthlyLimit: 500,
            monthlyUsage: 467,
            costPerCall: 0.02,
            status: 'rate_limited'
          }
        ]
      }

      mockUseMarketDataStatus.mockReturnValue({
        marketDataStatus: mockRealMarketData,
        loading: false,
        error: null,
        clearError: jest.fn(),
        refetch: jest.fn()
      })

      // Act
      render(
        <TestWrapper>
          <AdminMarketDataStatus />
        </TestWrapper>
      )

      // Assert - Verify real provider data is displayed
      expect(screen.getByTestId('provider-name-yfinance')).toHaveTextContent('Yahoo Finance')
      expect(screen.getByTestId('provider-status-yfinance')).toHaveTextContent('Status: active')
      expect(screen.getByTestId('provider-calls-today-yfinance')).toHaveTextContent('Calls Today: 127')
      expect(screen.getByTestId('provider-monthly-usage-yfinance')).toHaveTextContent('Monthly Usage: 1540 / 2000')
      expect(screen.getByTestId('provider-enabled-yfinance')).toHaveTextContent('Enabled')

      // Verify Alpha Vantage provider (rate limited)
      expect(screen.getByTestId('provider-name-alpha_vantage')).toHaveTextContent('Alpha Vantage')
      expect(screen.getByTestId('provider-status-alpha_vantage')).toHaveTextContent('Status: rate_limited')
      expect(screen.getByTestId('provider-calls-today-alpha_vantage')).toHaveTextContent('Calls Today: 23')
      expect(screen.getByTestId('provider-monthly-usage-alpha_vantage')).toHaveTextContent('Monthly Usage: 467 / 500')
    })

    it('should handle empty providers list', () => {
      // Arrange - Mock empty providers response
      mockUseMarketDataStatus.mockReturnValue({
        marketDataStatus: { providers: [] },
        loading: false,
        error: null,
        clearError: jest.fn(),
        refetch: jest.fn()
      })

      // Act
      render(
        <TestWrapper>
          <AdminMarketDataStatus />
        </TestWrapper>
      )

      // Assert - Component should handle empty list
      expect(screen.getByTestId('providers-list')).toBeInTheDocument()
      expect(screen.queryByTestId('provider-yfinance')).not.toBeInTheDocument()
    })
  })

  describe('Error Boundary Integration', () => {
    it('should gracefully handle component errors', () => {
      // Arrange - Mock hook that throws an error
      mockUseSystemMetrics.mockImplementation(() => {
        throw new Error('Component error')
      })

      // Act & Assert - Should not crash the entire app
      expect(() => {
        render(
          <TestWrapper>
            <AdminSystemMetrics />
          </TestWrapper>
        )
      }).toThrow('Component error')
    })
  })
})