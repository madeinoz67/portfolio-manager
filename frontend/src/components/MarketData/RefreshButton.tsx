'use client'

import React, { useState, useEffect } from 'react'

interface RefreshButtonProps {
  onRefresh: (force?: boolean) => Promise<any>
  disabled?: boolean
  cooldownSeconds?: number
  showCooldown?: boolean
  className?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'primary' | 'secondary' | 'ghost'
}

export function RefreshButton({
  onRefresh,
  disabled = false,
  cooldownSeconds = 60, // 1 minute cooldown by default
  showCooldown = true,
  className = '',
  size = 'md',
  variant = 'secondary'
}: RefreshButtonProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [cooldownRemaining, setCooldownRemaining] = useState(0)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  // Update cooldown timer
  useEffect(() => {
    if (cooldownRemaining > 0) {
      const timer = setTimeout(() => {
        setCooldownRemaining(prev => prev - 1)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [cooldownRemaining])

  // Check for stored last refresh time on mount
  useEffect(() => {
    const stored = localStorage.getItem('marketdata-last-refresh')
    if (stored) {
      const lastRefreshTime = new Date(stored)
      const timeSince = Math.floor((Date.now() - lastRefreshTime.getTime()) / 1000)
      const remaining = Math.max(0, cooldownSeconds - timeSince)

      if (remaining > 0) {
        setCooldownRemaining(remaining)
        setLastRefresh(lastRefreshTime)
      }
    }
  }, [cooldownSeconds])

  const handleRefresh = async (force = false) => {
    if (isRefreshing || (cooldownRemaining > 0 && !force) || disabled) {
      return
    }

    setIsRefreshing(true)

    try {
      await onRefresh(force)

      // Set cooldown only for manual refreshes (not forced)
      if (!force) {
        const now = new Date()
        setLastRefresh(now)
        setCooldownRemaining(cooldownSeconds)
        localStorage.setItem('marketdata-last-refresh', now.toISOString())
      }
    } catch (error) {
      console.error('Refresh failed:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'px-2 py-1 text-xs'
      case 'lg':
        return 'px-6 py-3 text-base'
      default:
        return 'px-4 py-2 text-sm'
    }
  }

  const getVariantClasses = () => {
    const base = 'font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2'

    switch (variant) {
      case 'primary':
        return `${base} bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500 disabled:bg-blue-300`
      case 'ghost':
        return `${base} text-gray-700 hover:bg-gray-100 focus:ring-gray-500 disabled:text-gray-400`
      default:
        return `${base} bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-400`
    }
  }

  const isDisabled = disabled || isRefreshing || cooldownRemaining > 0

  return (
    <div className="inline-flex items-center space-x-2">
      <button
        onClick={() => handleRefresh(false)}
        disabled={isDisabled}
        className={`${getSizeClasses()} ${getVariantClasses()} ${className} disabled:cursor-not-allowed`}
        title={
          cooldownRemaining > 0
            ? `Rate limited. Try again in ${cooldownRemaining}s`
            : isRefreshing
            ? 'Refreshing...'
            : 'Refresh market data'
        }
      >
        <div className="flex items-center space-x-2">
          <svg
            className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          <span>
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </span>
        </div>
      </button>

      {showCooldown && cooldownRemaining > 0 && (
        <span className="text-xs text-gray-500">
          ({cooldownRemaining}s)
        </span>
      )}

      {lastRefresh && cooldownRemaining === 0 && (
        <span className="text-xs text-gray-400">
          Last: {lastRefresh.toLocaleTimeString()}
        </span>
      )}
    </div>
  )
}

interface ForceRefreshButtonProps {
  onRefresh: (force?: boolean) => Promise<any>
  disabled?: boolean
  className?: string
  confirmMessage?: string
}

export function ForceRefreshButton({
  onRefresh,
  disabled = false,
  className = '',
  confirmMessage = 'Force refresh will fetch fresh data and may count against rate limits. Continue?'
}: ForceRefreshButtonProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const handleForceRefresh = async () => {
    if (isRefreshing || disabled) return

    if (!showConfirm) {
      setShowConfirm(true)
      return
    }

    setIsRefreshing(true)
    setShowConfirm(false)

    try {
      await onRefresh(true)
    } catch (error) {
      console.error('Force refresh failed:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleCancel = () => {
    setShowConfirm(false)
  }

  if (showConfirm) {
    return (
      <div className="inline-flex items-center space-x-2 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
        <span className="text-xs text-yellow-800">{confirmMessage}</span>
        <button
          onClick={handleForceRefresh}
          className="px-2 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700"
          disabled={isRefreshing}
        >
          Yes
        </button>
        <button
          onClick={handleCancel}
          className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
        >
          No
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={handleForceRefresh}
      disabled={disabled || isRefreshing}
      className={`px-3 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      title="Force refresh (ignores cache and rate limits)"
    >
      <div className="flex items-center space-x-1">
        <svg
          className={`h-3 w-3 ${isRefreshing ? 'animate-spin' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
        <span>
          {isRefreshing ? 'Forcing...' : 'Force'}
        </span>
      </div>
    </button>
  )
}