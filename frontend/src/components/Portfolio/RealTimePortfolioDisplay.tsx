'use client'

import React, { useMemo } from 'react'
import {
  StreamingMarketDataProvider,
  useStreamingMarketData,
  usePortfolioValue
} from '@/components/MarketData/StreamingMarketDataProvider'
import { ConnectionStatus } from '@/components/MarketData/ConnectionStatus'
import { RefreshButton, ForceRefreshButton } from '@/components/MarketData/RefreshButton'
import { StreamingPriceDisplay } from '@/components/MarketData/StreamingPriceDisplay'

interface Holding {
  id: string
  stock: {
    id: string
    symbol: string
    company_name: string
    current_price?: string
  }
  quantity: string
  average_cost: string
  current_value: string
  unrealized_gain_loss: string
  unrealized_gain_loss_percent: string
}

interface RealTimePortfolioDisplayProps {
  portfolioId: string
  holdings: Holding[]
  enableRealTime?: boolean
  className?: string
}

function PortfolioMetricsContent({ holdings }: { holdings: Holding[] }) {
  const {
    connectionStatus,
    error,
    lastUpdate,
    reconnectAttempts,
    refreshPrices,
    connectSSE
  } = useStreamingMarketData()

  // Convert holdings to format expected by usePortfolioValue
  const portfolioHoldings = useMemo(() => {
    return holdings.map(holding => ({
      symbol: holding.stock.symbol,
      quantity: parseFloat(holding.quantity),
      costBasis: parseFloat(holding.average_cost)
    }))
  }, [holdings])

  const portfolioValue = usePortfolioValue(portfolioHoldings)

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  return (
    <div className="space-y-6">
      {/* Connection Status and Controls Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-3 sm:space-y-0">
        <div className="flex items-center space-x-3">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Real-Time Portfolio
          </h2>
          <ConnectionStatus
            status={connectionStatus}
            lastUpdate={lastUpdate}
            error={error}
            reconnectAttempts={reconnectAttempts}
            maxReconnectAttempts={5}
            onReconnect={connectSSE}
          />
        </div>

        <div className="flex items-center space-x-2">
          <RefreshButton
            onRefresh={refreshPrices}
            cooldownSeconds={60}
            size="sm"
          />
          <ForceRefreshButton
            onRefresh={refreshPrices}
          />
        </div>
      </div>

      {/* Enhanced Portfolio Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 text-white">
          <h3 className="text-sm font-medium text-blue-100">Current Value</h3>
          <p className="text-2xl font-bold">
            {formatCurrency(portfolioValue.totalValue)}
          </p>
          {portfolioValue.lastUpdate && (
            <p className="text-xs text-blue-100 opacity-80">
              Updated: {new Date(portfolioValue.lastUpdate).toLocaleTimeString()}
            </p>
          )}
        </div>

        <div className="bg-gradient-to-r from-green-500 to-blue-500 rounded-lg p-4 text-white">
          <h3 className="text-sm font-medium text-green-100">Cost Basis</h3>
          <p className="text-2xl font-bold">
            {formatCurrency(portfolioValue.totalCostBasis)}
          </p>
        </div>

        <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg p-4 text-white">
          <h3 className="text-sm font-medium text-purple-100">Gain/Loss</h3>
          <p className={`text-2xl font-bold ${
            portfolioValue.totalGainLoss >= 0 ? 'text-green-100' : 'text-red-100'
          }`}>
            {portfolioValue.totalGainLoss >= 0 ? '+' : ''}{formatCurrency(portfolioValue.totalGainLoss)}
          </p>
        </div>

        <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-lg p-4 text-white">
          <h3 className="text-sm font-medium text-orange-100">Return %</h3>
          <p className={`text-2xl font-bold ${
            portfolioValue.totalGainLossPercent >= 0 ? 'text-green-100' : 'text-red-100'
          }`}>
            {portfolioValue.totalGainLossPercent >= 0 ? '+' : ''}{portfolioValue.totalGainLossPercent.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Data Quality Indicators */}
      {(!portfolioValue.hasAllPrices || error) && (
        <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <svg className="h-5 w-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <div>
              {!portfolioValue.hasAllPrices && (
                <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                  Missing price data for: {portfolioValue.missingPrices.join(', ')}
                </p>
              )}
              {error && (
                <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                  Connection issue: {error}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Holdings Display */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
          Holdings Breakdown
        </h3>

        <div className="space-y-3">
          {portfolioValue.holdings.map((holding) => (
            <div
              key={holding.symbol}
              className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {holding.symbol}
                    </span>
                    {holding.cached && (
                      <span className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                        Cached
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {holding.quantity} shares @ {formatCurrency(holding.currentPrice)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-500">
                    Cost basis: {formatCurrency(holding.costBasis)} per share
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="font-medium text-gray-900 dark:text-gray-100">
                  {formatCurrency(holding.currentValue)}
                </div>
                <div className={`text-sm ${
                  holding.gainLoss >= 0
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {holding.gainLoss >= 0 ? '+' : ''}{formatCurrency(holding.gainLoss)}
                  ({holding.gainLossPercent.toFixed(2)}%)
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-500">
                  Updated: {new Date(holding.lastUpdate).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export function RealTimePortfolioDisplay({
  portfolioId,
  holdings,
  enableRealTime = true,
  className = ''
}: RealTimePortfolioDisplayProps) {
  // Extract symbols from holdings
  const symbols = useMemo(() => {
    return holdings.map(holding => holding.stock.symbol)
  }, [holdings])

  if (holdings.length === 0) {
    return (
      <div className={`text-center py-8 text-gray-500 ${className}`}>
        <p>No holdings in this portfolio yet.</p>
        <p className="text-sm">Add some transactions to see real-time data.</p>
      </div>
    )
  }

  return (
    <StreamingMarketDataProvider
      symbols={symbols}
      portfolioIds={[portfolioId]}
      enableRealTime={enableRealTime}
      autoRefresh={true}
      refreshIntervalMs={900000} // 15 minutes
    >
      <div className={className}>
        <PortfolioMetricsContent holdings={holdings} />
      </div>
    </StreamingMarketDataProvider>
  )
}

// Simplified component for just metrics without full holdings display
interface RealTimeMetricsProps {
  portfolioId: string
  holdings: Holding[]
  enableRealTime?: boolean
  showControls?: boolean
  compact?: boolean
}

export function RealTimeMetrics({
  portfolioId,
  holdings,
  enableRealTime = true,
  showControls = false,
  compact = false
}: RealTimeMetricsProps) {
  const symbols = useMemo(() => {
    return holdings.map(holding => holding.stock.symbol)
  }, [holdings])

  if (holdings.length === 0) {
    return null
  }

  return (
    <StreamingMarketDataProvider
      symbols={symbols}
      portfolioIds={[portfolioId]}
      enableRealTime={enableRealTime}
      autoRefresh={true}
    >
      <RealTimeMetricsContent
        holdings={holdings}
        showControls={showControls}
        compact={compact}
      />
    </StreamingMarketDataProvider>
  )
}

function RealTimeMetricsContent({
  holdings,
  showControls,
  compact
}: {
  holdings: Holding[]
  showControls?: boolean
  compact?: boolean
}) {
  const {
    connectionStatus,
    error,
    lastUpdate,
    refreshPrices,
    connectSSE
  } = useStreamingMarketData()

  const portfolioHoldings = useMemo(() => {
    return holdings.map(holding => ({
      symbol: holding.stock.symbol,
      quantity: parseFloat(holding.quantity),
      costBasis: parseFloat(holding.average_cost)
    }))
  }, [holdings])

  const portfolioValue = usePortfolioValue(portfolioHoldings)

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value)
  }

  if (compact) {
    return (
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Value:</span>
            <span className="ml-1 font-semibold text-gray-900 dark:text-gray-100">
              {formatCurrency(portfolioValue.totalValue)}
            </span>
          </div>
          <div className={`${
            portfolioValue.totalGainLoss >= 0
              ? 'text-green-600 dark:text-green-400'
              : 'text-red-600 dark:text-red-400'
          }`}>
            <span className="text-sm">
              {portfolioValue.totalGainLoss >= 0 ? '+' : ''}{formatCurrency(portfolioValue.totalGainLoss)}
              ({portfolioValue.totalGainLossPercent.toFixed(2)}%)
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <ConnectionStatus
            status={connectionStatus}
            lastUpdate={lastUpdate}
            error={error}
            onReconnect={connectSSE}
          />
          {showControls && (
            <RefreshButton
              onRefresh={refreshPrices}
              size="sm"
              variant="ghost"
            />
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-4 text-white">
        <h3 className="text-sm font-medium text-blue-100">Current Value</h3>
        <p className="text-2xl font-bold">
          {formatCurrency(portfolioValue.totalValue)}
        </p>
        {connectionStatus === 'connected' && (
          <div className="flex items-center space-x-1 mt-1">
            <div className="h-1.5 w-1.5 bg-green-300 rounded-full animate-pulse"></div>
            <span className="text-xs text-blue-100">Live</span>
          </div>
        )}
      </div>

      <div className="bg-gradient-to-r from-green-500 to-blue-500 rounded-lg p-4 text-white">
        <h3 className="text-sm font-medium text-green-100">Cost Basis</h3>
        <p className="text-2xl font-bold">
          {formatCurrency(portfolioValue.totalCostBasis)}
        </p>
      </div>

      <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg p-4 text-white">
        <h3 className="text-sm font-medium text-purple-100">Gain/Loss</h3>
        <p className={`text-2xl font-bold ${
          portfolioValue.totalGainLoss >= 0 ? 'text-green-100' : 'text-red-100'
        }`}>
          {portfolioValue.totalGainLoss >= 0 ? '+' : ''}{formatCurrency(portfolioValue.totalGainLoss)}
        </p>
      </div>

      <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-lg p-4 text-white">
        <h3 className="text-sm font-medium text-orange-100">Return %</h3>
        <p className={`text-2xl font-bold ${
          portfolioValue.totalGainLossPercent >= 0 ? 'text-green-100' : 'text-red-100'
        }`}>
          {portfolioValue.totalGainLossPercent >= 0 ? '+' : ''}{portfolioValue.totalGainLossPercent.toFixed(2)}%
        </p>
      </div>
    </div>
  )
}