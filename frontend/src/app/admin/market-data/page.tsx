'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { MarketDataStatusTable } from '@/components/admin/MarketDataStatusTable'
import { toggleMarketDataProvider, getDashboardActivities, forcePriceUpdate, controlScheduler } from '@/services/admin'
import { DashboardActivity } from '@/types/admin'
import { formatDisplayDateTime } from '@/utils/timezone'
// import { useMarketDataStatus } from '@/hooks/useAdmin'
// import LoadingSpinner from '@/components/ui/LoadingSpinner'
// import ErrorMessage from '@/components/ui/ErrorMessage'

interface MarketDataProviderCardProps {
  name: string
  status: 'active' | 'inactive' | 'error'
  lastUpdate: string
  apiCallsToday: number
  dailyLimit: number
  errorRate?: number
  responseTime?: number
}

function MarketDataProviderCard({
  name,
  status,
  lastUpdate,
  apiCallsToday,
  dailyLimit,
  errorRate = 0,
  responseTime = 0
}: MarketDataProviderCardProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'active':
        return {
          color: 'text-green-600 dark:text-green-400',
          bgColor: 'bg-green-100 dark:bg-green-900/20',
          borderColor: 'border-green-200 dark:border-green-800',
          label: 'Active',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        }
      case 'inactive':
        return {
          color: 'text-gray-600 dark:text-gray-400',
          bgColor: 'bg-gray-100 dark:bg-gray-900/20',
          borderColor: 'border-gray-200 dark:border-gray-700',
          label: 'Inactive',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 4h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13m-5-8v2m0 6h.01" />
            </svg>
          )
        }
      case 'error':
        return {
          color: 'text-red-600 dark:text-red-400',
          bgColor: 'bg-red-100 dark:bg-red-900/20',
          borderColor: 'border-red-200 dark:border-red-800',
          label: 'Error',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        }
      default:
        return {
          color: 'text-gray-600 dark:text-gray-400',
          bgColor: 'bg-gray-100 dark:bg-gray-900/20',
          borderColor: 'border-gray-200 dark:border-gray-700',
          label: 'Unknown',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        }
    }
  }

  const statusConfig = getStatusConfig()
  const usagePercentage = (apiCallsToday / dailyLimit) * 100
  const formattedTime = formatDisplayDateTime(lastUpdate)

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border ${statusConfig.borderColor} p-6`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 ${statusConfig.bgColor} ${statusConfig.color} rounded-lg`}>
            {statusConfig.icon}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{name}</h3>
            <div className={`text-sm font-medium ${statusConfig.color}`}>
              {statusConfig.label}
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500 dark:text-gray-400">Last Update</div>
          <div className="text-sm font-medium text-gray-900 dark:text-white">{formattedTime}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-lg font-bold text-gray-900 dark:text-white">{apiCallsToday.toLocaleString()}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">API Calls Today</div>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-lg font-bold text-gray-900 dark:text-white">{dailyLimit.toLocaleString()}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Daily Limit</div>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className={`text-lg font-bold ${
            errorRate > 5
              ? 'text-red-600 dark:text-red-400'
              : errorRate > 1
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-green-600 dark:text-green-400'
          }`}>
            {errorRate.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Error Rate</div>
        </div>
        <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="text-lg font-bold text-gray-900 dark:text-white">{responseTime}ms</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Avg Response</div>
        </div>
      </div>

      {/* Usage Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">API Usage</span>
          <span className={`font-medium ${
            usagePercentage > 90
              ? 'text-red-600 dark:text-red-400'
              : usagePercentage > 75
                ? 'text-yellow-600 dark:text-yellow-400'
                : 'text-green-600 dark:text-green-400'
          }`}>
            {usagePercentage.toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              usagePercentage > 90
                ? 'bg-red-500'
                : usagePercentage > 75
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(usagePercentage, 100)}%` }}
          />
        </div>
      </div>
    </div>
  )
}

interface MarketDataStatsCardProps {
  title: string
  value: string | number
  subtitle?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  icon: React.ReactNode
}

