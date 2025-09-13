import { useState, useEffect, useRef, useCallback } from 'react'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import {
  PriceResponse,
  BulkPriceResponse,
  ServiceStatusResponse,
  SSEMessage,
  ConnectionStatus
} from '@/types/marketData'
import { useAuth } from '@/contexts/AuthContext'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface UseMarketDataStreamOptions {
  enableRealTime?: boolean
  autoRefresh?: boolean
  refreshIntervalMs?: number
  maxReconnectAttempts?: number
  reconnectDelayMs?: number
}

interface MarketDataStreamState {
  prices: Record<string, PriceResponse>
  serviceStatus: ServiceStatusResponse | null
  connectionStatus: ConnectionStatus
  error: string | null
  lastUpdate: string | null
  reconnectAttempts: number
}

export function useMarketDataStream(
  symbols: string[] = [],
  portfolioIds: string[] = [],
  options: UseMarketDataStreamOptions = {}
) {
  const {
    enableRealTime = true,
    autoRefresh = true,
    refreshIntervalMs = 900000, // 15 minutes
    maxReconnectAttempts = 5,
    reconnectDelayMs = 5000
  } = options

  const { token } = useAuth()
  const abortControllerRef = useRef<AbortController | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const refreshTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const [state, setState] = useState<MarketDataStreamState>({
    prices: {},
    serviceStatus: null,
    connectionStatus: 'disconnected',
    error: null,
    lastUpdate: null,
    reconnectAttempts: 0
  })

  // Get auth headers for API requests
  const getAuthHeaders = useCallback(() => {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Cache-Control': 'no-cache'
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return headers
  }, [token])

  // Fetch current prices from REST API
  const fetchPrices = useCallback(async (symbolsList: string[]): Promise<BulkPriceResponse | null> => {
    if (!token || symbolsList.length === 0) return null

    try {
      const symbolsParam = symbolsList.join('&symbols=')
      const response = await fetch(
        `${API_BASE_URL}/api/v1/market-data/prices?symbols=${symbolsParam}`,
        { headers: getAuthHeaders() }
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching prices:', error)
      setState(prev => ({
        ...prev,
        error: `Failed to fetch prices: ${error instanceof Error ? error.message : 'Unknown error'}`
      }))
      return null
    }
  }, [token, getAuthHeaders])

  // Fetch service status
  const fetchServiceStatus = useCallback(async (): Promise<ServiceStatusResponse | null> => {
    if (!token) return null

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/market-data/status`,
        { headers: getAuthHeaders() }
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching service status:', error)
      setState(prev => ({
        ...prev,
        error: `Failed to fetch service status: ${error instanceof Error ? error.message : 'Unknown error'}`
      }))
      return null
    }
  }, [token, getAuthHeaders])

  // Manual refresh function
  const refreshPrices = useCallback(async (force: boolean = false) => {
    if (!token) return

    try {
      const payload = {
        symbols: symbols.length > 0 ? symbols : undefined,
        force
      }

      const response = await fetch(
        `${API_BASE_URL}/api/v1/market-data/refresh`,
        {
          method: 'POST',
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()

      // Fetch updated prices after refresh
      const pricesData = await fetchPrices(symbols)
      if (pricesData) {
        setState(prev => ({
          ...prev,
          prices: pricesData.prices,
          lastUpdate: pricesData.fetched_at,
          error: null
        }))
      }

      return result
    } catch (error) {
      console.error('Error refreshing prices:', error)
      setState(prev => ({
        ...prev,
        error: `Failed to refresh prices: ${error instanceof Error ? error.message : 'Unknown error'}`
      }))
      throw error
    }
  }, [token, symbols, getAuthHeaders, fetchPrices])

  // Connect to SSE stream
  const connectSSE = useCallback(async () => {
    if (!enableRealTime || !token || (symbols.length === 0 && portfolioIds.length === 0)) {
      setState(prev => ({ ...prev, connectionStatus: 'disconnected' }))
      return
    }

    // Abort existing connection
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()

    setState(prev => ({
      ...prev,
      connectionStatus: 'connecting',
      error: null
    }))

    try {
      const url = new URL(`${API_BASE_URL}/api/v1/market-data/stream`)

      // Add query parameters
      if (symbols.length > 0) {
        symbols.forEach(symbol => url.searchParams.append('symbols', symbol))
      }
      if (portfolioIds.length > 0) {
        portfolioIds.forEach(id => url.searchParams.append('portfolio_ids', id))
      }

      await fetchEventSource(url.toString(), {
        headers: getAuthHeaders(),
        signal: abortControllerRef.current.signal,

        onopen: async (response) => {
          if (response.ok && response.headers.get('content-type')?.includes('text/event-stream')) {
            setState(prev => ({
              ...prev,
              connectionStatus: 'connected',
              reconnectAttempts: 0,
              error: null
            }))
            return
          }

          if (response.status >= 400 && response.status < 500 && response.status !== 429) {
            throw new Error(`HTTP ${response.status}: Authentication or authorization error`)
          } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`)
          }
        },

        onmessage: (event) => {
          try {
            const message: SSEMessage = JSON.parse(event.data)

            switch (message.type) {
              case 'connection':
                console.log('SSE Connection established:', message.connection_id)
                break

              case 'price_update':
                if (message.data) {
                  setState(prev => ({
                    ...prev,
                    prices: {
                      ...prev.prices,
                      ...Object.fromEntries(
                        Object.entries(message.data!).map(([symbol, priceData]) => [
                          symbol,
                          {
                            symbol,
                            price: priceData.price,
                            volume: priceData.volume,
                            market_cap: undefined,
                            fetched_at: priceData.timestamp,
                            cached: false
                          } as PriceResponse
                        ])
                      )
                    },
                    lastUpdate: message.timestamp || new Date().toISOString(),
                    error: null
                  }))
                }
                break

              case 'heartbeat':
                // Keep connection alive - no action needed
                break

              case 'error':
                setState(prev => ({
                  ...prev,
                  error: message.message || 'Stream error occurred'
                }))
                break
            }
          } catch (error) {
            console.error('Error parsing SSE message:', error)
            setState(prev => ({
              ...prev,
              error: 'Invalid message format received'
            }))
          }
        },

        onerror: (error) => {
          console.error('SSE error:', error)
          setState(prev => ({ ...prev, connectionStatus: 'error' }))

          // Attempt reconnection if not at max attempts
          if (state.reconnectAttempts < maxReconnectAttempts) {
            setState(prev => ({
              ...prev,
              connectionStatus: 'reconnecting',
              reconnectAttempts: prev.reconnectAttempts + 1
            }))

            reconnectTimeoutRef.current = setTimeout(() => {
              connectSSE()
            }, reconnectDelayMs)
          } else {
            setState(prev => ({
              ...prev,
              connectionStatus: 'failed',
              error: 'Max reconnection attempts reached'
            }))
          }

          throw error // This will cause fetchEventSource to stop retrying
        }
      })
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Connection was manually aborted
        setState(prev => ({ ...prev, connectionStatus: 'disconnected' }))
      } else {
        console.error('SSE connection error:', error)
        setState(prev => ({
          ...prev,
          connectionStatus: 'error',
          error: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
        }))
      }
    }
  }, [enableRealTime, token, symbols, portfolioIds, getAuthHeaders, state.reconnectAttempts, maxReconnectAttempts, reconnectDelayMs])

  // Disconnect SSE
  const disconnectSSE = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    setState(prev => ({ ...prev, connectionStatus: 'disconnected' }))
  }, [])

  // Setup auto-refresh
  const setupAutoRefresh = useCallback(() => {
    if (!autoRefresh || !token) return

    const refreshData = async () => {
      // Fetch latest prices
      if (symbols.length > 0) {
        const pricesData = await fetchPrices(symbols)
        if (pricesData) {
          setState(prev => ({
            ...prev,
            prices: { ...prev.prices, ...pricesData.prices },
            lastUpdate: pricesData.fetched_at
          }))
        }
      }

      // Fetch service status
      const statusData = await fetchServiceStatus()
      if (statusData) {
        setState(prev => ({ ...prev, serviceStatus: statusData }))
      }

      // Schedule next refresh
      refreshTimeoutRef.current = setTimeout(refreshData, refreshIntervalMs)
    }

    // Initial refresh
    refreshData()

    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current)
      }
    }
  }, [autoRefresh, token, symbols, refreshIntervalMs, fetchPrices, fetchServiceStatus])

  // Effect for SSE connection management
  useEffect(() => {
    if (enableRealTime && token) {
      connectSSE()
    } else {
      disconnectSSE()
    }

    return disconnectSSE
  }, [enableRealTime, token, symbols, portfolioIds, connectSSE, disconnectSSE])

  // Effect for auto-refresh setup
  useEffect(() => {
    return setupAutoRefresh()
  }, [setupAutoRefresh])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectSSE()
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current)
      }
    }
  }, [disconnectSSE])

  // Initial data fetch when symbols change
  useEffect(() => {
    if (token && symbols.length > 0) {
      fetchPrices(symbols).then(pricesData => {
        if (pricesData) {
          setState(prev => ({
            ...prev,
            prices: { ...prev.prices, ...pricesData.prices },
            lastUpdate: pricesData.fetched_at
          }))
        }
      })
    }

    if (token) {
      fetchServiceStatus().then(statusData => {
        if (statusData) {
          setState(prev => ({ ...prev, serviceStatus: statusData }))
        }
      })
    }
  }, [token, symbols, fetchPrices, fetchServiceStatus])

  return {
    ...state,
    refreshPrices,
    connectSSE,
    disconnectSSE,
    isConnected: state.connectionStatus === 'connected',
    isConnecting: state.connectionStatus === 'connecting',
    hasError: !!state.error
  }
}