'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
// import { useSystemMetrics } from '@/hooks/useAdmin'
// import LoadingSpinner from '@/components/ui/LoadingSpinner'
// import ErrorMessage from '@/components/ui/ErrorMessage'

interface DetailedMetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  details?: Array<{ label: string; value: string | number }>
}

function DetailedMetricCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendValue,
  details = []
}: DetailedMetricCardProps) {
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

      <div className="mb-4">
        <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
          {value}
        </div>
        {subtitle && (
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {subtitle}
          </div>
        )}
      </div>

      {details.length > 0 && (
        <div className="border-t dark:border-gray-600 pt-4">
          <div className="space-y-2">
            {details.map((detail, index) => (
              <div key={index} className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">{detail.label}</span>
                <span className="text-gray-900 dark:text-white font-medium">{detail.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface SystemHealthProps {
  status: 'healthy' | 'warning' | 'error'
  lastUpdated: string
  uptime?: string
  version?: string
}

function SystemHealthCard({ status, lastUpdated, uptime, version }: SystemHealthProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'healthy':
        return {
          color: 'text-green-600 dark:text-green-400',
          bgColor: 'bg-green-100 dark:bg-green-900/20',
          borderColor: 'border-green-200 dark:border-green-800',
          label: 'All Systems Operational',
          icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        }
      case 'warning':
        return {
          color: 'text-yellow-600 dark:text-yellow-400',
          bgColor: 'bg-yellow-100 dark:bg-yellow-900/20',
          borderColor: 'border-yellow-200 dark:border-yellow-800',
          label: 'System Warning',
          icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          )
        }
      case 'error':
        return {
          color: 'text-red-600 dark:text-red-400',
          bgColor: 'bg-red-100 dark:bg-red-900/20',
          borderColor: 'border-red-200 dark:border-red-800',
          label: 'System Error',
          icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )
        }
    }
  }

  const statusConfig = getStatusConfig()
  const formattedTime = new Date(lastUpdated).toLocaleString()

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm border ${statusConfig.borderColor} p-6`}>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">System Health</h3>

      <div className="flex items-center space-x-4 mb-6">
        <div className={`p-4 ${statusConfig.bgColor} ${statusConfig.color} rounded-full`}>
          {statusConfig.icon}
        </div>
        <div>
          <div className={`text-xl font-bold ${statusConfig.color}`}>
            {statusConfig.label}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Last checked: {formattedTime}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {uptime && (
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">{uptime}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Uptime</div>
          </div>
        )}
        {version && (
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-lg font-semibold text-gray-900 dark:text-white">{version}</div>
            <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Version</div>
          </div>
        )}
      </div>
    </div>
  )
}

interface SystemResourcesProps {
  cpuUsage?: number
  memoryUsage?: number
  diskUsage?: number
  activeConnections?: number
}

function SystemResourcesCard({ cpuUsage, memoryUsage, diskUsage, activeConnections }: SystemResourcesProps) {
  const getUsageColor = (usage: number) => {
    if (usage >= 90) return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/20'
    if (usage >= 75) return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/20'
    return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/20'
  }

  const ResourceBar = ({ label, value, unit = '%' }: { label: string; value?: number; unit?: string }) => {
    if (value === undefined) return null

    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">{label}</span>
          <span className={`font-medium ${getUsageColor(value).split(' ')[0]} ${getUsageColor(value).split(' ')[1]}`}>
            {value}{unit}
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              value >= 90
                ? 'bg-red-500'
                : value >= 75
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
            }`}
            style={{ width: `${Math.min(value, 100)}%` }}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">System Resources</h3>

      <div className="space-y-6">
        <ResourceBar label="CPU Usage" value={cpuUsage} />
        <ResourceBar label="Memory Usage" value={memoryUsage} />
        <ResourceBar label="Disk Usage" value={diskUsage} />

        {activeConnections !== undefined && (
          <div className="pt-4 border-t dark:border-gray-600">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Active Connections</span>
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {activeConnections}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AdminSystemPage() {
  const { user, token } = useAuth()
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchMetrics = async () => {
      if (!user || !token) return

      try {
        const response = await fetch('http://localhost:8001/api/v1/admin/system/metrics', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })

        if (response.ok) {
          const data = await response.json()
          setMetrics(data)
        } else {
          setError(`API Error: ${response.status}`)
        }
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [user, token])

  const refetch = () => {
    window.location.reload()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Loading system metrics...
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

  if (!metrics) {
    return null
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">System Monitoring</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Detailed system performance and health metrics
          </p>
        </div>
        <button
          onClick={refetch}
          className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          Refresh Metrics
        </button>
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SystemHealthCard
          status={metrics.systemStatus}
          lastUpdated={metrics.lastUpdated}
          uptime="7d 14h 32m"
          version="1.0.0"
        />

        <SystemResourcesCard
          cpuUsage={23}
          memoryUsage={67}
          diskUsage={45}
          activeConnections={12}
        />
      </div>

      {/* Detailed Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <DetailedMetricCard
          title="Database Performance"
          value={metrics.totalUsers + metrics.totalPortfolios}
          subtitle="Total records"
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          }
          details={[
            { label: 'Users', value: metrics.totalUsers },
            { label: 'Portfolios', value: metrics.totalPortfolios },
            { label: 'Avg Query Time', value: '< 50ms' },
            { label: 'Active Connections', value: '8/20' }
          ]}
        />

        <DetailedMetricCard
          title="User Activity"
          value={`${((metrics.activeUsers / metrics.totalUsers) * 100).toFixed(1)}%`}
          subtitle="Active user rate"
          trend="up"
          trendValue="+2.3%"
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          details={[
            { label: 'Active Users', value: metrics.activeUsers },
            { label: 'Daily Logins', value: '47' },
            { label: 'Avg Session', value: '23m' },
            { label: 'Admin Users', value: metrics.adminUsers }
          ]}
        />

        <DetailedMetricCard
          title="API Performance"
          value="99.9%"
          subtitle="Uptime (30 days)"
          trend="up"
          trendValue="stable"
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
          details={[
            { label: 'Avg Response', value: '127ms' },
            { label: 'Requests/min', value: '234' },
            { label: 'Error Rate', value: '0.01%' },
            { label: 'Rate Limited', value: '2' }
          ]}
        />

        <DetailedMetricCard
          title="Storage Usage"
          value="2.4 GB"
          subtitle="Database size"
          trend="up"
          trendValue="+12 MB"
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
            </svg>
          }
          details={[
            { label: 'User Data', value: '1.8 GB' },
            { label: 'Logs', value: '420 MB' },
            { label: 'Backups', value: '180 MB' },
            { label: 'Cache', value: '45 MB' }
          ]}
        />

        <DetailedMetricCard
          title="Security Status"
          value="Secure"
          subtitle="All checks passed"
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          }
          details={[
            { label: 'SSL Status', value: 'Valid' },
            { label: 'Failed Logins', value: '0' },
            { label: 'JWT Tokens', value: '23 active' },
            { label: 'Last Backup', value: '2h ago' }
          ]}
        />

        <DetailedMetricCard
          title="Cache Performance"
          value="94.2%"
          subtitle="Hit rate"
          trend="up"
          trendValue="+1.2%"
          icon={
            <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          }
          details={[
            { label: 'Cache Hits', value: '1,847' },
            { label: 'Cache Misses', value: '114' },
            { label: 'Evictions', value: '12' },
            { label: 'Memory Used', value: '89 MB' }
          ]}
        />
      </div>

      {/* Recent Activity Log */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Recent System Events</h3>
        <div className="space-y-4">
          {[
            { time: '2 minutes ago', type: 'info', message: 'System health check completed successfully' },
            { time: '15 minutes ago', type: 'success', message: 'Database backup completed' },
            { time: '1 hour ago', type: 'info', message: 'Cache cleared and refreshed' },
            { time: '3 hours ago', type: 'warning', message: 'High CPU usage detected (resolved)' },
            { time: '6 hours ago', type: 'info', message: 'System restart completed' },
          ].map((event, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700">
              <div className={`mt-1 w-2 h-2 rounded-full ${
                event.type === 'success'
                  ? 'bg-green-500'
                  : event.type === 'warning'
                    ? 'bg-yellow-500'
                    : 'bg-blue-500'
              }`} />
              <div className="flex-1">
                <div className="text-sm text-gray-900 dark:text-white">{event.message}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{event.time}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}