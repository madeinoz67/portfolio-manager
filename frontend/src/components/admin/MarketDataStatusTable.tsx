import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { MarketDataProvider } from '@/types/admin'
import { toggleMarketDataProvider } from '@/services/admin'

interface MarketDataStatusTableProps {
  providers: MarketDataProvider[]
  loading?: boolean
  className?: string
  onToggle?: (providerId: string, isEnabled: boolean) => void
}

export function MarketDataStatusTable({
  providers,
  loading = false,
  className = '',
  onToggle
}: MarketDataStatusTableProps) {
  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 ${className}`}>
        <div className="animate-pulse p-6">
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="h-10 w-10 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/3"></div>
                  <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/4"></div>
                </div>
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-16"></div>
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-20"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (providers.length === 0) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-12 text-center ${className}`}>
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">No providers configured</h3>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          No market data providers have been configured yet.
        </p>
      </div>
    )
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Provider
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Monthly Usage
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Last Update
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Cost
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {providers.map((provider) => (
              <ProviderRow key={provider.providerId} provider={provider} onToggle={onToggle} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

interface ProviderRowProps {
  provider: MarketDataProvider
  onToggle?: (providerId: string, isEnabled: boolean) => void
}

function ProviderRow({ provider, onToggle }: ProviderRowProps) {
  const [isToggling, setIsToggling] = useState(false)
  const router = useRouter()

  const handleToggle = async () => {
    if (!onToggle || isToggling) return

    setIsToggling(true)
    try {
      await onToggle(provider.providerId, !provider.isEnabled)
    } finally {
      setIsToggling(false)
    }
  }

  const handleProviderClick = () => {
    router.push(`/admin/market-data/providers/${provider.providerId}`)
  }

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'active':
        return {
          color: 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300',
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        }
      case 'disabled':
        return {
          color: 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300',
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
            </svg>
          )
        }
      case 'error':
        return {
          color: 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300',
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        }
      case 'rate_limited':
        return {
          color: 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300',
          icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          )
        }
      default:
        return {
          color: 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-300',
          icon: null
        }
    }
  }

  const statusConfig = getStatusConfig(provider.status)
  const usagePercentage = provider.monthlyLimit > 0 ? (provider.monthlyUsage / provider.monthlyLimit) * 100 : 0

  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-700">
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <div className="flex-shrink-0 h-10 w-10">
            <div className="h-10 w-10 rounded-lg bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <button
              onClick={handleProviderClick}
              className="text-left"
            >
              <div className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:underline">
                {provider.providerName}
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {provider.providerId}
              </div>
            </button>
          </div>
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex flex-col space-y-1">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig.color}`}>
            {statusConfig.icon && <span className="mr-1">{statusConfig.icon}</span>}
            {provider.status.replace('_', ' ')}
          </span>
          {!provider.isEnabled && (
            <div className="text-xs text-gray-500 dark:text-gray-400">Disabled</div>
          )}
          {provider.supportsBulkFetch && provider.isEnabled && (
            <div className="flex items-center space-x-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Bulk Enabled
              </span>
              {provider.bulkFetchLimit && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  ({provider.bulkFetchLimit} max)
                </span>
              )}
            </div>
          )}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900 dark:text-white">
          {provider.monthlyUsage.toLocaleString()} / {provider.monthlyLimit.toLocaleString()}
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              usagePercentage >= 90
                ? 'bg-red-500'
                : usagePercentage >= 75
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(usagePercentage, 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          {usagePercentage.toFixed(1)}% used
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="text-sm text-gray-900 dark:text-white">
          {new Date(provider.lastUpdate).toLocaleString()}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Calls today: {provider.apiCallsToday}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
        <div className="font-medium">
          ${provider.costPerCall.toFixed(4)}/call
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Monthly: ${(provider.monthlyUsage * provider.costPerCall).toFixed(2)}
        </div>
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center">
          <button
            onClick={handleToggle}
            disabled={isToggling}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
              provider.isEnabled
                ? 'bg-green-600 hover:bg-green-700'
                : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
            } ${isToggling ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <span className="sr-only">
              {provider.isEnabled ? 'Disable' : 'Enable'} {provider.providerName}
            </span>
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                provider.isEnabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
          <span className="ml-3 text-sm font-medium text-gray-900 dark:text-white">
            {provider.isEnabled ? 'Enabled' : 'Disabled'}
          </span>
          {isToggling && (
            <div className="ml-2">
              <svg className="w-4 h-4 animate-spin text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </div>
          )}
        </div>
      </td>
    </tr>
  )
}

export default MarketDataStatusTable