/**
 * Custom hook for admin dashboard functionality
 * Provides data fetching and state management for admin operations
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import {
  SystemMetrics,
  PaginatedUsersResponse,
  AdminUserDetails,
  MarketDataStatus,
  AdminUsersListParams,
  ProviderDetailResponse
} from '@/types/admin'
import { AdminApiClient, AdminApiError } from '@/services/admin'

// Simple cache with TTL (Time To Live)
interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

class AdminDataCache {
  private cache = new Map<string, CacheEntry<any>>()

  set<T>(key: string, data: T, ttlMs: number = 30000) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttlMs
    })
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return null
    }

    return entry.data
  }

  invalidate(key: string) {
    this.cache.delete(key)
  }

  clear() {
    this.cache.clear()
  }
}

const adminCache = new AdminDataCache()

// Debounce utility
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

export type AdminErrorType = 'NETWORK_ERROR' | 'HTTP_ERROR' | 'UNAUTHORIZED' | 'FORBIDDEN' | 'UNKNOWN_ERROR'

export interface AdminErrorDetails {
  message: string
  type: AdminErrorType
  status?: number
  retryable: boolean
  timestamp: Date
}

interface UseAdminOptions {
  onUnauthorized?: () => void
}

export function useAdmin(options?: UseAdminOptions) {
  const { token, user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<AdminErrorDetails | null>(null)
  const apiClientRef = useRef<AdminApiClient>()

  // Initialize API client
  useEffect(() => {
    if (token) {
      apiClientRef.current = new AdminApiClient(token)
    } else {
      apiClientRef.current = undefined
    }
  }, [token])

  // Check if current user has admin access
  const isAdmin = user?.role === 'admin'

  const classifyError = useCallback((error: unknown): AdminErrorDetails => {
    const timestamp = new Date()

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
        timestamp
      }
    }

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return {
          message: 'Request was cancelled',
          type: 'NETWORK_ERROR',
          retryable: true,
          timestamp
        }
      }

      if (error.message.includes('fetch') || error.message.includes('network')) {
        return {
          message: 'Network connection failed',
          type: 'NETWORK_ERROR',
          retryable: true,
          timestamp
        }
      }
    }

    return {
      message: 'An unexpected error occurred',
      type: 'UNKNOWN_ERROR',
      retryable: false,
      timestamp
    }
  }, [])

  const handleError = useCallback((error: unknown) => {
    const errorDetails = classifyError(error)
    setError(errorDetails)

    if (errorDetails.type === 'UNAUTHORIZED') {
      options?.onUnauthorized?.()
    }

    console.error('Admin API error:', error)
  }, [classifyError, options])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      apiClientRef.current?.abort()
    }
  }, [])

  const fetchProviderDetails = useCallback(async (providerId: string): Promise<ProviderDetailResponse> => {
    if (!apiClientRef.current) {
      throw new Error('API client not initialized')
    }

    try {
      return await apiClientRef.current.getProviderDetails(providerId)
    } catch (error) {
      // Don't handle or log cancellation errors
      if (error instanceof AdminApiError && error.message === 'Request was cancelled') {
        throw error // Just re-throw without logging
      }
      handleError(error)
      throw error
    }
  }, [handleError])

  return {
    isAdmin,
    loading,
    error,
    clearError,
    handleError,
    apiClient: apiClientRef.current,
    setLoading,
    fetchProviderDetails
  }
}

/**
 * Hook for fetching system metrics with caching
 */
export function useSystemMetrics(options?: UseAdminOptions) {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const { isAdmin, loading, error, clearError, handleError, apiClient, setLoading } = useAdmin(options)
  const cacheKey = 'system-metrics'

  const fetchMetrics = useCallback(async (forceRefresh = false) => {
    console.log('fetchMetrics called:', { isAdmin, hasApiClient: !!apiClient, forceRefresh })

    if (!isAdmin || !apiClient) {
      console.log('fetchMetrics early return:', { isAdmin, hasApiClient: !!apiClient })
      return
    }

    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cached = adminCache.get<SystemMetrics>(cacheKey)
      if (cached) {
        console.log('fetchMetrics using cached data:', cached)
        setMetrics(cached)
        return
      }
    }

    try {
      setLoading(true)
      clearError()

      console.log('fetchMetrics making API call...')
      const data = await apiClient.getSystemMetrics()
      console.log('fetchMetrics received data:', data)
      setMetrics(data)

      // Cache the result for 30 seconds
      adminCache.set(cacheKey, data, 30000)
    } catch (err) {
      console.log('fetchMetrics error:', err)
      handleError(err)
    } finally {
      setLoading(false)
    }
  }, [isAdmin, apiClient, setLoading, clearError, handleError, cacheKey])

  useEffect(() => {
    fetchMetrics()
  }, [fetchMetrics])

  const refetch = useCallback(() => {
    adminCache.invalidate(cacheKey)
    return fetchMetrics(true)
  }, [fetchMetrics, cacheKey])

  return {
    metrics,
    loading,
    error,
    clearError,
    refetch
  }
}

/**
 * Hook for managing users list with pagination and filtering
 * Includes debouncing for search and caching for performance
 */
