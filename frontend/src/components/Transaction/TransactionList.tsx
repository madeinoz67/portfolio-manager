'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Transaction } from '@/types/transaction'
import { useTransactions } from '@/hooks/useTransactions'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import Button from '@/components/ui/Button'
import TransactionFilter from './TransactionFilter'

interface TransactionListProps {
  portfolioId: string
}

export default function TransactionList({ portfolioId }: TransactionListProps) {
  const router = useRouter()
  const {
    transactions,
    loading,
    error,
    total,
    fetchTransactions,
    loadMoreTransactions,
    searchTransactions,
    hasMore,
    clearError
  } = useTransactions(portfolioId)

  const [currentFilters, setCurrentFilters] = useState<{
    startDate?: string
    endDate?: string
    stockSymbol?: string
  } | null>(null)
  const [showFilters, setShowFilters] = useState(false)

  useEffect(() => {
    if (portfolioId) {
      fetchTransactions()
    }
  }, [portfolioId, fetchTransactions])

  const handleFilter = async (filters: {
    startDate?: string
    endDate?: string
    stockSymbol?: string
  }) => {
    setCurrentFilters(filters)
    await searchTransactions(filters)
  }

  const handleClearFilters = async () => {
    setCurrentFilters(null)
    await fetchTransactions()
  }

  const handleLoadMore = () => {
    loadMoreTransactions(currentFilters || undefined)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const formatCurrency = (amount: string) => {
    return `$${parseFloat(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  if (loading && transactions.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <ErrorMessage 
        message={error} 
        onRetry={() => {
          clearError()
          fetchTransactions()
        }}
      />
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Transactions
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {total} total transaction{total !== 1 ? 's' : ''}
            </p>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </Button>
        </div>
      </div>

      {showFilters && (
        <div className="px-6">
          <TransactionFilter
            onFilter={handleFilter}
            onClear={handleClearFilters}
            loading={loading}
          />
        </div>
      )}

      {transactions.length === 0 ? (
        <div className="p-8 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No transactions yet
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Start building your portfolio by adding your first transaction.
          </p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Stock
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Total
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Fees
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {transactions.map((transaction) => (
                  <tr 
                    key={transaction.id} 
                    className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                    onClick={() => router.push(`/portfolios/${portfolioId}/transactions/${transaction.id}`)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {formatDate(transaction.transaction_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {transaction.stock.symbol}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                          {transaction.stock.company_name}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        transaction.transaction_type === 'BUY'
                          ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                          : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                      }`}>
                        {transaction.transaction_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white text-right">
                      {parseFloat(transaction.quantity).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white text-right">
                      {formatCurrency(transaction.price_per_share)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white text-right">
                      {formatCurrency(transaction.total_amount)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 text-right">
                      {parseFloat(transaction.fees) > 0 ? formatCurrency(transaction.fees) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {hasMore && (
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 text-center">
              <Button
                variant="secondary"
                onClick={handleLoadMore}
                loading={loading}
                disabled={loading}
              >
                Load More Transactions
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}