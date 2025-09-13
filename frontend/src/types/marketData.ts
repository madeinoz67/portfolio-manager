export interface MarketPrice {
  symbol: string
  price: number
  change: number
  change_percent: number
  volume?: number
  timestamp: string
  high_52week?: number
  low_52week?: number
  market_cap?: number
}

export interface HistoricalDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  adjusted_close?: number
}

export interface MarketStatistics {
  market_status: 'open' | 'closed' | 'pre_market' | 'after_hours'
  trading_hours?: {
    open: string
    close: string
    timezone: string
  }
  indices?: Record<string, MarketPrice>
  sectors?: Record<string, { change_percent: number }>
  next_open?: string
  last_close?: string
}

export interface WebSocketMessage {
  type: 'price_update' | 'market_status' | 'error' | 'heartbeat'
  data?: any
  timestamp?: string
}

export interface MarketDataSubscription {
  symbols: string[]
  type: 'real_time' | 'delayed'
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting' | 'failed'

export type HistoricalPeriod = '1day' | '1week' | '1month' | '3months' | '6months' | '1year' | '2years' | '5years'

export interface UseMarketDataOptions {
  enableRealTime?: boolean
  reconnectAttempts?: number
  reconnectDelay?: number
  throttleMs?: number
  maxSubscriptions?: number
}