'use client'

import React, { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: React.ErrorInfo
}

export class AdminErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Admin dashboard error:', error)
    console.error('Error info:', errorInfo)

    this.setState({
      error,
      errorInfo
    })

    // You could also log this to an error reporting service
    // logErrorToService(error, errorInfo)
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined
    })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-md w-full">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Admin Dashboard Error
                </h3>
              </div>
            </div>

            <div className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              <p className="mb-2">
                Something went wrong in the admin dashboard. This error has been logged.
              </p>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 p-3 bg-gray-100 dark:bg-gray-700 rounded border">
                  <summary className="cursor-pointer font-medium text-gray-800 dark:text-gray-200">
                    Error Details (Development)
                  </summary>
                  <pre className="mt-2 text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words">
                    {this.state.error.message}
                    {this.state.error.stack && `\n\nStack trace:\n${this.state.error.stack}`}
                  </pre>
                </details>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={this.handleReset}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default AdminErrorBoundary