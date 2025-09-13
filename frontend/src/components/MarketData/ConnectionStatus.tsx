'use client'

import React from 'react'
import { ConnectionStatus as ConnectionStatusType } from '@/types/marketData'

interface ConnectionStatusProps {
  status: ConnectionStatusType
  lastUpdate?: string | null
  error?: string | null
  reconnectAttempts?: number
  maxReconnectAttempts?: number
  onReconnect?: () => void
  className?: string
}

export function ConnectionStatus({
  status,
  lastUpdate,
  error,
  reconnectAttempts = 0,
  maxReconnectAttempts = 5,
  onReconnect,
  className = ''
}: ConnectionStatusProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'connecting':
      case 'reconnecting':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'disconnected':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      case 'error':
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'connected':
        return (
          <div className="flex h-2 w-2">
            <div className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75"></div>
            <div className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></div>
          </div>
        )
      case 'connecting':
      case 'reconnecting':
        return (
          <div className="animate-spin rounded-full h-2 w-2 border-b-2 border-yellow-600"></div>
        )
      case 'disconnected':
        return (
          <div className="h-2 w-2 rounded-full bg-gray-400"></div>
        )
      case 'error':
      case 'failed':
        return (
          <div className="h-2 w-2 rounded-full bg-red-500"></div>
        )
      default:
        return (
          <div className="h-2 w-2 rounded-full bg-gray-400"></div>
        )
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Live'
      case 'connecting':
        return 'Connecting...'
      case 'reconnecting':
        return `Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`
      case 'disconnected':
        return 'Disconnected'
      case 'error':
        return 'Error'
      case 'failed':
        return 'Connection Failed'
      default:
        return 'Unknown'
    }
  }

  const formatLastUpdate = (updateTime: string) => {
    try {
      const date = new Date(updateTime)
      const now = new Date()
      const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

      if (diffMinutes < 1) {
        return 'Just now'
      } else if (diffMinutes < 60) {
        return `${diffMinutes}m ago`
      } else {
        const diffHours = Math.floor(diffMinutes / 60)
        return `${diffHours}h ago`
      }
    } catch {
      return 'Unknown'
    }
  }

  const isStale = lastUpdate ?
    (new Date().getTime() - new Date(lastUpdate).getTime()) > 30 * 60 * 1000 : // 30 minutes
    false

  return (
    <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-lg border text-sm font-medium ${getStatusColor()} ${className}`}>
      {getStatusIcon()}
      <span>{getStatusText()}</span>

      {lastUpdate && (
        <span className={`text-xs ${isStale ? 'text-orange-600' : 'opacity-75'}`}>
          {isStale && '⚠️ '}
          {formatLastUpdate(lastUpdate)}
        </span>
      )}

      {error && (
        <span className="text-xs text-red-600 max-w-xs truncate" title={error}>
          {error}
        </span>
      )}

      {(status === 'error' || status === 'failed') && onReconnect && (
        <button
          onClick={onReconnect}
          className="text-xs underline hover:no-underline focus:outline-none"
          disabled={status === 'connecting' || status === 'reconnecting'}
        >
          Retry
        </button>
      )}
    </div>
  )
}