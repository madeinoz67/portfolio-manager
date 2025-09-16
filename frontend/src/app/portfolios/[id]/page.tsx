'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import TransactionForm from '@/components/Transaction/TransactionForm'
import TransactionList from '@/components/Transaction/TransactionList'
import HoldingsDisplay from '@/components/Portfolio/HoldingsDisplay'
import PortfolioEditForm from '@/components/Portfolio/PortfolioEditForm'
import PerformanceMetrics from '@/components/Portfolio/PerformanceMetrics'
import { useToast } from '@/components/ui/Toast'
import { useTransactions } from '@/hooks/useTransactions'
import { useHoldings } from '@/hooks/useHoldings'
import { usePortfolios } from '@/hooks/usePortfolios'
import { TransactionCreate } from '@/types/transaction'
import Button from '@/components/ui/Button'

interface Portfolio {
  id: string
  name: string
  description?: string
  total_value: string
  daily_change: string
  daily_change_percent: string
  created_at: string
  updated_at: string
}

interface Stock {
  id: string
  symbol: string
  company_name: string
  current_price?: string
  sector?: string
  market_cap?: string
}

interface Holding {
  id: string
  stock: Stock
  quantity: string
  average_cost: string
  current_value: string
  unrealized_gain_loss: string
  unrealized_gain_loss_percent: string
  recent_news_count: number
  created_at: string
  updated_at: string
}

interface Transaction {
  id: string
  stock: Stock
  transaction_type: 'BUY' | 'SELL'
  quantity: string
  price_per_share: string
  total_amount: string
  fees: string
  transaction_date: string
  notes?: string
}

