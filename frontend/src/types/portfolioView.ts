// Portfolio View Types - Feature 004: Tile/Table View Toggle
// TypeScript type definitions for portfolio view state management

import { Portfolio } from './portfolio'

// ============================================================================
// VIEW MODE TYPES
// ============================================================================

/**
 * Available view modes for portfolio display
 */
export type ViewMode = 'tiles' | 'table'

/**
 * Portfolio view state container
 */
export interface PortfolioViewState {
  /** Current display mode */
  viewMode: ViewMode
  /** Table-specific configuration */
  tableConfig: TableConfig
  /** Last updated timestamp for cache validation */
  lastUpdated: Date
}

// ============================================================================
// TABLE CONFIGURATION TYPES
// ============================================================================

/**
 * Configuration for table view display
 */
export interface TableConfig {
  /** Column definitions */
  columns: TableColumn[]
  /** Whether table supports sorting */
  sortable: boolean
  /** Responsive behavior configuration */
  responsive: ResponsiveConfig
}

/**
 * Individual table column configuration
 */
export interface TableColumn {
  /** Portfolio property key to display */
  key: keyof Portfolio
  /** Column header label */
  label: string
  /** Whether column is visible */
  visible: boolean
  /** Whether column supports sorting */
  sortable: boolean
  /** CSS width value (optional) */
  width?: string
  /** Text alignment within column */
  align: 'left' | 'center' | 'right'
  /** Display priority for responsive design (1 = highest priority) */
  priority: number
  /** Optional value formatter function */
  formatter?: (value: any, portfolio: Portfolio) => string | React.ReactNode
}

/**
 * Responsive behavior configuration for different screen sizes
 */
export interface ResponsiveConfig {
  /** Mobile screen configuration (< 768px) */
  mobile: {
    /** Maximum number of columns to show */
    maxColumns: number
    /** Column keys to hide on mobile */
    hiddenColumns: (keyof Portfolio)[]
    /** Scroll direction for overflow content */
    scrollDirection: 'horizontal' | 'vertical'
  }
  /** Tablet screen configuration (768px - 1024px) */
  tablet: {
    /** Maximum number of columns to show */
    maxColumns: number
    /** Column keys to hide on tablet */
    hiddenColumns: (keyof Portfolio)[]
  }
}

// ============================================================================
// PERSISTENCE TYPES
// ============================================================================

/**
 * Persisted view state for localStorage
 */
export interface PersistedViewState {
  /** View mode preference */
  viewMode: ViewMode
  /** Customized table columns (only modified ones) */
  tableColumns?: Partial<TableColumn>[]
  /** Timestamp when preferences were saved */
  timestamp: number
  /** Version for migration compatibility */
  version: string
}

// ============================================================================
// COMPONENT PROP TYPES
// ============================================================================

/**
 * Props for ViewToggle component
 */
export interface ViewToggleProps {
  /** Current view mode */
  viewMode: ViewMode
  /** Callback fired when view mode changes */
  onViewModeChange: (viewMode: ViewMode) => void
  /** Optional CSS classes */
  className?: string
  /** Disabled state */
  disabled?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
}

/**
 * Props for PortfolioTable component
 */
export interface PortfolioTableProps {
  /** Array of portfolios to display */
  portfolios: Portfolio[]
  /** Column configuration */
  columns: TableColumn[]
  /** Loading state */
  loading?: boolean
  /** Current sort configuration */
  sortBy?: keyof Portfolio
  /** Sort order */
  sortOrder?: 'asc' | 'desc'
  /** Callback when column header is clicked for sorting */
  onSort?: (column: keyof Portfolio) => void
  /** Callback when portfolio row is clicked */
  onPortfolioClick?: (portfolio: Portfolio) => void
  /** Callback when delete action is triggered */
  onPortfolioDelete?: (portfolio: Portfolio) => void
  /** Show action buttons in rows */
  showActions?: boolean
  /** Optional CSS classes */
  className?: string
  /** Empty state message */
  emptyMessage?: string
}

/**
 * Props for PortfolioTableRow component
 */
export interface PortfolioTableRowProps {
  /** Portfolio data for this row */
  portfolio: Portfolio
  /** Column definitions */
  columns: TableColumn[]
  /** Whether this row is selected/highlighted */
  selected?: boolean
  /** Row click handler */
  onClick?: (portfolio: Portfolio) => void
  /** Action handlers */
  onViewDetails?: (portfolio: Portfolio) => void
  onAddTrade?: (portfolio: Portfolio) => void
  onDelete?: (portfolio: Portfolio) => void
  /** Show action buttons */
  showActions?: boolean
}

// ============================================================================
// HOOK RETURN TYPES
// ============================================================================

/**
 * Return type for usePortfolioView hook
 */
export interface UsePortfolioViewReturn {
  /** Current view mode */
  viewMode: ViewMode
  /** Table column configuration */
  tableColumns: TableColumn[]
  /** Function to toggle between view modes */
  toggleViewMode: () => void
  /** Function to set specific view mode */
  setViewMode: (mode: ViewMode) => void
  /** Function to update table column configuration */
  updateTableColumns: (columns: TableColumn[]) => void
  /** Function to reset to default configuration */
  resetConfiguration: () => void
  /** Whether user preferences have been loaded */
  isLoaded: boolean
}

// ============================================================================
// ERROR TYPES
// ============================================================================

/**
 * View toggle specific error
 */
export interface ViewToggleError {
  type: 'TOGGLE_ERROR'
  message: string
  originalError?: Error
}

/**
 * Table rendering specific error
 */
export interface TableRenderError {
  type: 'TABLE_RENDER_ERROR'
  message: string
  failedColumn?: keyof Portfolio
  originalError?: Error
}

/**
 * Union type for all portfolio view errors
 */
export type PortfolioViewError = ViewToggleError | TableRenderError

// ============================================================================
// VALIDATION TYPES
// ============================================================================

/**
 * Validation result for configuration
 */
export interface ValidationResult {
  /** Whether validation passed */
  valid: boolean
  /** Error messages if validation failed */
  errors: string[]
  /** Warnings (non-blocking) */
  warnings: string[]
}