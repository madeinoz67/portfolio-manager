'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useAuth } from '@/contexts/AuthContext'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export interface Holding {
  id: string
  portfolio_id: string
  stock: {
    id: string
    symbol: string
    company_name: string
    exchange?: string
    current_price?: string
    daily_change?: string
    daily_change_percent?: string
    status: string
    last_price_update?: string
  }
  quantity: string
  average_cost: string
  current_value: string
  unrealized_gain_loss: string
  unrealized_gain_loss_percent: string
  created_at: string
  updated_at: string
  recent_news_count?: number
}

export function useHoldings(portfolioId: string, autoRefresh: boolean = true) {
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const { token } = useAuth()
  const refreshInterval = useRef<NodeJS.Timeout | null>(null)

  const getAuthHeaders = () => {
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  }

  const fetchHoldings = useCallback(async () => {
    if (!portfolioId || !token) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/portfolios/${portfolioId}/holdings`,
        {
          headers: getAuthHeaders()
        }
      )

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required. Please log in.')
        }
        if (response.status === 404) {
          throw new Error('Portfolio not found')
        }
        throw new Error(`Failed to fetch holdings: ${response.status}`)
      }

      const data: Holding[] = await response.json()
      setHoldings(data)
      setLastUpdated(new Date())
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch holdings'
      setError(errorMessage)
      console.error('Error fetching holdings:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [portfolioId, token])

  const calculatePortfolioSummary = useCallback(() => {
    if (holdings.length === 0) {
      return {
        totalValue: 0,
        totalCost: 0,
        totalGainLoss: 0,
        totalGainLossPercent: 0
      }
    }

    const totalValue = holdings.reduce((sum, holding) => 
      sum + parseFloat(holding.current_value), 0
    )

    const totalCost = holdings.reduce((sum, holding) => 
      sum + (parseFloat(holding.quantity) * parseFloat(holding.average_cost)), 0
    )

    const totalGainLoss = holdings.reduce((sum, holding) => 
      sum + parseFloat(holding.unrealized_gain_loss), 0
    )

    const totalGainLossPercent = totalCost > 0 ? (totalGainLoss / totalCost) * 100 : 0

    return {
      totalValue,
      totalCost,
      totalGainLoss,
      totalGainLossPercent
    }
  }, [holdings])

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh && portfolioId && token) {
      // Clear any existing interval
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current)
      }

      // Set up auto-refresh every 30 seconds (configurable)
      refreshInterval.current = setInterval(() => {
        fetchHoldings().catch(err => {
          console.error('Auto-refresh failed:', err)
          // Don't show error to user for background refreshes
        })
      }, 30000) // 30 seconds

      // Cleanup on unmount or dependency change
      return () => {
        if (refreshInterval.current) {
          clearInterval(refreshInterval.current)
          refreshInterval.current = null
        }
      }
    }
  }, [autoRefresh, portfolioId, token, fetchHoldings])

  // Initial load effect
  useEffect(() => {
    if (portfolioId && token) {
      fetchHoldings()
    }
  }, [portfolioId, token, fetchHoldings])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    holdings,
    loading,
    error,
    lastUpdated,
    fetchHoldings,
    calculatePortfolioSummary,
    clearError
  }
}