export default function PortfolioDetail() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const portfolioId = params?.id as string
  const { addToast } = useToast()

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showTransactionForm, setShowTransactionForm] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)

  const {
    transactions,
    createTransaction,
    refreshTransactions,
    loading: transactionLoading,
    error: transactionError
  } = useTransactions(portfolioId)

  const {
    holdings: holdingsData,
    calculatePortfolioSummary,
    fetchHoldings
  } = useHoldings(portfolioId)

  // Add usePortfolios hook to refresh global portfolio data
  const { fetchPortfolios } = usePortfolios()

  const fetchPortfolio = useCallback(async () => {
    if (!portfolioId) return

    try {
      setLoading(true)
      const token = localStorage.getItem('auth_token')
      if (!token) {
        router.push('/login')
        return
      }

      // Fetch portfolio details
      const portfolioResponse = await fetch(`http://localhost:8001/api/v1/portfolios/${portfolioId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!portfolioResponse.ok) {
        if (portfolioResponse.status === 401) {
          router.push('/login')
          return
        }
        throw new Error(`Failed to fetch portfolio: ${portfolioResponse.status}`)
      }

      const portfolioData = await portfolioResponse.json()
      setPortfolio(portfolioData)

      // Fetch portfolio holdings
      try {
        const holdingsResponse = await fetch(`http://localhost:8001/api/v1/portfolios/${portfolioId}/holdings`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })
        if (holdingsResponse.ok) {
          const holdingsData = await holdingsResponse.json()
          setHoldings(holdingsData)
        }
      } catch (err) {
        console.warn('Failed to fetch holdings:', err)
      }

    } catch (err) {
      console.error('Error fetching portfolio:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch portfolio')
    } finally {
      setLoading(false)
    }
  }, [portfolioId, router])

  useEffect(() => {
    fetchPortfolio()
  }, [fetchPortfolio])

  // Check for addTransaction query parameter and auto-open form
  useEffect(() => {
    const addTransactionParam = searchParams.get('addTransaction')
    if (addTransactionParam === 'true') {
      setShowTransactionForm(true)
      // Remove the query parameter from URL to clean it up
      const url = new URL(window.location.href)
      url.searchParams.delete('addTransaction')
      window.history.replaceState({}, '', url.toString())
    }
  }, [searchParams])

  const handleAddTransaction = async (transactionData: TransactionCreate) => {
    console.log('handleAddTransaction called with:', transactionData)
    
    try {
      console.log('Calling createTransaction...')
      const success = await createTransaction(transactionData)
      console.log('createTransaction returned:', success)
      
      if (success) {
        console.log('Transaction successful, showing success toast')
        addToast('Transaction added successfully!', 'success')
        setShowTransactionForm(false)
        
        console.log('Refreshing portfolio data...')
        // Refresh portfolio data to update totals
        await fetchPortfolio()
        // Also refresh global portfolios data for the dashboard
        await fetchPortfolios()
        console.log('Portfolio data refreshed')
        
        return true
      } else {
        console.log('Transaction failed, showing error toast')
        addToast('Failed to add transaction', 'error')
        return false
      }
    } catch (err) {
      console.error('Exception in handleAddTransaction:', err)
      addToast('Failed to add transaction', 'error')
      return false
    }
  }

  const handleRefreshData = async () => {
    await Promise.all([
      fetchPortfolio(),
      refreshTransactions(),
      fetchHoldings(),
      fetchPortfolios()
    ])
  }

  const handleTransactionUpdated = async () => {
    console.log('Transaction updated, refreshing portfolio data...')
    addToast('Transaction updated successfully!', 'success')

    // Refresh all portfolio-related data
    await Promise.all([
      fetchPortfolio(),
      refreshTransactions(),
      fetchHoldings(),
      fetchPortfolios()
    ])
    console.log('Portfolio data refreshed after transaction update')
  }

  const handleTransactionDeleted = async () => {
    console.log('Transaction deleted, refreshing portfolio data...')
    addToast('Transaction deleted successfully!', 'success')

    // Refresh all portfolio-related data
    await Promise.all([
      fetchPortfolio(),
      refreshTransactions(),
      fetchHoldings(),
      fetchPortfolios()
    ])
    console.log('Portfolio data refreshed after transaction deletion')
  }

  const handleUpdatePortfolio = (updatedPortfolio: Portfolio) => {
    setPortfolio(updatedPortfolio)
    setShowEditForm(false)
    addToast('Portfolio updated successfully!', 'success')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <ErrorMessage message={error} />
        </div>
      </div>
    )
  }

  if (!portfolio) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <ErrorMessage message="Portfolio not found" />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {portfolio.name}
              </h1>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowEditForm(true)}
              >
                Edit Portfolio
              </Button>
            </div>
            {portfolio.description && (
              <p className="text-gray-600 dark:text-gray-300">
                {portfolio.description}
              </p>
            )}
          </div>

          {/* Portfolio Edit Form */}
          {showEditForm && (
            <div className="mb-6">
              <PortfolioEditForm
                portfolio={portfolio}
                onUpdate={handleUpdatePortfolio}
                onCancel={() => setShowEditForm(false)}
              />
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
              <h3 className="text-sm font-medium text-blue-100">Total Value</h3>
              <p className="text-3xl font-bold">
                ${calculatePortfolioSummary().totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            
            <div className="bg-gradient-to-r from-green-500 to-blue-500 rounded-lg p-6 text-white">
              <h3 className="text-sm font-medium text-green-100">Total Cost</h3>
              <p className="text-3xl font-bold">
                ${calculatePortfolioSummary().totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg p-6 text-white">
              <h3 className="text-sm font-medium text-purple-100">Total Gain/Loss</h3>
              <p className={`text-3xl font-bold ${
                calculatePortfolioSummary().totalGainLoss >= 0 ? 'text-green-100' : 'text-red-100'
              }`}>
                {calculatePortfolioSummary().totalGainLoss >= 0 ? '+' : ''}${calculatePortfolioSummary().totalGainLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>

            <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-lg p-6 text-white">
              <h3 className="text-sm font-medium text-orange-100">Return %</h3>
              <p className={`text-3xl font-bold ${
                calculatePortfolioSummary().totalGainLossPercent >= 0 ? 'text-green-100' : 'text-red-100'
              }`}>
                {calculatePortfolioSummary().totalGainLossPercent >= 0 ? '+' : ''}{calculatePortfolioSummary().totalGainLossPercent.toFixed(2)}%
              </p>
            </div>
          </div>

          {/* Performance Metrics Section */}
          <div className="mb-8">
            <PerformanceMetrics portfolioId={portfolioId} />
          </div>

          {/* Holdings Section */}
          <div className="mb-8">
            <HoldingsDisplay portfolioId={portfolioId} />
          </div>

          {/* Transaction Management Section */}
          <div>
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Transaction Management
              </h2>
              <div className="flex gap-3">
                <Link href={`/analytics?portfolioId=${portfolioId}`}>
                  <Button
                    variant="secondary"
                    size="sm"
                  >
                    Portfolio Analysis
                  </Button>
                </Link>
                <Button
                  onClick={handleRefreshData}
                  variant="secondary"
                  size="sm"
                >
                  Refresh Data
                </Button>
                <Button
                  onClick={() => setShowTransactionForm(!showTransactionForm)}
                  size="sm"
                >
                  {showTransactionForm ? 'Hide Form' : 'Add Transaction'}
                </Button>
              </div>
            </div>

            {showTransactionForm && (
              <div className="mb-6">
                <TransactionForm
                  portfolioId={portfolioId}
                  onSubmit={handleAddTransaction}
                  onCancel={() => setShowTransactionForm(false)}
                />
              </div>
            )}

            <TransactionList
              portfolioId={portfolioId}
              onTransactionUpdated={handleTransactionUpdated}
              onTransactionDeleted={handleTransactionDeleted}
            />
          </div>
        </div>
      </div>
    </div>
  )
}