function MarketDataStatsCard({ title, value, subtitle, trend, trendValue, icon }: MarketDataStatsCardProps) {
  const getTrendColor = () => {
    if (!trend) return ''
    switch (trend) {
      case 'up': return 'text-green-600 dark:text-green-400'
      case 'down': return 'text-red-600 dark:text-red-400'
      default: return 'text-gray-600 dark:text-gray-400'
    }
  }

  const getTrendIcon = () => {
    if (!trend || trend === 'neutral') return null
    return (
      <svg
        className={`w-4 h-4 ${getTrendColor()}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        {trend === 'up' ? (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l6-6 6 6" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-6 6-6-6" />
        )}
      </svg>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-red-100 dark:bg-red-900/20 rounded-lg">
            {icon}
          </div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">{title}</h3>
        </div>
        {trend && trendValue && (
          <div className="flex items-center space-x-1">
            {getTrendIcon()}
            <span className={`text-sm font-medium ${getTrendColor()}`}>
              {trendValue}
            </span>
          </div>
        )}
      </div>

      <div>
        <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
          {value}
        </div>
        {subtitle && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {subtitle}
          </div>
        )}
      </div>
    </div>
  )
}

export default function AdminMarketDataPage() {
  const { user, token } = useAuth()
  const [marketDataStatus, setMarketDataStatus] = useState(null)
  const [apiUsageData, setApiUsageData] = useState(null)
  const [schedulerStatus, setSchedulerStatus] = useState(null)
  const [activities, setActivities] = useState<DashboardActivity[]>([])
  const [activitiesLoading, setActivitiesLoading] = useState(true)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [quickActionLoading, setQuickActionLoading] = useState(false)
  const [quickActionMessage, setQuickActionMessage] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!user || !token) return

      try {
        // Fetch provider status, API usage data, and scheduler status in parallel
        const [statusResponse, usageResponse, schedulerResponse] = await Promise.all([
          fetch('http://localhost:8001/api/v1/admin/market-data/status', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }),
          fetch('http://localhost:8001/api/v1/admin/api-usage', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          }),
          fetch('http://localhost:8001/api/v1/admin/scheduler/status', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          })
        ])

        if (statusResponse.ok && usageResponse.ok && schedulerResponse.ok) {
          const [statusData, usageData, schedulerData] = await Promise.all([
            statusResponse.json(),
            usageResponse.json(),
            schedulerResponse.json()
          ])
          setMarketDataStatus(statusData)
          setApiUsageData(usageData)
          setSchedulerStatus(schedulerData)
        } else {
          const statusError = statusResponse.ok ? null : statusResponse.status
          const usageError = usageResponse.ok ? null : usageResponse.status
          const schedulerError = schedulerResponse.ok ? null : schedulerResponse.status
          setError(`API Error: Status ${statusError}, Usage ${usageError}, Scheduler ${schedulerError}`)
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [user, token])

  // Fetch recent activities
  useEffect(() => {
    const fetchActivities = async () => {
      if (!user || !token) return

      try {
        setActivitiesLoading(true)
        const response = await getDashboardActivities({ token })
        setActivities(response.activities)
      } catch (err) {
        console.error('Failed to fetch dashboard activities:', err)
        // Keep existing activities on error
      } finally {
        setActivitiesLoading(false)
      }
    }

    fetchActivities()
  }, [user, token])

  const refetch = () => {
    setLoading(true)
    setError(null)
    // Re-trigger the useEffect by clearing and resetting the token state
    const currentToken = token
    if (currentToken) {
      const fetchData = async () => {
        try {
          const [statusResponse, usageResponse, schedulerResponse] = await Promise.all([
            fetch('http://localhost:8001/api/v1/admin/market-data/status', {
              headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json',
              },
            }),
            fetch('http://localhost:8001/api/v1/admin/api-usage', {
              headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json',
              },
            }),
            fetch('http://localhost:8001/api/v1/admin/scheduler/status', {
              headers: {
                'Authorization': `Bearer ${currentToken}`,
                'Content-Type': 'application/json',
              },
            })
          ])

          if (statusResponse.ok && usageResponse.ok && schedulerResponse.ok) {
            const [statusData, usageData, schedulerData] = await Promise.all([
              statusResponse.json(),
              usageResponse.json(),
              schedulerResponse.json()
            ])
            setMarketDataStatus(statusData)
            setApiUsageData(usageData)
            setSchedulerStatus(schedulerData)
          } else {
            const statusError = statusResponse.ok ? null : statusResponse.status
            const usageError = usageResponse.ok ? null : usageResponse.status
            const schedulerError = schedulerResponse.ok ? null : schedulerResponse.status
            setError(`API Error: Status ${statusError}, Usage ${usageError}, Scheduler ${schedulerError}`)
          }
        } catch (err) {
          setError(err.message)
        } finally {
          setLoading(false)
        }
      }
      fetchData()
    }
  }

  const handleProviderToggle = async (providerId: string, isEnabled: boolean) => {
    if (!token) return

    try {
      await toggleMarketDataProvider(providerId, { token })
      // Refresh data after successful toggle
      refetch()
    } catch (err) {
      setError(`Failed to toggle provider: ${err.message}`)
    }
  }

  const handleSchedulerControl = async (action: 'pause' | 'restart') => {
    if (!token) return

    try {
      const response = await fetch('http://localhost:8001/api/v1/admin/scheduler/control', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Failed to ${action} scheduler`)
      }

      const result = await response.json()

      if (result.success) {
        // Refresh scheduler status after successful control action
        refetch()
      } else {
        setError(result.message || `Failed to ${action} scheduler`)
      }
    } catch (err) {
      setError(`Failed to ${action} scheduler: ${err.message}`)
    }
  }

  // Quick Action Handlers
  const handleForcePriceUpdate = async () => {
    if (!token) return

    setQuickActionLoading(true)
    setQuickActionMessage(null)

    try {
      const result = await forcePriceUpdate({ token })
      setQuickActionMessage(`✅ ${result.message} - ${result.symbols_refreshed} symbols updated`)

      // Refresh data after successful update
      setTimeout(() => {
        refetch()
        setQuickActionMessage(null)
      }, 3000)
    } catch (err) {
      setQuickActionMessage(`❌ Failed to force price update: ${err.message}`)
      setTimeout(() => setQuickActionMessage(null), 5000)
    } finally {
      setQuickActionLoading(false)
    }
  }

  const handleSchedulerAction = async (action: 'pause' | 'restart') => {
    if (!token) return

    setQuickActionLoading(true)
    setQuickActionMessage(null)

    try {
      const result = await controlScheduler(action, { token })
      if (result.success) {
        setQuickActionMessage(`✅ ${result.message}`)
        // Refresh data after successful action
        setTimeout(() => {
          refetch()
          setQuickActionMessage(null)
        }, 2000)
      } else {
        setQuickActionMessage(`❌ ${result.message}`)
        setTimeout(() => setQuickActionMessage(null), 5000)
      }
    } catch (err) {
      setQuickActionMessage(`❌ Failed to ${action} scheduler: ${err.message}`)
      setTimeout(() => setQuickActionMessage(null), 5000)
    } finally {
      setQuickActionLoading(false)
    }
  }

  // Placeholder handlers for other quick actions
  const handleProviderSettings = () => {
    setQuickActionMessage("🚧 Provider Settings functionality coming soon!")
    setTimeout(() => setQuickActionMessage(null), 3000)
  }

  const handleCacheManagement = () => {
    setQuickActionMessage("🚧 Cache Management functionality coming soon!")
    setTimeout(() => setQuickActionMessage(null), 3000)
  }

  const handleViewApiLogs = () => {
    setQuickActionMessage("🚧 API Logs viewer functionality coming soon!")
    setTimeout(() => setQuickActionMessage(null), 3000)
  }

  const handleFailoverTesting = () => {
    setQuickActionMessage("🚧 Failover Testing functionality coming soon!")
    setTimeout(() => setQuickActionMessage(null), 3000)
  }

  const handleExportReports = () => {
    setQuickActionMessage("🚧 Export Reports functionality coming soon!")
    setTimeout(() => setQuickActionMessage(null), 3000)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Loading market data status...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-12 text-center">
        <div className="text-red-600">Error: {error}</div>
        <button
          onClick={refetch}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!marketDataStatus) {
    return null
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Market Data Management</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor data providers and API usage statistics
          </p>
        </div>
        <button
          onClick={refetch}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          Refresh Status
        </button>
      </div>

      {/* Market Data Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MarketDataStatsCard
          title="Total API Calls"
          value={apiUsageData?.summary?.total_requests_today?.toLocaleString() || '0'}
          subtitle="Today"
          trend={
            apiUsageData?.trends?.daily_change_percent > 0
              ? "up"
              : apiUsageData?.trends?.daily_change_percent < 0
                ? "down"
                : "neutral"
          }
          trendValue={
            apiUsageData?.trends?.daily_change_percent
              ? `${apiUsageData.trends.daily_change_percent > 0 ? '+' : ''}${apiUsageData.trends.daily_change_percent.toFixed(1)}%`
              : undefined
          }
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
          }
        />

        <MarketDataStatsCard
          title="Active Providers"
          value={marketDataStatus?.providers?.filter(p => p.status === 'active')?.length || 0}
          subtitle={`Out of ${marketDataStatus?.providers?.length || 0} configured`}
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          }
        />

        <MarketDataStatsCard
          title="Success Rate"
          value={`${(apiUsageData?.summary?.success_rate_today || 0).toFixed(2)}%`}
          subtitle="Last 24 hours"
          trend={
            (apiUsageData?.summary?.success_rate_today || 0) > 95
              ? "up"
              : (apiUsageData?.summary?.success_rate_today || 0) > 80
                ? "neutral"
                : "down"
          }
          trendValue={
            apiUsageData?.summary?.success_rate_today
              ? ((apiUsageData.summary.success_rate_today) > 95 ? '+0.2%' : (apiUsageData.summary.success_rate_today) > 80 ? '±0%' : '-2.1%')
              : undefined
          }
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        <MarketDataStatsCard
          title="Monthly Calls"
          value={apiUsageData?.summary?.total_requests_this_month?.toLocaleString() || '0'}
          subtitle="This month"
          trend={
            (apiUsageData?.trends?.weekly_change_count || 0) > 0
              ? "up"
              : (apiUsageData?.trends?.weekly_change_count || 0) < 0
                ? "down"
                : "neutral"
          }
          trendValue={
            apiUsageData?.trends?.weekly_change_count !== undefined
              ? `${apiUsageData.trends.weekly_change_count > 0 ? '+' : ''}${apiUsageData.trends.weekly_change_count}`
              : undefined
          }
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          }
        />

      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Quick Actions</h3>

        {/* Quick Action Message */}
        {quickActionMessage && (
          <div className="mb-4 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-blue-700 dark:text-blue-300">{quickActionMessage}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <button
            onClick={handleForcePriceUpdate}
            disabled={quickActionLoading}
            className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex items-center gap-2">
              <div className="font-medium text-gray-900 dark:text-white">Force Price Update</div>
              {quickActionLoading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              )}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Manually trigger price refresh</div>
          </button>

          <button
            onClick={handleProviderSettings}
            className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="font-medium text-gray-900 dark:text-white">Provider Settings</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Configure API keys and limits</div>
          </button>

          <button
            onClick={handleCacheManagement}
            className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="font-medium text-gray-900 dark:text-white">Cache Management</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Clear or refresh cached data</div>
          </button>

          <button
            onClick={handleViewApiLogs}
            className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="font-medium text-gray-900 dark:text-white">View API Logs</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Review detailed request logs</div>
          </button>

          <button
            onClick={handleFailoverTesting}
            className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="font-medium text-gray-900 dark:text-white">Failover Testing</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Test provider failover scenarios</div>
          </button>

          <button
            onClick={handleExportReports}
            className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <div className="font-medium text-gray-900 dark:text-white">Export Reports</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Generate usage and error reports</div>
          </button>
        </div>
      </div>

      {/* Market Data Providers */}
      <div className="space-y-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Data Providers</h2>

        <MarketDataStatusTable
          providers={marketDataStatus?.providers || []}
          loading={loading}
          onToggle={handleProviderToggle}
        />
      </div>

      {/* Scheduler Status */}
      {schedulerStatus && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Scheduler Status</h3>
            <div className="flex space-x-2">
              <button
                onClick={() => handleSchedulerControl('pause')}
                disabled={schedulerStatus.state !== 'running'}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  schedulerStatus.state !== 'running'
                    ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    : 'bg-yellow-600 hover:bg-yellow-700 text-white'
                }`}
              >
                Pause
              </button>
              <button
                onClick={() => handleSchedulerControl('restart')}
                disabled={schedulerStatus.state === 'running'}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  schedulerStatus.state === 'running'
                    ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    : schedulerStatus.state === 'error'
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {schedulerStatus.state === 'paused'
                  ? 'Resume'
                  : schedulerStatus.state === 'error'
                    ? 'Restart (Fix Error)'
                    : 'Start'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
            {/* Scheduler Status Card */}
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${
                  schedulerStatus.state === 'running'
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400'
                    : schedulerStatus.state === 'paused'
                      ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400'
                      : schedulerStatus.state === 'error'
                        ? 'bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400'
                        : 'bg-gray-100 dark:bg-gray-900/20 text-gray-600 dark:text-gray-400'
                }`}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {schedulerStatus.state === 'running' ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m-5-9h2a3 3 0 013 3v1M3 11v2a3 3 0 003 3h.5" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 4h4.018a2 2 0 01.485.06l3.76.94" />
                    )}
                  </svg>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                    Scheduler: {schedulerStatus.state || 'Unknown'}
                  </h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Status: {schedulerStatus.state === 'running'
                      ? 'Active'
                      : schedulerStatus.state === 'paused'
                        ? 'Paused'
                        : schedulerStatus.state === 'error'
                          ? 'Error'
                          : 'Stopped'}
                  </p>
                  {schedulerStatus.errorMessage && (
                    <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-800 rounded text-xs text-red-700 dark:text-red-400">
                      <div className="font-medium">Error:</div>
                      <div>{schedulerStatus.errorMessage}</div>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Total Runs:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {schedulerStatus.total_runs || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Successful:</span>
                  <span className="font-medium text-green-600 dark:text-green-400">
                    {schedulerStatus.successful_runs || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Failed:</span>
                  <span className="font-medium text-red-600 dark:text-red-400">
                    {schedulerStatus.failed_runs || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Restarts (1h):</span>
                  <span className={`font-medium ${
                    (schedulerStatus.restarts_last_hour || 0) > 2
                      ? 'text-red-600 dark:text-red-400'
                      : (schedulerStatus.restarts_last_hour || 0) > 0
                        ? 'text-yellow-600 dark:text-yellow-400'
                        : 'text-green-600 dark:text-green-400'
                  }`}>
                    {schedulerStatus.restarts_last_hour || 0}
                    {schedulerStatus.restart_trend === 'increasing' && (
                      <span className="ml-1 text-xs">↑</span>
                    )}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Restarts (24h):</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {schedulerStatus.restarts_last_24_hours || 0}
                  </span>
                </div>
              </div>
            </div>

            {/* Timing Information */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">Timing</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Last Run:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {schedulerStatus.lastRun
                      ? formatDisplayDateTime(schedulerStatus.lastRun)
                      : 'Never'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Next Run:</span>
                  <span className="font-medium text-blue-600 dark:text-blue-400">
                    {schedulerStatus.nextRun
                      ? formatDisplayDateTime(schedulerStatus.nextRun)
                      : 'Not scheduled'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Uptime:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {schedulerStatus.uptimeSeconds
                      ? Math.floor(schedulerStatus.uptimeSeconds / 3600) + 'h ' +
                        Math.floor((schedulerStatus.uptimeSeconds % 3600) / 60) + 'm'
                      : '0m'
                    }
                  </span>
                </div>
              </div>
            </div>

            {/* Recent Activity Stats */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">Recent Activity</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Symbols Processed:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {schedulerStatus.recent_activity?.total_symbols_processed || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Success Rate:</span>
                  <span className={`font-medium ${
                    (schedulerStatus.recent_activity?.success_rate || 0) > 95
                      ? 'text-green-600 dark:text-green-400'
                      : (schedulerStatus.recent_activity?.success_rate || 0) > 80
                        ? 'text-yellow-600 dark:text-yellow-400'
                        : 'text-red-600 dark:text-red-400'
                  }`}>
                    {(schedulerStatus.recent_activity?.success_rate || 0).toFixed(2)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Avg Response:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {schedulerStatus.recent_activity?.avg_response_time_ms || 0}ms
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Market Data Activity */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Recent Activity</h3>
        <div className="space-y-4">
          {activitiesLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            </div>
          ) : activities.length > 0 ? (
            activities.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
                <div className={`mt-1 w-2 h-2 rounded-full ${
                  activity.status === 'success'
                    ? 'bg-green-500'
                    : activity.status === 'warning'
                      ? 'bg-yellow-500'
                      : activity.status === 'error'
                        ? 'bg-red-500'
                        : 'bg-blue-500'
                }`} />
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <div className="text-sm text-gray-900 dark:text-white">{activity.description}</div>
                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-full">
                      {activity.provider_name}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {activity.relative_time} • {formatDisplayDateTime(activity.timestamp)}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No recent activity found
            </div>
          )}
        </div>
      </div>
    </div>
  )
}