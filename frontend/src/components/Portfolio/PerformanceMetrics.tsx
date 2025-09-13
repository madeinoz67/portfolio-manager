'use client'

import { useState } from 'react'
import { usePerformance } from '@/hooks/usePerformance'
import { PerformancePeriod } from '@/types/performance'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'

interface PerformanceMetricsProps {
  portfolioId: string
}

export default function PerformanceMetrics({ portfolioId }: PerformanceMetricsProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<string>(PerformancePeriod.ONE_MONTH)
  const { performance, loading, error, refreshPerformance, clearError } = usePerformance(portfolioId, selectedPeriod)

  const formatCurrency = (value: string) => {
    return `$${parseFloat(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercentage = (value: string) => {
    const num = parseFloat(value)
    const sign = num >= 0 ? '+' : ''
    return `${sign}${num.toFixed(2)}%`
  }

  const getColorClass = (value: string) => {
    const num = parseFloat(value)
    if (num > 0) return 'text-green-600 dark:text-green-400'
    if (num < 0) return 'text-red-600 dark:text-red-400'
    return 'text-gray-600 dark:text-gray-400'
  }

  const periodOptions = [
    { value: PerformancePeriod.ONE_DAY, label: '1D' },
    { value: PerformancePeriod.ONE_WEEK, label: '1W' },
    { value: PerformancePeriod.ONE_MONTH, label: '1M' },
    { value: PerformancePeriod.THREE_MONTHS, label: '3M' },
    { value: PerformancePeriod.SIX_MONTHS, label: '6M' },
    { value: PerformancePeriod.ONE_YEAR, label: '1Y' },
    { value: PerformancePeriod.YEAR_TO_DATE, label: 'YTD' },
    { value: PerformancePeriod.ALL, label: 'ALL' }
  ]

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <ErrorMessage 
          message={error} 
          onRetry={() => {
            clearError()
            refreshPerformance()
          }}
        />
      </div>
    )
  }

  if (!performance) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <p className="text-gray-600 dark:text-gray-400">No performance data available</p>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Performance Metrics
          </h2>
          <div className="flex items-center space-x-2">
            {periodOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setSelectedPeriod(option.value)}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  selectedPeriod === option.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Return</p>
            <p className={`text-2xl font-bold ${getColorClass(performance.total_return)}`}>
              {formatCurrency(performance.total_return)}
            </p>
          </div>

          <div className="text-center">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Annualized Return</p>
            <p className={`text-2xl font-bold ${getColorClass(performance.annualized_return)}`}>
              {formatPercentage(performance.annualized_return)}
            </p>
          </div>

          <div className="text-center">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Max Drawdown</p>
            <p className={`text-2xl font-bold ${getColorClass(performance.max_drawdown)}`}>
              {formatPercentage(performance.max_drawdown)}
            </p>
          </div>

          <div className="text-center">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Dividend Yield</p>
            <p className={`text-2xl font-bold ${getColorClass(performance.dividend_yield)}`}>
              {formatPercentage(performance.dividend_yield)}
            </p>
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Period Start Value</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {formatCurrency(performance.period_start_value)}
            </p>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Period End Value</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {formatCurrency(performance.period_end_value)}
            </p>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Dividends</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {formatCurrency(performance.total_dividends)}
            </p>
          </div>
        </div>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Data calculated on {new Date(performance.calculated_at).toLocaleString()}
          </p>
          <button
            onClick={refreshPerformance}
            disabled={loading}
            className="mt-2 inline-flex items-center px-3 py-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors disabled:opacity-50"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>
    </div>
  )
}