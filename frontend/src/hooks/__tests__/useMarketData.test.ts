/**
 * Tests for real-time market data integration
 * RED phase - These tests will fail initially as the features don't exist yet
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import { useMarketData } from '../useMarketData'

// Mock fetch globally
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

// Mock WebSocket
const mockWebSocket = {
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  send: jest.fn(),
  close: jest.fn(),
  readyState: WebSocket.OPEN
}

global.WebSocket = jest.fn(() => mockWebSocket) as any

// Mock auth context
const mockUseAuth = {
  token: 'test-token',
  user: { id: '1', email: 'test@example.com' }
}

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth
}))

describe('useMarketData', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    mockWebSocket.addEventListener.mockClear()
    mockWebSocket.removeEventListener.mockClear()
    mockWebSocket.send.mockClear()
    mockWebSocket.close.mockClear()
    ;(global.WebSocket as jest.Mock).mockClear()
    jest.clearAllTimers()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  describe('Real-time Price Updates', () => {
    it('should establish WebSocket connection for real-time updates', async () => {
      const symbols = ['AAPL', 'GOOGL']
      const { result } = renderHook(() => useMarketData(symbols))

      expect(global.WebSocket).toHaveBeenCalledWith(
        'ws://localhost:8001/api/v1/market-data/ws?symbols=AAPL,GOOGL&token=test-token'
      )
      expect(mockWebSocket.addEventListener).toHaveBeenCalledWith('message', expect.any(Function))
      expect(mockWebSocket.addEventListener).toHaveBeenCalledWith('error', expect.any(Function))
      expect(mockWebSocket.addEventListener).toHaveBeenCalledWith('close', expect.any(Function))
    })

    it('should handle real-time price updates via WebSocket', async () => {
      const symbols = ['AAPL']
      const { result } = renderHook(() => useMarketData(symbols))

      // First simulate WebSocket open event
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1]

      await act(async () => {
        openHandler?.()
      })

      // Simulate WebSocket message
      const mockPriceUpdate = {
        type: 'price_update',
        data: {
          symbol: 'AAPL',
          price: 150.25,
          change: 2.15,
          change_percent: 1.45,
          volume: 45678900,
          timestamp: '2024-01-15T10:30:00Z'
        }
      }

      const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'message'
      )?.[1]

      await act(async () => {
        messageHandler?.({ data: JSON.stringify(mockPriceUpdate) })
      })

      expect(result.current.prices).toEqual({
        'AAPL': {
          symbol: 'AAPL',
          price: 150.25,
          change: 2.15,
          change_percent: 1.45,
          volume: 45678900,
          timestamp: '2024-01-15T10:30:00Z'
        }
      })
      expect(result.current.connectionStatus).toBe('connected')
    })

    it('should handle multiple stock updates', async () => {
      const symbols = ['AAPL', 'GOOGL', 'MSFT']
      const { result } = renderHook(() => useMarketData(symbols))

      // First simulate WebSocket open event
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1]

      await act(async () => {
        openHandler?.()
      })

      const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'message'
      )?.[1]

      const updates = [
        {
          type: 'price_update',
          data: { symbol: 'AAPL', price: 150.25, change: 2.15, change_percent: 1.45 }
        },
        {
          type: 'price_update', 
          data: { symbol: 'GOOGL', price: 2800.50, change: -15.30, change_percent: -0.54 }
        },
        {
          type: 'price_update',
          data: { symbol: 'MSFT', price: 380.75, change: 5.20, change_percent: 1.38 }
        }
      ]

      for (const update of updates) {
        await act(async () => {
          messageHandler?.({ data: JSON.stringify(update) })
        })
      }

      expect(Object.keys(result.current.prices)).toHaveLength(3)
      expect(result.current.prices['AAPL'].price).toBe(150.25)
      expect(result.current.prices['GOOGL'].price).toBe(2800.50)
      expect(result.current.prices['MSFT'].price).toBe(380.75)
    })
  })

  describe('Historical Data Fetching', () => {
    it('should fetch historical price data for stocks', async () => {
      const mockHistoricalData = {
        'AAPL': [
          { date: '2024-01-12', open: 148.20, high: 150.50, low: 147.80, close: 149.75, volume: 52000000 },
          { date: '2024-01-13', open: 149.80, high: 151.20, low: 148.90, close: 150.95, volume: 48000000 },
          { date: '2024-01-14', open: 150.90, high: 152.10, low: 149.50, close: 151.80, volume: 45000000 }
        ]
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockHistoricalData
      } as Response)

      const { result } = renderHook(() => useMarketData(['AAPL']))

      await act(async () => {
        await result.current.fetchHistoricalData(['AAPL'], '1week')
      })

      expect(result.current.historicalData).toEqual(mockHistoricalData)
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/market-data/historical?symbols=AAPL&period=1week',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      )
    })

    it('should support different time periods for historical data', async () => {
      const { result } = renderHook(() => useMarketData(['AAPL']))

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({})
      } as Response)

      const periods = ['1day', '1week', '1month', '3months', '1year']

      for (const period of periods) {
        await act(async () => {
          await result.current.fetchHistoricalData(['AAPL'], period)
        })

        expect(mockFetch).toHaveBeenCalledWith(
          `http://localhost:8001/api/v1/market-data/historical?symbols=AAPL&period=${period}`,
          expect.any(Object)
        )
      }
    })
  })

  describe('Market Statistics', () => {
    it('should fetch market statistics and indicators', async () => {
      const mockMarketStats = {
        market_status: 'open',
        trading_hours: {
          open: '09:30',
          close: '16:00',
          timezone: 'America/New_York'
        },
        indices: {
          'SPY': { price: 445.20, change: 2.15, change_percent: 0.48 },
          'QQQ': { price: 380.50, change: 1.80, change_percent: 0.47 },
          'DIA': { price: 355.75, change: 1.25, change_percent: 0.35 }
        },
        sectors: {
          'Technology': { change_percent: 0.85 },
          'Healthcare': { change_percent: 0.42 },
          'Financials': { change_percent: 0.28 }
        }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMarketStats
      } as Response)

      const { result } = renderHook(() => useMarketData([]))

      await act(async () => {
        await result.current.fetchMarketStatistics()
      })

      expect(result.current.marketStatistics).toEqual(mockMarketStats)
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/market-data/statistics',
        expect.any(Object)
      )
    })

    it('should track market open/close status', async () => {
      const mockStats = {
        market_status: 'closed',
        next_open: '2024-01-16T09:30:00-05:00'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStats
      } as Response)

      const { result } = renderHook(() => useMarketData([]))

      await act(async () => {
        await result.current.fetchMarketStatistics()
      })

      expect(result.current.isMarketOpen).toBe(false)
      expect(result.current.marketStatistics.market_status).toBe('closed')
    })
  })

  describe('Connection Management', () => {
    it('should handle WebSocket connection errors', async () => {
      const { result } = renderHook(() => useMarketData(['AAPL']))

      // First simulate WebSocket open event
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1]

      await act(async () => {
        openHandler?.()
      })

      const errorHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'error'
      )?.[1]

      await act(async () => {
        errorHandler?.({ type: 'error', message: 'Connection failed' })
      })

      expect(result.current.connectionStatus).toBe('error')
      expect(result.current.error).toBeTruthy()
    })

    it('should attempt to reconnect on connection loss', async () => {
      const { result } = renderHook(() => useMarketData(['AAPL']))

      // First simulate WebSocket open event
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1]

      await act(async () => {
        openHandler?.()
      })

      const closeHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'close'
      )?.[1]

      await act(async () => {
        closeHandler?.({ code: 1006, reason: 'Connection lost' })
      })

      expect(result.current.connectionStatus).toBe('reconnecting')

      // Fast-forward reconnection delay
      await act(async () => {
        jest.advanceTimersByTime(5000)
      })

      // Should attempt to create new WebSocket connection
      expect(global.WebSocket).toHaveBeenCalledTimes(2)
    })

    it('should stop reconnection attempts after max retries', async () => {
      const { result } = renderHook(() => useMarketData(['AAPL']))

      // First simulate WebSocket open event
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1]

      await act(async () => {
        openHandler?.()
      })

      const closeHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'close'
      )?.[1]

      // Simulate multiple connection failures
      for (let i = 0; i < 6; i++) {
        await act(async () => {
          closeHandler?.({ code: 1006, reason: 'Connection lost' })
        })

        await act(async () => {
          jest.advanceTimersByTime(5000)
        })
      }

      expect(result.current.connectionStatus).toBe('failed')
      expect(result.current.reconnectAttempts).toBe(5) // Max retries
    })

    it('should clean up WebSocket connection on unmount', () => {
      const { unmount } = renderHook(() => useMarketData(['AAPL']))

      unmount()

      expect(mockWebSocket.close).toHaveBeenCalled()
    })
  })

  describe('Subscription Management', () => {
    it('should update subscriptions when symbols change', async () => {
      const { result, rerender } = renderHook(
        ({ symbols }) => useMarketData(symbols),
        { initialProps: { symbols: ['AAPL'] } }
      )

      // First simulate WebSocket open event to establish connection
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1]

      await act(async () => {
        openHandler?.()
      })

      // Clear previous calls
      mockWebSocket.send.mockClear()

      // Change symbols
      await act(async () => {
        rerender({ symbols: ['AAPL', 'GOOGL'] })
      })

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'subscribe',
          symbols: ['GOOGL']
        })
      )
    })

    it('should unsubscribe from removed symbols', async () => {
      const { result, rerender } = renderHook(
        ({ symbols }) => useMarketData(symbols),
        { initialProps: { symbols: ['AAPL', 'GOOGL', 'MSFT'] } }
      )

      // First simulate WebSocket open event to establish connection
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1]

      await act(async () => {
        openHandler?.()
      })

      // Clear previous calls
      mockWebSocket.send.mockClear()

      // Remove some symbols
      await act(async () => {
        rerender({ symbols: ['AAPL'] })
      })

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'unsubscribe',
          symbols: ['GOOGL', 'MSFT']
        })
      )
    })
  })

  describe('Data Validation and Error Handling', () => {
    it('should handle invalid price data gracefully', async () => {
      const { result } = renderHook(() => useMarketData(['AAPL']))

      // First simulate WebSocket open event
      const openHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'open'
      )?.[1]

      await act(async () => {
        openHandler?.()
      })

      const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'message'
      )?.[1]

      const invalidUpdate = {
        type: 'price_update',
        data: {
          symbol: 'AAPL',
          price: 'invalid',
          change: null
        }
      }

      await act(async () => {
        messageHandler?.({ data: JSON.stringify(invalidUpdate) })
      })

      // Should not update prices with invalid data
      expect(result.current.prices['AAPL']).toBeUndefined()
      expect(result.current.error).toBeTruthy()
    })

    it('should handle API errors for historical data', async () => {
      mockFetch.mockRejectedValueOnce(new Error('API Error'))

      const { result } = renderHook(() => useMarketData(['AAPL']))

      await act(async () => {
        await result.current.fetchHistoricalData(['AAPL'], '1week')
      })

      expect(result.current.error).toBe('Failed to fetch historical data')
      expect(result.current.historicalData).toEqual({})
    })

    it('should validate symbol format', async () => {
      const { result } = renderHook(() => useMarketData(['invalid-symbol', 'AAPL']))

      // Should filter out invalid symbols
      expect(global.WebSocket).toHaveBeenCalledWith(
        'ws://localhost:8001/api/v1/market-data/ws?symbols=AAPL&token=test-token'
      )
    })
  })

  describe('Performance Optimization', () => {
    it('should throttle rapid price updates', async () => {
      const { result } = renderHook(() => useMarketData(['AAPL']))

      const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
        call => call[0] === 'message'
      )?.[1]

      // Send multiple rapid updates
      const updates = Array.from({ length: 10 }, (_, i) => ({
        type: 'price_update',
        data: { symbol: 'AAPL', price: 150 + i, change: i }
      }))

      for (const update of updates) {
        await act(async () => {
          messageHandler?.({ data: JSON.stringify(update) })
        })
      }

      // Should only process the latest update due to throttling
      expect(result.current.prices['AAPL'].price).toBe(159) // Latest price
    })

    it('should limit number of concurrent subscriptions', async () => {
      const manySymbols = Array.from({ length: 150 }, (_, i) => `STOCK${i}`)
      const { result } = renderHook(() => useMarketData(manySymbols))

      // Should limit to maximum allowed subscriptions (e.g., 100)
      const wsCall = (global.WebSocket as jest.Mock).mock.calls[0][0]
      const url = new URL(wsCall.replace('ws://', 'http://'))
      const symbols = url.searchParams.get('symbols')?.split(',') || []
      
      expect(symbols.length).toBeLessThanOrEqual(100)
    })
  })
})