// Table Column Configuration Utilities - Feature 004: Tile/Table View Toggle
// Utilities for managing portfolio table column configuration and formatting

import { Portfolio } from '@/types/portfolio'
import { TableColumn, ResponsiveConfig } from '@/types/portfolioView'
import { getRelativeTime } from '@/utils/timezone'

// ============================================================================
// DEFAULT TABLE COLUMN CONFIGURATIONS
// ============================================================================

/**
 * Default table columns for portfolio display
 */
export const DEFAULT_TABLE_COLUMNS: TableColumn[] = [
  {
    key: 'name',
    label: 'Portfolio Name',
    visible: true,
    sortable: true,
    align: 'left',
    priority: 1,
    width: '200px'
  },
  {
    key: 'total_value',
    label: 'Total Value',
    visible: true,
    sortable: true,
    align: 'right',
    priority: 2,
    formatter: (value: string) => {
      const num = parseFloat(value || '0')
      return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    }
  },
  {
    key: 'daily_change',
    label: 'Daily Change',
    visible: true,
    sortable: true,
    align: 'right',
    priority: 3,
    formatter: (value: string, portfolio: Portfolio) => {
      const change = parseFloat(value || '0')
      const changePercent = parseFloat(portfolio.daily_change_percent || '0')
      const sign = change >= 0 ? '+' : ''
      const formattedChange = `${sign}$${Math.abs(change).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      const formattedPercent = `(${changePercent.toFixed(2)}%)`
      return `${formattedChange} ${formattedPercent}`
    }
  },
  {
    key: 'unrealized_gain_loss',
    label: 'Unrealized P&L',
    visible: true,
    sortable: true,
    align: 'right',
    priority: 4,
    formatter: (value: string, portfolio: Portfolio) => {
      const pnl = parseFloat(value || '0')
      const pnlPercent = parseFloat(portfolio.unrealized_gain_loss_percent || '0')
      const sign = pnl >= 0 ? '+' : ''
      const formattedPnl = `${sign}$${Math.abs(pnl).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      const formattedPercent = `(${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}%)`
      return `${formattedPnl} ${formattedPercent}`
    }
  },
  {
    key: 'created_at',
    label: 'Created',
    visible: true,
    sortable: true,
    align: 'center',
    priority: 5,
    formatter: (value: string) => {
      return new Date(value).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }
  },
  {
    key: 'price_last_updated',
    label: 'Last Updated',
    visible: true,
    sortable: false,
    align: 'center',
    priority: 6,
    formatter: (value: string, portfolio: Portfolio) => {
      // Use price_last_updated if available, otherwise fall back to updated_at
      const timestamp = value || portfolio.updated_at
      return timestamp ? getRelativeTime(timestamp) : '—'
    }
  }
]

/**
 * Default responsive configuration
 */
export const DEFAULT_RESPONSIVE_CONFIG: ResponsiveConfig = {
  mobile: {
    maxColumns: 3,
    hiddenColumns: ['unrealized_gain_loss', 'created_at', 'price_last_updated'],
    scrollDirection: 'horizontal'
  },
  tablet: {
    maxColumns: 4,
    hiddenColumns: ['created_at', 'price_last_updated']
  }
}

// ============================================================================
// COLUMN UTILITY FUNCTIONS
// ============================================================================

/**
 * Gets visible columns based on current responsive breakpoint
 */
export const getVisibleColumns = (
  columns: TableColumn[],
  responsive: ResponsiveConfig,
  viewport: 'mobile' | 'tablet' | 'desktop'
): TableColumn[] => {
  if (viewport === 'desktop') {
    return columns.filter(col => col.visible)
  }

  const config = viewport === 'mobile' ? responsive.mobile : responsive.tablet
  const hiddenKeys = config.hiddenColumns

  return columns
    .filter(col => col.visible && !hiddenKeys.includes(col.key))
    .sort((a, b) => a.priority - b.priority)
    .slice(0, config.maxColumns)
}

/**
 * Determines current viewport breakpoint
 */
export const getViewportBreakpoint = (): 'mobile' | 'tablet' | 'desktop' => {
  if (typeof window === 'undefined') return 'desktop'

  const width = window.innerWidth
  if (width < 768) return 'mobile'
  if (width < 1024) return 'tablet'
  return 'desktop'
}

/**
 * Sorts columns by priority for responsive display
 */
export const sortColumnsByPriority = (columns: TableColumn[]): TableColumn[] => {
  return [...columns].sort((a, b) => a.priority - b.priority)
}

/**
 * Validates table column configuration
 */
export const validateColumns = (columns: TableColumn[]): { valid: boolean; errors: string[] } => {
  const errors: string[] = []

  if (!Array.isArray(columns)) {
    errors.push('Columns must be an array')
    return { valid: false, errors }
  }

  if (columns.length === 0) {
    errors.push('At least one column is required')
    return { valid: false, errors }
  }

  // Check for required fields
  columns.forEach((column, index) => {
    if (!column.key || typeof column.key !== 'string') {
      errors.push(`Column ${index}: 'key' is required and must be a string`)
    }

    if (!column.label || typeof column.label !== 'string') {
      errors.push(`Column ${index}: 'label' is required and must be a string`)
    }

    if (typeof column.visible !== 'boolean') {
      errors.push(`Column ${index}: 'visible' must be a boolean`)
    }

    if (typeof column.sortable !== 'boolean') {
      errors.push(`Column ${index}: 'sortable' must be a boolean`)
    }

    if (!['left', 'center', 'right'].includes(column.align)) {
      errors.push(`Column ${index}: 'align' must be 'left', 'center', or 'right'`)
    }

    if (typeof column.priority !== 'number' || column.priority < 1) {
      errors.push(`Column ${index}: 'priority' must be a positive number`)
    }
  })

  // Check for duplicate priorities
  const priorities = columns.map(col => col.priority)
  const duplicates = priorities.filter((priority, index) => priorities.indexOf(priority) !== index)
  if (duplicates.length > 0) {
    errors.push(`Duplicate priorities found: ${duplicates.join(', ')}`)
  }

  // Check for duplicate keys
  const keys = columns.map(col => col.key)
  const duplicateKeys = keys.filter((key, index) => keys.indexOf(key) !== index)
  if (duplicateKeys.length > 0) {
    errors.push(`Duplicate column keys found: ${duplicateKeys.join(', ')}`)
  }

  return { valid: errors.length === 0, errors }
}

/**
 * Creates a deep copy of column configuration
 */
export const cloneColumns = (columns: TableColumn[]): TableColumn[] => {
  return columns.map(col => ({
    ...col,
    formatter: col.formatter // Functions are preserved by reference
  }))
}

/**
 * Merges user customizations with default columns
 */
export const mergeColumnCustomizations = (
  defaultColumns: TableColumn[],
  customizations: Partial<TableColumn>[]
): TableColumn[] => {
  const result = cloneColumns(defaultColumns)

  customizations.forEach(customization => {
    const index = result.findIndex(col => col.key === customization.key)
    if (index !== -1) {
      result[index] = {
        ...result[index],
        ...customization,
        // Preserve formatter unless explicitly overridden
        formatter: customization.formatter || result[index].formatter
      }
    }
  })

  return result
}

// ============================================================================
// FORMATTING UTILITIES
// ============================================================================

/**
 * Formats currency values with proper sign and locale
 */
export const formatCurrency = (
  value: string | number,
  options: {
    showSign?: boolean
    showPlusSign?: boolean
    minimumFractionDigits?: number
    maximumFractionDigits?: number
  } = {}
): string => {
  const {
    showSign = false,
    showPlusSign = false,
    minimumFractionDigits = 2,
    maximumFractionDigits = 2
  } = options

  const num = typeof value === 'string' ? parseFloat(value || '0') : value

  if (isNaN(num)) return '—'

  const absValue = Math.abs(num)
  const formattedValue = absValue.toLocaleString('en-US', {
    minimumFractionDigits,
    maximumFractionDigits
  })

  if (!showSign) {
    return `$${formattedValue}`
  }

  if (num > 0 && showPlusSign) {
    return `+$${formattedValue}`
  }

  if (num < 0) {
    return `-$${formattedValue}`
  }

  return `$${formattedValue}`
}

/**
 * Formats percentage values with proper sign
 */
export const formatPercentage = (
  value: string | number,
  options: {
    showPlusSign?: boolean
    minimumFractionDigits?: number
    maximumFractionDigits?: number
  } = {}
): string => {
  const {
    showPlusSign = false,
    minimumFractionDigits = 2,
    maximumFractionDigits = 2
  } = options

  const num = typeof value === 'string' ? parseFloat(value || '0') : value

  if (isNaN(num)) return '—'

  const formattedValue = num.toFixed(maximumFractionDigits)

  if (num > 0 && showPlusSign) {
    return `+${formattedValue}%`
  }

  return `${formattedValue}%`
}

/**
 * Gets CSS classes for table column alignment
 */
export const getAlignmentClasses = (align: 'left' | 'center' | 'right'): string => {
  switch (align) {
    case 'left':
      return 'text-left'
    case 'center':
      return 'text-center'
    case 'right':
      return 'text-right'
    default:
      return 'text-left'
  }
}

/**
 * Gets CSS classes for responsive column visibility
 */
export const getResponsiveVisibilityClasses = (
  column: TableColumn,
  responsive: ResponsiveConfig
): string => {
  const classes: string[] = []

  // Hide on mobile if in mobile hidden columns
  if (responsive.mobile.hiddenColumns.includes(column.key)) {
    classes.push('hidden md:table-cell')
  }

  // Hide on tablet if in tablet hidden columns
  if (responsive.tablet.hiddenColumns.includes(column.key)) {
    classes.push('hidden lg:table-cell')
  }

  return classes.join(' ')
}

/**
 * Creates column width style object
 */
export const getColumnWidthStyle = (column: TableColumn): React.CSSProperties => {
  if (!column.width) return {}

  return {
    width: column.width,
    minWidth: column.width,
    maxWidth: column.width
  }
}