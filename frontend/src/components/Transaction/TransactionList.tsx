'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Transaction } from '@/types/transaction'
import { useTransactions } from '@/hooks/useTransactions'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import Button from '@/components/ui/Button'
import TransactionFilter from './TransactionFilter'
import TransactionEditModal from './TransactionEditModal'
import { formatTimestampForLocalDisplay } from '@/utils/timezone'

interface TransactionListProps {
  portfolioId: string
  onTransactionUpdated?: () => void // Callback for when a transaction is edited
  onTransactionDeleted?: () => void // Callback for when a transaction is deleted
}

export default function TransactionList({
  portfolioId,
  onTransactionUpdated,
  onTransactionDeleted
}: TransactionListProps) {
  const router = useRouter()
  const {
    transactions,
    loading,
    error,
    total,
    fetchTransactions,
    loadMoreTransactions,
    searchTransactions,
    updateTransaction,
    deleteTransaction,
    hasMore,
    clearError
  } = useTransactions(portfolioId)

  const [currentFilters, setCurrentFilters] = useState<{
    startDate?: string
    endDate?: string
    stockSymbol?: string
  } | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null)
  const [deletingTransaction, setDeletingTransaction] = useState<Transaction | null>(null)

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

  const handleEdit = (transaction: Transaction) => {
    setEditingTransaction(transaction)
  }

  const handleCloseEditModal = () => {
    setEditingTransaction(null)
  }

  const handleUpdateTransaction = async (transactionId: string, updateData: any) => {
    const success = await updateTransaction(transactionId, updateData)
    if (success) {
      // Trigger portfolio data refresh
      onTransactionUpdated?.()
    }
    return success
  }

  const handleDelete = (transaction: Transaction) => {
    setDeletingTransaction(transaction)
  }

  const handleConfirmDelete = async () => {
    if (deletingTransaction) {
      const success = await deleteTransaction(deletingTransaction.id)
      if (success) {
        setDeletingTransaction(null)
        // Trigger portfolio data refresh
        onTransactionDeleted?.()
      }
    }
  }

  const handleCancelDelete = () => {
    setDeletingTransaction(null)
  }


  const formatCurrency = (amount: string) => {
    return `$${parseFloat(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const getTransactionTypeDisplay = (type: string) => {
    const typeDisplayMap: Record<string, { label: string; color: string }> = {
      BUY: { label: 'Buy', color: 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' },
      SELL: { label: 'Sell', color: 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100' },
      DIVIDEND: { label: 'Dividend', color: 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100' },
      STOCK_SPLIT: { label: 'Split', color: 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-100' },
      REVERSE_SPLIT: { label: 'Rev Split', color: 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-100' },
      TRANSFER_IN: { label: 'Transfer In', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100' },
      TRANSFER_OUT: { label: 'Transfer Out', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100' },
      SPIN_OFF: { label: 'Spin-off', color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-800 dark:text-indigo-100' },
      MERGER: { label: 'Merger', color: 'bg-pink-100 text-pink-800 dark:bg-pink-800 dark:text-pink-100' },
      BONUS_SHARES: { label: 'Bonus', color: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-800 dark:text-cyan-100' }
    }
    return typeDisplayMap[type] || { label: type, color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100' }
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
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {transactions.map((transaction) => {
                  const typeDisplay = getTransactionTypeDisplay(transaction.transaction_type)
                  return (
                  <tr 
                    key={transaction.id} 
                    className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {formatTimestampForLocalDisplay(transaction.transaction_date)}
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
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${typeDisplay.color}`}>
                        {typeDisplay.label}
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
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleEdit(transaction)
                          }}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
                          title="Edit transaction"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(transaction)
                          }}
                          className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 transition-colors"
                          title="Delete transaction"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                  )
                })}
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

      {/* Edit Modal */}
      <TransactionEditModal
        isOpen={editingTransaction !== null}
        onClose={handleCloseEditModal}
        transaction={editingTransaction}
        portfolioId={portfolioId}
        onUpdate={handleUpdateTransaction}
      />

      {/* Delete Confirmation Modal */}
      {deletingTransaction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mr-4">
                  <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 6.5c-.77.833-.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    Delete Transaction
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    This action cannot be undone.
                  </p>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  Are you sure you want to delete this transaction?
                </p>
                <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {deletingTransaction.stock.symbol} - {getTransactionTypeDisplay(deletingTransaction.transaction_type).label}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {formatTimestampForLocalDisplay(deletingTransaction.transaction_date)} • {formatCurrency(deletingTransaction.total_amount)}
                  </p>
                </div>
              </div>
              
              <div className="flex gap-3">
                <Button
                  onClick={handleConfirmDelete}
                  variant="danger"
                  loading={loading}
                  disabled={loading}
                  className="flex-1"
                >
                  Delete Transaction
                </Button>
                <Button
                  onClick={handleCancelDelete}
                  variant="secondary"
                  disabled={loading}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}