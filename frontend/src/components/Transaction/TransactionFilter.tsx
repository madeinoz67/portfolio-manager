'use client'

import { useState } from 'react'
import Button from '@/components/ui/Button'

interface TransactionFilterProps {
  onFilter: (filters: {
    startDate?: string
    endDate?: string
    stockSymbol?: string
  }) => void
  onClear: () => void
  loading?: boolean
}

export default function TransactionFilter({ onFilter, onClear, loading }: TransactionFilterProps) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [stockSymbol, setStockSymbol] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const filters: any = {}
    if (startDate) filters.startDate = startDate
    if (endDate) filters.endDate = endDate
    if (stockSymbol.trim()) filters.stockSymbol = stockSymbol.trim()
    
    onFilter(filters)
  }

  const handleClear = () => {
    setStartDate('')
    setEndDate('')
    setStockSymbol('')
    onClear()
  }

  const hasFilters = startDate || endDate || stockSymbol.trim()

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Stock Symbol Search */}
          <div>
            <label htmlFor="stockSymbol" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Stock Symbol
            </label>
            <input
              id="stockSymbol"
              type="text"
              value={stockSymbol}
              onChange={(e) => setStockSymbol(e.target.value)}
              placeholder="Search by symbol (e.g., AAPL)"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
            />
          </div>

          {/* Start Date */}
          <div>
            <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              From Date
            </label>
            <input
              id="startDate"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          {/* End Date */}
          <div>
            <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              To Date
            </label>
            <input
              id="endDate"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2">
          <Button
            type="submit"
            variant="primary"
            size="sm"
            loading={loading}
            disabled={loading}
          >
            {loading ? 'Searching...' : 'Apply Filters'}
          </Button>
          
          {hasFilters && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleClear}
              disabled={loading}
            >
              Clear Filters
            </Button>
          )}
        </div>

        {/* Quick Filters */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
          <div className="flex flex-wrap gap-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 self-center">Quick filters:</span>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                const today = new Date().toISOString().split('T')[0]
                setStartDate(today)
                setEndDate(today)
              }}
              disabled={loading}
            >
              Today
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                const today = new Date()
                const lastWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
                setStartDate(lastWeek.toISOString().split('T')[0])
                setEndDate(today.toISOString().split('T')[0])
              }}
              disabled={loading}
            >
              Last 7 Days
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                const today = new Date()
                const lastMonth = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
                setStartDate(lastMonth.toISOString().split('T')[0])
                setEndDate(today.toISOString().split('T')[0])
              }}
              disabled={loading}
            >
              Last 30 Days
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => {
                const today = new Date()
                const thisYear = new Date(today.getFullYear(), 0, 1)
                setStartDate(thisYear.toISOString().split('T')[0])
                setEndDate(today.toISOString().split('T')[0])
              }}
              disabled={loading}
            >
              This Year
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}