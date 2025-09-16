import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { Portfolio } from '@/types/portfolio'
import Button from '@/components/ui/Button'
import PortfolioDeletionModal from './PortfolioDeletionModal'
import { getRelativeTime, formatDisplayDateTime } from '@/utils/timezone'

interface PortfolioCardProps {
  portfolio: Portfolio
  onDeleted?: () => void
}

export default function PortfolioCard({ portfolio, onDeleted }: PortfolioCardProps) {
  const router = useRouter()
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const isPositiveChange = parseFloat(portfolio.daily_change) >= 0
  const totalValue = parseFloat(portfolio.total_value || '0')
  const dailyChange = parseFloat(portfolio.daily_change || '0')
  const dailyChangePercent = parseFloat(portfolio.daily_change_percent || '0')

  // Helper function to format portfolio timestamp properly
  const formatPortfolioTimestamp = (timestamp: string): string => {
    const relativeTime = getRelativeTime(timestamp)
    // If getRelativeTime returns an actual date (longer than 7 days),
    // use formatDisplayDateTime instead for proper timezone handling
    if (relativeTime.includes(',') || relativeTime.includes('Invalid')) {
      return formatDisplayDateTime(timestamp, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    }
    return relativeTime
  }

  const handleAddTrade = () => {
    router.push(`/portfolios/${portfolio.id}/add-transaction`)
  }

  const handleDeleteClick = () => {
    setShowDeleteModal(true)
  }

  const handleDeleteModalClose = () => {
    setShowDeleteModal(false)
  }

  const handleDeleted = () => {
    setShowDeleteModal(false)
    if (onDeleted) {
      onDeleted()
    }
  }

  return (
    <div className="group bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-lg dark:hover:shadow-2xl transition-all duration-300 border dark:border-gray-700 overflow-hidden">
      {/* Header with gradient accent */}
      <div className="h-2 bg-gradient-to-r from-blue-500 to-purple-600"></div>
      
      <div className="p-6">
        {/* Portfolio Name and Description */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
              {portfolio.name}
            </h3>
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${totalValue > 0 ? 'bg-green-500' : 'bg-gray-400'}`}></div>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {totalValue > 0 ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
          {portfolio.description && (
            <p className="text-gray-600 dark:text-gray-300 text-sm line-clamp-2">
              {portfolio.description}
            </p>
          )}
        </div>

        {/* Portfolio Metrics */}
        <div className="space-y-4 mb-6">
          {/* Total Value */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Portfolio Value</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Daily Performance */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className={`p-2 rounded-lg ${isPositiveChange ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
                  <svg className={`w-4 h-4 ${isPositiveChange ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isPositiveChange ? "M7 17l9.2-9.2M17 17V7H7" : "M17 7l-9.2 9.2M7 7v10h10"} />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Today's Change</p>
                  <div className="flex items-center space-x-2">
                    <span className={`font-bold ${isPositiveChange ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      ${Math.abs(dailyChange).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span className={`text-sm font-medium ${isPositiveChange ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      ({dailyChangePercent.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Portfolio Meta */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
          <span>Created: {new Date(portfolio.created_at).toLocaleDateString()}</span>
          <span className="flex items-center space-x-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Last updated: {portfolio.price_last_updated ? formatPortfolioTimestamp(portfolio.price_last_updated) : formatPortfolioTimestamp(portfolio.updated_at)}</span>
          </span>
        </div>

        {/* Action Buttons */}
        <div className={`flex gap-2 ${onDeleted ? 'grid grid-cols-3' : 'flex space-x-3'}`}>
          <Button
            size="sm"
            variant="primary"
            className="flex-1"
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            }
          >
            <Link href={`/portfolios/${portfolio.id}`} className="block w-full">
              View Details
            </Link>
          </Button>

          <Button
            size="sm"
            variant="outline"
            className="flex-1"
            onClick={handleAddTrade}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            }
          >
            Add Trade
          </Button>

          {onDeleted && (
            <Button
              size="sm"
              variant="ghost"
              className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-900/20"
              onClick={handleDeleteClick}
              icon={
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              }
              title="Delete Portfolio"
            >
              Delete
            </Button>
          )}
        </div>
      </div>

      {/* Delete Modal */}
      <PortfolioDeletionModal
        isOpen={showDeleteModal}
        onClose={handleDeleteModalClose}
        portfolio={portfolio}
        onDeleted={handleDeleted}
      />
    </div>
  )
}