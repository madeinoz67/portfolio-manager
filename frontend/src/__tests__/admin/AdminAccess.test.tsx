/**
 * TDD Test: Admin Access and Role Verification
 * Testing the admin role checking logic for audit log access
 */

import { render, screen, waitFor } from '@testing-library/react'
import { AuthContext } from '@/contexts/AuthContext'
import { AuditLogTable } from '@/components/admin/AuditLogTable'

// Mock the audit service
jest.mock('@/services/audit', () => ({
  fetchAuditLogs: jest.fn(),
}))

const mockUser = {
  id: 'admin-user-id',
  email: 'admin@example.com',
  first_name: 'Admin',
  last_name: 'User',
  role: 'admin' as const,
  is_active: true
}

const mockRegularUser = {
  id: 'regular-user-id',
  email: 'user@example.com',
  first_name: 'Regular',
  last_name: 'User',
  role: 'user' as const,
  is_active: true
}

const MockAuthProvider = ({
  children,
  user,
  loading = false
}: {
  children: React.ReactNode
  user: any
  loading?: boolean
}) => {
  const mockAuthValue = {
    user,
    loading,
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn(),
    updateProfile: jest.fn(),
    token: user ? 'mock-jwt-token' : null,
    refreshToken: jest.fn()
  }

  return (
    <AuthContext.Provider value={mockAuthValue}>
      {children}
    </AuthContext.Provider>
  )
}

describe('Admin Access Control', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should allow admin user to access audit logs', async () => {
    const { fetchAuditLogs } = require('@/services/audit')
    fetchAuditLogs.mockResolvedValue({
      data: [],
      pagination: {
        current_page: 1,
        total_pages: 0,
        total_items: 0,
        items_per_page: 50
      },
      filters: {},
      meta: {
        request_timestamp: new Date().toISOString(),
        processing_time_ms: 10,
        total_events_in_system: 0
      }
    })

    render(
      <MockAuthProvider user={mockUser}>
        <AuditLogTable />
      </MockAuthProvider>
    )

    // Should not show unauthorized message
    expect(screen.queryByText(/unauthorized access/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/error loading audit logs/i)).not.toBeInTheDocument()

    // Should show the audit log interface
    await waitFor(() => {
      expect(screen.getByText(/audit logs/i)).toBeInTheDocument()
    })
  })

  it('should deny regular user access to audit logs', async () => {
    render(
      <MockAuthProvider user={mockRegularUser}>
        <AuditLogTable />
      </MockAuthProvider>
    )

    // Should show unauthorized message
    await waitFor(() => {
      expect(screen.getByText(/unauthorized access/i)).toBeInTheDocument()
    })

    // Should not attempt to load audit logs
    const { fetchAuditLogs } = require('@/services/audit')
    expect(fetchAuditLogs).not.toHaveBeenCalled()
  })

  it('should deny access when user is not logged in', async () => {
    render(
      <MockAuthProvider user={null}>
        <AuditLogTable />
      </MockAuthProvider>
    )

    // Should show unauthorized message
    await waitFor(() => {
      expect(screen.getByText(/unauthorized access/i)).toBeInTheDocument()
    })
  })

  it('should show loading state while auth is loading', async () => {
    render(
      <MockAuthProvider user={null} loading={true}>
        <AuditLogTable />
      </MockAuthProvider>
    )

    // Should show loading state, not unauthorized
    expect(screen.queryByText(/unauthorized access/i)).not.toBeInTheDocument()
  })
})

describe('Admin Role String Validation', () => {
  it('should accept "admin" string role', () => {
    const testUser = { ...mockUser, role: 'admin' }

    render(
      <MockAuthProvider user={testUser}>
        <AuditLogTable />
      </MockAuthProvider>
    )

    expect(screen.queryByText(/unauthorized access/i)).not.toBeInTheDocument()
  })

  it('should accept "ADMIN" uppercase role', () => {
    const testUser = { ...mockUser, role: 'ADMIN' }

    render(
      <MockAuthProvider user={testUser}>
        <AuditLogTable />
      </MockAuthProvider>
    )

    expect(screen.queryByText(/unauthorized access/i)).not.toBeInTheDocument()
  })

  it('should reject invalid role values', () => {
    const testUser = { ...mockUser, role: 'administrator' }

    render(
      <MockAuthProvider user={testUser}>
        <AuditLogTable />
      </MockAuthProvider>
    )

    expect(screen.getByText(/unauthorized access/i)).toBeInTheDocument()
  })
})