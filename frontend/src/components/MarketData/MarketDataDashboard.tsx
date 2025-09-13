'use client'

import React, { useState } from 'react'
import {
  StreamingMarketDataProvider,
  useStreamingMarketData,
  useSymbolPrices,
  usePortfolioValue
} from './StreamingMarketDataProvider'
import { ConnectionStatus } from './ConnectionStatus'
import { RefreshButton, ForceRefreshButton } from './RefreshButton'
import { StreamingPriceDisplay, StreamingPriceList } from './StreamingPriceDisplay'

// Sample portfolio holdings for demo
const DEMO_HOLDINGS = [
  { symbol: 'AAPL', quantity: 100, costBasis: 150.00 },
  { symbol: 'GOOGL', quantity: 50, costBasis: 2500.00 },
  { symbol: 'MSFT', quantity: 75, costBasis: 300.00 },
  { symbol: 'TSLA', quantity: 25, costBasis: 800.00 },
  { symbol: 'AMZN', quantity: 30, costBasis: 3200.00 }
]

const DEMO_SYMBOLS = DEMO_HOLDINGS.map(h => h.symbol)

interface MarketDataDashboardContentProps {
  showPortfolio?: boolean
  showPriceList?: boolean
  showServiceStatus?: boolean
}

function MarketDataDashboardContent({
  showPortfolio = true,
  showPriceList = true,
  showServiceStatus = true
}: MarketDataDashboardContentProps) {
  const {
    prices,
    previousPrices,
    serviceStatus,
    connectionStatus,
    error,
    lastUpdate,
    reconnectAttempts,
    isConnected,
    hasError,
    refreshPrices,
    connectSSE
  } = useStreamingMarketData()

  const { symbolPrices, hasAllPrices } = useSymbolPrices(DEMO_SYMBOLS)
  const portfolioValue = usePortfolioValue(DEMO_HOLDINGS)

  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)

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
      {/* Header with Connection Status and Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Market Data Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time portfolio tracking with SSE streaming
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
          <ConnectionStatus
            status={connectionStatus}
            lastUpdate={lastUpdate}
            error={error}
            reconnectAttempts={reconnectAttempts}
            maxReconnectAttempts={5}
            onReconnect={connectSSE}
          />

          <div className="flex items-center space-x-2">
            <RefreshButton
              onRefresh={refreshPrices}
              disabled={!isConnected && !hasError}
              cooldownSeconds={60}
              size="sm"
            />
            <ForceRefreshButton
              onRefresh={refreshPrices}
              disabled={!isConnected && !hasError}
            />
          </div>
        </div>
      </div>

      {/* Error Display */}
      {hasError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-red-800 font-medium">Connection Error</span>
          </div>
          <p className="text-red-700 mt-1">{error}</p>
        </div>
      )}

      {/* Portfolio Overview */}
      {showPortfolio && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Portfolio Overview
            </h2>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <span>
                {hasAllPrices ? '✅' : '⚠️'}
                {portfolioValue.hasAllPrices ? 'All prices loaded' : `Missing ${portfolioValue.missingPrices.length} prices`}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Value</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {formatCurrency(portfolioValue.totalValue)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">Cost Basis</p>
              <p className="text-xl font-semibold text-gray-700 dark:text-gray-300">
                {formatCurrency(portfolioValue.totalCostBasis)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">Gain/Loss</p>
              <p className={`text-xl font-semibold ${
                portfolioValue.totalGainLoss >= 0
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
              }`}>
                {portfolioValue.totalGainLoss >= 0 ? '+' : ''}{formatCurrency(portfolioValue.totalGainLoss)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">Return %</p>
              <p className={`text-xl font-semibold ${
                portfolioValue.totalGainLossPercent >= 0
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-red-600 dark:text-red-400'
              }`}>
                {portfolioValue.totalGainLossPercent >= 0 ? '+' : ''}{portfolioValue.totalGainLossPercent.toFixed(2)}%
              </p>
            </div>
          </div>

          {/* Holdings Breakdown */}
          <div className="space-y-2">
            <h3 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-3">Holdings</h3>
            {portfolioValue.holdings.map(holding => (
              <div
                key={holding.symbol}
                className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {holding.symbol}
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {holding.quantity} shares @ {formatCurrency(holding.currentPrice)}
                  </span>
                  {holding.cached && (
                    <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                      Cached
                    </span>
                  )}
                </div>
                <div className="text-right">
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    {formatCurrency(holding.currentValue)}
                  </p>
                  <p className={`text-sm ${
                    holding.gainLoss >= 0
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {holding.gainLoss >= 0 ? '+' : ''}{formatCurrency(holding.gainLoss)} ({holding.gainLossPercent.toFixed(2)}%)
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Individual Price Displays */}
      {showPriceList && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Individual Stock Prices
          </h2>

          {selectedSymbol && prices[selectedSymbol] && (
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <h3 className="text-md font-medium">Selected: {selectedSymbol}</h3>
                <button
                  onClick={() => setSelectedSymbol(null)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  ×
                </button>
              </div>
              <StreamingPriceDisplay
                price={prices[selectedSymbol]}
                previousPrice={previousPrices[selectedSymbol]}
                showVolume={true}
                showMarketCap={true}
                showUpdateTime={true}
              />
            </div>
          )}

          <StreamingPriceList
            prices={prices}
            previousPrices={previousPrices}
            onSymbolClick={setSelectedSymbol}
          />
        </div>
      )}

      {/* Service Status */}
      {showServiceStatus && serviceStatus && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Service Status
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">
                Overall Status
              </h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    serviceStatus.status === 'healthy'
                      ? 'bg-green-100 text-green-800'
                      : serviceStatus.status === 'degraded'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {serviceStatus.status}
                  </span>
                </div>
                {serviceStatus.next_update_in_seconds && (
                  <div className="flex justify-between">
                    <span>Next update:</span>
                    <span>{Math.floor(serviceStatus.next_update_in_seconds / 60)}m {serviceStatus.next_update_in_seconds % 60}s</span>
                  </div>
                )}
              </div>
            </div>

            <div>
              <h3 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">
                Cache Statistics
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Total symbols:</span>
                  <span>{serviceStatus.cache_stats.total_symbols}</span>
                </div>
                <div className="flex justify-between">
                  <span>Fresh:</span>
                  <span className="text-green-600">{serviceStatus.cache_stats.fresh_symbols}</span>
                </div>
                <div className="flex justify-between">
                  <span>Stale:</span>
                  <span className="text-orange-600">{serviceStatus.cache_stats.stale_symbols}</span>
                </div>
                <div className="flex justify-between">
                  <span>Cache hit rate:</span>
                  <span>{(serviceStatus.cache_stats.cache_hit_rate * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Data Providers */}
          <div className="mt-4">
            <h3 className="text-md font-medium text-gray-900 dark:text-gray-100 mb-2">
              Data Providers
            </h3>
            <div className="space-y-2">
              {Object.entries(serviceStatus.providers_status).map(([name, status]) => (
                <div key={name} className="flex justify-between items-center">
                  <span className="capitalize">{name.replace('_', ' ')}</span>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      status.status === 'healthy'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {status.status}
                    </span>
                    <span className="text-xs text-gray-500">
                      Priority: {status.priority}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

interface MarketDataDashboardProps {
  symbols?: string[]
  portfolioIds?: string[]
  enableRealTime?: boolean
  showPortfolio?: boolean
  showPriceList?: boolean
  showServiceStatus?: boolean
}

export function MarketDataDashboard({
  symbols = DEMO_SYMBOLS,
  portfolioIds = [],
  enableRealTime = true,
  showPortfolio = true,
  showPriceList = true,
  showServiceStatus = true
}: MarketDataDashboardProps) {
  return (
    <StreamingMarketDataProvider
      symbols={symbols}
      portfolioIds={portfolioIds}
      enableRealTime={enableRealTime}
      autoRefresh={true}
      refreshIntervalMs={900000} // 15 minutes
      maxReconnectAttempts={5}
      reconnectDelayMs={5000}
    >
      <MarketDataDashboardContent
        showPortfolio={showPortfolio}
        showPriceList={showPriceList}
        showServiceStatus={showServiceStatus}
      />
    </StreamingMarketDataProvider>
  )
}