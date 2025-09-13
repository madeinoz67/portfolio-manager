'use client'

import { useState, useMemo } from 'react'
import { usePortfolios } from '@/hooks/usePortfolios'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'
import CreatePortfolioForm from '@/components/Portfolio/CreatePortfolioForm'
import PortfolioCard from '@/components/Portfolio/PortfolioCard'
import { PortfolioGridSkeleton } from '@/components/ui/PortfolioCardSkeleton'
import { useToast } from '@/components/ui/Toast'
import Navigation from '@/components/layout/Navigation'
import HeroSection from '@/components/dashboard/HeroSection'
import StatsCard, { StatsGrid } from '@/components/dashboard/StatsCard'
import Button from '@/components/ui/Button'

export default function Home() {
  const { portfolios, loading, error, createPortfolio } = usePortfolios()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const { addToast } = useToast()

  const handleCreatePortfolio = async (portfolioData: any) => {
    const success = await createPortfolio(portfolioData)
    if (success) {
      addToast('Portfolio created successfully!', 'success')
      setShowCreateForm(false)
      return true
    } else {
      addToast('Failed to create portfolio', 'error')
      return false
    }
  }

  // Calculate portfolio statistics
  const stats = useMemo(() => {
    const totalValue = portfolios.reduce((sum, p) => sum + parseFloat(p.total_value || '0'), 0)
    const totalChange = portfolios.reduce((sum, p) => sum + parseFloat(p.daily_change || '0'), 0)
    const totalChangePercent = totalValue > 0 ? (totalChange / (totalValue - totalChange)) * 100 : 0
    
    return {
      totalValue: totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      totalChange: Math.abs(totalChange).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      totalChangePercent: Math.abs(totalChangePercent).toFixed(2),
      isPositive: totalChange >= 0,
      portfolioCount: portfolios.length,
      activePortfolios: portfolios.filter(p => parseFloat(p.total_value || '0') > 0).length
    }
  }, [portfolios])

  // Filter portfolios based on search
  const filteredPortfolios = useMemo(() => {
    if (!searchQuery) return portfolios
    return portfolios.filter(portfolio =>
      portfolio.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (portfolio.description && portfolio.description.toLowerCase().includes(searchQuery.toLowerCase()))
    )
  }, [portfolios, searchQuery])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Hero Skeleton */}
          <div className="bg-gray-200 dark:bg-gray-700 rounded-2xl p-8 mb-8 animate-pulse h-48"></div>
          
          {/* Stats Skeleton */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-gray-200 dark:bg-gray-700 rounded-xl p-6 animate-pulse h-24"></div>
            ))}
          </div>
          
          {/* Portfolio Grid Skeleton */}
          <PortfolioGridSkeleton />
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <HeroSection
          totalValue={stats.totalValue}
          totalGain={stats.totalChange}
          gainPercent={stats.totalChangePercent}
          isPositive={stats.isPositive}
        />

        {/* Error message */}
        {error && <ErrorMessage message={error} className="mb-6" />}

        {/* Statistics Cards */}
        <StatsGrid>
          <StatsCard
            title="Total Portfolios"
            value={stats.portfolioCount.toString()}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            }
            description="Active investment portfolios"
          />
          
          <StatsCard
            title="Active Holdings"
            value={stats.activePortfolios.toString()}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
            description="Portfolios with positions"
          />
          
          <StatsCard
            title="Today's Change"
            value={`$${stats.totalChange}`}
            change={`${stats.totalChangePercent}%`}
            changeType={stats.isPositive ? 'positive' : 'negative'}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            }
            description="Daily performance"
          />
          
          <StatsCard
            title="Portfolio Value"
            value={`$${stats.totalValue}`}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            }
            description="Total invested capital"
          />
        </StatsGrid>

        {/* Portfolio Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Your Portfolios</h2>
            <p className="text-gray-600 dark:text-gray-400">Manage and track your investment portfolios</p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Search */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                placeholder="Search portfolios..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <Button
              onClick={() => setShowCreateForm(true)}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              }
            >
              New Portfolio
            </Button>
          </div>
        </div>

        {/* Create Portfolio Form */}
        {showCreateForm && (
          <div className="mb-8">
            <CreatePortfolioForm
              onSubmit={handleCreatePortfolio}
              onCancel={() => setShowCreateForm(false)}
            />
          </div>
        )}

        {/* Portfolios Grid */}
        {filteredPortfolios.length === 0 ? (
          <div className="text-center py-12">
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-12 border-2 border-dashed border-gray-300 dark:border-gray-600">
              <div className="mx-auto w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-4">
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                {searchQuery ? 'No portfolios found' : 'No portfolios yet'}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {searchQuery 
                  ? `No portfolios match "${searchQuery}". Try a different search term.`
                  : 'Create your first portfolio to start tracking your investments and building wealth.'
                }
              </p>
              {!searchQuery && (
                <Button onClick={() => setShowCreateForm(true)}>
                  Create Your First Portfolio
                </Button>
              )}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredPortfolios.map((portfolio) => (
              <PortfolioCard key={portfolio.id} portfolio={portfolio} />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}