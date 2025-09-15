// Trend information
export interface TrendData {
  trend: 'up' | 'down' | 'neutral'
  change: number
  change_percent: number
  opening_price?: number
}

// Backend API Response Types
export interface PriceResponse {
  symbol: string
  price: number
  volume?: number
  market_cap?: number
  fetched_at: string
  cached: boolean

  // Extended price information
  opening_price?: number
  high_price?: number
  low_price?: number
  previous_close?: number

  // Trend information
  trend?: TrendData

  // Market metrics
  fifty_two_week_high?: number
  fifty_two_week_low?: number
  dividend_yield?: number
  pe_ratio?: number
  beta?: number

  // Metadata
  currency?: string
  company_name?: string
}

export interface BulkPriceResponse {
  prices: Record<string, PriceResponse>
  fetched_at: string
  cached_count: number
  fresh_count: number
}

export interface ServiceStatusResponse {
  status: 'healthy' | 'degraded' | 'unavailable'
  providers_status: Record<string, {
    enabled: boolean
    priority: number
    rate_limit_per_day: number
    status: string
  }>
  next_update_in_seconds?: number
  last_update_at?: string
  cache_stats: {
    total_symbols: number
    fresh_symbols: number
    stale_symbols: number
    cache_hit_rate: number
  }
}

// SSE Message Types
export interface SSEMessage {
  type: 'connection' | 'price_update' | 'heartbeat' | 'error'
  connection_id?: string
  status?: string
  data?: Record<string, {
    price: number
    volume?: number
    timestamp: string
  }>
  timestamp?: string
  message?: string
}

// Legacy types for backward compatibility
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