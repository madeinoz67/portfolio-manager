// PortfolioTable Component - Feature 004: Tile/Table View Toggle
// Main table component for displaying portfolios in tabular format

import React, { useMemo, useCallback } from 'react'
import { Portfolio } from '@/types/portfolio'
import { PortfolioTableProps, TableColumn } from '@/types/portfolioView'
import PortfolioTableRow from './PortfolioTableRow'
import { useResponsiveColumns } from '@/hooks/usePortfolioView'
import { getAlignmentClasses, getResponsiveVisibilityClasses } from '@/utils/tableColumns'

/**
 * PortfolioTable component for displaying portfolios in tabular format
 */
const PortfolioTable: React.FC<PortfolioTableProps> = ({
  portfolios,
  columns,
  loading = false,
  sortBy,
  sortOrder = 'asc',
  onSort,
  onPortfolioClick,
  onPortfolioDelete,
  showActions = true,
  className = '',
  emptyMessage = 'No portfolios to display'
}) => {
  // ============================================================================
  // RESPONSIVE COLUMN MANAGEMENT
  // ============================================================================

  const { visibleColumns, viewport, isMobile } = useResponsiveColumns(columns)

  // ============================================================================
  // SORTING FUNCTIONS
  // ============================================================================

  const handleSort = useCallback((column: keyof Portfolio) => {
    if (!onSort || loading) return

    const columnConfig = columns.find(col => col.key === column)
    if (!columnConfig?.sortable) return

    onSort(column)
  }, [onSort, columns, loading])

  const getSortIcon = useCallback((column: TableColumn) => {
    if (!column.sortable || !sortBy || sortBy !== column.key) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      )
    }

    return sortOrder === 'asc' ? (
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
      </svg>
    ) : (
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
      </svg>
    )
  }, [sortBy, sortOrder])

  // ============================================================================
  // RENDER FUNCTIONS
  // ============================================================================

  const renderTableHeader = useCallback(() => {
    return (
      <thead className="bg-gray-50 dark:bg-gray-800">
        <tr>
          {visibleColumns.map((column) => {
            const isActive = sortBy === column.key
            const canSort = column.sortable && onSort && !loading

            return (
              <th
                key={column.key}
                scope="col"
                className={`
                  px-6 py-3 text-xs font-medium uppercase tracking-wider
                  ${getAlignmentClasses(column.align)}
                  ${getResponsiveVisibilityClasses(column, { mobile: { maxColumns: 3, hiddenColumns: [], scrollDirection: 'horizontal' }, tablet: { maxColumns: 4, hiddenColumns: [] } })}
                  ${canSort ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 select-none' : ''}
                  ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}
                `.trim()}
                style={column.width ? { width: column.width, minWidth: column.width } : undefined}
                onClick={canSort ? () => handleSort(column.key) : undefined}
                onKeyDown={canSort ? (e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    handleSort(column.key)
                  }
                } : undefined}
                tabIndex={canSort ? 0 : -1}
                role={canSort ? 'button' : 'columnheader'}
                aria-sort={isActive ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}
                aria-label={canSort ? `Sort by ${column.label} ${isActive ? (sortOrder === 'asc' ? 'descending' : 'ascending') : 'ascending'}` : column.label}
              >
                <div className="flex items-center space-x-1">
                  <span>{column.label}</span>
                  {canSort && (
                    <span role="img" aria-hidden="true" className="flex-shrink-0">
                      {getSortIcon(column)}
                    </span>
                  )}
                </div>
              </th>
            )
          })}

          {/* Actions Column Header */}
          {showActions && (
            <th
              scope="col"
              className="px-6 py-3 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider text-right"
            >
              Actions
            </th>
          )}
        </tr>
      </thead>
    )
  }, [visibleColumns, sortBy, sortOrder, onSort, loading, showActions, handleSort, getSortIcon])

  const renderSkeletonRows = useCallback(() => {
    return Array.from({ length: 3 }, (_, index) => (
      <tr key={`skeleton-${index}`} data-testid="table-skeleton-row">
        {visibleColumns.map((column) => (
          <td key={column.key} className="px-6 py-4 whitespace-nowrap">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-full"></div>
            </div>
          </td>
        ))}
        {showActions && (
          <td className="px-6 py-4 whitespace-nowrap text-right">
            <div className="animate-pulse flex space-x-2 justify-end">
              <div className="h-6 w-12 bg-gray-300 dark:bg-gray-600 rounded"></div>
              <div className="h-6 w-12 bg-gray-300 dark:bg-gray-600 rounded"></div>
              <div className="h-6 w-16 bg-gray-300 dark:bg-gray-600 rounded"></div>
            </div>
          </td>
        )}
      </tr>
    ))
  }, [visibleColumns, showActions])

  const renderTableBody = useCallback(() => {
    if (loading) {
      return (
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {renderSkeletonRows()}
        </tbody>
      )
    }

    if (portfolios.length === 0) {
      return (
        <tbody className="bg-white dark:bg-gray-900">
          <tr>
            <td
              colSpan={visibleColumns.length + (showActions ? 1 : 0)}
              className="px-6 py-12 text-center text-gray-500 dark:text-gray-400"
            >
              <div className="flex flex-col items-center">
                <svg
                  className="w-12 h-12 mb-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
                <p className="text-lg font-medium">{emptyMessage}</p>
              </div>
            </td>
          </tr>
        </tbody>
      )
    }

    return (
      <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
        {portfolios.map((portfolio) => (
          <PortfolioTableRow
            key={portfolio.id}
            portfolio={portfolio}
            columns={visibleColumns}
            onClick={onPortfolioClick}
            onDelete={onPortfolioDelete}
            showActions={showActions}
          />
        ))}
      </tbody>
    )
  }, [
    loading,
    portfolios,
    visibleColumns,
    showActions,
    onPortfolioClick,
    onPortfolioDelete,
    emptyMessage,
    renderSkeletonRows
  ])

  // ============================================================================
  // CSS CLASSES
  // ============================================================================

  const getTableClasses = () => {
    const baseClasses = 'min-w-full divide-y divide-gray-200 dark:divide-gray-700'
    const responsiveClasses = isMobile
      ? 'text-sm'
      : 'text-sm'

    return `${baseClasses} ${responsiveClasses}`
  }

  const getContainerClasses = () => {
    const baseClasses = `
      bg-white dark:bg-gray-900 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700
      ${className}
    `.trim()

    const responsiveClasses = isMobile
      ? 'overflow-x-auto -webkit-overflow-scrolling-touch'
      : 'overflow-hidden'

    return `${baseClasses} ${responsiveClasses}`
  }

  // ============================================================================
  // EARLY RETURNS
  // ============================================================================

  if (portfolios.length === 0 && !loading) {
    return (
      <div className="text-center py-12">
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-12 border-2 border-dashed border-gray-300 dark:border-gray-600">
          <div className="mx-auto w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-4">
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <p className="text-xl font-semibold text-gray-900 dark:text-white mb-2">{emptyMessage}</p>
        </div>
      </div>
    )
  }

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <div className={getContainerClasses()}>
      <div className="overflow-hidden">
        <table
          role="table"
          aria-label="Portfolios table"
          className={getTableClasses()}
        >
          {renderTableHeader()}
          {renderTableBody()}
        </table>
      </div>

      {/* Screen Reader Status */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {loading
          ? 'Loading portfolios...'
          : `Showing ${portfolios.length} portfolio${portfolios.length === 1 ? '' : 's'} in table view`
        }
      </div>
    </div>
  )
}

export default PortfolioTable