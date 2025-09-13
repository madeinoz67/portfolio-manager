'use client'

/**
 * Real-time Portfolio Value Component
 *
 * Displays live portfolio valuation with real-time price updates via SSE.
 * Shows current value, change from previous day, and per-holding breakdown.
 */

import React, { useMemo } from 'react'
import { usePortfolioMarketData } from '@/contexts/MarketDataContext'
import { ConnectionStatus } from '@/components/MarketData/ConnectionStatus'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Clock,
  AlertTriangle
} from 'lucide-react'

interface Holding {
  id: string
  symbol: string
  quantity: number
  cost_basis: number
  purchase_date: string
}

interface Portfolio {
  id: string
  name: string
  description?: string
  holdings: Holding[]
}

interface RealtimeValueProps {
  portfolio: Portfolio
  showBreakdown?: boolean
  showConnectionStatus?: boolean
  className?: string
}

interface HoldingValue {
  holding: Holding
  currentPrice: number | null
  marketValue: number
  totalCost: number
  unrealizedGain: number
  unrealizedGainPercent: number
  priceChange24h?: number
  priceChangePercent24h?: number
  isStale: boolean
}

export function RealtimeValue({
  portfolio,
  showBreakdown = true,
  showConnectionStatus = true,
  className = ''
}: RealtimeValueProps) {
  // Get real-time market data for all symbols in the portfolio
  const symbols = useMemo(() =>
    portfolio.holdings.map(h => h.symbol.toUpperCase()),
    [portfolio.holdings]
  )

  const {
    portfolioPrices,
    portfolioMetrics,
    connectionStatus,
    isConnected,
    hasError,
    getPrice,
    getFormattedPrice,
    isPriceStale,
    lastUpdate
  } = usePortfolioMarketData(portfolio.id, symbols)

  // Calculate holding-level values
  const holdingValues = useMemo((): HoldingValue[] => {
    return portfolio.holdings.map(holding => {
      const priceData = getPrice(holding.symbol)
      const currentPrice = priceData?.price || null
      const marketValue = currentPrice ? currentPrice * holding.quantity : 0
      const totalCost = holding.cost_basis * holding.quantity
      const unrealizedGain = marketValue - totalCost
      const unrealizedGainPercent = totalCost > 0 ? (unrealizedGain / totalCost) * 100 : 0

      return {
        holding,
        currentPrice,
        marketValue,
        totalCost,
        unrealizedGain,
        unrealizedGainPercent,
        isStale: isPriceStale(holding.symbol, 30)
      }
    })
  }, [portfolio.holdings, getPrice, isPriceStale])

  // Calculate portfolio totals
  const portfolioTotals = useMemo(() => {
    const totalMarketValue = holdingValues.reduce((sum, hv) => sum + hv.marketValue, 0)
    const totalCost = holdingValues.reduce((sum, hv) => sum + hv.totalCost, 0)
    const totalUnrealizedGain = totalMarketValue - totalCost
    const totalUnrealizedGainPercent = totalCost > 0 ? (totalUnrealizedGain / totalCost) * 100 : 0
    const holdingsWithPrices = holdingValues.filter(hv => hv.currentPrice !== null).length
    const holdingsWithStaleData = holdingValues.filter(hv => hv.isStale).length

    return {
      totalMarketValue,
      totalCost,
      totalUnrealizedGain,
      totalUnrealizedGainPercent,
      holdingsWithPrices,
      holdingsWithStaleData,
      totalHoldings: holdingValues.length
    }
  }, [holdingValues])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  const formatPercent = (percent: number) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`
  }

  const getChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="h-4 w-4 text-green-600" />
    if (change < 0) return <TrendingDown className="h-4 w-4 text-red-600" />
    return <DollarSign className="h-4 w-4 text-gray-500" />
  }

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600'
    if (change < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  if (portfolio.holdings.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center py-8 text-gray-500">
          No holdings in this portfolio
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Portfolio Value</CardTitle>
          {showConnectionStatus && (
            <ConnectionStatus
              status={connectionStatus}
              lastUpdate={lastUpdate}
              reconnectAttempts={0}
              maxReconnectAttempts={5}
              className="text-xs"
            />
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Portfolio Totals */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <div className="text-sm text-gray-600">Current Value</div>
            <div className="text-2xl font-bold">
              {portfolioTotals.holdingsWithPrices === 0 ? (
                <Skeleton className="h-8 w-32" />
              ) : (
                formatCurrency(portfolioTotals.totalMarketValue)
              )}
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-sm text-gray-600">Total Cost</div>
            <div className="text-xl font-medium text-gray-700">
              {formatCurrency(portfolioTotals.totalCost)}
            </div>
          </div>

          <div className="space-y-2">
            <div className="text-sm text-gray-600">Unrealized P&L</div>
            <div className={`text-xl font-medium flex items-center gap-2 ${getChangeColor(portfolioTotals.totalUnrealizedGain)}`}>
              {getChangeIcon(portfolioTotals.totalUnrealizedGain)}
              <span>
                {portfolioTotals.holdingsWithPrices === 0 ? (
                  <Skeleton className="h-6 w-24" />
                ) : (
                  <>
                    {formatCurrency(portfolioTotals.totalUnrealizedGain)}
                    <span className="text-sm ml-1">
                      ({formatPercent(portfolioTotals.totalUnrealizedGainPercent)})
                    </span>
                  </>
                )}
              </span>
            </div>
          </div>
        </div>

        {/* Data Quality Indicators */}
        <div className="flex flex-wrap gap-2 text-xs">
          <Badge variant="secondary">
            {portfolioTotals.holdingsWithPrices}/{portfolioTotals.totalHoldings} prices loaded
          </Badge>

          {portfolioTotals.holdingsWithStaleData > 0 && (
            <Badge variant="destructive" className="flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              {portfolioTotals.holdingsWithStaleData} stale price{portfolioTotals.holdingsWithStaleData !== 1 ? 's' : ''}
            </Badge>
          )}

          {isConnected && (
            <Badge variant="default" className="bg-green-600 flex items-center gap-1">
              <div className="w-2 h-2 bg-green-200 rounded-full animate-pulse"></div>
              Live Updates
            </Badge>
          )}
        </div>

        {/* Holdings Breakdown */}
        {showBreakdown && (
          <div className="space-y-4">
            <div className="text-sm font-medium text-gray-700">Holdings Breakdown</div>
            <div className="space-y-2">
              {holdingValues.map((hv) => (
                <div
                  key={hv.holding.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="font-medium flex items-center gap-2">
                        {hv.holding.symbol}
                        {hv.isStale && (
                          <Clock className="h-3 w-3 text-orange-500" title="Price data is stale" />
                        )}
                      </div>
                      <div className="text-xs text-gray-600">
                        {hv.holding.quantity.toLocaleString()} shares
                      </div>
                    </div>
                  </div>

                  <div className="text-right space-y-1">
                    <div className="font-medium">
                      {hv.currentPrice ? (
                        formatCurrency(hv.marketValue)
                      ) : (
                        <Skeleton className="h-4 w-16" />
                      )}
                    </div>
                    <div className={`text-xs ${getChangeColor(hv.unrealizedGain)}`}>
                      {hv.currentPrice ? (
                        <>
                          {formatCurrency(hv.unrealizedGain)}
                          ({formatPercent(hv.unrealizedGainPercent)})
                        </>
                      ) : (
                        <span className="text-gray-400">No price data</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error Display */}
        {hasError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-red-700">
              <AlertTriangle className="h-4 w-4" />
              Unable to load real-time price data. Showing last available prices.
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}