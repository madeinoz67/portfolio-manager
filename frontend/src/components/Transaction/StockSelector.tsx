'use client'

import { useState, useEffect, useMemo } from 'react'
import { useStocks, type Stock } from '@/hooks/useStocks'
import { useStockSearch } from '@/hooks/useStockSearch'

interface StockSelectorProps {
  selectedSymbol: string
  onSelectStock: (symbol: string, stock: Stock | null) => void
  error?: string
}

export default function StockSelector({ selectedSymbol, onSelectStock, error }: StockSelectorProps) {
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [validatingStock, setValidatingStock] = useState(false)
  const { stocks, loading: stocksLoading, searchStocks } = useStocks()
  const { searchResults, loading: searchLoading, search } = useStockSearch()

  // Load all stocks on mount
  useEffect(() => {
    searchStocks()
  }, [searchStocks])

  // Sync query state with selectedSymbol prop (for editing existing transactions)
  useEffect(() => {
    if (selectedSymbol && !query) {
      setQuery(selectedSymbol)
    }
  }, [selectedSymbol, query])

  // Combine local stocks and search results, prioritizing exact matches
  const filteredStocks = useMemo(() => {
    if (!query.trim()) return stocks.slice(0, 10) // Show first 10 by default

    const searchTerm = query.toLowerCase()

    // Filter existing stocks
    const localMatches = stocks.filter(stock =>
      stock.symbol.toLowerCase().includes(searchTerm) ||
      stock.company_name.toLowerCase().includes(searchTerm)
    )

    // Add search results that aren't already in local stocks
    const searchMatches = searchResults.filter(searchStock =>
      !stocks.some(localStock => localStock.symbol === searchStock.symbol)
    )

    // Combine and prioritize exact symbol matches
    const allMatches = [...localMatches, ...searchMatches]
    const exactMatch = allMatches.find(stock =>
      stock.symbol.toLowerCase() === searchTerm
    )

    if (exactMatch) {
      return [exactMatch, ...allMatches.filter(s => s.symbol !== exactMatch.symbol)].slice(0, 10)
    }

    return allMatches.slice(0, 10)
  }, [stocks, searchResults, query])

  const handleInputChange = (value: string) => {
    setQuery(value)
    setIsOpen(true)

    // Clear previous validation state
    setValidatingStock(false)

    if (value.trim().length >= 2) {
      // Search for stocks including potential new ones
      search(value.trim())
    }

    // Check for exact match in current stocks
    const exactMatch = stocks.find(stock =>
      stock.symbol.toUpperCase() === value.toUpperCase()
    )

    // If we have an exact match, use it
    if (exactMatch) {
      onSelectStock(value, exactMatch)
      return
    }

    // Check if this looks like a stock symbol (2-5 letters, alphanumeric)
    const isStockSymbol = /^[A-Za-z]{2,5}$/.test(value.trim())

    if (isStockSymbol) {
      // Allow the input but mark as potentially valid pending search
      onSelectStock(value, null)
    } else {
      // Invalid format
      onSelectStock(value, null)
    }
  }

  const handleSelectStock = (stock: Stock) => {
    setQuery(stock.symbol)
    setIsOpen(false)
    onSelectStock(stock.symbol, stock)
  }

  // Find selected stock from both local stocks and search results
  const selectedStock = useMemo(() => {
    const allStocks = [...stocks, ...searchResults]
    return allStocks.find(stock =>
      stock.symbol.toUpperCase() === selectedSymbol.toUpperCase()
    )
  }, [stocks, searchResults, selectedSymbol])

  // Check if we have a search result for the current query
  const hasSearchResult = searchResults.some(stock =>
    stock.symbol.toUpperCase() === query.toUpperCase()
  )

  return (
    <div className="relative">
      <label htmlFor="stock-selector" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        Stock Symbol *
      </label>

      <div className="relative">
        <input
          id="stock-selector"
          type="text"
          value={query || selectedSymbol}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)} // Delay to allow click
          placeholder="Search by symbol or company name (e.g., AAPL)"
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 ${
            error
              ? 'border-red-300 dark:border-red-600'
              : 'border-gray-300 dark:border-gray-600'
          }`}
        />

        {(stocksLoading || searchLoading || validatingStock) && (
          <div className="absolute right-3 top-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          </div>
        )}

        {/* Show validation status for new symbols */}
        {query && !selectedStock && hasSearchResult && (
          <div className="absolute right-10 top-2 text-green-600 dark:text-green-400">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>

      {/* Show message when no matches found but query looks like valid symbol */}
      {isOpen && query.length >= 2 && filteredStocks.length === 0 && !searchLoading && (
        <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg p-3">
          {/^[A-Za-z]{2,5}$/.test(query.trim()) ? (
            <div className="text-sm text-blue-600 dark:text-blue-400">
              <div className="font-medium">Looking for "{query.toUpperCase()}"?</div>
              <div>Type a valid ASX stock code and it will be validated automatically</div>
            </div>
          ) : (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              No stocks found. Try entering a valid ASX stock code (2-5 letters).
            </div>
          )}
        </div>
      )}

      {/* Dropdown */}
      {isOpen && filteredStocks.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
          {filteredStocks.map((stock) => {
            const isNewStock = !stocks.some(localStock => localStock.symbol === stock.symbol)
            return (
              <button
                key={stock.id}
                type="button"
                onClick={() => handleSelectStock(stock)}
                className={`w-full px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-700 ${
                  isNewStock ? 'border-l-4 border-l-green-500' : ''
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900 dark:text-white flex items-center">
                      {stock.symbol}
                      {isNewStock && (
                        <span className="ml-2 text-xs bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100 px-2 py-1 rounded-full">
                          New
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                      {stock.company_name}
                    </div>
                  </div>
                  {stock.current_price && (
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      ${parseFloat(stock.current_price).toFixed(2)}
                    </div>
                  )}
                </div>
              </button>
            )
          })}
        </div>
      )}

      {/* Selected stock info */}
      {selectedStock && (
        <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900 dark:text-white">
                {selectedStock.symbol} - {selectedStock.company_name}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {selectedStock.exchange}
              </div>
            </div>
            {selectedStock.current_price && (
              <div className="text-lg font-semibold text-gray-900 dark:text-white">
                ${parseFloat(selectedStock.current_price).toFixed(2)}
              </div>
            )}
          </div>
        </div>
      )}

      {error && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  )
}