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
  isEditing?: boolean
}

export default function TransactionForm({ 
  portfolioId, 
  onSubmit, 
  onCancel, 
  initialData,
  isEditing = false
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

    // Dynamic validation based on transaction type
    switch (formData.transaction_type) {
      case 'BUY':
      case 'SELL':
      case 'TRANSFER_IN':
      case 'TRANSFER_OUT':
        // Regular trading - need positive quantity and price
        if (formData.quantity <= 0) {
          newErrors.quantity = 'Quantity must be greater than 0'
        }
        if (formData.price_per_share <= 0) {
          newErrors.price_per_share = 'Price per share must be greater than 0'
        }
        break
        
      case 'DIVIDEND':
        // Dividends: quantity should be 0 (no shares added), price is dividend per share
        if (formData.quantity !== 0) {
          newErrors.quantity = 'Quantity should be 0 for dividends (no shares are added to holdings)'
        }
        if (formData.price_per_share <= 0) {
          newErrors.price_per_share = 'Dividend amount per share must be greater than 0'
        }
        break
        
      case 'STOCK_SPLIT':
      case 'BONUS_SHARES':
      case 'SPIN_OFF':
        // These add shares but at no cost
        if (formData.quantity <= 0) {
          newErrors.quantity = 'Quantity of new shares must be greater than 0'
        }
        if (formData.price_per_share !== 0) {
          newErrors.price_per_share = 'Price should be 0 for this transaction type'
        }
        break
        
      case 'REVERSE_SPLIT':
      case 'MERGER':
        // These typically remove shares and may have different validation
        if (formData.quantity < 0) {
          newErrors.quantity = 'Quantity cannot be negative'
        }
        if (formData.price_per_share < 0) {
          newErrors.price_per_share = 'Price cannot be negative'
        }
        break
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
        {isEditing ? 'Edit Transaction' : 'Add Transaction'}
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
            <optgroup label="Trading">
              <option value="BUY">Buy</option>
              <option value="SELL">Sell</option>
            </optgroup>
            <optgroup label="Income">
              <option value="DIVIDEND">Dividend</option>
            </optgroup>
            <optgroup label="Corporate Actions">
              <option value="STOCK_SPLIT">Stock Split</option>
              <option value="REVERSE_SPLIT">Reverse Split</option>
              <option value="SPIN_OFF">Spin-off</option>
              <option value="MERGER">Merger</option>
              <option value="BONUS_SHARES">Bonus Shares</option>
            </optgroup>
            <optgroup label="Transfers">
              <option value="TRANSFER_IN">Transfer In</option>
              <option value="TRANSFER_OUT">Transfer Out</option>
            </optgroup>
          </select>
        </div>

        {/* Transaction Type Helper Text */}
        {['DIVIDEND', 'STOCK_SPLIT', 'REVERSE_SPLIT', 'SPIN_OFF', 'MERGER', 'BONUS_SHARES'].includes(formData.transaction_type) && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              {formData.transaction_type === 'DIVIDEND' && 'For dividends, enter 0 quantity and the dividend amount per share as price.'}
              {formData.transaction_type === 'STOCK_SPLIT' && 'For stock splits, enter the additional shares received and set price to 0.'}
              {formData.transaction_type === 'REVERSE_SPLIT' && 'For reverse splits, enter 0 quantity and 0 price.'}
              {formData.transaction_type === 'SPIN_OFF' && 'For spin-offs, enter the new shares received and set price to 0.'}
              {formData.transaction_type === 'MERGER' && 'For mergers, enter 0 quantity and the price per share received.'}
              {formData.transaction_type === 'BONUS_SHARES' && 'For bonus shares, enter the bonus shares received and set price to 0.'}
            </p>
          </div>
        )}

        {/* Quantity and Price */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {formData.transaction_type === 'DIVIDEND' ? 'Quantity (optional for dividends)' : 
               formData.transaction_type === 'STOCK_SPLIT' ? 'Additional Shares *' :
               formData.transaction_type === 'SPIN_OFF' ? 'New Shares Received *' :
               formData.transaction_type === 'BONUS_SHARES' ? 'Bonus Shares Received *' :
               'Quantity *'}
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
              {formData.transaction_type === 'DIVIDEND' ? 'Dividend per Share *' :
               ['STOCK_SPLIT', 'REVERSE_SPLIT', 'SPIN_OFF', 'BONUS_SHARES'].includes(formData.transaction_type) ? 'Price per Share (usually 0)' :
               'Price per Share *'}
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
{isEditing ? (
              formData.transaction_type === 'BUY' ? 'Update Buy Transaction' :
              formData.transaction_type === 'SELL' ? 'Update Sell Transaction' :
              formData.transaction_type === 'DIVIDEND' ? 'Update Dividend' :
              formData.transaction_type === 'STOCK_SPLIT' ? 'Update Stock Split' :
              formData.transaction_type === 'REVERSE_SPLIT' ? 'Update Reverse Split' :
              formData.transaction_type === 'TRANSFER_IN' ? 'Update Transfer In' :
              formData.transaction_type === 'TRANSFER_OUT' ? 'Update Transfer Out' :
              formData.transaction_type === 'SPIN_OFF' ? 'Update Spin-off' :
              formData.transaction_type === 'MERGER' ? 'Update Merger' :
              formData.transaction_type === 'BONUS_SHARES' ? 'Update Bonus Shares' :
              'Update Transaction'
            ) : (
              formData.transaction_type === 'BUY' ? 'Add Buy Transaction' :
              formData.transaction_type === 'SELL' ? 'Add Sell Transaction' :
              formData.transaction_type === 'DIVIDEND' ? 'Add Dividend' :
              formData.transaction_type === 'STOCK_SPLIT' ? 'Add Stock Split' :
              formData.transaction_type === 'REVERSE_SPLIT' ? 'Add Reverse Split' :
              formData.transaction_type === 'TRANSFER_IN' ? 'Add Transfer In' :
              formData.transaction_type === 'TRANSFER_OUT' ? 'Add Transfer Out' :
              formData.transaction_type === 'SPIN_OFF' ? 'Add Spin-off' :
              formData.transaction_type === 'MERGER' ? 'Add Merger' :
              formData.transaction_type === 'BONUS_SHARES' ? 'Add Bonus Shares' :
              'Add Transaction'
            )}
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