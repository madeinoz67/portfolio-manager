'use client'

import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { usePortfolios } from '@/hooks/usePortfolios'
import Navigation from '@/components/layout/Navigation'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import StatsCard, { StatsGrid } from '@/components/dashboard/StatsCard'
import PerformanceChart from '@/components/analytics/PerformanceChart'
import AssetAllocationChart from '@/components/analytics/AssetAllocationChart'
import PortfolioComparison from '@/components/analytics/PortfolioComparison'
import TimeRangeSelector from '@/components/analytics/TimeRangeSelector'

export default function Analytics() {
  const searchParams = useSearchParams()
  const portfolioId = searchParams?.get('portfolioId')
  const { portfolios, loading, error } = usePortfolios()
  const [selectedTimeRange, setSelectedTimeRange] = useState('1M')
  
  // Filter portfolios based on portfolioId query parameter
  const filteredPortfolios = useMemo(() => {
    if (portfolioId) {
      return portfolios.filter(p => p.id === portfolioId)
    }
    return portfolios
  }, [portfolios, portfolioId])
  
  // Get the specific portfolio for title if analyzing single portfolio
  const selectedPortfolio = useMemo(() => {
    if (portfolioId && filteredPortfolios.length > 0) {
      return filteredPortfolios[0]
    }
    return null
  }, [portfolioId, filteredPortfolios])

  // Calculate analytics metrics based on filtered portfolios
  const analytics = useMemo(() => {
    const activePortfolios = filteredPortfolios
    const totalValue = activePortfolios.reduce((sum, p) => sum + parseFloat(p.total_value || '0'), 0)
    const totalChange = activePortfolios.reduce((sum, p) => sum + parseFloat(p.daily_change || '0'), 0)
    const totalChangePercent = totalValue > 0 ? (totalChange / (totalValue - totalChange)) * 100 : 0
    
    // Calculate best and worst performing portfolios (only relevant for multi-portfolio view)
    const bestPerformer = activePortfolios.reduce((best, current) => {
      const currentChange = parseFloat(current.daily_change_percent || '0')
      const bestChange = parseFloat(best.daily_change_percent || '0')
      return currentChange > bestChange ? current : best
    }, activePortfolios[0] || {})
    
    const worstPerformer = activePortfolios.reduce((worst, current) => {
      const currentChange = parseFloat(current.daily_change_percent || '0')
      const worstChange = parseFloat(worst.daily_change_percent || '0')
      return currentChange < worstChange ? current : worst
    }, activePortfolios[0] || {})

    return {
      totalValue: totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      totalChange: Math.abs(totalChange).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      totalChangePercent: Math.abs(totalChangePercent).toFixed(2),
      isPositive: totalChange >= 0,
      bestPerformer,
      worstPerformer,
      portfolioCount: activePortfolios.length,
      averageReturn: activePortfolios.length > 0 ? (totalChangePercent / activePortfolios.length).toFixed(2) : '0.00'
    }
  }, [filteredPortfolios])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                {selectedPortfolio ? `${selectedPortfolio.name} Analytics` : 'Analytics Dashboard'}
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                {selectedPortfolio 
                  ? `Performance analysis for ${selectedPortfolio.name}` 
                  : 'Comprehensive analysis of your portfolio performance'
                }
              </p>
            </div>
            <TimeRangeSelector 
              selected={selectedTimeRange} 
              onSelect={setSelectedTimeRange}
            />
          </div>
        </div>

        {error && <ErrorMessage message={error} className="mb-6" />}

        {/* Key Metrics */}
        <StatsGrid>
          <StatsCard
            title="Total Portfolio Value"
            value={`$${analytics.totalValue}`}
            change={`${analytics.totalChangePercent}%`}
            changeType={analytics.isPositive ? 'positive' : 'negative'}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            }
            description="Total invested capital"
          />
          
          <StatsCard
            title="Daily Change"
            value={`$${analytics.totalChange}`}
            change={`${analytics.totalChangePercent}%`}
            changeType={analytics.isPositive ? 'positive' : 'negative'}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
            description="Today's performance"
          />
          
          <StatsCard
            title={selectedPortfolio ? "Current Portfolio" : "Best Performer"}
            value={selectedPortfolio ? selectedPortfolio.name : (analytics.bestPerformer?.name || 'N/A')}
            change={`${selectedPortfolio ? selectedPortfolio.daily_change_percent : (analytics.bestPerformer?.daily_change_percent || '0')}%`}
            changeType="positive"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            description={selectedPortfolio ? "Portfolio being analyzed" : "Top performing portfolio"}
          />
          
          <StatsCard
            title="Average Return"
            value={`${analytics.averageReturn}%`}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
            description="Across all portfolios"
          />
        </StatsGrid>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Performance Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Portfolio Performance
              </h3>
              <PerformanceChart 
                portfolios={filteredPortfolios} 
                timeRange={selectedTimeRange}
              />
            </div>
          </div>

          {/* Asset Allocation */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Asset Allocation
              </h3>
              <AssetAllocationChart portfolios={filteredPortfolios} />
            </div>
          </div>
        </div>

        {/* Portfolio Comparison - only show if multiple portfolios or general view */}
        {(!selectedPortfolio || filteredPortfolios.length > 1) && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Portfolio Comparison
              </h3>
              <PortfolioComparison portfolios={filteredPortfolios} />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}