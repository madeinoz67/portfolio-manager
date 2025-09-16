'use client'

import React, { useEffect, useState, use } from 'react'
import { useRouter } from 'next/navigation'
import { ProviderDetailResponse } from '@/types/admin'
import { useAdmin } from '@/hooks/useAdmin'
import { AdminApiError } from '@/services/admin'

interface ProviderDetailPageProps {
  params: Promise<{
    providerId: string
  }>
}

export default function ProviderDetailPage({ params }: ProviderDetailPageProps) {
  const router = useRouter()
  const { providerId } = use(params)
  const [providerDetail, setProviderDetail] = useState<ProviderDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { fetchProviderDetails } = useAdmin()

  useEffect(() => {
    const abortController = new AbortController()

    const loadProviderDetails = async () => {
      try {
        setLoading(true)
        setError(null)
        const details = await fetchProviderDetails(providerId)
        if (!abortController.signal.aborted) {
          setProviderDetail(details)
        }
      } catch (err) {
        if (!abortController.signal.aborted) {
          // Check if it's a cancellation error and ignore it
          if (err instanceof AdminApiError && err.message === 'Request was cancelled') {
            return // Silently ignore cancellation errors
          }
          console.error('Error loading provider details:', err)
          setError('Failed to load provider details')
        }
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false)
        }
      }
    }

    loadProviderDetails()

    return () => {
      abortController.abort()
    }
  }, [providerId, fetchProviderDetails])

  const handleBackClick = () => {
    router.push('/admin/market-data')
  }


  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse space-y-8">
            <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-1/3"></div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-6 space-y-4">
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
                  <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <button
            onClick={handleBackClick}
            className="mb-6 inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Market Data
          </button>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <div className="flex">
              <svg className="w-5 h-5 text-red-400 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">Error Loading Provider Details</h3>
                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                  {error}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!providerDetail) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <button
            onClick={handleBackClick}
            className="mb-6 inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Market Data
          </button>
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">Provider not found</h3>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              The requested provider could not be found.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={handleBackClick}
            className="mb-6 inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Market Data
          </button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                {providerDetail.providerName}
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-300">
                Provider ID: {providerDetail.providerId} • Priority: {providerDetail.priority}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                providerDetail.isEnabled
                  ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                  : 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
              }`}>
                {providerDetail.isEnabled ? 'Enabled' : 'Disabled'}
              </span>

              {/* Bulk Updates Status Tag */}
              {providerDetail.isEnabled && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300">
                  <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                  Bulk Updates
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Requests Today
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                    {providerDetail.usageStats.today.totalRequests.toLocaleString()}
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Success Rate
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                    {providerDetail.usageStats.today.successRate.toFixed(1)}%
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Avg Response Time
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                    {providerDetail.usageStats.today.avgResponseTime}ms
                  </dd>
                </dl>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Cost Today
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900 dark:text-white">
                    ${providerDetail.usageStats.today.totalCost.toFixed(2)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Usage Statistics */}
          <div className="lg:col-span-2 space-y-8">
            {/* Today vs Yesterday */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Usage Comparison</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Today</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-300">Requests</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {providerDetail.usageStats.today.totalRequests}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-300">Errors</span>
                        <span className="text-sm font-medium text-red-600 dark:text-red-400">
                          {providerDetail.usageStats.today.totalErrors}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-300">Rate Limits</span>
                        <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
                          {providerDetail.usageStats.today.rateLimitHits}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Yesterday</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-300">Requests</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {providerDetail.usageStats.yesterday.totalRequests}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-300">Errors</span>
                        <span className="text-sm font-medium text-red-600 dark:text-red-400">
                          {providerDetail.usageStats.yesterday.totalErrors}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-300">Rate Limits</span>
                        <span className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
                          {providerDetail.usageStats.yesterday.rateLimitHits}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Performance Metrics</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                      {providerDetail.performanceMetrics.successRate.toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">Success Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-red-600 dark:text-red-400">
                      {providerDetail.performanceMetrics.errorRate.toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">Error Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                      {providerDetail.performanceMetrics.avgResponseTime}ms
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">Avg Response</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                      {providerDetail.performanceMetrics.uptimePercentage.toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">Uptime</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            {/* Configuration */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Configuration</h3>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">API Endpoint</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-white break-all">
                    {providerDetail.configuration.apiEndpoint}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Rate Limits</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                    {providerDetail.rateLimitPerMinute}/min, {providerDetail.rateLimitPerDay}/day
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Timeout</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                    {providerDetail.configuration.timeout}ms
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Last Updated</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                    {new Date(providerDetail.lastUpdated).toLocaleString()}
                  </dd>
                </div>
              </div>
            </div>

            {/* Cost Analysis */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Cost Analysis</h3>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-300">Today</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    ${providerDetail.costAnalysis.totalCostToday.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-300">This Month</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    ${providerDetail.costAnalysis.totalCostThisMonth.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-300">Projected Monthly</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    ${providerDetail.costAnalysis.projectedMonthlyCost.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-300">Per Request</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    ${providerDetail.costAnalysis.costPerRequest.toFixed(4)}
                  </span>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Recent Activity</h3>
              </div>
              <div className="p-6">
                {providerDetail.recentActivity.length > 0 ? (
                  <div className="space-y-3">
                    {providerDetail.recentActivity.slice(0, 5).map((activity, index) => (
                      <div key={index} className="flex items-start space-x-3">
                        <div className={`flex-shrink-0 w-2 h-2 rounded-full mt-2 ${
                          activity.status === 'success' ? 'bg-green-500' :
                          activity.status === 'error' ? 'bg-red-500' : 'bg-yellow-500'
                        }`}></div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-900 dark:text-white">
                            {activity.description}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(activity.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 dark:text-gray-400">No recent activity</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}