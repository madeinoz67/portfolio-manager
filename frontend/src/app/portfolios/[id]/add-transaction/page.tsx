'use client'

import { useParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import TransactionForm from '@/components/Transaction/TransactionForm'
import { useTransactions } from '@/hooks/useTransactions'
import { useToast } from '@/components/ui/Toast'
import { TransactionCreate } from '@/types/transaction'
import Button from '@/components/ui/Button'

export default function AddTransactionPage() {
  const params = useParams()
  const router = useRouter()
  const portfolioId = params?.id as string
  const { addToast } = useToast()
  const { createTransaction } = useTransactions(portfolioId)

  const handleAddTransaction = async (transactionData: TransactionCreate) => {
    try {
      const success = await createTransaction(transactionData)
      
      if (success) {
        addToast('Transaction added successfully!', 'success')
        router.push(`/portfolios/${portfolioId}`)
        return true
      } else {
        addToast('Failed to add transaction', 'error')
        return false
      }
    } catch (err) {
      console.error('Exception in handleAddTransaction:', err)
      addToast('Failed to add transaction', 'error')
      return false
    }
  }

  const handleCancel = () => {
    router.push(`/portfolios/${portfolioId}`)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCancel}
              icon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              }
            >
              Back to Portfolio
            </Button>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Add New Transaction
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Add a new transaction to your portfolio
          </p>
        </div>

        {/* Transaction Form */}
        <TransactionForm
          portfolioId={portfolioId}
          onSubmit={handleAddTransaction}
          onCancel={handleCancel}
        />
      </div>
    </div>
  )
}