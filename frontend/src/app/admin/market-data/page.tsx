'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { MarketDataStatusTable } from '@/components/admin/MarketDataStatusTable'
import { toggleMarketDataProvider } from '@/services/admin'
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
  const formattedTime = new Date(lastUpdate).toLocaleString()

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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      if (!user || !token) return

      try {
        // Fetch both provider status and API usage data in parallel
        const [statusResponse, usageResponse] = await Promise.all([
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
          })
        ])

        if (statusResponse.ok && usageResponse.ok) {
          const [statusData, usageData] = await Promise.all([
            statusResponse.json(),
            usageResponse.json()
          ])
          setMarketDataStatus(statusData)
          setApiUsageData(usageData)
        } else {
          const statusError = statusResponse.ok ? null : statusResponse.status
          const usageError = usageResponse.ok ? null : usageResponse.status
          setError(`API Error: Status ${statusError}, Usage ${usageError}`)
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [user, token])

  const refetch = () => {
    setLoading(true)
    setError(null)
    // Re-trigger the useEffect by clearing and resetting the token state
    const currentToken = token
    if (currentToken) {
      const fetchData = async () => {
        try {
          const [statusResponse, usageResponse] = await Promise.all([
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
            })
          ])

          if (statusResponse.ok && usageResponse.ok) {
            const [statusData, usageData] = await Promise.all([
              statusResponse.json(),
              usageResponse.json()
            ])
            setMarketDataStatus(statusData)
            setApiUsageData(usageData)
          } else {
            const statusError = statusResponse.ok ? null : statusResponse.status
            const usageError = usageResponse.ok ? null : usageResponse.status
            setError(`API Error: Status ${statusError}, Usage ${usageError}`)
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
          value={`${apiUsageData?.summary?.success_rate_today || 0}%`}
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
              ? apiUsageData.summary.success_rate_today > 95 ? '+0.2%' : apiUsageData.summary.success_rate_today > 80 ? '±0%' : '-2.1%'
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

      {/* Market Data Providers */}
      <div className="space-y-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Data Providers</h2>

        <MarketDataStatusTable
          providers={marketDataStatus?.providers || []}
          loading={loading}
          onToggle={handleProviderToggle}
        />
      </div>

      {/* Recent Market Data Activity */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Recent Activity</h3>
        <div className="space-y-4">
          {[
            {
              time: '2 minutes ago',
              type: 'success',
              message: 'Successfully updated prices for 25 symbols',
              provider: 'Alpha Vantage'
            },
            {
              time: '15 minutes ago',
              type: 'success',
              message: 'Batch price update completed for S&P 500 stocks',
              provider: 'Yahoo Finance'
            },
            {
              time: '1 hour ago',
              type: 'info',
              message: 'Switched to backup provider due to rate limiting',
              provider: 'Alpha Vantage'
            },
            {
              time: '3 hours ago',
              type: 'warning',
              message: 'High error rate detected, increased retry intervals',
              provider: 'Yahoo Finance'
            },
            {
              time: '6 hours ago',
              type: 'info',
              message: 'Daily rate limits reset for all providers',
              provider: 'System'
            },
          ].map((activity, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
              <div className={`mt-1 w-2 h-2 rounded-full ${
                activity.type === 'success'
                  ? 'bg-green-500'
                  : activity.type === 'warning'
                    ? 'bg-yellow-500'
                    : 'bg-blue-500'
              }`} />
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <div className="text-sm text-gray-900 dark:text-white">{activity.message}</div>
                  <span className="inline-flex px-2 py-1 text-xs font-medium bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-full">
                    {activity.provider}
                  </span>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{activity.time}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Configuration Panel */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <button className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div className="font-medium text-gray-900 dark:text-white">Force Price Update</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Manually trigger price refresh</div>
          </button>

          <button className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div className="font-medium text-gray-900 dark:text-white">Provider Settings</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Configure API keys and limits</div>
          </button>

          <button className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div className="font-medium text-gray-900 dark:text-white">Cache Management</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Clear or refresh cached data</div>
          </button>

          <button className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div className="font-medium text-gray-900 dark:text-white">View API Logs</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Review detailed request logs</div>
          </button>

          <button className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div className="font-medium text-gray-900 dark:text-white">Failover Testing</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Test provider failover scenarios</div>
          </button>

          <button className="p-4 text-left rounded-lg border dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div className="font-medium text-gray-900 dark:text-white">Export Reports</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">Generate usage and error reports</div>
          </button>
        </div>
      </div>
    </div>
  )
}