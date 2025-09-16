'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'

// TypeScript interfaces for API responses
interface PortfolioUpdateStats24h {
  totalUpdates: number
  successfulUpdates: number
  failedUpdates: number
  successRate: number
  avgUpdateDurationMs: number
  uniquePortfolios: number
  updateFrequencyPerHour: number
  commonErrorTypes: Record<string, number>
}

interface QueueHealthMetrics {
  currentQueueSize: number
  avgProcessingRate: number
  maxQueueSize1h: number
  rateLimitHits1h: number
  memoryUsageTrend: 'increasing' | 'decreasing' | 'stable'
  queueHealthStatus: 'healthy' | 'warning' | 'critical' | 'unknown'
}

interface StormProtectionMetrics {
  totalCoalescedUpdates: number
  totalIndividualUpdates: number
  coalescingEfficiency: number
  avgSymbolsPerUpdate: number
  stormEventsDetected: number
  protectionEffectiveness: number
}

interface PortfolioPerformanceItem {
  portfolioId: string
  portfolioName: string
  totalUpdates: number
  successRate: number
  avgDurationMs: number
  lastUpdated: string
}

interface UpdateLagAnalysis {
  avgLagMs: number
  medianLagMs: number
  p95LagMs: number
  maxLagMs: number
  samplesAnalyzed: number
  lagDistribution: {
    '0-1s': number
    '1-5s': number
    '5s+': number
  }
}

interface LiveQueueMetrics {
  pendingUpdates: number
  activePortfolios: number
  rateLimitHits: number
  isProcessing: boolean
  totalSymbolsQueued: number
}

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  status?: 'healthy' | 'warning' | 'critical' | 'neutral'
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
}

