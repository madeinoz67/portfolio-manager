'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Button from '@/components/ui/Button'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

interface Portfolio {
  id: string
  name: string
  description?: string
}

interface PortfolioEditFormProps {
  portfolio: Portfolio
  onUpdate: (updatedPortfolio: Portfolio) => void
  onCancel: () => void
}

export default function PortfolioEditForm({ portfolio, onUpdate, onCancel }: PortfolioEditFormProps) {
  const [name, setName] = useState(portfolio.name)
  const [description, setDescription] = useState(portfolio.description || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { token } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!token) {
      setError('Authentication required')
      return
    }

    if (!name.trim()) {
      setError('Portfolio name is required')
      return
    }

    if (name.length > 100) {
      setError('Portfolio name must be 100 characters or less')
      return
    }

    if (description.length > 500) {
      setError('Description must be 500 characters or less')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`http://localhost:8001/api/v1/portfolios/${portfolio.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || undefined,
        }),
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication failed. Please log in again.')
        }
        if (response.status === 404) {
          throw new Error('Portfolio not found')
        }
        if (response.status === 422) {
          const errorData = await response.json()
          throw new Error(errorData.detail?.[0]?.msg || 'Validation error')
        }
        throw new Error(`Failed to update portfolio: ${response.status}`)
      }

      const updatedPortfolio = await response.json()
      onUpdate(updatedPortfolio)
    } catch (err) {
      console.error('Error updating portfolio:', err)
      setError(err instanceof Error ? err.message : 'Failed to update portfolio')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Edit Portfolio
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Portfolio Name *
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            placeholder="Enter portfolio name"
            maxLength={100}
            required
            disabled={loading}
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {name.length}/100 characters
          </p>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            placeholder="Enter portfolio description (optional)"
            rows={3}
            maxLength={500}
            disabled={loading}
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {description.length}/500 characters
          </p>
        </div>

        <div className="flex items-center gap-3 pt-4">
          <Button
            type="submit"
            disabled={loading || !name.trim()}
            className="flex items-center gap-2"
          >
            {loading && <LoadingSpinner size="sm" />}
            {loading ? 'Updating...' : 'Update Portfolio'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}