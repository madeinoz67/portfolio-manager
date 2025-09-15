/**
 * Portfolio API service functions
 * Provides typed HTTP client functions for portfolio endpoints
 */

import type { Portfolio } from '@/types'

const getApiBaseUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export interface PortfolioApiOptions {
  token?: string
  signal?: AbortSignal
}

export interface PortfolioDeleteConfirmation {
  confirmationName: string
}

export interface PortfolioDeleteResponse {
  message: string
  portfolio_id: string
  deleted_at: string
}

class PortfolioApiError extends Error {
  public status: number
  public response: Response

  constructor(message: string, status: number, response: Response) {
    super(message)
    this.name = 'PortfolioApiError'
    this.status = status
    this.response = response
  }
}

/**
 * Helper function to make authenticated portfolio API calls
 */
async function portfolioFetch(
  endpoint: string,
  options: PortfolioApiOptions & RequestInit = {}
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
        // Handle both FastAPI format (detail) and our custom format
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch {
        // Use default error message if JSON parsing fails
      }

      throw new PortfolioApiError(errorMessage, response.status, response)
    }

    return response
  } catch (error) {
    // Handle network errors
    if (error instanceof PortfolioApiError) {
      throw error
    }

    if (error instanceof TypeError) {
      if (error.message.includes('Failed to fetch')) {
        throw new PortfolioApiError(
          'Network connection failed. Please check your internet connection and ensure the backend server is running.',
          0,
          {} as Response
        )
      }
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new PortfolioApiError('Request was cancelled', 0, {} as Response)
    }

    throw new PortfolioApiError(
      `Request failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      0,
      {} as Response
    )
  }
}

/**
 * Soft delete a portfolio with confirmation
 */
export async function deletePortfolio(
  portfolioId: string,
  confirmation: PortfolioDeleteConfirmation,
  options: PortfolioApiOptions = {}
): Promise<PortfolioDeleteResponse> {
  const response = await portfolioFetch(`/api/v1/portfolios/${portfolioId}/delete`, {
    method: 'POST',
    body: JSON.stringify({
      confirmation_name: confirmation.confirmationName
    }),
    ...options
  })

  return response.json()
}

/**
 * Hard delete a portfolio with confirmation (permanent removal)
 */
export async function hardDeletePortfolio(
  portfolioId: string,
  confirmation: PortfolioDeleteConfirmation,
  options: PortfolioApiOptions = {}
): Promise<PortfolioDeleteResponse> {
  const response = await portfolioFetch(`/api/v1/portfolios/${portfolioId}/hard-delete`, {
    method: 'POST',
    body: JSON.stringify({
      confirmation_name: confirmation.confirmationName
    }),
    ...options
  })

  return response.json()
}

/**
 * Portfolio API client with error handling
 */
export class PortfolioApiClient {
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

  private getOptions(customOptions: PortfolioApiOptions = {}): PortfolioApiOptions {
    this.controller = new AbortController()

    return {
      token: this.token,
      signal: this.controller.signal,
      ...customOptions
    }
  }

  async deletePortfolio(
    portfolioId: string,
    confirmation: PortfolioDeleteConfirmation
  ): Promise<PortfolioDeleteResponse> {
    return deletePortfolio(portfolioId, confirmation, this.getOptions())
  }

  async hardDeletePortfolio(
    portfolioId: string,
    confirmation: PortfolioDeleteConfirmation
  ): Promise<PortfolioDeleteResponse> {
    return hardDeletePortfolio(portfolioId, confirmation, this.getOptions())
  }
}

export { PortfolioApiError }