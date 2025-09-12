import { useState, useEffect } from 'react'
import { Portfolio, CreatePortfolioData } from '@/types/portfolio'
import { useAuth } from '@/contexts/AuthContext'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export function usePortfolios() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { token, user } = useAuth()

  const getAuthHeaders = () => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return headers
  }

  const fetchPortfolios = async () => {
    if (!token || !user) {
      setPortfolios([])
      setLoading(false)
      setError(null)
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
        setError(null)
      } else if (response.status === 401) {
        setError('Authentication required. Please log in.')
      } else {
        setError('Failed to fetch portfolios')
      }
    } catch (error) {
      setError('Connection error')
      console.error('Error fetching portfolios:', error)
    } finally {
      setLoading(false)
    }
  }

  const createPortfolio = async (portfolioData: CreatePortfolioData) => {
    if (!token) {
      setError('Authentication required. Please log in.')
      return false
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/portfolios`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(portfolioData),
      })
      
      if (response.ok) {
        await fetchPortfolios() // Refresh the list
        return true
      } else if (response.status === 401) {
        setError('Authentication required. Please log in.')
        return false
      } else {
        setError('Failed to create portfolio')
        return false
      }
    } catch (error) {
      setError('Connection error')
      console.error('Error creating portfolio:', error)
      return false
    }
  }

  useEffect(() => {
    fetchPortfolios()
  }, [token, user]) // Re-fetch when auth state changes

  return {
    portfolios,
    loading,
    error,
    fetchPortfolios,
    createPortfolio
  }
}