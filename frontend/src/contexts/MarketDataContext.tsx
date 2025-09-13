'use client'

/**
 * Market Data Context Provider
 *
 * Provides real-time market data updates across the application using SSE streaming.
 * Manages portfolio-specific subscriptions and price data caching.
 */

import React, { createContext, useContext, useCallback, useMemo } from 'react'
import { useMarketDataStream } from '@/hooks/useMarketDataStream'
import type {
  PriceResponse,
  ServiceStatusResponse,
  ConnectionStatus
} from '@/types/marketData'

interface MarketDataContextValue {
  // Price data
  prices: Record<string, PriceResponse>
  serviceStatus: ServiceStatusResponse | null
  lastUpdate: string | null

  // Connection state
  connectionStatus: ConnectionStatus
  isConnected: boolean
  isConnecting: boolean
  hasError: boolean
  error: string | null

  // Actions
  refreshPrices: (force?: boolean) => Promise<any>
  connectSSE: () => void
  disconnectSSE: () => void

  // Utility functions
  getPrice: (symbol: string) => PriceResponse | null
  getFormattedPrice: (symbol: string, currency?: string) => string
  isPriceStale: (symbol: string, maxAgeMinutes?: number) => boolean
  getConnectionStatusColor: () => string
  getConnectionStatusText: () => string
}

interface MarketDataProviderProps {
  children: React.ReactNode
  symbols?: string[]
  portfolioIds?: string[]
  enableRealTime?: boolean
  autoRefresh?: boolean
  refreshIntervalMs?: number
}

const MarketDataContext = createContext<MarketDataContextValue | null>(null)

export function MarketDataProvider({
  children,
  symbols = [],
  portfolioIds = [],
  enableRealTime = true,
  autoRefresh = true,
  refreshIntervalMs = 900000 // 15 minutes
}: MarketDataProviderProps) {
  const marketDataStream = useMarketDataStream(symbols, portfolioIds, {
    enableRealTime,
    autoRefresh,
    refreshIntervalMs,
    maxReconnectAttempts: 5,
    reconnectDelayMs: 5000
  })

  // Utility function to get a specific price
  const getPrice = useCallback((symbol: string): PriceResponse | null => {
    return marketDataStream.prices[symbol.toUpperCase()] || null
  }, [marketDataStream.prices])

  // Format price for display with currency symbol
  const getFormattedPrice = useCallback((symbol: string, currency = 'AUD'): string => {
    const priceData = getPrice(symbol)
    if (!priceData) return 'N/A'

    const formatter = new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 4
    })

    return formatter.format(priceData.price)
  }, [getPrice])

  // Check if price data is stale
  const isPriceStale = useCallback((symbol: string, maxAgeMinutes = 30): boolean => {
    const priceData = getPrice(symbol)
    if (!priceData) return true

    const priceTime = new Date(priceData.fetched_at)
    const now = new Date()
    const ageMinutes = (now.getTime() - priceTime.getTime()) / (1000 * 60)

    return ageMinutes > maxAgeMinutes
  }, [getPrice])

  // Get connection status color for UI indicators
  const getConnectionStatusColor = useCallback((): string => {
    switch (marketDataStream.connectionStatus) {
      case 'connected':
        return 'text-green-500'
      case 'connecting':
      case 'reconnecting':
        return 'text-yellow-500'
      case 'error':
      case 'failed':
        return 'text-red-500'
      case 'disconnected':
      default:
        return 'text-gray-500'
    }
  }, [marketDataStream.connectionStatus])

  // Get human-readable connection status text
  const getConnectionStatusText = useCallback((): string => {
    switch (marketDataStream.connectionStatus) {
      case 'connected':
        return 'Live'
      case 'connecting':
        return 'Connecting...'
      case 'reconnecting':
        return 'Reconnecting...'
      case 'error':
        return 'Connection Error'
      case 'failed':
        return 'Connection Failed'
      case 'disconnected':
      default:
        return 'Disconnected'
    }
  }, [marketDataStream.connectionStatus])

  // Context value with memoization for performance
  const contextValue = useMemo<MarketDataContextValue>(() => ({
    // Data
    prices: marketDataStream.prices,
    serviceStatus: marketDataStream.serviceStatus,
    lastUpdate: marketDataStream.lastUpdate,

    // Connection state
    connectionStatus: marketDataStream.connectionStatus,
    isConnected: marketDataStream.isConnected,
    isConnecting: marketDataStream.isConnecting,
    hasError: marketDataStream.hasError,
    error: marketDataStream.error,

    // Actions
    refreshPrices: marketDataStream.refreshPrices,
    connectSSE: marketDataStream.connectSSE,
    disconnectSSE: marketDataStream.disconnectSSE,

    // Utility functions
    getPrice,
    getFormattedPrice,
    isPriceStale,
    getConnectionStatusColor,
    getConnectionStatusText
  }), [
    marketDataStream,
    getPrice,
    getFormattedPrice,
    isPriceStale,
    getConnectionStatusColor,
    getConnectionStatusText
  ])

  return (
    <MarketDataContext.Provider value={contextValue}>
      {children}
    </MarketDataContext.Provider>
  )
}

// Hook to consume market data context
export function useMarketData() {
  const context = useContext(MarketDataContext)

  if (!context) {
    throw new Error('useMarketData must be used within a MarketDataProvider')
  }

  return context
}

// Higher-order component for wrapping components with market data
export function withMarketData<P extends object>(
  Component: React.ComponentType<P>,
  marketDataProps: Omit<MarketDataProviderProps, 'children'> = {}
) {
  return function MarketDataWrappedComponent(props: P) {
    return (
      <MarketDataProvider {...marketDataProps}>
        <Component {...props} />
      </MarketDataProvider>
    )
  }
}

// Hook for portfolio-specific market data
export function usePortfolioMarketData(portfolioId: string, symbols: string[] = []) {
  const baseMarketData = useMarketData()

  // Filter price data to only include symbols from this portfolio
  const portfolioPrices = useMemo(() => {
    if (symbols.length === 0) return {}

    return Object.fromEntries(
      symbols.map(symbol => [
        symbol,
        baseMarketData.getPrice(symbol)
      ]).filter(([, price]) => price !== null)
    ) as Record<string, PriceResponse>
  }, [baseMarketData.prices, symbols, baseMarketData.getPrice])

  // Calculate portfolio-level metrics
  const portfolioMetrics = useMemo(() => {
    const prices = Object.values(portfolioPrices)
    const totalValue = prices.reduce((sum, price) => sum + price.price, 0)
    const hasStaleData = symbols.some(symbol => baseMarketData.isPriceStale(symbol))
    const lastUpdateTime = prices.reduce((latest, price) => {
      const priceTime = new Date(price.fetched_at).getTime()
      return priceTime > latest ? priceTime : latest
    }, 0)

    return {
      totalSymbols: symbols.length,
      pricesAvailable: prices.length,
      hasStaleData,
      lastUpdate: lastUpdateTime > 0 ? new Date(lastUpdateTime).toISOString() : null,
      averagePrice: prices.length > 0 ? totalValue / prices.length : 0
    }
  }, [portfolioPrices, symbols, baseMarketData.isPriceStale])

  return {
    ...baseMarketData,
    portfolioPrices,
    portfolioMetrics,
    symbols
  }
}