export function useAdminUsers(initialParams: AdminUsersListParams = {}, options?: UseAdminOptions) {
  const [users, setUsers] = useState<PaginatedUsersResponse | null>(null)
  const [params, setParams] = useState<AdminUsersListParams>(initialParams)
  const { isAdmin, loading, error, clearError, handleError, apiClient, setLoading } = useAdmin(options)

  // Debounce search parameters to reduce API calls
  const debouncedParams = useDebounce(params, 300)

  // Generate cache key from parameters
  const cacheKey = useMemo(() => {
    const searchParams = new URLSearchParams()
    if (debouncedParams.page !== undefined) searchParams.set('page', debouncedParams.page.toString())
    if (debouncedParams.size !== undefined) searchParams.set('size', debouncedParams.size.toString())
    if (debouncedParams.role) searchParams.set('role', debouncedParams.role)
    if (debouncedParams.active !== undefined) searchParams.set('active', debouncedParams.active.toString())
    return `admin-users-${searchParams.toString()}`
  }, [debouncedParams])

  const fetchUsers = useCallback(async (searchParams: AdminUsersListParams = debouncedParams, forceRefresh = false) => {
    if (!isAdmin || !apiClient) return

    // Generate cache key for this specific request
    const sp = new URLSearchParams()
    if (searchParams.page !== undefined) sp.set('page', searchParams.page.toString())
    if (searchParams.size !== undefined) sp.set('size', searchParams.size.toString())
    if (searchParams.role) sp.set('role', searchParams.role)
    if (searchParams.active !== undefined) sp.set('active', searchParams.active.toString())
    const requestCacheKey = `admin-users-${sp.toString()}`

    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cached = adminCache.get<PaginatedUsersResponse>(requestCacheKey)
      if (cached) {
        setUsers(cached)
        return
      }
    }

    try {
      setLoading(true)
      clearError()

      const data = await apiClient.getUsers(searchParams)
      setUsers(data)

      // Cache the result for 1 minute
      adminCache.set(requestCacheKey, data, 60000)
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }, [isAdmin, apiClient, debouncedParams, setLoading, clearError, handleError])

  const updateParams = useCallback((newParams: AdminUsersListParams) => {
    setParams(newParams)
    // Clear cache when params change to force fresh data
    adminCache.clear()
  }, [])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const refetch = useCallback(() => {
    adminCache.invalidate(cacheKey)
    return fetchUsers(debouncedParams, true)
  }, [fetchUsers, debouncedParams, cacheKey])

  return {
    users,
    params,
    loading,
    error,
    clearError,
    updateParams,
    refetch
  }
}

/**
 * Hook for fetching detailed user information with caching
 */
export function useUserDetails(userId: string | null, options?: UseAdminOptions) {
  const [userDetails, setUserDetails] = useState<AdminUserDetails | null>(null)
  const { isAdmin, loading, error, clearError, handleError, apiClient, setLoading } = useAdmin(options)

  const cacheKey = userId ? `user-details-${userId}` : null

  const fetchUserDetails = useCallback(async (id: string, forceRefresh = false) => {
    if (!isAdmin || !apiClient) return

    // Check cache first (unless force refresh)
    if (!forceRefresh && cacheKey) {
      const cached = adminCache.get<AdminUserDetails>(cacheKey)
      if (cached) {
        setUserDetails(cached)
        return
      }
    }

    try {
      setLoading(true)
      clearError()

      const data = await apiClient.getUserDetails(id)
      setUserDetails(data)

      // Cache the result for 2 minutes
      if (cacheKey) {
        adminCache.set(cacheKey, data, 120000)
      }
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }, [isAdmin, apiClient, setLoading, clearError, handleError, cacheKey])

  useEffect(() => {
    if (userId) {
      fetchUserDetails(userId)
    } else {
      setUserDetails(null)
    }
  }, [userId, fetchUserDetails])

  const refetch = useCallback(() => {
    if (userId && cacheKey) {
      adminCache.invalidate(cacheKey)
      return fetchUserDetails(userId, true)
    }
  }, [userId, cacheKey, fetchUserDetails])

  return {
    userDetails,
    loading,
    error,
    clearError,
    refetch
  }
}

/**
 * Hook for fetching market data status with caching
 */
export function useMarketDataStatus(options?: UseAdminOptions) {
  const [marketDataStatus, setMarketDataStatus] = useState<MarketDataStatus | null>(null)
  const { isAdmin, loading, error, clearError, handleError, apiClient, setLoading } = useAdmin(options)
  const cacheKey = 'market-data-status'

  const fetchMarketDataStatus = useCallback(async (forceRefresh = false) => {
    if (!isAdmin || !apiClient) return

    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cached = adminCache.get<MarketDataStatus>(cacheKey)
      if (cached) {
        setMarketDataStatus(cached)
        return
      }
    }

    try {
      setLoading(true)
      clearError()

      const data = await apiClient.getMarketDataStatus()
      setMarketDataStatus(data)

      // Cache the result for 1 minute (market data status changes frequently)
      adminCache.set(cacheKey, data, 60000)
    } catch (err) {
      handleError(err)
    } finally {
      setLoading(false)
    }
  }, [isAdmin, apiClient, setLoading, clearError, handleError, cacheKey])

  useEffect(() => {
    fetchMarketDataStatus()
  }, [fetchMarketDataStatus])

  const refetch = useCallback(() => {
    adminCache.invalidate(cacheKey)
    return fetchMarketDataStatus(true)
  }, [fetchMarketDataStatus, cacheKey])

  return {
    marketDataStatus,
    loading,
    error,
    clearError,
    refetch
  }
}