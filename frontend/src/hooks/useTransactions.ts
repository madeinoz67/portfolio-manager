'use client'

import { useState, useCallback } from 'react'
import { Transaction, TransactionCreate, TransactionListResponse } from '@/types/transaction'

const API_BASE = 'http://localhost:8001'

export function useTransactions(portfolioId: string) {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  const getAuthHeaders = () => {
    const token = localStorage.getItem('auth_token')
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  }

  const fetchTransactions = useCallback(async (limit = 50, offset = 0) => {
    if (!portfolioId) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/portfolios/${portfolioId}/transactions?limit=${limit}&offset=${offset}`,
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
        throw new Error(`Failed to fetch transactions: ${response.status}`)
      }

      const data: TransactionListResponse = await response.json()
      
      if (offset === 0) {
        setTransactions(data.transactions)
      } else {
        setTransactions(prev => [...prev, ...data.transactions])
      }
      
      setTotal(data.total)
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch transactions'
      setError(errorMessage)
      console.error('Error fetching transactions:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [portfolioId])

  const createTransaction = useCallback(async (transactionData: TransactionCreate): Promise<boolean> => {
    if (!portfolioId) {
      setError('Portfolio ID is required')
      return false
    }

    console.log('Creating transaction with data:', transactionData)
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${API_BASE}/api/v1/portfolios/${portfolioId}/transactions`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify(transactionData)
        }
      )

      console.log('Transaction API response status:', response.status)

      if (!response.ok) {
        const responseText = await response.text()
        console.error('Transaction API error response:', responseText)
        
        if (response.status === 401) {
          throw new Error('Authentication required. Please log in.')
        }
        if (response.status === 404) {
          throw new Error('Portfolio not found')
        }
        if (response.status === 422) {
          try {
            const errorData = JSON.parse(responseText)
            const errorMessage = errorData.detail?.[0]?.msg || 'Invalid transaction data'
            throw new Error(errorMessage)
          } catch {
            throw new Error('Invalid transaction data')
          }
        }
        throw new Error(`Failed to create transaction: ${response.status}`)
      }

      const newTransaction: Transaction = await response.json()
      console.log('Transaction created successfully:', newTransaction)
      
      // Add new transaction to the beginning of the list
      setTransactions(prev => [newTransaction, ...prev])
      setTotal(prev => prev + 1)
      
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create transaction'
      console.error('Error creating transaction:', err)
      setError(errorMessage)
      return false
    } finally {
      setLoading(false)
    }
  }, [portfolioId])

  const refreshTransactions = useCallback(() => {
    return fetchTransactions(50, 0)
  }, [fetchTransactions])

  const loadMoreTransactions = useCallback(() => {
    return fetchTransactions(50, transactions.length)
  }, [fetchTransactions, transactions.length])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    transactions,
    loading,
    error,
    total,
    fetchTransactions,
    createTransaction,
    refreshTransactions,
    loadMoreTransactions,
    clearError,
    hasMore: transactions.length < total
  }
}