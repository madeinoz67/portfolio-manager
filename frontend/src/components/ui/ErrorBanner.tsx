'use client'

import React from 'react'
import { AuthError } from '@/types/auth'

interface ErrorBannerProps {
  error: AuthError | null
  onDismiss?: () => void
  className?: string
}

export function ErrorBanner({ error, onDismiss, className = '' }: ErrorBannerProps) {
  if (!error) return null

  const getErrorIcon = (type: AuthError['type']) => {
    switch (type) {
      case 'network':
        return (
          <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        )
      case 'timeout':
        return (
          <svg className="h-5 w-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'server':
        return (
          <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
        )
      case 'auth':
        return (
          <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        )
      default:
        return (
          <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )
    }
  }

  const getErrorColor = (type: AuthError['type']) => {
    switch (type) {
      case 'timeout':
        return 'bg-orange-50 border-orange-200 text-orange-800'
      case 'network':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      case 'server':
      case 'auth':
        return 'bg-red-50 border-red-200 text-red-800'
      default:
        return 'bg-red-50 border-red-200 text-red-800'
    }
  }

  const getSuggestedAction = (type: AuthError['type']) => {
    switch (type) {
      case 'network':
        return 'Check your internet connection and try again.'
      case 'timeout':
        return 'The server is taking longer than usual to respond. Please try again.'
      case 'server':
        return 'There appears to be a server issue. Please try again in a few moments.'
      case 'auth':
        return 'Please check your credentials and try again.'
      default:
        return 'Please try again or contact support if the problem persists.'
    }
  }

  return (
    <div className={`rounded-lg border p-4 ${getErrorColor(error.type)} ${className}`}>
      <div className="flex">
        <div className="flex-shrink-0">
          {getErrorIcon(error.type)}
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium">
            {error.message}
          </h3>
          <div className="mt-1 text-sm">
            <p className="mb-2">{getSuggestedAction(error.type)}</p>
            {error.details && (
              <details className="text-xs opacity-75">
                <summary className="cursor-pointer hover:opacity-100">Technical details</summary>
                <p className="mt-1 font-mono">{error.details}</p>
                <p className="mt-1">Time: {error.timestamp.toLocaleString()}</p>
              </details>
            )}
          </div>
          {onDismiss && (
            <div className="mt-3">
              <button
                type="button"
                className="text-sm font-medium underline hover:no-underline focus:outline-none"
                onClick={onDismiss}
              >
                Dismiss
              </button>
            </div>
          )}
        </div>
        {onDismiss && (
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                type="button"
                onClick={onDismiss}
                className={`inline-flex rounded-md p-1.5 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 ${
                  error.type === 'timeout' ? 'hover:bg-orange-100 focus:ring-orange-500' :
                  error.type === 'network' ? 'hover:bg-yellow-100 focus:ring-yellow-500' : ''
                }`}
              >
                <span className="sr-only">Dismiss</span>
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}