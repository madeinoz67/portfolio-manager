'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import Button from '@/components/ui/Button'
import { useAuth } from '@/contexts/AuthContext'

interface Stock {
  id: string
  symbol: string
  company_name: string
  current_price?: string
  exchange?: string
  sector?: string
  market_cap?: string
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
  processed_date: string
  notes?: string
  source_type: string
  is_verified: boolean
}

export default function TransactionDetail() {
  const params = useParams()
  const router = useRouter()
  const { token } = useAuth()
  const portfolioId = params?.id as string
  const transactionId = params?.transactionId as string

  const [transaction, setTransaction] = useState<Transaction | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTransaction = useCallback(async () => {
    if (!portfolioId || !transactionId || !token) return

    try {
      setLoading(true)
      setError(null)

      const response = await fetch(
        `http://localhost:8001/api/v1/portfolios/${portfolioId}/transactions/${transactionId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      )

      if (!response.ok) {
        if (response.status === 401) {
          router.push('/login')
          return
        }
        if (response.status === 404) {
          throw new Error('Transaction not found')
        }
        throw new Error(`Failed to fetch transaction: ${response.status}`)
      }

      const transactionData = await response.json()
      setTransaction(transactionData)
    } catch (err) {
      console.error('Error fetching transaction:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch transaction')
    } finally {
      setLoading(false)
    }
  }, [portfolioId, transactionId, token, router])

  useEffect(() => {
    fetchTransaction()
  }, [fetchTransaction])

  const formatCurrency = (amount: string) => {
    return `$${parseFloat(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
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
        <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <ErrorMessage 
            message={error} 
            onRetry={fetchTransaction}
          />
        </div>
      </div>
    )
  }

  if (!transaction) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <ErrorMessage message="Transaction not found" />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <nav className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400 mb-4">
            <Link href="/portfolios" className="hover:text-gray-700 dark:hover:text-gray-300">
              Portfolios
            </Link>
            <span>/</span>
            <Link href={`/portfolios/${portfolioId}`} className="hover:text-gray-700 dark:hover:text-gray-300">
              Portfolio
            </Link>
            <span>/</span>
            <span className="text-gray-900 dark:text-white">Transaction Details</span>
          </nav>
          
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Transaction Details
            </h1>
            <Link href={`/portfolios/${portfolioId}`}>
              <Button variant="secondary">
                Back to Portfolio
              </Button>
            </Link>
          </div>
        </div>

        {/* Transaction Details Card */}
        <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {transaction.stock.symbol} - {transaction.stock.company_name}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {transaction.stock.exchange && `${transaction.stock.exchange} • `}
                  Transaction ID: {transaction.id}
                </p>
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                transaction.transaction_type === 'BUY'
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
              }`}>
                {transaction.transaction_type}
              </div>
            </div>
          </div>

          {/* Details Grid */}
          <div className="px-6 py-6">
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Quantity</dt>
                <dd className="mt-1 text-lg text-gray-900 dark:text-white">
                  {parseFloat(transaction.quantity).toLocaleString()} shares
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Price per Share</dt>
                <dd className="mt-1 text-lg text-gray-900 dark:text-white">
                  {formatCurrency(transaction.price_per_share)}
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Amount</dt>
                <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-white">
                  {formatCurrency(transaction.total_amount)}
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Fees</dt>
                <dd className="mt-1 text-lg text-gray-900 dark:text-white">
                  {formatCurrency(transaction.fees)}
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Transaction Date</dt>
                <dd className="mt-1 text-lg text-gray-900 dark:text-white">
                  {formatDate(transaction.transaction_date)}
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Processed Date</dt>
                <dd className="mt-1 text-lg text-gray-900 dark:text-white">
                  {formatDateTime(transaction.processed_date)}
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Source</dt>
                <dd className="mt-1 text-lg text-gray-900 dark:text-white">
                  {transaction.source_type}
                </dd>
              </div>

              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Status</dt>
                <dd className="mt-1">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    transaction.is_verified
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                      : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                  }`}>
                    {transaction.is_verified ? 'Verified' : 'Pending'}
                  </span>
                </dd>
              </div>

              {transaction.notes && (
                <div className="md:col-span-2">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Notes</dt>
                  <dd className="mt-1 text-lg text-gray-900 dark:text-white">
                    {transaction.notes}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Stock Information */}
          {transaction.stock.current_price && (
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Current Stock Information
              </h3>
              <dl className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">Current Price</dt>
                  <dd className="text-sm text-gray-900 dark:text-white">
                    {formatCurrency(transaction.stock.current_price)}
                  </dd>
                </div>
                {transaction.stock.sector && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">Sector</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">
                      {transaction.stock.sector}
                    </dd>
                  </div>
                )}
                {transaction.stock.market_cap && (
                  <div>
                    <dt className="text-xs font-medium text-gray-500 dark:text-gray-400">Market Cap</dt>
                    <dd className="text-sm text-gray-900 dark:text-white">
                      {transaction.stock.market_cap}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}