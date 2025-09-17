// PortfolioTableRow Component - Feature 004: Tile/Table View Toggle
// Individual table row component for portfolio data display

import React, { useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Portfolio } from '@/types/portfolio'
import { PortfolioTableRowProps } from '@/types/portfolioView'
import Button from '@/components/ui/Button'

/**
 * PortfolioTableRow component for displaying individual portfolio data in table format
 */
const PortfolioTableRow: React.FC<PortfolioTableRowProps> = ({
  portfolio,
  columns,
  selected = false,
  onClick,
  onViewDetails,
  onAddTrade,
  onDelete,
  showActions = true
}) => {
  const router = useRouter()

  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================

  const handleRowClick = useCallback((event: React.MouseEvent) => {
    // Don't trigger row click if user clicked on a button
    if (event.target instanceof HTMLElement && event.target.closest('button')) {
      return
    }

    if (onClick) {
      onClick(portfolio)
    } else {
      // Default action: navigate to portfolio details
      router.push(`/portfolios/${portfolio.id}`)
    }
  }, [onClick, portfolio, router])

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      if (onClick) {
        onClick(portfolio)
      } else {
        router.push(`/portfolios/${portfolio.id}`)
      }
    }
  }, [onClick, portfolio, router])

  const handleViewDetails = useCallback(() => {
    if (onViewDetails) {
      onViewDetails(portfolio)
    } else {
      router.push(`/portfolios/${portfolio.id}`)
    }
  }, [onViewDetails, portfolio, router])

  const handleAddTrade = useCallback(() => {
    if (onAddTrade) {
      onAddTrade(portfolio)
    } else {
      router.push(`/portfolios/${portfolio.id}/add-transaction`)
    }
  }, [onAddTrade, portfolio, router])

  const handleDelete = useCallback(() => {
    if (onDelete) {
      onDelete(portfolio)
    }
  }, [onDelete, portfolio])

  // ============================================================================
  // CELL RENDERING
  // ============================================================================

  const renderCell = useCallback((column: typeof columns[0]) => {
    const value = portfolio[column.key]
    let cellContent: React.ReactNode

    if (column.formatter) {
      cellContent = column.formatter(value, portfolio)
    } else {
      cellContent = value || '—'
    }

    const alignmentClass = column.align === 'right' ? 'text-right'
      : column.align === 'center' ? 'text-center'
      : 'text-left'

    return (
      <td
        key={column.key}
        className={`px-6 py-4 whitespace-nowrap text-sm ${alignmentClass}`}
        style={column.width ? { width: column.width, minWidth: column.width } : undefined}
      >
        <div className="truncate" title={typeof cellContent === 'string' ? cellContent : undefined}>
          {cellContent}
        </div>
      </td>
    )
  }, [portfolio])

  const renderActionsCell = useCallback(() => {
    if (!showActions) return null

    return (
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="flex items-center space-x-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleViewDetails}
            className="text-blue-600 hover:text-blue-700"
            title="View portfolio details"
          >
            View
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={handleAddTrade}
            className="text-green-600 hover:text-green-700"
            title="Add trade to portfolio"
          >
            Trade
          </Button>
          {onDelete && (
            <Button
              size="sm"
              variant="ghost"
              onClick={handleDelete}
              className="text-red-600 hover:text-red-700"
              title="Delete portfolio"
            >
              Delete
            </Button>
          )}
        </div>
      </td>
    )
  }, [showActions, handleViewDetails, handleAddTrade, handleDelete, onDelete])

  // ============================================================================
  // CSS CLASSES
  // ============================================================================

  const getRowClasses = () => {
    const baseClasses = `
      transition-colors duration-200 ease-in-out
      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset
      cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50
    `.trim()

    const selectedClasses = selected
      ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
      : 'border-gray-200 dark:border-gray-700'

    return `${baseClasses} ${selectedClasses}`
  }

  // ============================================================================
  // RENDER
  // ============================================================================

  const visibleColumns = columns.filter(col => col.visible)

  return (
    <tr
      role="row"
      tabIndex={0}
      className={getRowClasses()}
      onClick={handleRowClick}
      onKeyDown={handleKeyDown}
      aria-selected={selected}
      data-testid="portfolio-table-row"
    >
      {/* Data Cells */}
      {visibleColumns.map(renderCell)}

      {/* Actions Cell */}
      {renderActionsCell()}
    </tr>
  )
}

export default PortfolioTableRow