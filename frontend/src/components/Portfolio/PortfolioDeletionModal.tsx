/**
 * Portfolio deletion modal with confirmation.
 * Requires exact portfolio name match before allowing deletion.
 */

'use client'

import { useState, useEffect, useContext } from 'react'
import Button from '@/components/ui/Button'
import { AuthContext } from '@/contexts/AuthContext'
import { deletePortfolio, hardDeletePortfolio } from '@/services/portfolio'
import type { Portfolio } from '@/types/portfolio'

interface PortfolioDeletionModalProps {
  isOpen: boolean
  onClose: () => void
  portfolio: Portfolio
  onDeleted: () => void
  allowHardDelete?: boolean
}

export default function PortfolioDeletionModal({
  isOpen,
  onClose,
  portfolio,
  onDeleted,
  allowHardDelete = false,
}: PortfolioDeletionModalProps) {
  const { user, token } = useContext(AuthContext)
  const [confirmationName, setConfirmationName] = useState('')
  const [isHardDelete, setIsHardDelete] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setConfirmationName('')
      setIsHardDelete(false)
      setError(null)
    }
  }, [isOpen])

  const isConfirmationValid = confirmationName === portfolio.name
  const canDelete = isConfirmationValid && !isLoading

  const handleDelete = async () => {
    if (!canDelete || !user) return

    setIsLoading(true)
    setError(null)

    try {
      if (isHardDelete) {
        await hardDeletePortfolio(portfolio.id, { confirmationName }, { token })
      } else {
        await deletePortfolio(portfolio.id, { confirmationName }, { token })
      }

      onDeleted()
      onClose()
    } catch (err: any) {
      setError(err.message || 'Failed to delete portfolio')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancel = () => {
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Delete Portfolio
          </h2>
          <p className="text-gray-600 dark:text-gray-300">
            You are about to delete the portfolio:
          </p>
          <p className="font-medium text-gray-900 dark:text-white mt-1">
            {portfolio.name}
          </p>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
            To confirm deletion, please enter the portfolio name exactly as shown above:
          </p>
          <input
            type="text"
            placeholder="Portfolio name"
            value={confirmationName}
            onChange={(e) => setConfirmationName(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {allowHardDelete && (
          <div className="mb-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={isHardDelete}
                onChange={(e) => setIsHardDelete(e.target.checked)}
                className="rounded border-gray-300 text-red-600 focus:ring-red-500"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Permanently delete (this action cannot be undone)
              </span>
            </label>
            {isHardDelete && (
              <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                This action cannot be undone. All holdings and transactions will be permanently removed.
              </p>
            )}
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        <div className="flex space-x-3">
          <Button
            variant="secondary"
            onClick={handleCancel}
            className="flex-1"
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleDelete}
            disabled={!canDelete}
            loading={isLoading}
            className="flex-1"
          >
            {isLoading ? 'Deleting...' : 'Delete Portfolio'}
          </Button>
        </div>
      </div>
    </div>
  )
}