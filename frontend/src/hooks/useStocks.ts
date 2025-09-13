'use client'

import { useState, useCallback } from 'react'

export interface Stock {
  id: string
  symbol: string
  company_name: string
  exchange: string
  current_price: string | null
  daily_change: string | null
  daily_change_percent: string | null
  status: string
  last_price_update: string | null
}

const API_BASE = 'http://localhost:8001'

export function useStocks() {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const getAuthHeaders = () => {
    const token = localStorage.getItem('auth_token')
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  }

  const searchStocks = useCallback(async (query?: string, limit = 20) => {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      if (query) params.append('q', query)
      params.append('limit', limit.toString())

      const response = await fetch(
        `${API_BASE}/api/v1/stocks?${params.toString()}`,
        {
          headers: getAuthHeaders()
        }
      )

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required. Please log in.')
        }
        throw new Error(`Failed to search stocks: ${response.status}`)
      }

      const data: Stock[] = await response.json()
      setStocks(data)
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to search stocks'
      setError(errorMessage)
      console.error('Error searching stocks:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const getAllStocks = useCallback(async () => {
    return searchStocks(undefined, 50)
  }, [searchStocks])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    stocks,
    loading,
    error,
    searchStocks,
    getAllStocks,
    clearError
  }
}