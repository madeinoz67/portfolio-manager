import { useState, useEffect, useCallback, useRef } from 'react'
import { Portfolio, CreatePortfolioData } from '@/types/portfolio'
import { useAuth } from '@/contexts/AuthContext'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export type ErrorType = 'NETWORK_ERROR' | 'HTTP_ERROR' | 'OFFLINE_ERROR' | 'UNKNOWN_ERROR'

export interface ErrorDetails {
  message: string
  type: ErrorType
  retryable: boolean
  timestamp: Date
}

export interface RecoveryAction {
  type: 'retry' | 'refresh' | 'contact'
  label: string
  action: () => void
}

interface UsePortfoliosOptions {
  onUnauthorized?: (redirectPath: string) => void
}

export function usePortfolios(options?: UsePortfoliosOptions) {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [errorType, setErrorType] = useState<ErrorType | null>(null)
  const [errorDetails, setErrorDetails] = useState<ErrorDetails | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [isRetrying, setIsRetrying] = useState(false)
  const [canRetry, setCanRetry] = useState(true)
  const [isOffline, setIsOffline] = useState(!navigator.onLine)
  
  const { token, user } = useAuth()
  const retryTimeoutRef = useRef<NodeJS.Timeout>()
  const maxRetries = 2

  const getAuthHeaders = () => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return headers
  }

  const classifyError = (error: any): ErrorDetails => {
    let errorType: ErrorType = 'UNKNOWN_ERROR'
    let message = 'An unexpected error occurred'
    let retryable = false

    if (!navigator.onLine) {
      errorType = 'OFFLINE_ERROR'
      message = 'You appear to be offline. Please check your internet connection.'
      retryable = true
    } else if (error instanceof Error && (error.message.includes('Network Error') || error.message.includes('fetch'))) {
      errorType = 'NETWORK_ERROR'
      message = error.message
      retryable = true
    } else if (error.status) {
      errorType = 'HTTP_ERROR'
      retryable = error.status >= 500
      
      switch (error.status) {
        case 401:
          message = 'Authentication required. Please log in.'
          retryable = false
          break
        case 404:
          message = 'The requested resource was not found.'
          retryable = false
          break
        case 429:
          message = 'Too many requests. Please wait a moment and try again.'
          retryable = true
          break
        case 503:
          message = 'Service temporarily unavailable. Please try again later.'
          retryable = true
          break
        default:
          message = error.message || `HTTP ${error.status} error`
      }
    } else if (error.message) {
      message = error.message
      retryable = error.message.includes('Network Error')
    }

    return {
      message,
      type: errorType,
      retryable,
      timestamp: new Date()
    }
  }

  const getUserFriendlyError = (errorDetails: ErrorDetails): string => {
    switch (errorDetails.type) {
      case 'OFFLINE_ERROR':
        return 'You appear to be offline. Please check your internet connection.'
      case 'NETWORK_ERROR':
        if (retryCount >= maxRetries) {
          return 'Unable to connect after multiple attempts. Please check your internet connection.'
        }
        return errorDetails.message
      case 'HTTP_ERROR':
        return errorDetails.message
      default:
        return errorDetails.message
    }
  }

  const getRecoveryActions = (): RecoveryAction[] => {
    return [
      {
        type: 'retry',
        label: 'Try Again',
        action: manualRetry
      },
      {
        type: 'refresh',
        label: 'Refresh Page',
        action: () => window.location.reload()
      },
      {
        type: 'contact',
        label: 'Contact Support',
        action: () => console.log('Contact support clicked')
      }
    ]
  }

  const resetErrorState = () => {
    setError(null)
    setErrorType(null)
    setErrorDetails(null)
    setIsRetrying(false)
  }

  const handleError = (err: any, shouldRetry: boolean = true) => {
    const details = classifyError(err)
    setErrorDetails(details)
    setErrorType(details.type)
    setError(getUserFriendlyError(details))

    if (err.status === 401 && options?.onUnauthorized) {
      options.onUnauthorized('/login')
      return
    }

    if (shouldRetry && details.retryable && retryCount < maxRetries) {
      scheduleRetry()
    } else {
      setRetryCount(0)
      setIsRetrying(false)
      setCanRetry(details.retryable)
    }
  }

  const scheduleRetry = () => {
    const currentRetryCount = retryCount
    setIsRetrying(true)
    setRetryCount(prev => prev + 1)
    const delay = Math.pow(2, currentRetryCount) * 1000

    retryTimeoutRef.current = setTimeout(() => {
      fetchPortfolios(false)
    }, delay)
  }

  const manualRetry = useCallback(() => {
    setRetryCount(0)
    fetchPortfolios(true)
  }, [])

  const fetchPortfolios = async (resetRetries: boolean = true) => {
    if (!token || !user) {
      setPortfolios([])
      setLoading(false)
      resetErrorState()
      if (resetRetries) setRetryCount(0)
      return
    }

    if (resetRetries) {
      setRetryCount(0)
      resetErrorState()
    }

    // Check if we're offline at the start
    if (!navigator.onLine) {
      setLoading(false)
      handleError({ message: 'You appear to be offline. Please check your internet connection.' }, false)
      return
    }

    try {
      setLoading(true)
      
      const response = await fetch(`${API_BASE_URL}/api/v1/portfolios`, {
        headers: getAuthHeaders(),
      })
      
      if (response.ok) {
        const data = await response.json()
        setPortfolios(data)
        resetErrorState()
        setRetryCount(0)
        setCanRetry(true)
      } else {
        const errorData = await response.json().catch(() => ({}))
        const error = {
          status: response.status,
          message: errorData.detail || `HTTP ${response.status} error`
        }
        throw error
      }
    } catch (err) {
      console.error('Error fetching portfolios:', err)
      handleError(err)
    } finally {
      setLoading(false)
    }
  }

  const createPortfolio = async (portfolioData: CreatePortfolioData) => {
    if (!token) {
      handleError({ status: 401, message: 'Authentication required. Please log in.' }, false)
      return false
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/portfolios`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(portfolioData),
      })
      
      if (response.ok) {
        await fetchPortfolios()
        return true
      } else {
        const errorData = await response.json().catch(() => ({}))
        const error = {
          status: response.status,
          message: errorData.detail || 'Failed to create portfolio'
        }
        throw error
      }
    } catch (err) {
      console.error('Error creating portfolio:', err)
      handleError(err, false)
      return false
    }
  }

  // Handle online/offline events
  useEffect(() => {
    const handleOnline = () => {
      setIsOffline(false)
      if (error && errorType === 'OFFLINE_ERROR') {
        fetchPortfolios()
      }
    }

    const handleOffline = () => {
      setIsOffline(true)
      handleError({ message: 'You appear to be offline. Please check your internet connection.' }, false)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [error, errorType])

  useEffect(() => {
    fetchPortfolios()
    
    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current)
      }
    }
  }, [token, user])

  return {
    portfolios,
    loading,
    error,
    errorType,
    errorDetails,
    userFriendlyError: errorDetails ? getUserFriendlyError(errorDetails) : null,
    retryCount,
    isRetrying,
    canRetry,
    isOffline,
    recoveryActions: getRecoveryActions(),
    fetchPortfolios: () => fetchPortfolios(true),
    createPortfolio,
    manualRetry
  }
}