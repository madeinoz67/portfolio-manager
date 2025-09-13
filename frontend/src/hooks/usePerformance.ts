'use client'

import { useState, useEffect, useCallback } from 'react'
import { PerformanceMetrics, PerformancePeriod } from '@/types/performance'
import { useAuth } from '@/contexts/AuthContext'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export function usePerformance(portfolioId: string, period: string = PerformancePeriod.ONE_MONTH) {
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { token } = useAuth()

  const getAuthHeaders = () => {
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  }

  const fetchPerformance = useCallback(async () => {
    if (!portfolioId) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/portfolios/${portfolioId}/performance?period=${period}`,
        {
          headers: getAuthHeaders()
        }
      )

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required. Please log in.')
        }
        if (response.status === 404) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Portfolio not found')
        }
        throw new Error(`Failed to fetch performance: ${response.status}`)
      }

      const data: PerformanceMetrics = await response.json()
      setPerformance(data)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch performance'
      setError(errorMessage)
      console.error('Error fetching performance:', err)
    } finally {
      setLoading(false)
    }
  }, [portfolioId, period, token])

  const refreshPerformance = useCallback(() => {
    return fetchPerformance()
  }, [fetchPerformance])

  useEffect(() => {
    if (portfolioId) {
      fetchPerformance()
    }
  }, [fetchPerformance])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    performance,
    loading,
    error,
    refreshPerformance,
    clearError
  }
}