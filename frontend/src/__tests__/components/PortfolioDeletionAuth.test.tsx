/**
 * TDD Test: Portfolio Deletion Authentication
 * Testing that portfolio deletion modal properly includes authentication token
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AuthContext } from '@/contexts/AuthContext'
import PortfolioDeletionModal from '@/components/Portfolio/PortfolioDeletionModal'

// Mock the portfolio service
jest.mock('@/services/portfolio', () => ({
  deletePortfolio: jest.fn(),
  hardDeletePortfolio: jest.fn(),
}))

const mockPortfolio = {
  id: 'portfolio-123',
  name: 'Test Portfolio',
  description: 'Test portfolio for deletion',
  total_value: '1000.00',
  daily_change: '50.00',
  daily_change_percent: '5.0',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  owner_id: 'user-123'
}

const MockAuthProvider = ({
  children,
  user = null,
  token = null,
  loading = false
}: {
  children: React.ReactNode
  user?: any
  token?: string | null
  loading?: boolean
}) => {
  const mockAuthValue = {
    user,
    token,
    loading,
    login: jest.fn(),
    logout: jest.fn(),
    register: jest.fn(),
    updateProfile: jest.fn(),
    refreshToken: jest.fn()
  }

  return (
    <AuthContext.Provider value={mockAuthValue}>
      {children}
    </AuthContext.Provider>
  )
}

describe('Portfolio Deletion Authentication', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should include authentication token when deleting portfolio', async () => {
    const { deletePortfolio } = require('@/services/portfolio')
    deletePortfolio.mockResolvedValue({ message: 'Portfolio deleted successfully' })

    const mockUser = {
      id: 'user-123',
      email: 'user@example.com',
      role: 'user'
    }
    const mockToken = 'valid-jwt-token'

    const onDeleted = jest.fn()
    const onClose = jest.fn()

    render(
      <MockAuthProvider user={mockUser} token={mockToken}>
        <PortfolioDeletionModal
          isOpen={true}
          onClose={onClose}
          portfolio={mockPortfolio}
          onDeleted={onDeleted}
        />
      </MockAuthProvider>
    )

    // Enter portfolio name for confirmation
    const confirmationInput = screen.getByPlaceholderText('Portfolio name')
    fireEvent.change(confirmationInput, { target: { value: 'Test Portfolio' } })

    // Click delete button
    const deleteButton = screen.getByRole('button', { name: 'Delete Portfolio' })
    fireEvent.click(deleteButton)

    // Verify API was called with correct parameters including token
    await waitFor(() => {
      expect(deletePortfolio).toHaveBeenCalledWith(
        'portfolio-123',
        { confirmationName: 'Test Portfolio' },
        { token: 'valid-jwt-token' }
      )
    })
  })

  it('should show authentication error when no token is provided', async () => {
    const { deletePortfolio } = require('@/services/portfolio')
    deletePortfolio.mockRejectedValue(new Error('Authentication required. Provide either Bearer token or X-API-Key header.'))

    const mockUser = {
      id: 'user-123',
      email: 'user@example.com',
      role: 'user'
    }
    // No token provided
    const mockToken = null

    const onDeleted = jest.fn()
    const onClose = jest.fn()

    render(
      <MockAuthProvider user={mockUser} token={mockToken}>
        <PortfolioDeletionModal
          isOpen={true}
          onClose={onClose}
          portfolio={mockPortfolio}
          onDeleted={onDeleted}
        />
      </MockAuthProvider>
    )

    // Enter portfolio name for confirmation
    const confirmationInput = screen.getByPlaceholderText('Portfolio name')
    fireEvent.change(confirmationInput, { target: { value: 'Test Portfolio' } })

    // Click delete button
    const deleteButton = screen.getByRole('button', { name: 'Delete Portfolio' })
    fireEvent.click(deleteButton)

    // Should show authentication error
    await waitFor(() => {
      expect(screen.getByText(/authentication required/i)).toBeInTheDocument()
    })

    // Verify API was still called but with null token
    expect(deletePortfolio).toHaveBeenCalledWith(
      'portfolio-123',
      { confirmationName: 'Test Portfolio' },
      { token: null }
    )
  })

  it('should not attempt deletion when user is not logged in', async () => {
    const { deletePortfolio } = require('@/services/portfolio')

    const onDeleted = jest.fn()
    const onClose = jest.fn()

    render(
      <MockAuthProvider user={null} token={null}>
        <PortfolioDeletionModal
          isOpen={true}
          onClose={onClose}
          portfolio={mockPortfolio}
          onDeleted={onDeleted}
        />
      </MockAuthProvider>
    )

    // Enter portfolio name for confirmation
    const confirmationInput = screen.getByPlaceholderText('Portfolio name')
    fireEvent.change(confirmationInput, { target: { value: 'Test Portfolio' } })

    // Click delete button
    const deleteButton = screen.getByRole('button', { name: 'Delete Portfolio' })
    fireEvent.click(deleteButton)

    // Should not call API when no user
    await waitFor(() => {
      expect(deletePortfolio).not.toHaveBeenCalled()
    })
  })

  it('should include token for hard delete as well', async () => {
    const { hardDeletePortfolio } = require('@/services/portfolio')
    hardDeletePortfolio.mockResolvedValue({ message: 'Portfolio permanently deleted' })

    const mockUser = {
      id: 'user-123',
      email: 'user@example.com',
      role: 'user'
    }
    const mockToken = 'valid-jwt-token'

    const onDeleted = jest.fn()
    const onClose = jest.fn()

    render(
      <MockAuthProvider user={mockUser} token={mockToken}>
        <PortfolioDeletionModal
          isOpen={true}
          onClose={onClose}
          portfolio={mockPortfolio}
          onDeleted={onDeleted}
          allowHardDelete={true}
        />
      </MockAuthProvider>
    )

    // Enter portfolio name for confirmation
    const confirmationInput = screen.getByPlaceholderText('Portfolio name')
    fireEvent.change(confirmationInput, { target: { value: 'Test Portfolio' } })

    // Check hard delete option
    const hardDeleteCheckbox = screen.getByRole('checkbox')
    fireEvent.click(hardDeleteCheckbox)

    // Click delete button
    const deleteButton = screen.getByRole('button', { name: 'Delete Portfolio' })
    fireEvent.click(deleteButton)

    // Verify hard delete API was called with token
    await waitFor(() => {
      expect(hardDeletePortfolio).toHaveBeenCalledWith(
        'portfolio-123',
        { confirmationName: 'Test Portfolio' },
        { token: 'valid-jwt-token' }
      )
    })
  })
})