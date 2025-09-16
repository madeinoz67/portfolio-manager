/**
 * End-to-end integration tests for admin dashboard
 * These tests call the real backend APIs to verify frontend-backend integration
 *
 * Note: These tests require the backend server to be running
 * Run with: npm run test:integration
 */

import { AdminApiClient } from '@/services/adminService'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

// Skip integration tests if not in integration test mode
const runIntegrationTests = process.env.NODE_ENV === 'test' && process.env.TEST_TYPE === 'integration'

describe('Admin Dashboard Integration Tests', () => {
  let adminApiClient: AdminApiClient
  let adminToken: string

  beforeAll(async () => {
    if (!runIntegrationTests) {
      console.log('Skipping integration tests. Set TEST_TYPE=integration to run.')
      return
    }

    // Authenticate as admin user to get real token
    const authResponse = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'admin@test.com',
        password: 'admin123'
      })
    })

    if (!authResponse.ok) {
      throw new Error('Failed to authenticate admin user for integration tests')
    }

    const authData = await authResponse.json()
    adminToken = authData.access_token
    adminApiClient = new AdminApiClient(adminToken)
  })

  // Skip all tests if not in integration mode
  beforeEach(() => {
    if (!runIntegrationTests) {
      console.log('Skipping integration test')
      return
    }
  })

  describe('System Metrics Integration', () => {
    it('should fetch real system metrics from running backend', async () => {
      // Act - Call real backend API
      const metrics = await adminApiClient.getSystemMetrics()

      // Assert - Verify we get real data structure
      expect(metrics).toHaveProperty('totalUsers')
      expect(metrics).toHaveProperty('totalPortfolios')
      expect(metrics).toHaveProperty('activeUsers')
      expect(metrics).toHaveProperty('adminUsers')
      expect(metrics).toHaveProperty('systemStatus')
      expect(metrics).toHaveProperty('lastUpdated')

      // Verify data types and reasonable values
      expect(typeof metrics.totalUsers).toBe('number')
      expect(metrics.totalUsers).toBeGreaterThanOrEqual(0)
      expect(typeof metrics.totalPortfolios).toBe('number')
      expect(metrics.totalPortfolios).toBeGreaterThanOrEqual(0)
      expect(['healthy', 'warning', 'error']).toContain(metrics.systemStatus)

      // Verify admin users count is reasonable (at least 1 for test admin)
      expect(metrics.adminUsers).toBeGreaterThanOrEqual(1)

      console.log('Real system metrics:', {
        users: metrics.totalUsers,
        portfolios: metrics.totalPortfolios,
        status: metrics.systemStatus
      })
    })
  })

  describe('Users List Integration', () => {
    it('should fetch real user list with pagination', async () => {
      // Act - Call real backend API
      const usersData = await adminApiClient.getUsers({ page: 1, size: 10 })

      // Assert - Verify real paginated response
      expect(usersData).toHaveProperty('users')
      expect(usersData).toHaveProperty('total')
      expect(usersData).toHaveProperty('page')
      expect(usersData).toHaveProperty('pages')

      expect(Array.isArray(usersData.users)).toBe(true)
      expect(typeof usersData.total).toBe('number')
      expect(usersData.page).toBe(1)

      // If there are users, verify their structure
      if (usersData.users.length > 0) {
        const firstUser = usersData.users[0]
        expect(firstUser).toHaveProperty('id')
        expect(firstUser).toHaveProperty('email')
        expect(firstUser).toHaveProperty('role')
        expect(firstUser).toHaveProperty('isActive')
        expect(firstUser).toHaveProperty('createdAt')
        expect(firstUser).toHaveProperty('portfolioCount')

        // Verify user role is valid
        expect(['admin', 'user']).toContain(firstUser.role)
        expect(typeof firstUser.portfolioCount).toBe('number')
      }

      console.log(`Real users data: ${usersData.total} total users, showing ${usersData.users.length}`)
    })

    it('should handle user role filtering', async () => {
      // Act - Filter for admin users only
      const adminUsers = await adminApiClient.getUsers({ role: 'admin' })

      // Assert - All returned users should be admins
      expect(adminUsers.users.every(user => user.role === 'admin')).toBe(true)
      expect(adminUsers.total).toBeGreaterThanOrEqual(1) // At least our test admin

      console.log(`Found ${adminUsers.total} admin users`)
    })
  })

  describe('User Details Integration', () => {
    it('should fetch detailed user information', async () => {
      // Arrange - First get a user ID from the users list
      const usersData = await adminApiClient.getUsers({ page: 1, size: 1 })

      if (usersData.users.length === 0) {
        pending('No users found for detailed testing')
        return
      }

      const userId = usersData.users[0].id

      // Act - Fetch detailed user info
      const userDetails = await adminApiClient.getUserDetails(userId)

      // Assert - Verify detailed response structure
      expect(userDetails).toHaveProperty('id')
      expect(userDetails).toHaveProperty('email')
      expect(userDetails).toHaveProperty('totalAssets')
      expect(userDetails).toHaveProperty('portfolios')

      expect(userDetails.id).toBe(userId)
      expect(typeof userDetails.totalAssets).toBe('number')
      expect(Array.isArray(userDetails.portfolios)).toBe(true)

      // Verify portfolio structure if user has portfolios
      if (userDetails.portfolios.length > 0) {
        const firstPortfolio = userDetails.portfolios[0]
        expect(firstPortfolio).toHaveProperty('id')
        expect(firstPortfolio).toHaveProperty('name')
        expect(firstPortfolio).toHaveProperty('value')
        expect(firstPortfolio).toHaveProperty('lastUpdated')
      }

      console.log(`User ${userDetails.email}: $${userDetails.totalAssets} in ${userDetails.portfolios.length} portfolios`)
    })
  })

  describe('Market Data Status Integration', () => {
    it('should fetch real market data provider status', async () => {
      // Act - Call real backend API
      const marketDataStatus = await adminApiClient.getMarketDataStatus()

      // Assert - Verify response structure
      expect(marketDataStatus).toHaveProperty('providers')
      expect(Array.isArray(marketDataStatus.providers)).toBe(true)
      expect(marketDataStatus.providers.length).toBeGreaterThan(0)

      // Verify provider structure
      const firstProvider = marketDataStatus.providers[0]
      expect(firstProvider).toHaveProperty('providerId')
      expect(firstProvider).toHaveProperty('providerName')
      expect(firstProvider).toHaveProperty('isEnabled')
      expect(firstProvider).toHaveProperty('lastUpdate')
      expect(firstProvider).toHaveProperty('apiCallsToday')
      expect(firstProvider).toHaveProperty('monthlyLimit')
      expect(firstProvider).toHaveProperty('monthlyUsage')
      expect(firstProvider).toHaveProperty('status')

      // Verify data types and valid values
      expect(typeof firstProvider.apiCallsToday).toBe('number')
      expect(firstProvider.apiCallsToday).toBeGreaterThanOrEqual(0)
      expect(typeof firstProvider.monthlyUsage).toBe('number')
      expect(firstProvider.monthlyUsage).toBeGreaterThanOrEqual(0)
      expect(['active', 'disabled', 'error', 'rate_limited']).toContain(firstProvider.status)

      console.log('Market data providers:', marketDataStatus.providers.map(p => ({
        name: p.providerName,
        callsToday: p.apiCallsToday,
        monthlyUsage: p.monthlyUsage,
        status: p.status
      })))
    })
  })

  describe('API Usage Statistics Integration', () => {
    it('should fetch real API usage data', async () => {
      // Act - Call API usage endpoint directly (not in AdminApiClient yet)
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/api-usage`, {
        headers: { 'Authorization': `Bearer ${adminToken}` }
      })

      expect(response.ok).toBe(true)
      const apiUsage = await response.json()

      // Assert - Verify real usage data structure
      expect(apiUsage).toHaveProperty('summary')
      expect(apiUsage).toHaveProperty('by_provider')
      expect(apiUsage).toHaveProperty('by_date')
      expect(apiUsage).toHaveProperty('rate_limits')

      // Verify summary statistics
      const summary = apiUsage.summary
      expect(typeof summary.total_requests_today).toBe('number')
      expect(typeof summary.total_requests_this_month).toBe('number')
      expect(typeof summary.errors_today).toBe('number')
      expect(typeof summary.success_rate_today).toBe('number')

      // Verify provider breakdown
      expect(Array.isArray(apiUsage.by_provider)).toBe(true)
      if (apiUsage.by_provider.length > 0) {
        const provider = apiUsage.by_provider[0]
        expect(provider).toHaveProperty('provider_name')
        expect(provider).toHaveProperty('requests_today')
        expect(provider).toHaveProperty('requests_this_month')
      }

      // Verify daily breakdown
      expect(Array.isArray(apiUsage.by_date)).toBe(true)
      if (apiUsage.by_date.length > 0) {
        const dayData = apiUsage.by_date[0]
        expect(dayData).toHaveProperty('date')
        expect(dayData).toHaveProperty('total_requests')
        expect(dayData).toHaveProperty('successful_requests')
        expect(dayData).toHaveProperty('failed_requests')
      }

      console.log('API usage summary:', {
        requestsToday: summary.total_requests_today,
        requestsThisMonth: summary.total_requests_this_month,
        errorsToday: summary.errors_today,
        successRate: `${summary.success_rate_today}%`
      })
    })
  })

  describe('Authentication and Authorization Integration', () => {
    it('should reject requests without valid admin token', async () => {
      // Arrange - Create client without token
      const unauthenticatedClient = new AdminApiClient('')

      // Act & Assert - Should get 401 error
      await expect(unauthenticatedClient.getSystemMetrics()).rejects.toThrow()
    })

    it('should handle token expiration gracefully', async () => {
      // Arrange - Create client with fake/expired token
      const expiredClient = new AdminApiClient('expired.jwt.token')

      // Act & Assert - Should get authentication error
      await expect(expiredClient.getSystemMetrics()).rejects.toThrow()
    })
  })

  describe('Performance and Caching', () => {
    it('should complete requests within reasonable time', async () => {
      const startTime = Date.now()

      // Act - Make several concurrent requests
      const promises = [
        adminApiClient.getSystemMetrics(),
        adminApiClient.getUsers({ page: 1, size: 5 }),
        adminApiClient.getMarketDataStatus()
      ]

      await Promise.all(promises)
      const endTime = Date.now()
      const duration = endTime - startTime

      // Assert - Requests should complete within 5 seconds
      expect(duration).toBeLessThan(5000)
      console.log(`All admin API requests completed in ${duration}ms`)
    })
  })
})