'use client'

import React, { useState, useEffect } from 'react'
import Navigation from '@/components/layout/Navigation'
import Button from '@/components/ui/Button'
import { formatDisplayDateTime } from '@/utils/timezone'
import { StreamingPriceDisplay } from '@/components/MarketData/StreamingPriceDisplay'
import { MarketDataViewToggle, ViewMode } from '@/components/MarketData/MarketDataViewToggle'
import { MarketDataTableView } from '@/components/MarketData/MarketDataTableView'
import { PriceResponse } from '@/types/marketData'

// Use the comprehensive PriceResponse type instead of basic PriceData
type PriceData = PriceResponse

export default function MarketDataPage() {
  const [symbols, setSymbols] = useState<string[]>([])
  const [newSymbol, setNewSymbol] = useState('')
  const [priceData, setPriceData] = useState<Record<string, PriceData>>({})
  const [loading, setLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('tiles')

  // Helper function to validate cached price data
  const validateCachedPriceData = (priceData: Record<string, PriceData>): boolean => {
    try {
      for (const [symbol, data] of Object.entries(priceData)) {
        if (data.fetched_at) {
          const testDate = new Date(data.fetched_at);
          if (isNaN(testDate.getTime())) {
            console.warn(`Invalid cached date for ${symbol}:`, data.fetched_at);
            return false;
          }
        }
      }
      return true;
    } catch (error) {
      console.warn('Error validating cached price data:', error);
      return false;
    }
  };

  // Load persisted data on mount
  useEffect(() => {
    const savedSymbols = localStorage.getItem('market_data_symbols')
    const savedPriceData = localStorage.getItem('market_data_prices')
    const savedLastUpdated = localStorage.getItem('market_data_last_updated')
    const savedViewMode = localStorage.getItem('market_data_view_mode')

    if (savedViewMode && (savedViewMode === 'tiles' || savedViewMode === 'table')) {
      setViewMode(savedViewMode as ViewMode)
    }

    if (savedSymbols) {
      const parsedSymbols = JSON.parse(savedSymbols)
      setSymbols(parsedSymbols)
    } else {
      // Default symbols if none saved
      const defaultSymbols = ['CBA', 'BHP', 'WBC', 'CSL']
      setSymbols(defaultSymbols)
      localStorage.setItem('market_data_symbols', JSON.stringify(defaultSymbols))
    }

    if (savedPriceData) {
      try {
        const parsedPriceData = JSON.parse(savedPriceData);
        // Validate cached data before using it
        if (validateCachedPriceData(parsedPriceData)) {
          setPriceData(parsedPriceData);
        } else {
          console.warn('Clearing invalid cached price data');
          localStorage.removeItem('market_data_prices');
          localStorage.removeItem('market_data_last_updated');
        }
      } catch (error) {
        console.warn('Error parsing cached price data, clearing cache:', error);
        localStorage.removeItem('market_data_prices');
        localStorage.removeItem('market_data_last_updated');
      }
    }

    if (savedLastUpdated) {
      try {
        const lastUpdatedDate = new Date(savedLastUpdated);
        if (!isNaN(lastUpdatedDate.getTime())) {
          setLastUpdated(lastUpdatedDate);
        }
      } catch (error) {
        console.warn('Invalid last updated date in cache:', error);
        localStorage.removeItem('market_data_last_updated');
      }
    }
  }, [])

  const fetchPrices = async (symbolsToFetch: string[]) => {
    if (symbolsToFetch.length === 0) return

    setLoading(true)
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) throw new Error('No auth token')

      const params = new URLSearchParams()
      symbolsToFetch.forEach(symbol => params.append('symbols', symbol))

      const response = await fetch(`http://localhost:8001/api/v1/market-data/prices?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) throw new Error('Failed to fetch prices')

      const data = await response.json()
      const newPriceData = { ...priceData, ...data.prices }
      setPriceData(newPriceData)
      const now = new Date()
      setLastUpdated(now)

      // Persist to localStorage
      localStorage.setItem('market_data_prices', JSON.stringify(newPriceData))
      localStorage.setItem('market_data_last_updated', now.toISOString())
    } catch (error) {
      console.error('Error fetching prices:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddSymbol = () => {
    if (newSymbol.trim() && !symbols.includes(newSymbol.trim())) {
      const newSymbolUpper = newSymbol.trim().toUpperCase()
      const newSymbols = [...symbols, newSymbolUpper]
      setSymbols(newSymbols)
      setNewSymbol('')

      // Persist symbols to localStorage
      localStorage.setItem('market_data_symbols', JSON.stringify(newSymbols))

      // Fetch price for the new symbol
      fetchPrices([newSymbolUpper])
    }
  }

  const handleRemoveSymbol = (symbol: string) => {
    const newSymbols = symbols.filter(s => s !== symbol)
    setSymbols(newSymbols)

    // Remove price data for the removed symbol
    const newPriceData = { ...priceData }
    delete newPriceData[symbol]
    setPriceData(newPriceData)

    // Persist changes to localStorage
    localStorage.setItem('market_data_symbols', JSON.stringify(newSymbols))
    localStorage.setItem('market_data_prices', JSON.stringify(newPriceData))
  }

  const handleRefresh = () => {
    fetchPrices(symbols)
  }

  const handleViewModeChange = (newViewMode: ViewMode) => {
    setViewMode(newViewMode)
    localStorage.setItem('market_data_view_mode', newViewMode)
  }

  // Fetch prices when symbols are loaded
  useEffect(() => {
    if (symbols.length > 0) {
      fetchPrices(symbols)
    }
  }, [symbols.length]) // Trigger when symbols are first loaded

  // Auto-refresh every 15 minutes
  useEffect(() => {
    const interval = setInterval(() => {
      fetchPrices(symbols)
    }, 15 * 60 * 1000) // 15 minutes

    return () => clearInterval(interval)
  }, [symbols])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 mb-8 shadow-sm border dark:border-gray-700">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Market Data
          </h1>
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-gray-600 dark:text-gray-400">
                ASX stock prices via Yahoo Finance
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Prices auto-update every 15 minutes • Data may be delayed
              </p>
              {lastUpdated && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Last updated: {formatDisplayDateTime(lastUpdated.toISOString())}
                </p>
              )}
            </div>
            <div className="flex items-center gap-4">
              <MarketDataViewToggle
                currentView={viewMode}
                onViewChange={handleViewModeChange}
              />
              <Button
                onClick={handleRefresh}
                disabled={loading}
                variant="outline"
                size="sm"
              >
                {loading ? 'Refreshing...' : 'Refresh Prices'}
              </Button>
            </div>
          </div>

          <div className="flex items-center gap-4 mb-6">
            <input
              type="text"
              placeholder="Add symbol (e.g., ANZ)"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleAddSymbol()
                }
              }}
              className="block w-full max-w-xs px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <Button onClick={handleAddSymbol} disabled={!newSymbol.trim()}>
              Add Symbol
            </Button>
          </div>

          <div className="flex flex-wrap gap-2 mb-8">
            {symbols.map(symbol => (
              <button
                key={symbol}
                onClick={() => handleRemoveSymbol(symbol)}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                {symbol}
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            ))}
          </div>

          {viewMode === 'tiles' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {symbols.map(symbol => {
                const priceInfo = priceData[symbol]
                const isLoading = loading && !priceInfo

                return (
                  <div
                    key={symbol}
                    className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border dark:border-gray-700"
                  >
                    {isLoading ? (
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div className="text-xl font-bold text-gray-900 dark:text-white">{symbol}</div>
                          <div className="bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 text-xs px-2 py-1 rounded-full">
                            Loading...
                          </div>
                        </div>
                        <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-9 w-24 rounded"></div>
                        <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-4 w-32 rounded"></div>
                      </div>
                    ) : priceInfo ? (
                      <StreamingPriceDisplay
                        price={priceInfo}
                        showVolume={true}
                        showMarketCap={true}
                        showUpdateTime={true}
                        compact={false}
                      />
                    ) : (
                      <div className="text-center py-8">
                        <div className="text-xl font-bold text-gray-900 dark:text-white mb-2">{symbol}</div>
                        <span className="text-gray-500">No price data available</span>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border dark:border-gray-700">
              <MarketDataTableView
                symbols={symbols}
                priceData={priceData}
                onRemoveSymbol={handleRemoveSymbol}
                loading={loading}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  )
}