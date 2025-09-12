'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Portfolio {
  id: string
  name: string
  description?: string
  total_value: string
  daily_change: string
  daily_change_percent: string
  created_at: string
  updated_at: string
}

export default function Home() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newPortfolio, setNewPortfolio] = useState({ name: '', description: '' })

  // Fetch portfolios from API
  const fetchPortfolios = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8001/api/v1/portfolios')
      if (response.ok) {
        const data = await response.json()
        setPortfolios(data)
        setError(null)
      } else {
        setError('Failed to fetch portfolios')
      }
    } catch (error) {
      setError('Connection error')
      console.error('Error fetching portfolios:', error)
    } finally {
      setLoading(false)
    }
  }

  // Create new portfolio
  const createPortfolio = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch('http://localhost:8001/api/v1/portfolios', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newPortfolio),
      })
      
      if (response.ok) {
        setNewPortfolio({ name: '', description: '' })
        setShowCreateForm(false)
        fetchPortfolios() // Refresh the list
      } else {
        setError('Failed to create portfolio')
      }
    } catch (error) {
      setError('Connection error')
      console.error('Error creating portfolio:', error)
    }
  }

  useEffect(() => {
    fetchPortfolios()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Portfolio Dashboard</h1>
          <p className="mt-2 text-gray-600">Manage your investment portfolios</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Create Portfolio Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Create New Portfolio
          </button>
        </div>

        {/* Create Portfolio Form */}
        {showCreateForm && (
          <div className="mb-6 bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-4">Create New Portfolio</h3>
            <form onSubmit={createPortfolio} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Portfolio Name
                </label>
                <input
                  type="text"
                  required
                  maxLength={100}
                  value={newPortfolio.name}
                  onChange={(e) => setNewPortfolio({...newPortfolio, name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter portfolio name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <textarea
                  maxLength={500}
                  value={newPortfolio.description}
                  onChange={(e) => setNewPortfolio({...newPortfolio, description: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter description"
                  rows={3}
                />
              </div>
              <div className="flex space-x-2">
                <button
                  type="submit"
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Create Portfolio
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Portfolios Grid */}
        {portfolios.length === 0 ? (
          <div className="bg-white p-8 rounded-lg shadow-md text-center">
            <p className="text-gray-500 text-lg">No portfolios found</p>
            <p className="text-gray-400 mt-2">Create your first portfolio to get started</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {portfolios.map((portfolio) => (
              <div key={portfolio.id} className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {portfolio.name}
                </h3>
                {portfolio.description && (
                  <p className="text-gray-600 text-sm mb-4">
                    {portfolio.description}
                  </p>
                )}
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Total Value:</span>
                    <span className="font-semibold">${portfolio.total_value}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Daily Change:</span>
                    <span className={`font-semibold ${
                      parseFloat(portfolio.daily_change) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      ${portfolio.daily_change} ({portfolio.daily_change_percent}%)
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 pt-2">
                    Created: {new Date(portfolio.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="mt-4 flex space-x-2">
                  <Link
                    href={`/portfolios/${portfolio.id}`}
                    className="flex-1 bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors text-center"
                  >
                    View Details
                  </Link>
                  <Link
                    href={`/portfolios/${portfolio.id}`}
                    className="flex-1 bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 transition-colors text-center"
                  >
                    Add Transaction
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}