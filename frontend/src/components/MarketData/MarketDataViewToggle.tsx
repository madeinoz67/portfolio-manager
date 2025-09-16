'use client'

import React from 'react'

export type ViewMode = 'tiles' | 'table'

interface MarketDataViewToggleProps {
  currentView: ViewMode
  onViewChange: (view: ViewMode) => void
  className?: string
}

export function MarketDataViewToggle({
  currentView,
  onViewChange,
  className = ''
}: MarketDataViewToggleProps) {
  return (
    <div
      className={`flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1 ${className}`}
      role="group"
      aria-label="View selection"
    >
      <button
        onClick={() => onViewChange('tiles')}
        className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          currentView === 'tiles'
            ? 'bg-blue-500 text-white shadow-sm'
            : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'
        }`}
        aria-pressed={currentView === 'tiles'}
        aria-label="Tiles view"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
          />
        </svg>
        <span>Tiles</span>
      </button>

      <button
        onClick={() => onViewChange('table')}
        className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          currentView === 'table'
            ? 'bg-blue-500 text-white shadow-sm'
            : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100'
        }`}
        aria-pressed={currentView === 'table'}
        aria-label="Table view"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 10h18M3 14h18M3 6h18M3 18h18"
          />
        </svg>
        <span>Table</span>
      </button>
    </div>
  )
}