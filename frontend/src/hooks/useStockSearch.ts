import { useState, useCallback, useRef, useEffect } from 'react'
import { StockSearchResult, StockSuggestion, SearchFilters, CachedSearchResult } from '@/types/stock'
import { useAuth } from '@/contexts/AuthContext'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface UseStockSearchOptions {
  debounceDelay?: number
  suggestionsDebounceDelay?: number
  cacheTimeout?: number
  maxRecentSearches?: number
  minQueryLength?: number
}

export function useStockSearch(options: UseStockSearchOptions = {}) {
  const {
    debounceDelay = 300,
    suggestionsDebounceDelay = 150,
    cacheTimeout = 5 * 60 * 1000, // 5 minutes
    maxRecentSearches = 10,
    minQueryLength = 2
  } = options

  const [searchResults, setSearchResults] = useState<StockSearchResult[]>([])
  const [suggestions, setSuggestions] = useState<StockSuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [recentSearches, setRecentSearches] = useState<StockSearchResult[]>([])

  const { token } = useAuth()
  const debounceTimeoutRef = useRef<NodeJS.Timeout>()
  const suggestionsTimeoutRef = useRef<NodeJS.Timeout>()
  const cacheRef = useRef<Map<string, CachedSearchResult>>(new Map())

  const getAuthHeaders = () => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return headers
  }

  const buildSearchUrl = (query: string, filters?: SearchFilters) => {
    const params = new URLSearchParams({ query })
    
    if (filters?.sector) {
      params.append('sector', filters.sector)
    }
    if (filters?.exchange) {
      params.append('exchange', filters.exchange)
    }
    if (filters?.market_cap_min) {
      params.append('market_cap_min', filters.market_cap_min.toString())
    }
    if (filters?.market_cap_max) {
      params.append('market_cap_max', filters.market_cap_max.toString())
    }
    if (filters?.price_min) {
      params.append('price_min', filters.price_min.toString())
    }
    if (filters?.price_max) {
      params.append('price_max', filters.price_max.toString())
    }

    return `${API_BASE_URL}/api/v1/stocks/search?${params.toString()}`
  }

  const getCacheKey = (query: string, filters?: SearchFilters) => {
    return JSON.stringify({ query: query.toLowerCase(), filters })
  }

  const isCacheValid = (cached: CachedSearchResult) => {
    return Date.now() - cached.timestamp < cacheTimeout
  }

  const performSearch = async (query: string, filters?: SearchFilters) => {
    if (!query.trim() || query.length < minQueryLength) {
      setSearchResults([])
      return
    }

    const cacheKey = getCacheKey(query, filters)
    const cached = cacheRef.current.get(cacheKey)

    if (cached && isCacheValid(cached)) {
      setSearchResults(cached.results)
      return
    }

    try {
      setLoading(true)
      setError(null)

      const url = buildSearchUrl(query, filters)
      const response = await fetch(url, {
        headers: getAuthHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status} error`)
      }

      const results: StockSearchResult[] = await response.json()
      setSearchResults(results)

      // Cache the results
      cacheRef.current.set(cacheKey, {
        query,
        results,
        timestamp: Date.now(),
        filters
      })

    } catch (err) {
      console.error('Error searching stocks:', err)
      let errorMessage = 'Failed to search stocks. Please try again.'
      
      if (err instanceof Error) {
        // For known error types, keep the original message
        if (err.message.includes('HTTP') || err.message.includes('Server')) {
          errorMessage = err.message
        }
        // For network errors, use the generic message
      }
      
      setError(errorMessage)
      setSearchResults([])
    } finally {
      setLoading(false)
    }
  }

  const performSuggestionsSearch = async (query: string) => {
    if (!query.trim() || query.length < 1) {
      setSuggestions([])
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/stocks/suggestions?query=${encodeURIComponent(query)}`, {
        headers: getAuthHeaders(),
      })

      if (response.ok) {
        const results: StockSuggestion[] = await response.json()
        setSuggestions(results)
      }
    } catch (err) {
      console.error('Error fetching suggestions:', err)
      // Don't show errors for suggestions, just fail silently
      setSuggestions([])
    }
  }

  const search = useCallback((query: string) => {
    // Clear previous error immediately when starting new search
    setError(null)

    // Clear existing debounce timer
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    // Set up new debounced search
    debounceTimeoutRef.current = setTimeout(() => {
      performSearch(query)
    }, debounceDelay)
  }, [debounceDelay])

  const searchWithFilters = useCallback((query: string, filters: SearchFilters) => {
    setError(null)

    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    debounceTimeoutRef.current = setTimeout(() => {
      performSearch(query, filters)
    }, debounceDelay)
  }, [debounceDelay])

  const getSuggestions = useCallback((query: string) => {
    if (suggestionsTimeoutRef.current) {
      clearTimeout(suggestionsTimeoutRef.current)
    }

    suggestionsTimeoutRef.current = setTimeout(() => {
      performSuggestionsSearch(query)
    }, suggestionsDebounceDelay)
  }, [suggestionsDebounceDelay])

  const addToRecentSearches = useCallback((stock: StockSearchResult) => {
    setRecentSearches(prev => {
      // Remove if already exists
      const filtered = prev.filter(item => item.symbol !== stock.symbol)
      // Add to beginning
      const updated = [stock, ...filtered]
      // Limit to max count
      return updated.slice(0, maxRecentSearches)
    })
  }, [maxRecentSearches])

  const clearRecentSearches = useCallback(() => {
    setRecentSearches([])
  }, [])

  const clearCache = useCallback(() => {
    cacheRef.current.clear()
    setSearchResults([])
  }, [])

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
      if (suggestionsTimeoutRef.current) {
        clearTimeout(suggestionsTimeoutRef.current)
      }
    }
  }, [])

  return {
    searchResults,
    suggestions,
    loading,
    error,
    recentSearches,
    search,
    searchWithFilters,
    getSuggestions,
    addToRecentSearches,
    clearRecentSearches,
    clearCache
  }
}