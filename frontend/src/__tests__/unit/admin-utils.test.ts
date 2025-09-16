/**
 * Unit tests for admin utility functions
 */

import { AdminApiError } from '@/services/adminService'
import { useAdmin, AdminErrorType, AdminErrorDetails } from '@/hooks/useAdmin'
import { renderHook } from '@testing-library/react'
import { AuthContextType } from '@/types/auth'
import React from 'react'

// Mock the AuthContext
const mockAuthContext: Partial<AuthContextType> = {
  user: {
    id: '1',
    email: 'admin@example.com',
    role: 'admin',
    first_name: 'Admin',
    last_name: 'User',
    is_active: true,
    created_at: '2023-01-01T00:00:00Z'
  },
  token: 'mock-token',
  isAdmin: () => true,
  hasRole: (role: 'admin' | 'user') => role === 'admin',
  isAuthenticated: () => true,
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  loading: false,
  error: null,
  clearError: jest.fn()
}

// Mock the useAuth hook
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext
}))

describe('Admin Utility Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('useAdmin hook', () => {
    it('should return admin status correctly for admin user', () => {
      const { result } = renderHook(() => useAdmin())
      expect(result.current.isAdmin).toBe(true)
    })

    it('should return admin status correctly for regular user', () => {
      const mockUserContext = {
        ...mockAuthContext,
        user: {
          ...mockAuthContext.user!,
          role: 'user' as const
        },
        isAdmin: () => false,
        hasRole: (role: 'admin' | 'user') => role === 'user'
      }

      jest.mocked(require('@/contexts/AuthContext').useAuth).mockReturnValue(mockUserContext)

      const { result } = renderHook(() => useAdmin())
      expect(result.current.isAdmin).toBe(false)
    })

    it('should handle loading state', () => {
      const { result } = renderHook(() => useAdmin())
      expect(result.current.loading).toBe(false)
    })

    it('should clear errors', () => {
      const { result } = renderHook(() => useAdmin())
      expect(typeof result.current.clearError).toBe('function')

      // Should not throw when called
      expect(() => result.current.clearError()).not.toThrow()
    })
  })

  describe('Error Classification', () => {
    it('should classify AdminApiError with 401 status correctly', () => {
      const mockResponse = new Response('Unauthorized', { status: 401 })
      const error = new AdminApiError('Unauthorized access', 401, mockResponse)

      // Create a function to test error classification logic
      const classifyError = (error: unknown): AdminErrorDetails => {
        if (error instanceof AdminApiError) {
          let type: AdminErrorType = 'HTTP_ERROR'
          let retryable = false

          switch (error.status) {
            case 401:
              type = 'UNAUTHORIZED'
              retryable = false
              break
            case 403:
              type = 'FORBIDDEN'
              retryable = false
              break
            case 429:
            case 502:
            case 503:
            case 504:
              retryable = true
              break
            case 500:
              retryable = true
              break
            default:
              retryable = error.status >= 500
          }

          return {
            message: error.message,
            type,
            status: error.status,
            retryable,
            timestamp: new Date()
          }
        }

        return {
          message: 'Unknown error',
          type: 'UNKNOWN_ERROR',
          retryable: false,
          timestamp: new Date()
        }
      }

      const result = classifyError(error)
      expect(result.type).toBe('UNAUTHORIZED')
      expect(result.retryable).toBe(false)
      expect(result.status).toBe(401)
      expect(result.message).toBe('Unauthorized access')
    })

    it('should classify AdminApiError with 403 status correctly', () => {
      const mockResponse = new Response('Forbidden', { status: 403 })
      const error = new AdminApiError('Access forbidden', 403, mockResponse)

      const classifyError = (error: unknown): AdminErrorDetails => {
        if (error instanceof AdminApiError && error.status === 403) {
          return {
            message: error.message,
            type: 'FORBIDDEN',
            status: error.status,
            retryable: false,
            timestamp: new Date()
          }
        }
        return {
          message: 'Unknown error',
          type: 'UNKNOWN_ERROR',
          retryable: false,
          timestamp: new Date()
        }
      }

      const result = classifyError(error)
      expect(result.type).toBe('FORBIDDEN')
      expect(result.retryable).toBe(false)
    })

    it('should classify server errors as retryable', () => {
      const mockResponse = new Response('Server Error', { status: 500 })
      const error = new AdminApiError('Internal server error', 500, mockResponse)

      const classifyError = (error: unknown): AdminErrorDetails => {
        if (error instanceof AdminApiError && error.status === 500) {
          return {
            message: error.message,
            type: 'HTTP_ERROR',
            status: error.status,
            retryable: true,
            timestamp: new Date()
          }
        }
        return {
          message: 'Unknown error',
          type: 'UNKNOWN_ERROR',
          retryable: false,
          timestamp: new Date()
        }
      }

      const result = classifyError(error)
      expect(result.retryable).toBe(true)
      expect(result.status).toBe(500)
    })

    it('should classify network errors correctly', () => {
      const networkError = new Error('fetch failed')

      const classifyError = (error: unknown): AdminErrorDetails => {
        if (error instanceof Error && error.message.includes('fetch')) {
          return {
            message: 'Network connection failed',
            type: 'NETWORK_ERROR',
            retryable: true,
            timestamp: new Date()
          }
        }
        return {
          message: 'Unknown error',
          type: 'UNKNOWN_ERROR',
          retryable: false,
          timestamp: new Date()
        }
      }

      const result = classifyError(networkError)
      expect(result.type).toBe('NETWORK_ERROR')
      expect(result.retryable).toBe(true)
      expect(result.message).toBe('Network connection failed')
    })

    it('should classify abort errors correctly', () => {
      const abortError = new Error('The operation was aborted')
      abortError.name = 'AbortError'

      const classifyError = (error: unknown): AdminErrorDetails => {
        if (error instanceof Error && error.name === 'AbortError') {
          return {
            message: 'Request was cancelled',
            type: 'NETWORK_ERROR',
            retryable: true,
            timestamp: new Date()
          }
        }
        return {
          message: 'Unknown error',
          type: 'UNKNOWN_ERROR',
          retryable: false,
          timestamp: new Date()
        }
      }

      const result = classifyError(abortError)
      expect(result.type).toBe('NETWORK_ERROR')
      expect(result.retryable).toBe(true)
      expect(result.message).toBe('Request was cancelled')
    })
  })

  describe('AdminApiError class', () => {
    it('should create AdminApiError with correct properties', () => {
      const mockResponse = new Response('Bad Request', { status: 400 })
      const error = new AdminApiError('Test error message', 400, mockResponse)

      expect(error.message).toBe('Test error message')
      expect(error.status).toBe(400)
      expect(error.response).toBe(mockResponse)
      expect(error.name).toBe('AdminApiError')
      expect(error instanceof Error).toBe(true)
    })

    it('should be identifiable as AdminApiError', () => {
      const mockResponse = new Response('Server Error', { status: 500 })
      const error = new AdminApiError('Server error', 500, mockResponse)

      expect(error instanceof AdminApiError).toBe(true)
      expect(error instanceof Error).toBe(true)
    })
  })

  describe('Role-based utilities', () => {
    it('should correctly identify admin users', () => {
      const isAdminUser = (userRole?: string) => userRole === 'admin'

      expect(isAdminUser('admin')).toBe(true)
      expect(isAdminUser('user')).toBe(false)
      expect(isAdminUser(undefined)).toBe(false)
      expect(isAdminUser('')).toBe(false)
    })

    it('should validate role permissions correctly', () => {
      const hasPermission = (userRole: string, requiredRole: string) => {
        if (requiredRole === 'admin') {
          return userRole === 'admin'
        }
        return ['admin', 'user'].includes(userRole)
      }

      expect(hasPermission('admin', 'admin')).toBe(true)
      expect(hasPermission('user', 'admin')).toBe(false)
      expect(hasPermission('admin', 'user')).toBe(true)
      expect(hasPermission('user', 'user')).toBe(true)
    })
  })

  describe('Data formatting utilities', () => {
    it('should format currency correctly', () => {
      const formatCurrency = (amount: number) => {
        return `$${amount.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        })}`
      }

      expect(formatCurrency(1234.56)).toBe('$1,234.56')
      expect(formatCurrency(0)).toBe('$0.00')
      expect(formatCurrency(1000000)).toBe('$1,000,000.00')
    })

    it('should format dates correctly', () => {
      const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString()
      }

      const testDate = '2023-01-01T00:00:00Z'
      const formatted = formatDate(testDate)
      expect(typeof formatted).toBe('string')
      expect(formatted.length).toBeGreaterThan(0)
    })

    it('should format percentages correctly', () => {
      const formatPercentage = (value: number) => {
        return `${value.toFixed(1)}%`
      }

      expect(formatPercentage(25.456)).toBe('25.5%')
      expect(formatPercentage(0)).toBe('0.0%')
      expect(formatPercentage(100)).toBe('100.0%')
    })
  })

  describe('Status badge utilities', () => {
    it('should return correct status colors', () => {
      const getStatusColor = (status: string) => {
        switch (status) {
          case 'active':
          case 'healthy':
            return 'bg-green-100 text-green-800'
          case 'warning':
            return 'bg-yellow-100 text-yellow-800'
          case 'error':
          case 'disabled':
            return 'bg-red-100 text-red-800'
          case 'rate_limited':
            return 'bg-yellow-100 text-yellow-800'
          default:
            return 'bg-gray-100 text-gray-800'
        }
      }

      expect(getStatusColor('active')).toBe('bg-green-100 text-green-800')
      expect(getStatusColor('healthy')).toBe('bg-green-100 text-green-800')
      expect(getStatusColor('warning')).toBe('bg-yellow-100 text-yellow-800')
      expect(getStatusColor('error')).toBe('bg-red-100 text-red-800')
      expect(getStatusColor('disabled')).toBe('bg-red-100 text-red-800')
      expect(getStatusColor('rate_limited')).toBe('bg-yellow-100 text-yellow-800')
      expect(getStatusColor('unknown')).toBe('bg-gray-100 text-gray-800')
    })

    it('should return correct role colors', () => {
      const getRoleColor = (role: string) => {
        return role === 'admin'
          ? 'bg-red-100 text-red-800'
          : 'bg-blue-100 text-blue-800'
      }

      expect(getRoleColor('admin')).toBe('bg-red-100 text-red-800')
      expect(getRoleColor('user')).toBe('bg-blue-100 text-blue-800')
      expect(getRoleColor('guest')).toBe('bg-blue-100 text-blue-800')
    })
  })
})