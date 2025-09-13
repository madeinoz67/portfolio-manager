/**
 * Integration Tests for AuthContext
 * Tests the authentication context and error handling scenarios
 */

import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { AuthError } from '@/types/auth'

// Test component that uses AuthContext
function TestComponent() {
  const { user, login, register, logout, loading, error, clearError } = useAuth()

  return (
    <div>
      <div data-testid="loading">{loading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="user">{user ? user.email : 'No User'}</div>
      <div data-testid="error">{error ? error.message : 'No Error'}</div>

      <button
        data-testid="login-btn"
        onClick={() => login({ email: 'test@example.com', password: 'test123456' })}
      >
        Login
      </button>

      <button
        data-testid="register-btn"
        onClick={() => register({ email: 'test@example.com', password: 'test123456', full_name: 'Test User' })}
      >
        Register
      </button>

      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>

      <button data-testid="clear-error-btn" onClick={clearError}>
        Clear Error
      </button>
    </div>
  )
}

function renderWithAuth() {
  return render(
    <AuthProvider>
      <TestComponent />
    </AuthProvider>
  )
}

describe('AuthContext Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  describe('Initial State', () => {
    it('should initialize with correct default state', () => {
      renderWithAuth()

      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
      expect(screen.getByTestId('user')).toHaveTextContent('No User')
      expect(screen.getByTestId('error')).toHaveTextContent('No Error')
    })

    it('should attempt to load user from localStorage token on mount', async () => {
      const mockToken = 'stored_token_123'
      localStorage.getItem = jest.fn().mockReturnValue(mockToken)

      // Mock successful /me endpoint
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          id: '123',
          email: 'stored@example.com',
          role: 'user'
        })
      })

      renderWithAuth()

      // Should initially be loading
      expect(screen.getByTestId('loading')).toHaveTextContent('Loading')

      // Should call /me endpoint with stored token
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8001/api/v1/auth/me',
          expect.objectContaining({
            headers: expect.objectContaining({
              'Authorization': `Bearer ${mockToken}`
            })
          })
        )
      })

      // Should set user and stop loading
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('stored@example.com')
        expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
      })
    })
  })

  describe('Login Flow', () => {
    it('should handle successful login', async () => {
      const user = userEvent.setup()

      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'new_token_456',
          user: {
            id: '456',
            email: 'test@example.com',
            role: 'user'
          }
        })
      })

      renderWithAuth()

      await user.click(screen.getByTestId('login-btn'))

      // Should show loading during request
      expect(screen.getByTestId('loading')).toHaveTextContent('Loading')

      // Should call login endpoint
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8001/api/v1/auth/login',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: 'test@example.com',
              password: 'test123456'
            })
          })
        )
      })

      // Should set user and token, stop loading
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
        expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
      })

      expect(localStorage.setItem).toHaveBeenCalledWith('auth_token', 'new_token_456')
    })

    it('should handle login with 401 authentication error', async () => {
      const user = userEvent.setup()

      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({
          detail: 'Invalid credentials'
        })
      })

      renderWithAuth()

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Invalid credentials')
        expect(screen.getByTestId('user')).toHaveTextContent('No User')
        expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
      })
    })

    it('should handle network timeout error', async () => {
      const user = userEvent.setup()

      // Mock AbortError (timeout)
      const abortError = new Error('AbortError')
      abortError.name = 'AbortError'
      global.fetch = jest.fn().mockRejectedValue(abortError)

      renderWithAuth()

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Request timed out')
        expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
      })
    })

    it('should handle network connection error', async () => {
      const user = userEvent.setup()

      // Mock network error
      const networkError = new Error('fetch failed')
      global.fetch = jest.fn().mockRejectedValue(networkError)

      renderWithAuth()

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Connection error')
        expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading')
      })
    })

    it('should ensure timeout cleanup happens in try/finally', async () => {
      const user = userEvent.setup()

      // Mock clearTimeout to track calls
      const mockClearTimeout = jest.fn()
      global.clearTimeout = mockClearTimeout

      // Mock fetch to fail
      global.fetch = jest.fn().mockRejectedValue(new Error('Network error'))

      renderWithAuth()

      await user.click(screen.getByTestId('login-btn'))

      // Wait for error to appear (indicating finally block executed)
      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Connection error')
      })

      // Verify clearTimeout was called even when fetch failed
      expect(mockClearTimeout).toHaveBeenCalled()
    })
  })

  describe('Registration Flow', () => {
    it('should handle successful registration and auto-login', async () => {
      const user = userEvent.setup()

      // Mock successful registration (returns 201) followed by login
      global.fetch = jest.fn()
        .mockResolvedValueOnce({
          ok: true,
          status: 201,
          json: () => Promise.resolve({ message: 'User created' })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            access_token: 'new_token_789',
            user: {
              id: '789',
              email: 'test@example.com',
              role: 'user'
            }
          })
        })

      renderWithAuth()

      await user.click(screen.getByTestId('register-btn'))

      // Should call register endpoint first, then login
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8001/api/v1/auth/register',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({
              email: 'test@example.com',
              password: 'test123456',
              full_name: 'Test User'
            })
          })
        )
      })

      // After registration, should auto-login
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8001/api/v1/auth/login',
          expect.anything()
        )
      })

      // Should end up logged in
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })
    })

    it('should handle registration validation error (400)', async () => {
      const user = userEvent.setup()

      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({
          detail: 'Password too short'
        })
      })

      renderWithAuth()

      await user.click(screen.getByTestId('register-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Password too short')
        expect(screen.getByTestId('user')).toHaveTextContent('No User')
      })
    })

    it('should handle duplicate email registration (409)', async () => {
      const user = userEvent.setup()

      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 409,
        json: () => Promise.resolve({
          message: 'Email already exists'
        })
      })

      renderWithAuth()

      await user.click(screen.getByTestId('register-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Email already exists')
      })
    })
  })

  describe('Error Handling', () => {
    it('should clear errors when clearError is called', async () => {
      const user = userEvent.setup()

      // First cause an error
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Test error' })
      })

      renderWithAuth()

      await user.click(screen.getByTestId('login-btn'))

      // Verify error is shown
      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Test error')
      })

      // Clear the error
      await user.click(screen.getByTestId('clear-error-btn'))

      expect(screen.getByTestId('error')).toHaveTextContent('No Error')
    })

    it('should handle server error (500)', async () => {
      const user = userEvent.setup()

      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        text: () => Promise.resolve('Server Error Details')
      })

      renderWithAuth()

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('error')).toHaveTextContent('Login failed')
      })
    })

    it('should categorize errors correctly', async () => {
      const user = userEvent.setup()

      // Network timeout error
      const timeoutError = new Error('AbortError')
      timeoutError.name = 'AbortError'
      global.fetch = jest.fn().mockRejectedValue(timeoutError)

      renderWithAuth()

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        const errorText = screen.getByTestId('error').textContent
        expect(errorText).toContain('Request timed out')
      })
    })
  })

  describe('Token Management', () => {
    it('should handle invalid token from localStorage', async () => {
      localStorage.getItem = jest.fn().mockReturnValue('invalid_token')

      // Mock 401 response for /me endpoint
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 401,
        text: () => Promise.resolve('Unauthorized')
      })

      renderWithAuth()

      // Should clear invalid token and show session expired error
      await waitFor(() => {
        expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token')
        expect(screen.getByTestId('error')).toHaveTextContent('Session expired')
      })
    })

    it('should logout and clear localStorage', async () => {
      const user = userEvent.setup()

      // First login
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'token_123',
          user: { id: '123', email: 'test@example.com', role: 'user' }
        })
      })

      renderWithAuth()

      await user.click(screen.getByTestId('login-btn'))

      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      // Then logout
      await user.click(screen.getByTestId('logout-btn'))

      expect(screen.getByTestId('user')).toHaveTextContent('No User')
      expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token')
    })
  })

  describe('Concurrent Requests', () => {
    it('should handle multiple concurrent login attempts gracefully', async () => {
      const user = userEvent.setup()

      // Mock successful response
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'token_concurrent',
          user: { id: '123', email: 'test@example.com', role: 'user' }
        })
      })

      renderWithAuth()

      // Click login multiple times quickly
      const loginBtn = screen.getByTestId('login-btn')
      await user.click(loginBtn)
      await user.click(loginBtn)
      await user.click(loginBtn)

      // Should handle gracefully without errors
      await waitFor(() => {
        expect(screen.getByTestId('user')).toHaveTextContent('test@example.com')
      })

      // Should not have error state
      expect(screen.getByTestId('error')).toHaveTextContent('No Error')
    })
  })
})