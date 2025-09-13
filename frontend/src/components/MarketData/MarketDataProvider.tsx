'use client'

import React, { createContext, useContext, ReactNode } from 'react'
import { useMarketData } from '@/hooks/useMarketData'
import { MarketPrice, HistoricalDataPoint, MarketStatistics, ConnectionStatus, HistoricalPeriod } from '@/types/marketData'

interface MarketDataContextType {
  prices: Record<string, MarketPrice>
  historicalData: Record<string, HistoricalDataPoint[]>
  marketStatistics: MarketStatistics
  connectionStatus: ConnectionStatus
  error: string | null
  isMarketOpen: boolean
  reconnectAttempts: number
  fetchHistoricalData: (symbols: string[], period: HistoricalPeriod) => Promise<void>
  fetchMarketStatistics: () => Promise<void>
}

const MarketDataContext = createContext<MarketDataContextType | undefined>(undefined)

interface MarketDataProviderProps {
  children: ReactNode
  symbols: string[]
}

export function MarketDataProvider({ children, symbols }: MarketDataProviderProps) {
  const marketData = useMarketData(symbols)

  return (
    <MarketDataContext.Provider value={marketData}>
      {children}
    </MarketDataContext.Provider>
  )
}

export function useMarketDataContext() {
  const context = useContext(MarketDataContext)
  if (context === undefined) {
    throw new Error('useMarketDataContext must be used within a MarketDataProvider')
  }
  return context
}