function PortfolioMetricCard({ title, value, subtitle, icon, status = 'neutral', trend, trendValue }: MetricCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy': return 'text-green-600 dark:text-green-400'
      case 'warning': return 'text-yellow-600 dark:text-yellow-400'
      case 'critical': return 'text-red-600 dark:text-red-400'
      default: return 'text-blue-600 dark:text-blue-400'
    }
  }

  const getStatusBgColor = () => {
    switch (status) {
      case 'healthy': return 'bg-green-100 dark:bg-green-900/20'
      case 'warning': return 'bg-yellow-100 dark:bg-yellow-900/20'
      case 'critical': return 'bg-red-100 dark:bg-red-900/20'
      default: return 'bg-blue-100 dark:bg-blue-900/20'
    }
  }

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
      <svg className={`w-4 h-4 ${getTrendColor()}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
          <div className={`p-2 ${getStatusBgColor()} rounded-lg`}>
            <div className={getStatusColor()}>{icon}</div>
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
          {typeof value === 'number' ? value.toLocaleString() : value}
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

interface SectionHeaderProps {
  title: string
  description: string
  action?: React.ReactNode
}

function SectionHeader({ title, description, action }: SectionHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{description}</p>
      </div>
      {action}
    </div>
  )
}

export default function PortfolioUpdateMetrics() {
  const { token } = useAuth()
  const [stats24h, setStats24h] = useState<PortfolioUpdateStats24h | null>(null)
  const [queueHealth, setQueueHealth] = useState<QueueHealthMetrics | null>(null)
  const [stormProtection, setStormProtection] = useState<StormProtectionMetrics | null>(null)
  const [portfolioPerformance, setPortfolioPerformance] = useState<PortfolioPerformanceItem[]>([])
  const [lagAnalysis, setLagAnalysis] = useState<UpdateLagAnalysis | null>(null)
  const [liveQueue, setLiveQueue] = useState<LiveQueueMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchMetrics = async () => {
    if (!token) return

    try {
      setRefreshing(true)

      const endpoints = [
        '/admin/portfolio-updates/stats/24h',
        '/admin/portfolio-updates/queue/health',
        '/admin/portfolio-updates/storm-protection',
        '/admin/portfolio-updates/performance/breakdown?limit=5',
        '/admin/portfolio-updates/lag-analysis',
        '/admin/portfolio-updates/queue/live'
      ]

      const requests = endpoints.map(endpoint =>
        fetch(`http://localhost:8001/api/v1${endpoint}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })
      )

      const responses = await Promise.all(requests)
      const data = await Promise.all(responses.map(r => r.json()))

      setStats24h(data[0])
      setQueueHealth(data[1])
      setStormProtection(data[2])
      setPortfolioPerformance(data[3])
      setLagAnalysis(data[4])
      setLiveQueue(data[5])

      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchMetrics()

    // Set up auto-refresh every 10 seconds for live metrics to catch price update triggers
    const interval = setInterval(fetchMetrics, 10000)
    return () => clearInterval(interval)
  }, [token])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Loading portfolio metrics...
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
          onClick={() => fetchMetrics()}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg"
        >
          Retry
        </button>
      </div>
    )
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const getHealthStatus = (status: string) => {
    switch (status) {
      case 'healthy': return 'healthy'
      case 'warning': return 'warning'
      case 'critical': return 'critical'
      default: return 'neutral'
    }
  }

  return (
    <div className="space-y-8">
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Portfolio Update Monitoring</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Real-time performance metrics and system health (auto-refresh every 10s)
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {refreshing && (
            <div className="flex items-center text-blue-600 dark:text-blue-400">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-sm">Updating...</span>
            </div>
          )}
          <button
            onClick={fetchMetrics}
            disabled={refreshing}
            className={`bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg font-medium transition-colors ${
              refreshing ? 'cursor-not-allowed' : 'cursor-pointer'
            }`}
          >
            <div className="flex items-center space-x-2">
              <svg
                className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span>{refreshing ? 'Refreshing' : 'Refresh'}</span>
            </div>
          </button>
        </div>
      </div>

      {/* Live Queue Status */}
      {liveQueue && (
        <div>
          <SectionHeader
            title="Live Queue Status"
            description="Real-time portfolio update queue metrics"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <PortfolioMetricCard
              title="Pending Updates"
              value={liveQueue.pendingUpdates}
              status={liveQueue.pendingUpdates > 20 ? 'warning' : liveQueue.pendingUpdates > 50 ? 'critical' : 'healthy'}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="Active Portfolios"
              value={liveQueue.activePortfolios}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="Processing Status"
              value={liveQueue.isProcessing ? 'Active' : 'Stopped'}
              status={liveQueue.isProcessing ? 'healthy' : 'critical'}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={liveQueue.isProcessing ? "M14.828 14.828a4 4 0 01-5.656 0M9 10h1.586a1 1 0 01.707.293l4.828 4.829a2 2 0 002.828 0 2 2 0 000-2.829L14.07 7.464a1 1 0 01-.293-.707V6a2 2 0 00-2-2H8a2 2 0 00-2 2v1c0 .295.134.576.366.765L9 10z" : "M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"} />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="Rate Limit Hits"
              value={liveQueue.rateLimitHits}
              status={liveQueue.rateLimitHits > 5 ? 'warning' : liveQueue.rateLimitHits > 15 ? 'critical' : 'healthy'}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="Symbols Queued"
              value={liveQueue.totalSymbolsQueued}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m0 0V1a1 1 0 011-1h2a1 1 0 011 1v8l-5 5H8a1 1 0 01-1-1V4z" />
                </svg>
              }
            />
          </div>
        </div>
      )}

      {/* 24-Hour Statistics */}
      {stats24h && (
        <div>
          <SectionHeader
            title="24-Hour Statistics"
            description="Portfolio update performance over the last 24 hours"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <PortfolioMetricCard
              title="Total Updates"
              value={stats24h.totalUpdates}
              subtitle={`${stats24h.updateFrequencyPerHour.toFixed(1)} per hour`}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="Success Rate"
              value={`${stats24h.successRate}%`}
              subtitle={`${stats24h.successfulUpdates} / ${stats24h.totalUpdates} successful`}
              status={stats24h.successRate >= 95 ? 'healthy' : stats24h.successRate >= 85 ? 'warning' : 'critical'}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="Average Duration"
              value={formatDuration(stats24h.avgUpdateDurationMs)}
              subtitle="Per portfolio update"
              status={stats24h.avgUpdateDurationMs < 200 ? 'healthy' : stats24h.avgUpdateDurationMs < 500 ? 'warning' : 'critical'}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="Unique Portfolios"
              value={stats24h.uniquePortfolios}
              subtitle="Received updates"
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              }
            />
          </div>
        </div>
      )}

      {/* Queue Health & Storm Protection */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Queue Health */}
        {queueHealth && (
          <div>
            <SectionHeader
              title="Queue Health"
              description="Processing performance and resource usage"
            />
            <div className="space-y-4">
              <PortfolioMetricCard
                title="Queue Status"
                value={queueHealth.queueHealthStatus.charAt(0).toUpperCase() + queueHealth.queueHealthStatus.slice(1)}
                subtitle={`${queueHealth.currentQueueSize} items pending`}
                status={getHealthStatus(queueHealth.queueHealthStatus)}
                icon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                }
              />
              <div className="grid grid-cols-2 gap-4">
                <PortfolioMetricCard
                  title="Processing Rate"
                  value={`${queueHealth.avgProcessingRate.toFixed(1)}/min`}
                  icon={
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  }
                />
                <PortfolioMetricCard
                  title="Memory Trend"
                  value={queueHealth.memoryUsageTrend.charAt(0).toUpperCase() + queueHealth.memoryUsageTrend.slice(1)}
                  status={queueHealth.memoryUsageTrend === 'increasing' ? 'warning' : 'healthy'}
                  icon={
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                    </svg>
                  }
                />
              </div>
            </div>
          </div>
        )}

        {/* Storm Protection */}
        {stormProtection && (
          <div>
            <SectionHeader
              title="Storm Protection"
              description="Update coalescing and efficiency metrics"
            />
            <div className="space-y-4">
              <PortfolioMetricCard
                title="Protection Effectiveness"
                value={`${stormProtection.protectionEffectiveness.toFixed(1)}%`}
                subtitle="Load reduction achieved"
                status={stormProtection.protectionEffectiveness >= 70 ? 'healthy' : stormProtection.protectionEffectiveness >= 40 ? 'warning' : 'critical'}
                icon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                }
              />
              <div className="grid grid-cols-2 gap-4">
                <PortfolioMetricCard
                  title="Coalescing Rate"
                  value={`${stormProtection.coalescingEfficiency.toFixed(1)}%`}
                  icon={
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  }
                />
                <PortfolioMetricCard
                  title="Storm Events"
                  value={stormProtection.stormEventsDetected}
                  icon={
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  }
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Update Lag Analysis */}
      {lagAnalysis && lagAnalysis.samplesAnalyzed > 0 && (
        <div>
          <SectionHeader
            title="Update Lag Analysis"
            description={`Response time analysis from ${lagAnalysis.samplesAnalyzed} samples`}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <PortfolioMetricCard
              title="Average Lag"
              value={formatDuration(lagAnalysis.avgLagMs)}
              status={lagAnalysis.avgLagMs < 1000 ? 'healthy' : lagAnalysis.avgLagMs < 3000 ? 'warning' : 'critical'}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="Median Lag"
              value={formatDuration(lagAnalysis.medianLagMs)}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="95th Percentile"
              value={formatDuration(lagAnalysis.p95LagMs)}
              status={lagAnalysis.p95LagMs < 2000 ? 'healthy' : lagAnalysis.p95LagMs < 5000 ? 'warning' : 'critical'}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              }
            />
            <PortfolioMetricCard
              title="Max Lag"
              value={formatDuration(lagAnalysis.maxLagMs)}
              status={lagAnalysis.maxLagMs < 5000 ? 'healthy' : lagAnalysis.maxLagMs < 10000 ? 'warning' : 'critical'}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
                </svg>
              }
            />
          </div>

          {/* Lag Distribution */}
          <div className="mt-6 bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Response Time Distribution</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {lagAnalysis.lagDistribution['0-1s']}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Under 1 second</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                  {lagAnalysis.lagDistribution['1-5s']}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">1-5 seconds</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {lagAnalysis.lagDistribution['5s+']}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Over 5 seconds</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Portfolio Performance */}
      {portfolioPerformance.length > 0 && (
        <div>
          <SectionHeader
            title="Top Portfolio Performance"
            description="Most active portfolios by update volume"
          />
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border dark:border-gray-700 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Portfolio
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Updates (24h)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Success Rate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Avg Duration
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Last Updated
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {portfolioPerformance.map((portfolio) => (
                    <tr key={portfolio.portfolioId}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {portfolio.portfolioName}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {portfolio.portfolioId.slice(0, 8)}...
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {portfolio.totalUpdates}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          portfolio.successRate >= 95
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : portfolio.successRate >= 85
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                            : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        }`}>
                          {portfolio.successRate.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {formatDuration(portfolio.avgDurationMs)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {new Date(portfolio.lastUpdated).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}