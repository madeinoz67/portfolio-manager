'use client'

import React from 'react'
import { PriceResponse } from '@/types/marketData'
import { parseServerDate, getRelativeTime, isWithinTimeRange } from '@/utils/timezone'

interface StreamingPriceDisplayProps {
  price: PriceResponse
  previousPrice?: number
  showVolume?: boolean
  showMarketCap?: boolean
  showUpdateTime?: boolean
  compact?: boolean
  className?: string
}

export function StreamingPriceDisplay({
  price,
  previousPrice,
  showVolume = false,
  showMarketCap = false,
  showUpdateTime = true,
  compact = false,
  className = ''
}: StreamingPriceDisplayProps) {
  // Calculate change from previous price if available
  const change = previousPrice ? price.price - previousPrice : 0
  const changePercent = previousPrice ? (change / previousPrice) * 100 : 0
  const hasChange = previousPrice !== undefined

  const isPositive = change >= 0
  const changeColor = isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
  const neutralColor = 'text-gray-600 dark:text-gray-400'

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

  const formatMarketCap = (value: number) => {
    if (value >= 1e12) return `${(value / 1e12).toFixed(1)}T`
    if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`
    return `$${value.toLocaleString()}`
  }

  const formatUpdateTime = (timestamp: string) => {
    return getRelativeTime(timestamp)
  }

  const isStale = !isWithinTimeRange(price.fetched_at, 30)

  if (compact) {
    return (
      <div className={`flex items-center justify-between ${className}`}>
        <div className="flex items-center space-x-2">
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {formatPrice(price.price)}
          </span>
          {hasChange && (
            <span className={`text-sm font-medium ${changeColor}`}>
              {isPositive ? '+' : ''}{change.toFixed(2)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2 text-xs text-gray-500">
          {price.cached && (
            <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">
              Cached
            </span>
          )}
          {isStale && (
            <span className="px-1.5 py-0.5 bg-orange-100 text-orange-700 rounded">
              Stale
            </span>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline space-x-3">
          <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {formatPrice(price.price)}
          </span>
          <span className="text-lg font-medium text-gray-500 dark:text-gray-400">
            {price.symbol}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {price.cached && (
            <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-md">
              Cached
            </span>
          )}
          {isStale && (
            <span className="px-2 py-1 text-xs bg-orange-100 text-orange-700 rounded-md">
              ⚠️ Stale
            </span>
          )}
        </div>
      </div>

      {hasChange && (
        <div className={`flex items-center space-x-1 ${changeColor}`}>
          <span className="font-medium">
            {isPositive ? '+' : ''}{change.toFixed(2)}
          </span>
          <span>
            ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
          </span>
          <span className="text-xs">
            from previous
          </span>
        </div>
      )}

      <div className="flex items-center space-x-6 text-sm text-gray-600 dark:text-gray-400">
        {showVolume && price.volume && (
          <div>
            <span className="font-medium">Volume:</span> {formatVolume(price.volume)}
          </div>
        )}

        {showMarketCap && price.market_cap && (
          <div>
            <span className="font-medium">Market Cap:</span> {formatMarketCap(price.market_cap)}
          </div>
        )}
      </div>

      {showUpdateTime && (
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-500">
          <span>
            Last updated: {formatUpdateTime(price.fetched_at)}
          </span>
          <span>
            Source: {price.cached ? 'Cache' : 'Live'}
          </span>
        </div>
      )}
    </div>
  )
}

interface PriceListProps {
  prices: Record<string, PriceResponse>
  previousPrices?: Record<string, number>
  onSymbolClick?: (symbol: string) => void
  className?: string
}

export function StreamingPriceList({
  prices,
  previousPrices = {},
  onSymbolClick,
  className = ''
}: PriceListProps) {
  const symbols = Object.keys(prices).sort()

  if (symbols.length === 0) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        No price data available
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {symbols.map(symbol => {
        const price = prices[symbol]
        const previousPrice = previousPrices[symbol]

        return (
          <div
            key={symbol}
            className={`p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
              onSymbolClick ? 'cursor-pointer' : ''
            }`}
            onClick={() => onSymbolClick?.(symbol)}
          >
            <StreamingPriceDisplay
              price={price}
              previousPrice={previousPrice}
              compact={true}
              showVolume={true}
            />
          </div>
        )
      })}
    </div>
  )
}