'use client'

import { useState, useEffect, useMemo } from 'react'
import { useStocks, type Stock } from '@/hooks/useStocks'

interface StockSelectorProps {
  selectedSymbol: string
  onSelectStock: (symbol: string, stock: Stock | null) => void
  error?: string
}

export default function StockSelector({ selectedSymbol, onSelectStock, error }: StockSelectorProps) {
  const [query, setQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const { stocks, loading, searchStocks } = useStocks()

  // Load all stocks on mount
  useEffect(() => {
    searchStocks()
  }, [searchStocks])

  // Filter stocks based on query
  const filteredStocks = useMemo(() => {
    if (!query.trim()) return stocks.slice(0, 10) // Show first 10 by default
    
    const searchTerm = query.toLowerCase()
    return stocks.filter(stock => 
      stock.symbol.toLowerCase().includes(searchTerm) ||
      stock.company_name.toLowerCase().includes(searchTerm)
    ).slice(0, 10)
  }, [stocks, query])

  const handleInputChange = (value: string) => {
    setQuery(value)
    setIsOpen(true)
    
    // Find exact match for validation
    const exactMatch = stocks.find(stock => 
      stock.symbol.toUpperCase() === value.toUpperCase()
    )
    
    onSelectStock(value, exactMatch || null)
  }

  const handleSelectStock = (stock: Stock) => {
    setQuery(stock.symbol)
    setIsOpen(false)
    onSelectStock(stock.symbol, stock)
  }

  const selectedStock = stocks.find(stock => 
    stock.symbol.toUpperCase() === selectedSymbol.toUpperCase()
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
        
        {loading && (
          <div className="absolute right-3 top-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && filteredStocks.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
          {filteredStocks.map((stock) => (
            <button
              key={stock.id}
              type="button"
              onClick={() => handleSelectStock(stock)}
              className="w-full px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-700"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {stock.symbol}
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
          ))}
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