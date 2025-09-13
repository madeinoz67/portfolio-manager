'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import Navigation from '@/components/layout/Navigation'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/ErrorMessage'

interface Stock {
  id: string
  symbol: string
  company_name: string
  current_price?: string
  sector?: string
  market_cap?: string
}

interface Holding {
  id: string
  portfolio_id: string
  stock: Stock
  quantity: string
  average_cost: string
  current_value: string
  unrealized_gain_loss: string
  unrealized_gain_loss_percent: string
  created_at: string
  updated_at: string
}

interface NewsNotice {
  id: string
  stock_id: string
  title: string
  summary?: string
  content?: string
  notice_type: 'NEWS' | 'EARNINGS' | 'DIVIDEND' | 'MERGER_ACQUISITION' | 'REGULATORY_FILING' | 'CORPORATE_ACTION' | 'ANALYST_REPORT' | 'PRESS_RELEASE'
  published_date: string
  source?: string
  external_url?: string
  document_url?: string
  created_at: string
  updated_at: string
}

const NoticeTypeColors = {
  EARNINGS: 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100',
  DIVIDEND: 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100',
  PRESS_RELEASE: 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-100',
  CORPORATE_ACTION: 'bg-orange-100 text-orange-800 dark:bg-orange-800 dark:text-orange-100',
  REGULATORY_FILING: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100',
  MERGER_ACQUISITION: 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100',
  ANALYST_REPORT: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-800 dark:text-indigo-100',
  NEWS: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
}

const NoticeTypeIcons = {
  EARNINGS: '💰',
  DIVIDEND: '💵',
  PRESS_RELEASE: '📢',
  CORPORATE_ACTION: '🏢',
  REGULATORY_FILING: '📋',
  MERGER_ACQUISITION: '🤝',
  ANALYST_REPORT: '📊',
  NEWS: '📰'
}

export default function HoldingDetail() {
  const params = useParams()
  const router = useRouter()
  const portfolioId = params?.id as string
  const holdingId = params?.holdingId as string

  const [holding, setHolding] = useState<Holding | null>(null)
  const [newsNotices, setNewsNotices] = useState<NewsNotice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHoldingDetail = async () => {
      if (!portfolioId || !holdingId) return

      try {
        setLoading(true)
        const token = localStorage.getItem('auth_token')
        if (!token) {
          router.push('/login')
          return
        }

        // Fetch holding details
        const holdingResponse = await fetch(`http://localhost:8001/api/v1/portfolios/${portfolioId}/holdings/${holdingId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })

        if (!holdingResponse.ok) {
          if (holdingResponse.status === 401) {
            router.push('/login')
            return
          }
          throw new Error(`Failed to fetch holding: ${holdingResponse.status}`)
        }

        const holdingData = await holdingResponse.json()
        setHolding(holdingData)

        // Fetch news and notices
        try {
          const newsResponse = await fetch(`http://localhost:8001/api/v1/portfolios/${portfolioId}/holdings/${holdingId}/news`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          })
          if (newsResponse.ok) {
            const newsData = await newsResponse.json()
            setNewsNotices(newsData)
          }
        } catch (err) {
          console.warn('Failed to fetch news:', err)
        }
      } catch (err) {
        console.error('Error fetching holding detail:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch holding details')
      } finally {
        setLoading(false)
      }
    }

    fetchHoldingDetail()
  }, [portfolioId, holdingId, router])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <ErrorMessage message={error} />
        </div>
      </div>
    )
  }

  if (!holding) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <ErrorMessage message="Holding not found" />
        </div>
      </div>
    )
  }

  const currentPrice = parseFloat(holding.stock.current_price || '0')
  const avgCost = parseFloat(holding.average_cost)
  const quantity = parseFloat(holding.quantity)
  const currentValue = parseFloat(holding.current_value)
  const gainLoss = parseFloat(holding.unrealized_gain_loss)
  const gainLossPercent = parseFloat(holding.unrealized_gain_loss_percent)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <nav className="flex mb-6" aria-label="Breadcrumb">
          <ol className="flex items-center space-x-4">
            <li>
              <Link href="/portfolios" className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
                Portfolios
              </Link>
            </li>
            <li className="flex">
              <svg className="flex-shrink-0 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              <Link href={`/portfolios/${portfolioId}`} className="ml-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
                Portfolio
              </Link>
            </li>
            <li className="flex">
              <svg className="flex-shrink-0 h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
              <span className="ml-4 text-gray-700 dark:text-gray-200 font-medium">{holding.stock.symbol}</span>
            </li>
          </ol>
        </nav>

        <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
          {/* Header */}
          <div className="px-6 py-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  {holding.stock.symbol}
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-300 mt-1">
                  {holding.stock.company_name}
                </p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${currentPrice.toFixed(2)}
                </div>
                <div className={`text-sm font-medium ${
                  gainLoss >= 0 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {gainLoss >= 0 ? '+' : ''}${gainLoss.toFixed(2)} ({gainLossPercent >= 0 ? '+' : ''}{gainLossPercent.toFixed(2)}%)
                </div>
              </div>
            </div>
          </div>

          {/* Position Summary */}
          <div className="px-6 py-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              Position Summary
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Shares</dt>
                <dd className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {quantity.toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Average Cost</dt>
                <dd className="text-2xl font-semibold text-gray-900 dark:text-white">
                  ${avgCost.toFixed(2)}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Current Value</dt>
                <dd className="text-2xl font-semibold text-gray-900 dark:text-white">
                  ${currentValue.toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Cost Basis</dt>
                <dd className="text-2xl font-semibold text-gray-900 dark:text-white">
                  ${(quantity * avgCost).toLocaleString()}
                </dd>
              </div>
            </div>
          </div>

          {/* News & Notices Timeline */}
          <div className="px-6 py-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
              News & Notices Timeline
            </h2>
            {newsNotices.length > 0 ? (
              <div className="flow-root">
                <ul className="-mb-8">
                  {newsNotices.map((notice, noticeIdx) => (
                    <li key={notice.id}>
                      <div className="relative pb-8">
                        {noticeIdx !== newsNotices.length - 1 ? (
                          <span
                            className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200 dark:bg-gray-600"
                            aria-hidden="true"
                          />
                        ) : null}
                        <div className="relative flex space-x-3">
                          <div>
                            <span className="h-8 w-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-sm">
                              {NoticeTypeIcons[notice.notice_type]}
                            </span>
                          </div>
                          <div className="min-w-0 flex-1 pt-1.5">
                            <div className="flex items-center space-x-2 mb-2">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${NoticeTypeColors[notice.notice_type]}`}>
                                {notice.notice_type.replace('_', ' ')}
                              </span>
                              <time className="text-sm text-gray-500 dark:text-gray-400">
                                {new Date(notice.published_date).toLocaleDateString('en-US', {
                                  year: 'numeric',
                                  month: 'long',
                                  day: 'numeric'
                                })}
                              </time>
                            </div>
                            <div>
                              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                                {notice.title}
                              </h3>
                              {notice.summary && (
                                <p className="text-gray-700 dark:text-gray-300 mt-1">
                                  {notice.summary}
                                </p>
                              )}
                              {notice.source && (
                                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                  Source: {notice.source}
                                </p>
                              )}
                              <div className="flex space-x-3 mt-3">
                                {notice.external_url && (
                                  <a 
                                    href={notice.external_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                                  >
                                    Read More →
                                  </a>
                                )}
                                {notice.document_url && (
                                  <a 
                                    href={notice.document_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-green-600 dark:text-green-400 hover:underline"
                                  >
                                    📄 Document
                                  </a>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p>No news or notices found for this holding</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}