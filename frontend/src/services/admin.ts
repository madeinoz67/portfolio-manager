/**
 * Admin API service functions
 * Provides typed HTTP client functions for admin endpoints
 */

import {
  SystemMetrics,
  PaginatedUsersResponse,
  AdminUserDetails,
  MarketDataStatus,
  AdminUsersListParams,
  ApiError
} from '@/types/admin'

const getApiBaseUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export interface AdminApiOptions {
  token?: string
  signal?: AbortSignal
}

class AdminApiError extends Error {
  public status: number
  public response: Response

  constructor(message: string, status: number, response: Response) {
    super(message)
    this.name = 'AdminApiError'
    this.status = status
    this.response = response
  }
}

/**
 * Helper function to make authenticated admin API calls
 */
async function adminFetch(
  endpoint: string,
  options: AdminApiOptions & RequestInit = {}
): Promise<Response> {
  const { token, signal, ...fetchOptions } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  try {
    const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
      ...fetchOptions,
      headers,
      signal
    })

    if (!response.ok) {
      const errorBody = await response.text().catch(() => 'Unknown error')
      let errorMessage = `Request failed with status ${response.status}`

      try {
        const errorData = JSON.parse(errorBody)
        // Handle both FastAPI format (detail) and our ApiError format (message)
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch {
        // Use default error message if JSON parsing fails
      }

      throw new AdminApiError(errorMessage, response.status, response)
    }

    return response
  } catch (error) {
    // Handle network errors (Failed to fetch, CORS, connection refused, etc.)
    if (error instanceof AdminApiError) {
      // Re-throw AdminApiError (HTTP errors)
      throw error
    }

    // Handle network/fetch errors
    if (error instanceof TypeError) {
      if (error.message.includes('Failed to fetch')) {
        throw new AdminApiError(
          'Network connection failed. Please check your internet connection and ensure the backend server is running.',
          0, // Use 0 for network errors
          {} as Response
        )
      }
      if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
        throw new AdminApiError(
          `Network error: ${error.message}`,
          0,
          {} as Response
        )
      }
    }

    // Handle AbortError (request cancellation)
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new AdminApiError('Request was cancelled', 0, {} as Response)
    }

    // Handle any other errors
    throw new AdminApiError(
      `Request failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      0,
      {} as Response
    )
  }
}

/**
 * Get system-wide metrics and statistics
 */
export async function getSystemMetrics(options: AdminApiOptions = {}): Promise<SystemMetrics> {
  const response = await adminFetch('/api/v1/admin/system/metrics', {
    method: 'GET',
    ...options
  })

  return response.json()
}

/**
 * Get paginated list of users with filtering options
 */
export async function getUsers(
  params: AdminUsersListParams = {},
  options: AdminApiOptions = {}
): Promise<PaginatedUsersResponse> {
  const searchParams = new URLSearchParams()

  if (params.page !== undefined) searchParams.set('page', params.page.toString())
  if (params.size !== undefined) searchParams.set('size', params.size.toString())
  if (params.role) searchParams.set('role', params.role)
  if (params.active !== undefined) searchParams.set('active', params.active.toString())

  const queryString = searchParams.toString()
  const endpoint = `/api/v1/admin/users${queryString ? `?${queryString}` : ''}`

  const response = await adminFetch(endpoint, {
    method: 'GET',
    ...options
  })

  return response.json()
}

/**
 * Get detailed information about a specific user
 */
export async function getUserDetails(
  userId: string,
  options: AdminApiOptions = {}
): Promise<AdminUserDetails> {
  const response = await adminFetch(`/api/v1/admin/users/${userId}`, {
    method: 'GET',
    ...options
  })

  return response.json()
}

/**
 * Get market data providers status and usage
 */
export async function getMarketDataStatus(options: AdminApiOptions = {}): Promise<MarketDataStatus> {
  const response = await adminFetch('/api/v1/admin/market-data/status', {
    method: 'GET',
    ...options
  })

  return response.json()
}

/**
 * Toggle market data provider enabled/disabled status
 */
export async function toggleMarketDataProvider(
  providerId: string,
  options: AdminApiOptions = {}
): Promise<{ message: string; isEnabled: boolean; providerId: string }> {
  const response = await adminFetch(`/api/v1/admin/market-data/providers/${providerId}/toggle`, {
    method: 'PATCH',
    ...options
  })

  return response.json()
}

/**
 * Admin API client with error handling and retry logic
 */
export class AdminApiClient {
  private token?: string
  private controller?: AbortController

  constructor(token?: string) {
    this.token = token
  }

  setToken(token?: string) {
    this.token = token
  }

  abort() {
    this.controller?.abort()
    this.controller = undefined
  }

  private getOptions(customOptions: AdminApiOptions = {}): AdminApiOptions {
    this.controller = new AbortController()

    return {
      token: this.token,
      signal: this.controller.signal,
      ...customOptions
    }
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    return getSystemMetrics(this.getOptions())
  }

  async getUsers(params: AdminUsersListParams = {}): Promise<PaginatedUsersResponse> {
    return getUsers(params, this.getOptions())
  }

  async getUserDetails(userId: string): Promise<AdminUserDetails> {
    return getUserDetails(userId, this.getOptions())
  }

  async getMarketDataStatus(): Promise<MarketDataStatus> {
    return getMarketDataStatus(this.getOptions())
  }

  async toggleMarketDataProvider(providerId: string): Promise<{ message: string; isEnabled: boolean; providerId: string }> {
    return toggleMarketDataProvider(providerId, this.getOptions())
  }
}

// Export individual functions for direct use
export { AdminApiError }