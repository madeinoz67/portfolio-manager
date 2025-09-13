'use client'

import React, { createContext, useContext, ReactNode, useRef, useEffect } from 'react'
import { useMarketDataStream } from '@/hooks/useMarketDataStream'
import {
  PriceResponse,
  ServiceStatusResponse,
  ConnectionStatus
} from '@/types/marketData'

interface StreamingMarketDataContextType {
  prices: Record<string, PriceResponse>
  previousPrices: Record<string, number>
  serviceStatus: ServiceStatusResponse | null
  connectionStatus: ConnectionStatus
  error: string | null
  lastUpdate: string | null
  reconnectAttempts: number
  isConnected: boolean
  isConnecting: boolean
  hasError: boolean
  refreshPrices: (force?: boolean) => Promise<any>
  connectSSE: () => void
  disconnectSSE: () => void
}

const StreamingMarketDataContext = createContext<StreamingMarketDataContextType | undefined>(undefined)

interface StreamingMarketDataProviderProps {
  children: ReactNode
  symbols?: string[]
  portfolioIds?: string[]
  enableRealTime?: boolean
  autoRefresh?: boolean
  refreshIntervalMs?: number
  maxReconnectAttempts?: number
  reconnectDelayMs?: number
}

export function StreamingMarketDataProvider({
  children,
  symbols = [],
  portfolioIds = [],
  enableRealTime = true,
  autoRefresh = true,
  refreshIntervalMs = 900000, // 15 minutes
  maxReconnectAttempts = 5,
  reconnectDelayMs = 5000
}: StreamingMarketDataProviderProps) {
  const previousPricesRef = useRef<Record<string, number>>({})

  const marketDataStream = useMarketDataStream(symbols, portfolioIds, {
    enableRealTime,
    autoRefresh,
    refreshIntervalMs,
    maxReconnectAttempts,
    reconnectDelayMs
  })

  // Track previous prices for change calculation
  useEffect(() => {
    Object.entries(marketDataStream.prices).forEach(([symbol, priceData]) => {
      if (previousPricesRef.current[symbol] === undefined) {
        // First time seeing this symbol, store current price as previous
        previousPricesRef.current[symbol] = priceData.price
      } else if (previousPricesRef.current[symbol] !== priceData.price) {
        // Price changed, update previous price
        const oldPrice = previousPricesRef.current[symbol]
        previousPricesRef.current[symbol] = priceData.price

        // Optional: Log price changes
        const change = priceData.price - oldPrice
        const changePercent = (change / oldPrice) * 100
        console.log(`${symbol}: $${oldPrice} -> $${priceData.price} (${change > 0 ? '+' : ''}${change.toFixed(2)}, ${changePercent.toFixed(2)}%)`)
      }
    })
  }, [marketDataStream.prices])

  const contextValue: StreamingMarketDataContextType = {
    ...marketDataStream,
    previousPrices: previousPricesRef.current
  }

  return (
    <StreamingMarketDataContext.Provider value={contextValue}>
      {children}
    </StreamingMarketDataContext.Provider>
  )
}

export function useStreamingMarketData() {
  const context = useContext(StreamingMarketDataContext)
  if (context === undefined) {
    throw new Error('useStreamingMarketData must be used within a StreamingMarketDataProvider')
  }
  return context
}

// Higher-order component for easy integration
interface WithStreamingMarketDataProps {
  symbols?: string[]
  portfolioIds?: string[]
  enableRealTime?: boolean
}

export function withStreamingMarketData<P extends object>(
  Component: React.ComponentType<P>,
  options: WithStreamingMarketDataProps = {}
) {
  const WrappedComponent = (props: P) => {
    return (
      <StreamingMarketDataProvider {...options}>
        <Component {...props} />
      </StreamingMarketDataProvider>
    )
  }

  WrappedComponent.displayName = `withStreamingMarketData(${Component.displayName || Component.name})`
  return WrappedComponent
}

// Utility hook for specific symbols
export function useSymbolPrices(symbols: string[]) {
  const { prices, previousPrices, isConnected, lastUpdate } = useStreamingMarketData()

  const symbolPrices = symbols.reduce((acc, symbol) => {
    if (prices[symbol]) {
      acc[symbol] = {
        current: prices[symbol],
        previous: previousPrices[symbol],
        change: previousPrices[symbol] ? prices[symbol].price - previousPrices[symbol] : 0,
        changePercent: previousPrices[symbol] ?
          ((prices[symbol].price - previousPrices[symbol]) / previousPrices[symbol]) * 100 : 0
      }
    }
    return acc
  }, {} as Record<string, {
    current: PriceResponse
    previous: number
    change: number
    changePercent: number
  }>)

  return {
    symbolPrices,
    isConnected,
    lastUpdate,
    hasAllPrices: symbols.every(symbol => prices[symbol] !== undefined)
  }
}

// Utility hook for portfolio value calculation
export function usePortfolioValue(holdings: Array<{ symbol: string; quantity: number; costBasis?: number }>) {
  const { prices, isConnected, lastUpdate } = useStreamingMarketData()

  const portfolioValue = holdings.reduce((acc, holding) => {
    const priceData = prices[holding.symbol]
    if (priceData) {
      const currentValue = priceData.price * holding.quantity
      const costBasis = holding.costBasis ? holding.costBasis * holding.quantity : 0
      const gainLoss = costBasis > 0 ? currentValue - costBasis : 0

      acc.totalValue += currentValue
      acc.totalCostBasis += costBasis
      acc.totalGainLoss += gainLoss
      acc.holdings.push({
        symbol: holding.symbol,
        quantity: holding.quantity,
        currentPrice: priceData.price,
        currentValue,
        costBasis: holding.costBasis || 0,
        gainLoss,
        gainLossPercent: costBasis > 0 ? (gainLoss / costBasis) * 100 : 0,
        cached: priceData.cached,
        lastUpdate: priceData.fetched_at
      })
    }
    return acc
  }, {
    totalValue: 0,
    totalCostBasis: 0,
    totalGainLoss: 0,
    totalGainLossPercent: 0,
    holdings: [] as Array<{
      symbol: string
      quantity: number
      currentPrice: number
      currentValue: number
      costBasis: number
      gainLoss: number
      gainLossPercent: number
      cached: boolean
      lastUpdate: string
    }>
  })

  // Calculate total gain/loss percentage
  if (portfolioValue.totalCostBasis > 0) {
    portfolioValue.totalGainLossPercent = (portfolioValue.totalGainLoss / portfolioValue.totalCostBasis) * 100
  }

  const missingPrices = holdings
    .filter(holding => !prices[holding.symbol])
    .map(holding => holding.symbol)

  return {
    ...portfolioValue,
    isConnected,
    lastUpdate,
    missingPrices,
    hasAllPrices: missingPrices.length === 0
  }
}