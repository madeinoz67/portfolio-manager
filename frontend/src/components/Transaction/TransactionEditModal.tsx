'use client'

import { useState, useEffect } from 'react'
import { Transaction, TransactionCreate } from '@/types/transaction'
import TransactionForm from './TransactionForm'

interface TransactionEditModalProps {
  isOpen: boolean
  onClose: () => void
  transaction: Transaction | null
  portfolioId: string
  onUpdate: (transactionId: string, updateData: any) => Promise<boolean>
}

export default function TransactionEditModal({
  isOpen,
  onClose,
  transaction,
  portfolioId,
  onUpdate
}: TransactionEditModalProps) {
  const [isClosing, setIsClosing] = useState(false)

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  const handleClose = () => {
    setIsClosing(true)
    setTimeout(() => {
      setIsClosing(false)
      onClose()
    }, 200)
  }

  const handleSubmit = async (updateData: TransactionCreate): Promise<boolean> => {
    if (!transaction) return false
    
    const success = await onUpdate(transaction.id, updateData)
    if (success) {
      handleClose()
    }
    return success
  }

  if (!isOpen && !isClosing) return null

  const initialData: Partial<TransactionCreate> = transaction ? {
    stock_symbol: transaction.stock.symbol,
    transaction_type: transaction.transaction_type,
    quantity: parseFloat(transaction.quantity),
    price_per_share: parseFloat(transaction.price_per_share),
    fees: parseFloat(transaction.fees),
    transaction_date: transaction.transaction_date,
    notes: transaction.notes || ''
  } : undefined

  return (
    <div 
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-black transition-opacity duration-200 ${
        isClosing ? 'bg-opacity-0' : 'bg-opacity-50'
      }`}
      onClick={handleClose}
    >
      <div 
        className={`bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto transform transition-all duration-200 ${
          isClosing ? 'scale-95 opacity-0' : 'scale-100 opacity-100'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Edit Transaction
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6">
          <TransactionForm
            portfolioId={portfolioId}
            onSubmit={handleSubmit}
            onCancel={handleClose}
            initialData={initialData}
            isEditing={true}
          />
        </div>
      </div>
    </div>
  )
}