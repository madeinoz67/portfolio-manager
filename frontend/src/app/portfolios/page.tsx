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
import Button from '@/components/ui/Button'

export default function PortfoliosPage() {
  const { portfolios, loading, error, createPortfolio, fetchPortfolios } = usePortfolios()
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'name' | 'value' | 'change' | 'created'>('name')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
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

  const handlePortfolioDeleted = () => {
    addToast('Portfolio deleted successfully', 'success')
    fetchPortfolios()
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

  // Filter and sort portfolios
  const filteredAndSortedPortfolios = useMemo(() => {
    let filtered = portfolios
    
    // Apply search filter
    if (searchQuery) {
      filtered = portfolios.filter(portfolio =>
        portfolio.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (portfolio.description && portfolio.description.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    }
    
    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      let aValue: any, bValue: any
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase()
          bValue = b.name.toLowerCase()
          break
        case 'value':
          aValue = parseFloat(a.total_value || '0')
          bValue = parseFloat(b.total_value || '0')
          break
        case 'change':
          aValue = parseFloat(a.daily_change || '0')
          bValue = parseFloat(b.daily_change || '0')
          break
        case 'created':
          aValue = new Date(a.created_at)
          bValue = new Date(b.created_at)
          break
        default:
          return 0
      }
      
      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1
      return 0
    })
    
    return sorted
  }, [portfolios, searchQuery, sortBy, sortOrder])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-gray-200 dark:bg-gray-700 rounded-2xl p-8 mb-8 animate-pulse h-32"></div>
          <PortfolioGridSkeleton />
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 mb-8 shadow-sm border dark:border-gray-700">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div className="mb-6 lg:mb-0">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Your Portfolios
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Manage and monitor your investment portfolios
              </p>
              
              {/* Quick Stats */}
              <div className="flex flex-wrap gap-6 mt-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Value:</span>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">${stats.totalValue}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Today's Change:</span>
                  <span className={`text-lg font-bold ${stats.isPositive ? 'text-green-600' : 'text-red-600'}`}>
                    {stats.isPositive ? '+' : '-'}${stats.totalChange} ({stats.totalChangePercent}%)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-500 dark:text-gray-400">Active:</span>
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    {stats.activePortfolios}/{stats.portfolioCount}
                  </span>
                </div>
              </div>
            </div>
            
            <Button
              onClick={() => setShowCreateForm(true)}
              size="lg"
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

        {/* Error message */}
        {error && <ErrorMessage message={error} className="mb-6" />}

        {/* Create Portfolio Form */}
        {showCreateForm && (
          <div className="mb-8">
            <CreatePortfolioForm
              onSubmit={handleCreatePortfolio}
              onCancel={() => setShowCreateForm(false)}
            />
          </div>
        )}

        {/* Filters and Search */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 mb-6 shadow-sm border dark:border-gray-700">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
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
            
            {/* Sort Controls */}
            <div className="flex gap-3">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="name">Name</option>
                <option value="value">Value</option>
                <option value="change">Change</option>
                <option value="created">Created</option>
              </select>
              
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {sortOrder === 'asc' ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Results Summary */}
        <div className="mb-6">
          <p className="text-gray-600 dark:text-gray-400">
            {filteredAndSortedPortfolios.length === portfolios.length
              ? `Showing all ${portfolios.length} portfolios`
              : `Showing ${filteredAndSortedPortfolios.length} of ${portfolios.length} portfolios`}
          </p>
        </div>

        {/* Portfolios Grid */}
        {filteredAndSortedPortfolios.length === 0 ? (
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
            {filteredAndSortedPortfolios.map((portfolio) => (
              <PortfolioCard
                key={portfolio.id}
                portfolio={portfolio}
                onDeleted={handlePortfolioDeleted}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}