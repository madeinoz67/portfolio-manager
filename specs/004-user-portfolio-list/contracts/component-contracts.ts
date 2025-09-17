// Component Contracts for Portfolio List View Enhancement
// These TypeScript interfaces define the contracts for all components in the feature

import { Portfolio } from '@/types/portfolio'

// ============================================================================
// VIEW TOGGLE COMPONENT CONTRACT
// ============================================================================

export interface ViewToggleProps {
  /** Current view mode */
  viewMode: 'tiles' | 'table'
  /** Callback fired when view mode changes */
  onViewModeChange: (viewMode: 'tiles' | 'table') => void
  /** Optional CSS classes */
  className?: string
  /** Disabled state */
  disabled?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
}

export interface ViewToggleEvents {
  /** Emitted when tiles view is selected */
  onTilesSelected: () => void
  /** Emitted when table view is selected */
  onTableSelected: () => void
}

// ============================================================================
// PORTFOLIO TABLE COMPONENT CONTRACT
// ============================================================================

export interface TableColumn {
  /** Portfolio property key to display */
  key: keyof Portfolio
  /** Column header label */
  label: string
  /** Whether column is visible */
  visible: boolean
  /** Whether column supports sorting */
  sortable: boolean
  /** Column width (CSS value) */
  width?: string
  /** Text alignment */
  align: 'left' | 'center' | 'right'
  /** Display priority for responsive design (1 = highest) */
  priority: number
  /** Optional value formatter function */
  formatter?: (value: any, portfolio: Portfolio) => string | React.ReactNode
}

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

export interface PortfolioTableEvents {
  /** Emitted when portfolio row is clicked */
  onRowClick: (portfolio: Portfolio, event: React.MouseEvent) => void
  /** Emitted when sort column changes */
  onSortChange: (column: keyof Portfolio, order: 'asc' | 'desc') => void
  /** Emitted when action button is clicked */
  onAction: (action: 'view' | 'edit' | 'delete' | 'add-trade', portfolio: Portfolio) => void
}

// ============================================================================
// PORTFOLIO VIEW CONTAINER CONTRACT
// ============================================================================

export interface PortfolioViewContainerProps {
  /** Array of portfolios to display */
  portfolios: Portfolio[]
  /** Loading state */
  loading?: boolean
  /** Error message if any */
  error?: string
  /** Callback for portfolio creation */
  onCreatePortfolio?: (portfolioData: any) => Promise<boolean>
  /** Callback when portfolio is deleted */
  onPortfolioDeleted?: () => void
  /** Initial view mode */
  initialViewMode?: 'tiles' | 'table'
  /** Show create portfolio form */
  showCreateForm?: boolean
}

export interface PortfolioViewState {
  /** Current view mode */
  viewMode: 'tiles' | 'table'
  /** Table configuration */
  tableConfig: {
    columns: TableColumn[]
    sortable: boolean
  }
  /** Last updated timestamp */
  lastUpdated: Date
}

// ============================================================================
// RESPONSIVE CONFIGURATION CONTRACT
// ============================================================================

export interface ResponsiveConfig {
  mobile: {
    /** Maximum columns to show on mobile */
    maxColumns: number
    /** Columns to hide on mobile (by key) */
    hiddenColumns: (keyof Portfolio)[]
    /** Scroll direction for overflow */
    scrollDirection: 'horizontal' | 'vertical'
  }
  tablet: {
    /** Maximum columns to show on tablet */
    maxColumns: number
    /** Columns to hide on tablet (by key) */
    hiddenColumns: (keyof Portfolio)[]
  }
}

// ============================================================================
// HOOK CONTRACTS
// ============================================================================

export interface UsePortfolioViewReturn {
  /** Current view mode */
  viewMode: 'tiles' | 'table'
  /** Table column configuration */
  tableColumns: TableColumn[]
  /** Function to toggle between view modes */
  toggleViewMode: () => void
  /** Function to set specific view mode */
  setViewMode: (mode: 'tiles' | 'table') => void
  /** Function to update table column configuration */
  updateTableColumns: (columns: TableColumn[]) => void
  /** Function to reset to default configuration */
  resetConfiguration: () => void
  /** Whether user preferences are loaded */
  isLoaded: boolean
}

// ============================================================================
// PERSISTENCE CONTRACT
// ============================================================================

export interface PersistedViewState {
  /** View mode preference */
  viewMode: 'tiles' | 'table'
  /** Customized table columns (only modified ones) */
  tableColumns?: Partial<TableColumn>[]
  /** Timestamp when preferences were saved */
  timestamp: number
  /** Version for migration compatibility */
  version: string
}

export interface ViewPreferencesService {
  /** Load user preferences from storage */
  loadPreferences(): PersistedViewState | null
  /** Save user preferences to storage */
  savePreferences(state: PersistedViewState): void
  /** Clear all saved preferences */
  clearPreferences(): void
  /** Get default configuration */
  getDefaultConfiguration(): PortfolioViewState
}

// ============================================================================
// ERROR HANDLING CONTRACTS
// ============================================================================

export interface ViewToggleError {
  type: 'TOGGLE_ERROR'
  message: string
  originalError?: Error
}

export interface TableRenderError {
  type: 'TABLE_RENDER_ERROR'
  message: string
  failedColumn?: keyof Portfolio
  originalError?: Error
}

export type PortfolioViewError = ViewToggleError | TableRenderError

// ============================================================================
// ACCESSIBILITY CONTRACTS
// ============================================================================

export interface AccessibilityProps {
  /** ARIA label for screen readers */
  'aria-label'?: string
  /** ARIA described by reference */
  'aria-describedby'?: string
  /** Tab index for keyboard navigation */
  tabIndex?: number
  /** Role for semantic markup */
  role?: string
}

export interface TableAccessibilityProps extends AccessibilityProps {
  /** Column headers mapping for screen readers */
  columnHeaders: Record<keyof Portfolio, string>
  /** Row description for screen readers */
  rowDescriptor?: (portfolio: Portfolio) => string
  /** Sortable column announcements */
  sortAnnouncement?: (column: keyof Portfolio, order: 'asc' | 'desc') => string
}

// ============================================================================
// VALIDATION CONTRACTS
// ============================================================================

export interface ValidationResult {
  /** Whether validation passed */
  valid: boolean
  /** Error messages if validation failed */
  errors: string[]
  /** Warnings (non-blocking) */
  warnings: string[]
}

export interface ColumnConfigValidator {
  /** Validate table column configuration */
  validateColumns(columns: TableColumn[]): ValidationResult
  /** Validate individual column */
  validateColumn(column: TableColumn): ValidationResult
  /** Validate responsive configuration */
  validateResponsiveConfig(config: ResponsiveConfig): ValidationResult
}

// ============================================================================
// PERFORMANCE CONTRACTS
// ============================================================================

export interface PerformanceMetrics {
  /** Time to render view toggle */
  toggleRenderTime: number
  /** Time to render table */
  tableRenderTime: number
  /** Number of portfolios rendered */
  portfolioCount: number
  /** Memory usage estimate */
  memoryUsage?: number
}