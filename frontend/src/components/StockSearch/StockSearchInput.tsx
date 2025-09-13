'use client'

import { useState, useRef, useEffect } from 'react'
import { useStockSearch } from '@/hooks/useStockSearch'
import { StockSearchResult } from '@/types/stock'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

interface StockSearchInputProps {
  onSelectStock: (stock: StockSearchResult) => void
  placeholder?: string
  value?: string
  disabled?: boolean
  className?: string
}

export default function StockSearchInput({
  onSelectStock,
  placeholder = "Search for stocks...",
  value = "",
  disabled = false,
  className = ""
}: StockSearchInputProps) {
  const [query, setQuery] = useState(value)
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  const {
    searchResults,
    suggestions,
    loading,
    error,
    recentSearches,
    search,
    getSuggestions,
    addToRecentSearches
  } = useStockSearch({
    debounceDelay: 300,
    suggestionsDebounceDelay: 150,
    minQueryLength: 2
  })

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value
    setQuery(newQuery)
    setSelectedIndex(-1)
    
    if (newQuery.length >= 2) {
      search(newQuery)
      getSuggestions(newQuery)
      setShowDropdown(true)
    } else {
      setShowDropdown(false)
    }
  }

  // Handle stock selection
  const handleSelectStock = (stock: StockSearchResult) => {
    setQuery(`${stock.symbol} - ${stock.company_name}`)
    setShowDropdown(false)
    addToRecentSearches(stock)
    onSelectStock(stock)
  }

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown) return

    const items = searchResults.length > 0 ? searchResults : recentSearches

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => (prev < items.length - 1 ? prev + 1 : prev))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => (prev > 0 ? prev - 1 : prev))
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && items[selectedIndex]) {
          handleSelectStock(items[selectedIndex])
        }
        break
      case 'Escape':
        setShowDropdown(false)
        setSelectedIndex(-1)
        break
    }
  }

  // Handle focus
  const handleFocus = () => {
    if (query.length >= 2 || recentSearches.length > 0) {
      setShowDropdown(true)
    }
  }

  // Handle blur
  const handleBlur = (e: React.FocusEvent) => {
    // Delay hiding dropdown to allow for clicks
    setTimeout(() => {
      if (!dropdownRef.current?.contains(e.relatedTarget as Node)) {
        setShowDropdown(false)
        setSelectedIndex(-1)
      }
    }, 100)
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        inputRef.current &&
        !inputRef.current.contains(event.target as Node) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false)
        setSelectedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Format price display
  const formatPrice = (price?: string) => {
    if (!price) return ''
    return `$${parseFloat(price).toFixed(2)}`
  }

  // Format market cap display
  const formatMarketCap = (marketCap?: string) => {
    if (!marketCap) return ''
    const value = parseFloat(marketCap)
    if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`
    return `$${value.toLocaleString()}`
  }

  const displayResults = searchResults.length > 0 ? searchResults : recentSearches
  const showRecentSearches = query.length < 2 && recentSearches.length > 0

  return (
    <div className={`relative ${className}`}>
      {/* Input Field */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={`
            w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent
            dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
            ${error ? 'border-red-500' : ''}
          `}
        />
        
        {/* Loading Spinner */}
        {loading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <LoadingSpinner size="sm" />
          </div>
        )}
        
        {/* Search Icon */}
        {!loading && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}

      {/* Dropdown */}
      {showDropdown && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto dark:bg-gray-800 dark:border-gray-600"
        >
          {/* Recent Searches Header */}
          {showRecentSearches && (
            <div className="px-4 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
              Recent Searches
            </div>
          )}

          {/* Search Results Header */}
          {searchResults.length > 0 && (
            <div className="px-4 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
              Search Results ({searchResults.length})
            </div>
          )}

          {/* Results List */}
          {displayResults.length > 0 ? (
            displayResults.map((stock, index) => (
              <button
                key={stock.symbol}
                onClick={() => handleSelectStock(stock)}
                className={`
                  w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-700
                  ${index === selectedIndex ? 'bg-blue-50 dark:bg-blue-900' : ''}
                  ${index === displayResults.length - 1 ? '' : 'border-b border-gray-100 dark:border-gray-700'}
                `}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-gray-900 dark:text-white">
                        {stock.symbol}
                      </span>
                      {stock.current_price && (
                        <span className="text-green-600 dark:text-green-400 font-medium">
                          {formatPrice(stock.current_price)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                      {stock.company_name}
                    </p>
                    {stock.sector && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        {stock.sector}
                        {stock.market_cap && ` • ${formatMarketCap(stock.market_cap)}`}
                      </p>
                    )}
                  </div>
                </div>
              </button>
            ))
          ) : query.length >= 2 && !loading ? (
            <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
              No stocks found for "{query}"
            </div>
          ) : !showRecentSearches ? (
            <div className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
              Start typing to search for stocks...
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}