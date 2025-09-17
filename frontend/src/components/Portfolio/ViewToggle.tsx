// ViewToggle Component - Feature 004: Tile/Table View Toggle
// Toggle control for switching between tile and table portfolio views

import React, { useCallback } from 'react'
import { ViewToggleProps } from '@/types/portfolioView'

/**
 * ViewToggle component for switching between portfolio view modes
 */
const ViewToggle: React.FC<ViewToggleProps> = ({
  viewMode,
  onViewModeChange,
  className = '',
  disabled = false,
  size = 'md'
}) => {
  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================

  const handleTilesClick = useCallback(() => {
    if (!disabled && viewMode !== 'tiles') {
      onViewModeChange('tiles')
    }
  }, [disabled, viewMode, onViewModeChange])

  const handleTableClick = useCallback(() => {
    if (!disabled && viewMode !== 'table') {
      onViewModeChange('table')
    }
  }, [disabled, viewMode, onViewModeChange])

  const handleKeyDown = useCallback((
    event: React.KeyboardEvent<HTMLButtonElement>,
    targetMode: 'tiles' | 'table'
  ) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      if (!disabled && viewMode !== targetMode) {
        onViewModeChange(targetMode)
      }
    }
  }, [disabled, viewMode, onViewModeChange])

  // ============================================================================
  // CSS CLASSES
  // ============================================================================

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-8 px-3 text-sm'
      case 'lg':
        return 'h-12 px-6 text-base'
      case 'md':
      default:
        return 'h-10 px-4 text-sm'
    }
  }

  const getButtonClasses = (mode: 'tiles' | 'table') => {
    const baseClasses = `
      relative inline-flex items-center justify-center
      font-medium transition-all duration-200 ease-in-out
      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed
      ${getSizeClasses()}
    `.trim()

    const isActive = viewMode === mode
    const position = mode === 'tiles' ? 'first' : 'last'

    const positionClasses = position === 'first'
      ? 'rounded-l-lg border-r-0'
      : 'rounded-r-lg border-l-0'

    const stateClasses = isActive
      ? 'bg-blue-600 text-white border-blue-600 shadow-sm z-10'
      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:text-gray-900'

    return `${baseClasses} ${positionClasses} ${stateClasses} border`
  }

  const containerClasses = `
    inline-flex rounded-lg shadow-sm
    ${className}
  `.trim()

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div
      className={containerClasses}
      role="group"
      aria-label="Portfolio view toggle"
    >
      {/* Tiles View Button */}
      <button
        type="button"
        role="button"
        aria-pressed={viewMode === 'tiles'}
        aria-label="Switch to tiles view"
        disabled={disabled}
        onClick={handleTilesClick}
        onKeyDown={(e) => handleKeyDown(e, 'tiles')}
        className={getButtonClasses('tiles')}
      >
        <svg
          className="w-4 h-4 mr-2"
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

      {/* Table View Button */}
      <button
        type="button"
        role="button"
        aria-pressed={viewMode === 'table'}
        aria-label="Switch to table view"
        disabled={disabled}
        onClick={handleTableClick}
        onKeyDown={(e) => handleKeyDown(e, 'table')}
        className={getButtonClasses('table')}
      >
        <svg
          className="w-4 h-4 mr-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
        <span>Table</span>
      </button>

      {/* Screen Reader Status */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {viewMode === 'tiles' ? 'Tiles view active' : 'Table view active'}
      </div>
    </div>
  )
}

export default ViewToggle