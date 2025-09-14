/**
 * Unit tests for admin components
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { SystemMetricsCard } from '@/components/admin/SystemMetricsCard'
import { UserManagementTable } from '@/components/admin/UserManagementTable'
import { MarketDataStatusTable } from '@/components/admin/MarketDataStatusTable'
import { AdminUserListItem, MarketDataProvider } from '@/types/admin'

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
  }),
}))

describe('Admin Components', () => {
  describe('SystemMetricsCard', () => {
    const mockIcon = React.createElement('svg', { 'data-testid': 'mock-icon' })

    it('should render basic system metrics card', () => {
      render(
        <SystemMetricsCard
          title="Test Metric"
          value="42"
          icon={mockIcon}
        />
      )

      expect(screen.getByText('Test Metric')).toBeInTheDocument()
      expect(screen.getByText('42')).toBeInTheDocument()
      expect(screen.getByTestId('mock-icon')).toBeInTheDocument()
    })

    it('should render system metrics card with subtitle', () => {
      render(
        <SystemMetricsCard
          title="Total Users"
          value="1,234"
          subtitle="Registered accounts"
          icon={mockIcon}
        />
      )

      expect(screen.getByText('Total Users')).toBeInTheDocument()
      expect(screen.getByText('1,234')).toBeInTheDocument()
      expect(screen.getByText('Registered accounts')).toBeInTheDocument()
    })

    it('should render trend indicator for positive trend', () => {
      render(
        <SystemMetricsCard
          title="Active Users"
          value="567"
          trend="up"
          trendValue="+12%"
          icon={mockIcon}
        />
      )

      expect(screen.getByText('Active Users')).toBeInTheDocument()
      expect(screen.getByText('567')).toBeInTheDocument()
      expect(screen.getByText('+12%')).toBeInTheDocument()
    })

    it('should render trend indicator for negative trend', () => {
      render(
        <SystemMetricsCard
          title="Server Errors"
          value="3"
          trend="down"
          trendValue="-50%"
          icon={mockIcon}
        />
      )

      expect(screen.getByText('Server Errors')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument()
      expect(screen.getByText('-50%')).toBeInTheDocument()
    })

    it('should not render trend indicator for neutral trend', () => {
      render(
        <SystemMetricsCard
          title="System Status"
          value="Stable"
          trend="neutral"
          trendValue="0%"
          icon={mockIcon}
        />
      )

      expect(screen.getByText('System Status')).toBeInTheDocument()
      expect(screen.getByText('Stable')).toBeInTheDocument()
      expect(screen.queryByText('0%')).not.toBeInTheDocument()
    })

    it('should apply custom className', () => {
      const { container } = render(
        <SystemMetricsCard
          title="Test"
          value="test"
          icon={mockIcon}
          className="custom-class"
        />
      )

      expect(container.firstChild).toHaveClass('custom-class')
    })
  })

  describe('UserManagementTable', () => {
    const mockUsers: AdminUserListItem[] = [
      {
        id: '1',
        email: 'admin@example.com',
        firstName: 'John',
        lastName: 'Doe',
        role: 'admin',
        isActive: true,
        createdAt: '2023-01-01T00:00:00Z',
        portfolioCount: 5,
        lastLoginAt: '2023-12-01T00:00:00Z'
      },
      {
        id: '2',
        email: 'user@example.com',
        firstName: 'Jane',
        lastName: 'Smith',
        role: 'user',
        isActive: false,
        createdAt: '2023-02-01T00:00:00Z',
        portfolioCount: 2,
        lastLoginAt: '2023-11-01T00:00:00Z'
      }
    ]

    it('should render user table with data', () => {
      render(<UserManagementTable users={mockUsers} />)

      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('admin@example.com')).toBeInTheDocument()
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
      expect(screen.getByText('user@example.com')).toBeInTheDocument()
    })

    it('should display user roles correctly', () => {
      render(<UserManagementTable users={mockUsers} />)

      const adminBadges = screen.getAllByText('admin')
      const userBadges = screen.getAllByText('user')

      expect(adminBadges).toHaveLength(1)
      expect(userBadges).toHaveLength(1)
    })

    it('should display active/inactive status', () => {
      render(<UserManagementTable users={mockUsers} />)

      expect(screen.getByText('Active')).toBeInTheDocument()
      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })

    it('should display portfolio counts', () => {
      render(<UserManagementTable users={mockUsers} />)

      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
    })

    it('should render "View Details" links', () => {
      render(<UserManagementTable users={mockUsers} />)

      const detailLinks = screen.getAllByText('View Details')
      expect(detailLinks).toHaveLength(2)

      expect(detailLinks[0]).toHaveAttribute('href', '/admin/users/1')
      expect(detailLinks[1]).toHaveAttribute('href', '/admin/users/2')
    })

    it('should show loading state', () => {
      render(<UserManagementTable users={[]} loading={true} />)

      // Should show loading skeleton
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
    })

    it('should show empty state when no users', () => {
      render(<UserManagementTable users={[]} />)

      expect(screen.getByText('No users found')).toBeInTheDocument()
      expect(screen.getByText('No users match the current filters.')).toBeInTheDocument()
    })

    it('should display user initials when no first name', () => {
      const usersWithoutName: AdminUserListItem[] = [
        {
          id: '3',
          email: 'test@example.com',
          role: 'user',
          isActive: true,
          createdAt: '2023-01-01T00:00:00Z',
          portfolioCount: 0
        }
      ]

      render(<UserManagementTable users={usersWithoutName} />)

      expect(screen.getByText('T')).toBeInTheDocument() // First letter of email
      expect(screen.getByText('test@example.com')).toBeInTheDocument()
    })
  })

  describe('MarketDataStatusTable', () => {
    const mockProviders: MarketDataProvider[] = [
      {
        providerId: 'alpha-vantage',
        providerName: 'Alpha Vantage',
        isEnabled: true,
        lastUpdate: '2023-12-01T00:00:00Z',
        apiCallsToday: 150,
        monthlyLimit: 1000,
        monthlyUsage: 500,
        costPerCall: 0.01,
        status: 'active'
      },
      {
        providerId: 'yahoo-finance',
        providerName: 'Yahoo Finance',
        isEnabled: false,
        lastUpdate: '2023-11-30T00:00:00Z',
        apiCallsToday: 0,
        monthlyLimit: 0,
        monthlyUsage: 0,
        costPerCall: 0,
        status: 'disabled'
      },
      {
        providerId: 'twelve-data',
        providerName: 'Twelve Data',
        isEnabled: true,
        lastUpdate: '2023-12-01T10:00:00Z',
        apiCallsToday: 950,
        monthlyLimit: 1000,
        monthlyUsage: 980,
        costPerCall: 0.02,
        status: 'rate_limited'
      }
    ]

    it('should render market data provider table', () => {
      render(<MarketDataStatusTable providers={mockProviders} />)

      expect(screen.getByText('Alpha Vantage')).toBeInTheDocument()
      expect(screen.getByText('Yahoo Finance')).toBeInTheDocument()
      expect(screen.getByText('Twelve Data')).toBeInTheDocument()
    })

    it('should display provider status correctly', () => {
      render(<MarketDataStatusTable providers={mockProviders} />)

      expect(screen.getByText('active')).toBeInTheDocument()
      expect(screen.getByText('disabled')).toBeInTheDocument()
      expect(screen.getByText('rate limited')).toBeInTheDocument()
    })

    it('should display usage statistics', () => {
      render(<MarketDataStatusTable providers={mockProviders} />)

      expect(screen.getByText('500 / 1,000')).toBeInTheDocument()
      expect(screen.getByText('0 / 0')).toBeInTheDocument()
      expect(screen.getByText('980 / 1,000')).toBeInTheDocument()
    })

    it('should display usage percentages', () => {
      render(<MarketDataStatusTable providers={mockProviders} />)

      expect(screen.getByText('50.0% used')).toBeInTheDocument()
      expect(screen.getByText('0.0% used')).toBeInTheDocument()
      expect(screen.getByText('98.0% used')).toBeInTheDocument()
    })

    it('should display cost information', () => {
      render(<MarketDataStatusTable providers={mockProviders} />)

      expect(screen.getByText('$0.0100/call')).toBeInTheDocument()
      expect(screen.getByText('$0.0000/call')).toBeInTheDocument()
      expect(screen.getByText('$0.0200/call')).toBeInTheDocument()

      expect(screen.getByText('Monthly: $5.00')).toBeInTheDocument()
      expect(screen.getByText('Monthly: $0.00')).toBeInTheDocument()
      expect(screen.getByText('Monthly: $19.60')).toBeInTheDocument()
    })

    it('should display API calls today', () => {
      render(<MarketDataStatusTable providers={mockProviders} />)

      expect(screen.getByText('Calls today: 150')).toBeInTheDocument()
      expect(screen.getByText('Calls today: 0')).toBeInTheDocument()
      expect(screen.getByText('Calls today: 950')).toBeInTheDocument()
    })

    it('should show loading state', () => {
      render(<MarketDataStatusTable providers={[]} loading={true} />)

      expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
    })

    it('should show empty state when no providers', () => {
      render(<MarketDataStatusTable providers={[]} />)

      expect(screen.getByText('No providers configured')).toBeInTheDocument()
      expect(screen.getByText('No market data providers have been configured yet.')).toBeInTheDocument()
    })

    it('should render usage progress bars with correct colors', () => {
      const { container } = render(<MarketDataStatusTable providers={mockProviders} />)

      const progressBars = container.querySelectorAll('.h-2.rounded-full')

      // First provider (50% usage) should be green
      expect(progressBars[0]).toHaveClass('bg-green-500')

      // Third provider (98% usage) should be red
      expect(progressBars[2]).toHaveClass('bg-red-500')
    })

    it('should handle edge case of zero monthly limit', () => {
      const providersWithZeroLimit: MarketDataProvider[] = [
        {
          providerId: 'test',
          providerName: 'Test Provider',
          isEnabled: true,
          lastUpdate: '2023-12-01T00:00:00Z',
          apiCallsToday: 100,
          monthlyLimit: 0,
          monthlyUsage: 50,
          costPerCall: 0,
          status: 'active'
        }
      ]

      render(<MarketDataStatusTable providers={providersWithZeroLimit} />)

      expect(screen.getByText('50 / 0')).toBeInTheDocument()
    })
  })
})