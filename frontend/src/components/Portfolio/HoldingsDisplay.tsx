'use client'

import { useHoldings, type Holding } from '@/hooks/useHoldings'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import Button from '@/components/ui/Button'
import { getRelativeTime } from '@/utils/timezone'

interface HoldingsDisplayProps {
  portfolioId: string
}

export default function HoldingsDisplay({ portfolioId }: HoldingsDisplayProps) {
  const {
    holdings,
    loading,
    error,
    fetchHoldings,
    calculatePortfolioSummary,
    clearError
  } = useHoldings(portfolioId)

  const summary = calculatePortfolioSummary()

  const formatCurrency = (amount: number) => {
    return `$${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercent = (percent: number) => {
    const sign = percent >= 0 ? '+' : ''
    return `${sign}${percent.toFixed(2)}%`
  }

  // Trend calculation functions (similar to market-data table)
  const calculateTrendData = (stock: any, holding?: any) => {
    // First try to use stock daily_change data (preferred)
    if (stock.daily_change && stock.daily_change_percent) {
      const change = parseFloat(stock.daily_change)
      const changePercent = parseFloat(stock.daily_change_percent)
      const trend = change > 0 ? 'up' : change < 0 ? 'down' : 'neutral'

      return {
        trend,
        change,
        change_percent: changePercent
      }
    }

    // Fallback: use holding's unrealized gain/loss data
    if (holding) {
      const gainLoss = parseFloat(holding.unrealized_gain_loss)
      const gainLossPercent = parseFloat(holding.unrealized_gain_loss_percent)

      if (!isNaN(gainLoss) && !isNaN(gainLossPercent)) {
        const trend = gainLoss > 0 ? 'up' : gainLoss < 0 ? 'down' : 'neutral'

        return {
          trend,
          change: gainLoss,
          change_percent: gainLossPercent
        }
      }
    }

    return null
  }

  const formatTrendChange = (change: number) => {
    if (change === 0) return '$0.00'
    return change >= 0 ? `+$${change.toFixed(2)}` : `-$${Math.abs(change).toFixed(2)}`
  }

  const formatTrendPercent = (changePercent: number) => {
    if (changePercent === 0) return '(0.00%)'
    return changePercent >= 0 ? `(+${changePercent.toFixed(2)}%)` : `(${changePercent.toFixed(2)}%)`
  }

  const getTrendColor = (trend: string | null) => {
    if (!trend) return 'text-gray-600 dark:text-gray-400'
    switch (trend) {
      case 'up':
        return 'text-green-600 dark:text-green-400'
      case 'down':
        return 'text-red-600 dark:text-red-400'
      case 'neutral':
        return 'text-gray-600 dark:text-gray-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getTrendIcon = (trend: string | null) => {
    if (!trend) {
      return (
        <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center" aria-label="No trend data">
          <span className="w-2 h-2 bg-black dark:bg-white rounded-full" />
        </div>
      )
    }

    if (trend === 'up') {
      return (
        <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center" aria-label="Upward trend">
          <svg
            className="w-3 h-3 stroke-current text-green-600 dark:text-green-400"
            viewBox="0 0 16 16"
            fill="none"
          >
            <path d="M3 13L13 3M13 3H7M13 3V9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      )
    }

    if (trend === 'down') {
      return (
        <div className="w-6 h-6 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center" aria-label="Downward trend">
          <svg
            className="w-3 h-3 stroke-current text-red-600 dark:text-red-400"
            viewBox="0 0 16 16"
            fill="none"
          >
            <path d="M3 3L13 13M13 13H7M13 13V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      )
    }

    if (trend === 'neutral') {
      return (
        <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center" aria-label="Neutral trend">
          <svg
            className="w-3 h-3 fill-current text-gray-600 dark:text-gray-400"
            viewBox="0 0 20 20"
          >
            <path d="M3 10h14v2H3z" />
          </svg>
        </div>
      )
    }

    return (
      <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center" aria-label="No trend data">
        <span className="w-2 h-2 bg-black dark:bg-white rounded-full" />
      </div>
    )
  }

  if (loading) {
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
          fetchHoldings()
        }}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Holdings Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Holdings
            </h2>
            <Button
              variant="secondary"
              size="sm"
              onClick={fetchHoldings}
              loading={loading}
            >
              Refresh
            </Button>
          </div>
        </div>

        {holdings.length === 0 ? (
          <div className="p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No holdings yet
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Add transactions to start building your portfolio holdings.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Stock
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Avg Cost
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Current Price
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Market Value
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Gain/Loss
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Return %
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Trend
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Last Updated
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {holdings.map((holding) => (
                  <tr key={holding.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {holding.stock.symbol}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {holding.stock.company_name}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white text-right">
                      {parseFloat(holding.quantity).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white text-right">
                      {formatCurrency(parseFloat(holding.average_cost))}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white text-right">
                      {holding.stock.current_price ? 
                        formatCurrency(parseFloat(holding.stock.current_price)) : 
                        '—'
                      }
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white text-right">
                      {formatCurrency(parseFloat(holding.current_value))}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-right ${
                      parseFloat(holding.unrealized_gain_loss) >= 0 
                        ? 'text-green-600 dark:text-green-400' 
                        : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatCurrency(parseFloat(holding.unrealized_gain_loss))}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-right ${
                      parseFloat(holding.unrealized_gain_loss_percent) >= 0
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatPercent(parseFloat(holding.unrealized_gain_loss_percent))}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {(() => {
                        const trendData = calculateTrendData(holding.stock, holding)
                        const trendColor = getTrendColor(trendData?.trend || null)

                        return (
                          <div className={`flex flex-col items-center space-y-1 ${trendColor}`}>
                            <div className="flex justify-center items-center">
                              {getTrendIcon(trendData?.trend || null)}
                            </div>
                            {trendData && (
                              <div className="flex flex-col items-center text-xs font-medium">
                                <span>{formatTrendChange(trendData.change)}</span>
                                <span>{formatTrendPercent(trendData.change_percent)}</span>
                              </div>
                            )}
                          </div>
                        )
                      })()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 text-right">
                      {holding.stock.last_price_update ? getRelativeTime(holding.stock.last_price_update) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}