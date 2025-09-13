'use client'

import { useState } from 'react'
import Button from '@/components/ui/Button'
import StockSelector from './StockSelector'
import { TransactionCreate, TransactionType } from '@/types/transaction'
import { Stock } from '@/hooks/useStocks'

interface TransactionFormProps {
  portfolioId: string
  onSubmit: (transaction: TransactionCreate) => Promise<boolean>
  onCancel: () => void
  initialData?: Partial<TransactionCreate>
}

export default function TransactionForm({ 
  portfolioId, 
  onSubmit, 
  onCancel, 
  initialData 
}: TransactionFormProps) {
  const [formData, setFormData] = useState<TransactionCreate>({
    stock_symbol: initialData?.stock_symbol || '',
    transaction_type: initialData?.transaction_type || 'BUY',
    quantity: initialData?.quantity || 0,
    price_per_share: initialData?.price_per_share || 0,
    fees: initialData?.fees || 0,
    transaction_date: initialData?.transaction_date || new Date().toISOString().split('T')[0],
    notes: initialData?.notes || ''
  })
  
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null)

  const handleStockSelect = (symbol: string, stock: Stock | null) => {
    setFormData(prev => ({ ...prev, stock_symbol: symbol }))
    setSelectedStock(stock)
    
    // Auto-fill price if stock has current price
    if (stock?.current_price && formData.price_per_share === 0) {
      setFormData(prev => ({ 
        ...prev, 
        price_per_share: parseFloat(stock.current_price!) 
      }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.stock_symbol.trim()) {
      newErrors.stock_symbol = 'Stock symbol is required'
    } else if (!selectedStock) {
      newErrors.stock_symbol = 'Please select a valid stock from the list'
    }

    if (formData.quantity <= 0) {
      newErrors.quantity = 'Quantity must be greater than 0'
    }

    if (formData.price_per_share <= 0) {
      newErrors.price_per_share = 'Price per share must be greater than 0'
    }

    if (formData.fees < 0) {
      newErrors.fees = 'Fees cannot be negative'
    }

    if (!formData.transaction_date) {
      newErrors.transaction_date = 'Transaction date is required'
    } else if (new Date(formData.transaction_date) > new Date()) {
      newErrors.transaction_date = 'Transaction date cannot be in the future'
    }

    if (formData.notes && formData.notes.length > 1000) {
      newErrors.notes = 'Notes cannot exceed 1000 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      console.log('Form validation failed:', errors)
      return
    }

    console.log('Submitting transaction form:', formData)
    setLoading(true)
    
    try {
      const transactionData = {
        ...formData,
        stock_symbol: formData.stock_symbol.toUpperCase()
      }
      
      console.log('Calling onSubmit with:', transactionData)
      const success = await onSubmit(transactionData)
      
      console.log('onSubmit returned:', success)
      
      if (success) {
        console.log('Transaction successful, resetting form')
        // Reset form on success
        setFormData({
          stock_symbol: '',
          transaction_type: 'BUY',
          quantity: 0,
          price_per_share: 0,
          fees: 0,
          transaction_date: new Date().toISOString().split('T')[0],
          notes: ''
        })
      } else {
        console.log('Transaction failed')
      }
    } catch (error) {
      console.error('Error in form submission:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: keyof TransactionCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const totalAmount = formData.quantity * formData.price_per_share

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
        Add Transaction
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Stock Symbol */}
        <StockSelector
          selectedSymbol={formData.stock_symbol}
          onSelectStock={handleStockSelect}
          error={errors.stock_symbol}
        />

        {/* Transaction Type */}
        <div>
          <label htmlFor="transaction_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Transaction Type *
          </label>
          <select
            id="transaction_type"
            value={formData.transaction_type}
            onChange={(e) => handleInputChange('transaction_type', e.target.value as TransactionType)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            disabled={loading}
          >
            <option value="BUY">Buy</option>
            <option value="SELL">Sell</option>
          </select>
        </div>

        {/* Quantity and Price */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Quantity *
            </label>
            <input
              type="number"
              id="quantity"
              value={formData.quantity || ''}
              onChange={(e) => handleInputChange('quantity', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.001"
              placeholder="100"
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.quantity ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={loading}
            />
            {errors.quantity && (
              <p className="text-red-500 text-sm mt-1">{errors.quantity}</p>
            )}
          </div>

          <div>
            <label htmlFor="price_per_share" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Price per Share *
            </label>
            <input
              type="number"
              id="price_per_share"
              value={formData.price_per_share || ''}
              onChange={(e) => handleInputChange('price_per_share', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.01"
              placeholder="150.00"
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.price_per_share ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={loading}
            />
            {errors.price_per_share && (
              <p className="text-red-500 text-sm mt-1">{errors.price_per_share}</p>
            )}
          </div>
        </div>

        {/* Fees and Date */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="fees" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Fees
            </label>
            <input
              type="number"
              id="fees"
              value={formData.fees || ''}
              onChange={(e) => handleInputChange('fees', parseFloat(e.target.value) || 0)}
              min="0"
              step="0.01"
              placeholder="5.00"
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.fees ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={loading}
            />
            {errors.fees && (
              <p className="text-red-500 text-sm mt-1">{errors.fees}</p>
            )}
          </div>

          <div>
            <label htmlFor="transaction_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Transaction Date *
            </label>
            <input
              type="date"
              id="transaction_date"
              value={formData.transaction_date}
              onChange={(e) => handleInputChange('transaction_date', e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                errors.transaction_date ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={loading}
            />
            {errors.transaction_date && (
              <p className="text-red-500 text-sm mt-1">{errors.transaction_date}</p>
            )}
          </div>
        </div>

        {/* Total Amount Display */}
        {totalAmount > 0 && (
          <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-md">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Total Amount: <span className="font-semibold">${totalAmount.toFixed(2)}</span>
              {formData.fees > 0 && (
                <span className="text-xs"> (+ ${formData.fees.toFixed(2)} fees)</span>
              )}
            </p>
          </div>
        )}

        {/* Notes */}
        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Notes
          </label>
          <textarea
            id="notes"
            value={formData.notes}
            onChange={(e) => handleInputChange('notes', e.target.value)}
            placeholder="Optional notes about this transaction..."
            rows={3}
            maxLength={1000}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
              errors.notes ? 'border-red-500' : 'border-gray-300'
            }`}
            disabled={loading}
          />
          {errors.notes && (
            <p className="text-red-500 text-sm mt-1">{errors.notes}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">
            {formData.notes?.length || 0}/1000 characters
          </p>
        </div>

        {/* Form Actions */}
        <div className="flex gap-3 pt-4">
          <Button
            type="submit"
            loading={loading}
            disabled={loading}
            className="flex-1"
          >
            {formData.transaction_type === 'BUY' ? 'Add Buy Transaction' : 'Add Sell Transaction'}
          </Button>
          
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}