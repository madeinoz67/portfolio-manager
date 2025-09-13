'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import TransactionForm from '@/components/transaction/TransactionForm'
import TransactionList from '@/components/transaction/TransactionList'
import { useToast } from '@/components/ui/Toast'
import { useTransactions } from '@/hooks/useTransactions'
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
  const portfolioId = params?.id as string
  const { addToast } = useToast()

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showTransactionForm, setShowTransactionForm] = useState(false)

  const {
    transactions,
    createTransaction,
    refreshTransactions,
    loading: transactionLoading,
    error: transactionError
  } = useTransactions(portfolioId)

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
      refreshTransactions()
    ])
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
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {portfolio.name}
            </h1>
            {portfolio.description && (
              <p className="text-gray-600 dark:text-gray-300">
                {portfolio.description}
              </p>
            )}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
              <h3 className="text-sm font-medium text-blue-100">Total Value</h3>
              <p className="text-3xl font-bold">
                ${parseFloat(portfolio.total_value).toLocaleString()}
              </p>
            </div>
            
            <div className="bg-gradient-to-r from-green-500 to-blue-500 rounded-lg p-6 text-white">
              <h3 className="text-sm font-medium text-green-100">Daily Change</h3>
              <p className="text-3xl font-bold">
                ${parseFloat(portfolio.daily_change).toFixed(2)}
              </p>
            </div>
            
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg p-6 text-white">
              <h3 className="text-sm font-medium text-purple-100">Change %</h3>
              <p className="text-3xl font-bold">
                {parseFloat(portfolio.daily_change_percent).toFixed(2)}%
              </p>
            </div>
          </div>

          {/* Holdings Section */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Stock Holdings
            </h2>
            {holdings.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Stock
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Avg Cost
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Current Value
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Gain/Loss
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        %
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {holdings.map((holding) => (
                      <tr key={holding.id}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Link 
                            href={`/portfolios/${portfolioId}/holdings/${holding.id}`}
                            className="block hover:bg-gray-50 dark:hover:bg-gray-700 -m-2 p-2 rounded transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
                                  {holding.stock.symbol} →
                                </div>
                                <div className="text-sm text-gray-500 dark:text-gray-300">
                                  {holding.stock.company_name}
                                </div>
                              </div>
                              {holding.recent_news_count > 0 && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100 ml-2 flex-shrink-0">
                                  <span className="mr-1">📰</span>
                                  {holding.recent_news_count}
                                </span>
                              )}
                            </div>
                          </Link>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {parseFloat(holding.quantity).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          ${parseFloat(holding.average_cost).toFixed(2)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          ${parseFloat(holding.current_value).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`font-medium ${
                            parseFloat(holding.unrealized_gain_loss) >= 0
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-red-600 dark:text-red-400'
                          }`}>
                            {parseFloat(holding.unrealized_gain_loss) >= 0 ? '+' : ''}
                            ${parseFloat(holding.unrealized_gain_loss).toFixed(2)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`font-medium ${
                            parseFloat(holding.unrealized_gain_loss_percent) >= 0
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-red-600 dark:text-red-400'
                          }`}>
                            {parseFloat(holding.unrealized_gain_loss_percent) >= 0 ? '+' : ''}
                            {parseFloat(holding.unrealized_gain_loss_percent).toFixed(2)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p>No holdings found in this portfolio</p>
              </div>
            )}
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
            />
          </div>
        </div>
      </div>
    </div>
  )
}