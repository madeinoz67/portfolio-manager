'use client'

import React from 'react'
import { PriceResponse } from '@/types/marketData'
import { parseServerDate, getRelativeTime, isWithinTimeRange } from '@/utils/timezone'
import { TrendIndicator } from './TrendIndicator'

interface MarketDataTableViewProps {
  symbols: string[]
  priceData: Record<string, PriceResponse>
  onRemoveSymbol?: (symbol: string) => void
  loading?: boolean
  className?: string
}

export function MarketDataTableView({
  symbols,
  priceData,
  onRemoveSymbol,
  loading = false,
  className = ''
}: MarketDataTableViewProps) {
  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    }).format(value)
  }

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(1)}B`
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(1)}M`
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(1)}K`
    return volume.toLocaleString()
  }

  const formatChange = (change: number, isPositive: boolean) => {
    const sign = isPositive ? '+' : ''
    return `${sign}$${Math.abs(change).toFixed(2)}`
  }

  const formatChangePercent = (changePercent: number, isPositive: boolean) => {
    const sign = isPositive ? '+' : ''
    return `${sign}${changePercent.toFixed(2)}%`
  }

  if (symbols.length === 0) {
    return (
      <div className={`text-center py-12 text-gray-500 dark:text-gray-400 ${className}`}>
        <div className="text-lg">No stocks to display</div>
        <div className="text-sm mt-2">Add a stock symbol to get started</div>
      </div>
    )
  }

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full border-collapse min-w-[700px]">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="text-left py-3 px-2 sm:px-4 font-semibold text-gray-900 dark:text-gray-100 min-w-[80px]">
              Symbol
            </th>
            <th className="text-right py-3 px-2 sm:px-4 font-semibold text-gray-900 dark:text-gray-100 min-w-[100px]">
              Price
            </th>
            <th className="text-center py-3 px-2 sm:px-4 font-semibold text-gray-900 dark:text-gray-100 min-w-[70px]">
              Trend
            </th>
            <th className="text-right py-3 px-2 sm:px-4 font-semibold text-gray-900 dark:text-gray-100 min-w-[90px]">
              Change
            </th>
            <th className="text-right py-3 px-2 sm:px-4 font-semibold text-gray-900 dark:text-gray-100 min-w-[90px]">
              Change %
            </th>
            <th className="text-right py-3 px-2 sm:px-4 font-semibold text-gray-900 dark:text-gray-100 min-w-[80px]">
              Volume
            </th>
            <th className="text-right py-3 px-2 sm:px-4 font-semibold text-gray-900 dark:text-gray-100 min-w-[120px] hidden sm:table-cell">
              Last Updated
            </th>
            {onRemoveSymbol && (
              <th className="text-center py-3 px-2 sm:px-4 font-semibold text-gray-900 dark:text-gray-100 min-w-[80px]">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {symbols.map(symbol => {
            const price = priceData[symbol]
            const isLoading = loading && !price
            const isStale = price ? !isWithinTimeRange(price.fetched_at, 30) : false

            if (isLoading) {
              return (
                <tr key={symbol} className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-4 px-2 sm:px-4">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-gray-900 dark:text-gray-100">
                        {symbol}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500">Loading...</td>
                  <td className="py-4 px-2 sm:px-4 text-center text-gray-500">-</td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500">-</td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500">-</td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500">-</td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500 hidden sm:table-cell">-</td>
                  {onRemoveSymbol && (
                    <td className="py-4 px-2 sm:px-4 text-center">
                      <button
                        onClick={() => onRemoveSymbol(symbol)}
                        className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                        aria-label={`Remove ${symbol}`}
                      >
                        ×
                      </button>
                    </td>
                  )}
                </tr>
              )
            }

            if (!price) {
              return (
                <tr key={symbol} className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-4 px-2 sm:px-4">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-gray-900 dark:text-gray-100">
                        {symbol}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500">No data</td>
                  <td className="py-4 px-2 sm:px-4 text-center text-gray-500">-</td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500">-</td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500">-</td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500">-</td>
                  <td className="py-4 px-2 sm:px-4 text-right text-gray-500 hidden sm:table-cell">-</td>
                  {onRemoveSymbol && (
                    <td className="py-4 px-2 sm:px-4 text-center">
                      <button
                        onClick={() => onRemoveSymbol(symbol)}
                        className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                        aria-label={`Remove ${symbol}`}
                      >
                        ×
                      </button>
                    </td>
                  )}
                </tr>
              )
            }

            const isPositive = price.trend ? price.trend.direction === 'up' : false
            const isNegative = price.trend ? price.trend.direction === 'down' : false
            const changeColor = isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'

            // Determine trend indicator colors and icons
            const getTrendIcon = () => {
              if (!price.trend) {
                return (
                  <span className="inline-block w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full" aria-label="No trend data" />
                )
              }

              if (price.trend.direction === 'up') {
                return (
                  <svg
                    className="w-4 h-4 fill-current"
                    viewBox="0 0 20 20"
                    aria-label="Up trend"
                  >
                    <path d="M10 2L15 8H5L10 2Z" />
                  </svg>
                )
              }

              if (price.trend.direction === 'down') {
                return (
                  <svg
                    className="w-4 h-4 fill-current"
                    viewBox="0 0 20 20"
                    aria-label="Down trend"
                  >
                    <path d="M10 18L5 12H15L10 18Z" />
                  </svg>
                )
              }

              return (
                <span className="inline-block w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full" aria-label="No trend data" />
              )
            }

            const getTrendColor = () => {
              if (!price.trend) return 'text-gray-600 dark:text-gray-400'
              if (price.trend.direction === 'up') return 'text-green-600 dark:text-green-400'
              if (price.trend.direction === 'down') return 'text-red-600 dark:text-red-400'
              return 'text-gray-600 dark:text-gray-400'
            }

            return (
              <tr key={symbol} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <td className="py-4 px-2 sm:px-4">
                  <div className="flex items-center space-x-1 sm:space-x-2">
                    <span className="font-semibold text-gray-900 dark:text-gray-100 text-sm sm:text-base">
                      {symbol}
                    </span>
                    {price.cached && (
                      <span className="px-1 sm:px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded">
                        C
                      </span>
                    )}
                    {isStale && (
                      <span className="px-1 sm:px-1.5 py-0.5 text-xs bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300 rounded">
                        S
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-4 px-2 sm:px-4 text-right">
                  <span className="font-semibold text-gray-900 dark:text-gray-100 text-sm sm:text-base">
                    {formatPrice(price.price)}
                  </span>
                </td>
                <td className={`py-4 px-2 sm:px-4 text-center ${getTrendColor()}`}>
                  <div className="flex justify-center items-center">
                    {getTrendIcon()}
                  </div>
                </td>
                <td className={`py-4 px-2 sm:px-4 text-right ${changeColor}`}>
                  {price.trend ? (
                    <span className="font-medium text-sm sm:text-base">
                      {formatChange(price.trend.change, isPositive)}
                    </span>
                  ) : (
                    <span className="text-gray-500">-</span>
                  )}
                </td>
                <td className={`py-4 px-2 sm:px-4 text-right ${changeColor}`}>
                  {price.trend ? (
                    <span className="font-medium text-sm sm:text-base">
                      {formatChangePercent(price.trend.change_percent, isPositive)}
                    </span>
                  ) : (
                    <span className="text-gray-500">-</span>
                  )}
                </td>
                <td className="py-4 px-2 sm:px-4 text-right text-gray-600 dark:text-gray-400 text-sm sm:text-base">
                  {price.volume ? formatVolume(price.volume) : '-'}
                </td>
                <td className="py-4 px-2 sm:px-4 text-right text-gray-500 dark:text-gray-400 text-xs sm:text-sm hidden sm:table-cell">
                  {getRelativeTime(price.fetched_at)}
                </td>
                {onRemoveSymbol && (
                  <td className="py-4 px-2 sm:px-4 text-center">
                    <button
                      onClick={() => onRemoveSymbol(symbol)}
                      className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 font-bold text-lg"
                      aria-label={`Remove ${symbol}`}
                    >
                      ×
                    </button>
                  </td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}