/**
 * Tests for stock search functionality
 * RED phase - These tests will fail initially as the features don't exist yet
 */
import { renderHook, waitFor, act } from '@testing-library/react'
import { useStockSearch } from '../useStockSearch'

// Mock fetch globally
global.fetch = jest.fn()
const mockFetch = fetch as jest.MockedFunction<typeof fetch>

// Mock auth context
const mockUseAuth = {
  token: 'test-token',
  user: { id: '1', email: 'test@example.com' }
}

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth
}))

describe('useStockSearch', () => {
  beforeEach(() => {
    mockFetch.mockClear()
    jest.clearAllTimers()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  describe('Basic Search Functionality', () => {
    it('should search for stocks with debounced input', async () => {
      const mockSearchResults = [
        {
          symbol: 'AAPL',
          company_name: 'Apple Inc.',
          current_price: '150.25',
          sector: 'Technology',
          market_cap: '2500000000000'
        },
        {
          symbol: 'GOOGL',
          company_name: 'Alphabet Inc.',
          current_price: '2800.50',
          sector: 'Technology',
          market_cap: '1800000000000'
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSearchResults
      } as Response)

      const { result } = renderHook(() => useStockSearch())

      // Initial state
      expect(result.current.searchResults).toEqual([])
      expect(result.current.loading).toBe(false)
      expect(result.current.error).toBe(null)

      // Trigger search
      await act(async () => {
        result.current.search('Apple')
      })

      // Should debounce - no immediate API call
      expect(mockFetch).not.toHaveBeenCalled()

      // Fast-forward debounce timer
      await act(async () => {
        jest.advanceTimersByTime(300) // Default debounce delay
      })

      await waitFor(() => {
        expect(result.current.searchResults).toEqual(mockSearchResults)
        expect(result.current.loading).toBe(false)
        expect(result.current.error).toBe(null)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/stocks/search?query=Apple',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      )
    })

    it('should handle empty search query', async () => {
      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.search('')
      })

      expect(result.current.searchResults).toEqual([])
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('should handle search query less than minimum length', async () => {
      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.search('A') // Single character
      })

      expect(result.current.searchResults).toEqual([])
      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('Advanced Search Features', () => {
    it('should support search by symbol and company name', async () => {
      const mockResults = [
        {
          symbol: 'MSFT',
          company_name: 'Microsoft Corporation',
          current_price: '380.75',
          sector: 'Technology',
          market_cap: '2800000000000'
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResults
      } as Response)

      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.search('MSFT')
      })

      await act(async () => {
        jest.advanceTimersByTime(300)
      })

      await waitFor(() => {
        expect(result.current.searchResults).toEqual(mockResults)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/stocks/search?query=MSFT',
        expect.any(Object)
      )
    })

    it('should support filtering by sector', async () => {
      const mockResults = [
        {
          symbol: 'JPM',
          company_name: 'JPMorgan Chase & Co.',
          current_price: '145.80',
          sector: 'Financials',
          market_cap: '425000000000'
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResults
      } as Response)

      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.searchWithFilters('bank', { sector: 'Financials' })
      })

      await act(async () => {
        jest.advanceTimersByTime(300)
      })

      await waitFor(() => {
        expect(result.current.searchResults).toEqual(mockResults)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/stocks/search?query=bank&sector=Financials',
        expect.any(Object)
      )
    })

    it('should support search suggestions/autocomplete', async () => {
      const mockSuggestions = [
        { symbol: 'AAPL', company_name: 'Apple Inc.' },
        { symbol: 'AMZN', company_name: 'Amazon.com Inc.' },
        { symbol: 'AMD', company_name: 'Advanced Micro Devices Inc.' }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSuggestions
      } as Response)

      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.getSuggestions('A')
      })

      await act(async () => {
        jest.advanceTimersByTime(150) // Faster for suggestions
      })

      await waitFor(() => {
        expect(result.current.suggestions).toEqual(mockSuggestions)
      })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/stocks/suggestions?query=A',
        expect.any(Object)
      )
    })
  })

  describe('Recent Searches', () => {
    it('should track and return recent searches', async () => {
      const { result } = renderHook(() => useStockSearch())

      const mockStock = {
        symbol: 'TSLA',
        company_name: 'Tesla Inc.',
        current_price: '250.00',
        sector: 'Consumer Discretionary',
        market_cap: '800000000000'
      }

      await act(async () => {
        result.current.addToRecentSearches(mockStock)
      })

      expect(result.current.recentSearches).toEqual([mockStock])
      expect(result.current.recentSearches).toHaveLength(1)
    })

    it('should limit recent searches to maximum count', async () => {
      const { result } = renderHook(() => useStockSearch())

      const stocks = Array.from({ length: 12 }, (_, i) => ({
        symbol: `STOCK${i}`,
        company_name: `Company ${i}`,
        current_price: '100.00',
        sector: 'Technology',
        market_cap: '1000000000'
      }))

      for (const stock of stocks) {
        await act(async () => {
          result.current.addToRecentSearches(stock)
        })
      }

      expect(result.current.recentSearches).toHaveLength(10) // Max limit
      expect(result.current.recentSearches[0].symbol).toBe('STOCK11') // Most recent first
    })

    it('should clear recent searches', async () => {
      const { result } = renderHook(() => useStockSearch())

      const mockStock = {
        symbol: 'NVDA',
        company_name: 'NVIDIA Corporation',
        current_price: '450.00',
        sector: 'Technology',
        market_cap: '1100000000000'
      }

      await act(async () => {
        result.current.addToRecentSearches(mockStock)
      })

      expect(result.current.recentSearches).toHaveLength(1)

      await act(async () => {
        result.current.clearRecentSearches()
      })

      expect(result.current.recentSearches).toEqual([])
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network Error'))

      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.search('ERROR')
      })

      await act(async () => {
        jest.advanceTimersByTime(300)
      })

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to search stocks. Please try again.')
        expect(result.current.searchResults).toEqual([])
        expect(result.current.loading).toBe(false)
      })
    })

    it('should handle HTTP error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal Server Error' })
      } as Response)

      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.search('ERROR500')
      })

      await act(async () => {
        jest.advanceTimersByTime(300)
      })

      await waitFor(() => {
        expect(result.current.error).toBe('Internal Server Error')
        expect(result.current.loading).toBe(false)
      })
    })

    it('should reset error state on new search', async () => {
      // First, trigger an error
      mockFetch.mockRejectedValueOnce(new Error('Network Error'))

      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.search('ERROR')
      })

      await act(async () => {
        jest.advanceTimersByTime(300)
      })

      await waitFor(() => {
        expect(result.current.error).toBeTruthy()
      })

      // Then, make a successful search
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [{ symbol: 'AAPL', company_name: 'Apple Inc.' }]
      } as Response)

      await act(async () => {
        result.current.search('Apple')
      })

      expect(result.current.error).toBe(null) // Error should be cleared immediately
    })
  })

  describe('Loading States', () => {
    it('should show loading state during search', async () => {
      let resolvePromise: (value: any) => void
      const searchPromise = new Promise((resolve) => {
        resolvePromise = resolve
      })

      mockFetch.mockReturnValueOnce(searchPromise as any)

      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.search('Loading')
      })

      await act(async () => {
        jest.advanceTimersByTime(300)
      })

      expect(result.current.loading).toBe(true)

      // Resolve the promise
      await act(async () => {
        resolvePromise!({
          ok: true,
          json: async () => []
        })
      })

      await waitFor(() => {
        expect(result.current.loading).toBe(false)
      })
    })
  })

  describe('Cache Management', () => {
    it('should cache search results', async () => {
      const mockResults = [
        {
          symbol: 'AAPL',
          company_name: 'Apple Inc.',
          current_price: '150.25',
          sector: 'Technology',
          market_cap: '2500000000000'
        }
      ]

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResults
      } as Response)

      const { result } = renderHook(() => useStockSearch())

      // First search
      await act(async () => {
        result.current.search('Apple')
      })

      await act(async () => {
        jest.advanceTimersByTime(300)
      })

      await waitFor(() => {
        expect(result.current.searchResults).toEqual(mockResults)
      })

      expect(mockFetch).toHaveBeenCalledTimes(1)

      // Second identical search - should use cache
      await act(async () => {
        result.current.search('Apple')
      })

      await act(async () => {
        jest.advanceTimersByTime(300)
      })

      // Should still have results but no additional API call
      expect(result.current.searchResults).toEqual(mockResults)
      expect(mockFetch).toHaveBeenCalledTimes(1) // No additional call
    })

    it('should provide cache clear functionality', async () => {
      const { result } = renderHook(() => useStockSearch())

      await act(async () => {
        result.current.clearCache()
      })

      expect(result.current.searchResults).toEqual([])
    })
  })
})