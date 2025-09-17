// usePortfolioView Hook - Feature 004: Tile/Table View Toggle
// Custom React hook for managing portfolio view state and persistence

import { useState, useEffect, useCallback, useMemo } from 'react'
import { ViewMode, UsePortfolioViewReturn, PersistedViewState, TableColumn } from '@/types/portfolioView'
import { DEFAULT_TABLE_COLUMNS, DEFAULT_RESPONSIVE_CONFIG, validateColumns, mergeColumnCustomizations } from '@/utils/tableColumns'

// ============================================================================
// CONSTANTS
// ============================================================================

const STORAGE_KEY = 'portfolio-view-preferences'
const CURRENT_VERSION = '1.0.0'
const EXPIRATION_DAYS = 30
const SAVE_DEBOUNCE_MS = 300

// ============================================================================
// PERSISTENCE UTILITIES
// ============================================================================

/**
 * Safely gets data from localStorage
 */
const getStoredData = (): PersistedViewState | null => {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return null
    }

    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return null

    const parsed = JSON.parse(stored)

    // Check expiration
    const age = Date.now() - parsed.timestamp
    const maxAge = EXPIRATION_DAYS * 24 * 60 * 60 * 1000
    if (age > maxAge) {
      localStorage.removeItem(STORAGE_KEY)
      return null
    }

    return parsed
  } catch (error) {
    console.warn('Failed to load portfolio view preferences:', error)
    return null
  }
}

/**
 * Safely saves data to localStorage
 */
const saveStoredData = (data: PersistedViewState): void => {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (error) {
    console.warn('Failed to save portfolio view preferences:', error)
  }
}

/**
 * Validates and migrates old data formats
 */
const migrateStoredData = (data: any): PersistedViewState | null => {
  if (!data || typeof data !== 'object') return null

  // Ensure required fields exist
  if (!data.viewMode || !['tiles', 'table'].includes(data.viewMode)) {
    return null
  }

  // Migrate from old format if needed
  const migrated: PersistedViewState = {
    viewMode: data.viewMode,
    tableColumns: data.tableColumns || data.columns, // Handle old 'columns' field
    timestamp: typeof data.timestamp === 'number' ? data.timestamp : Date.now(),
    version: data.version || '1.0.0'
  }

  return migrated
}

// ============================================================================
// MAIN HOOK IMPLEMENTATION
// ============================================================================

/**
 * Custom hook for managing portfolio view state and preferences
 */
export const usePortfolioView = (): UsePortfolioViewReturn => {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================

  const [viewMode, setViewModeState] = useState<ViewMode>('tiles')
  const [tableColumns, setTableColumnsState] = useState<TableColumn[]>(DEFAULT_TABLE_COLUMNS)
  const [isLoaded, setIsLoaded] = useState(false)
  const [saveTimeout, setSaveTimeout] = useState<NodeJS.Timeout | null>(null)

  // ============================================================================
  // INITIALIZATION
  // ============================================================================

  useEffect(() => {
    const loadPersistedState = () => {
      const stored = getStoredData()

      if (stored) {
        const migrated = migrateStoredData(stored)
        if (migrated) {
          setViewModeState(migrated.viewMode)

          if (migrated.tableColumns) {
            const mergedColumns = mergeColumnCustomizations(
              DEFAULT_TABLE_COLUMNS,
              migrated.tableColumns
            )
            const validation = validateColumns(mergedColumns)
            if (validation.valid) {
              setTableColumnsState(mergedColumns)
            }
          }
        }
      }

      setIsLoaded(true)
    }

    loadPersistedState()
  }, [])

  // ============================================================================
  // PERSISTENCE FUNCTIONS
  // ============================================================================

  const debouncedSave = useCallback((newViewMode: ViewMode, newColumns: TableColumn[]) => {
    // Clear existing timeout
    if (saveTimeout) {
      clearTimeout(saveTimeout)
    }

    // Set new debounced save
    const timeout = setTimeout(() => {
      const dataToSave: PersistedViewState = {
        viewMode: newViewMode,
        tableColumns: newColumns.map(col => ({
          key: col.key,
          label: col.label,
          visible: col.visible,
          sortable: col.sortable,
          width: col.width,
          align: col.align,
          priority: col.priority
          // Note: formatter functions are not persisted
        })),
        timestamp: Date.now(),
        version: CURRENT_VERSION
      }

      saveStoredData(dataToSave)
    }, SAVE_DEBOUNCE_MS)

    setSaveTimeout(timeout)
  }, [saveTimeout])

  // ============================================================================
  // PUBLIC API FUNCTIONS
  // ============================================================================

  const toggleViewMode = useCallback(() => {
    const newMode: ViewMode = viewMode === 'tiles' ? 'table' : 'tiles'
    setViewModeState(newMode)
    debouncedSave(newMode, tableColumns)
  }, [viewMode, tableColumns, debouncedSave])

  const setViewMode = useCallback((mode: ViewMode) => {
    if (!['tiles', 'table'].includes(mode)) {
      console.warn(`Invalid view mode: ${mode}. Must be 'tiles' or 'table'`)
      return
    }

    if (mode !== viewMode) {
      setViewModeState(mode)
      debouncedSave(mode, tableColumns)
    }
  }, [viewMode, tableColumns, debouncedSave])

  const updateTableColumns = useCallback((newColumns: TableColumn[]) => {
    const validation = validateColumns(newColumns)

    if (!validation.valid) {
      console.warn('Invalid table columns configuration:', validation.errors)
      return
    }

    setTableColumnsState(newColumns)
    debouncedSave(viewMode, newColumns)
  }, [viewMode, debouncedSave])

  const resetConfiguration = useCallback(() => {
    setViewModeState('tiles')
    setTableColumnsState(DEFAULT_TABLE_COLUMNS)

    // Clear stored data
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.removeItem(STORAGE_KEY)
      }
    } catch (error) {
      console.warn('Failed to clear stored preferences:', error)
    }
  }, [])

  // ============================================================================
  // CROSS-TAB SYNCHRONIZATION
  // ============================================================================

  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key !== STORAGE_KEY) return

      if (event.newValue) {
        try {
          const newData = JSON.parse(event.newValue)
          const migrated = migrateStoredData(newData)

          if (migrated) {
            setViewModeState(migrated.viewMode)

            if (migrated.tableColumns) {
              const mergedColumns = mergeColumnCustomizations(
                DEFAULT_TABLE_COLUMNS,
                migrated.tableColumns
              )
              const validation = validateColumns(mergedColumns)
              if (validation.valid) {
                setTableColumnsState(mergedColumns)
              }
            }
          }
        } catch (error) {
          console.warn('Failed to sync preferences from other tab:', error)
        }
      }
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('storage', handleStorageChange)
      return () => window.removeEventListener('storage', handleStorageChange)
    }
  }, [])

  // ============================================================================
  // CLEANUP
  // ============================================================================

  useEffect(() => {
    return () => {
      if (saveTimeout) {
        clearTimeout(saveTimeout)
      }
    }
  }, [saveTimeout])

  // ============================================================================
  // RETURN MEMOIZED API
  // ============================================================================

  return useMemo(() => ({
    viewMode,
    tableColumns,
    toggleViewMode,
    setViewMode,
    updateTableColumns,
    resetConfiguration,
    isLoaded
  }), [
    viewMode,
    tableColumns,
    toggleViewMode,
    setViewMode,
    updateTableColumns,
    resetConfiguration,
    isLoaded
  ])
}

// ============================================================================
// ADDITIONAL UTILITY HOOKS
// ============================================================================

/**
 * Hook for responsive table column visibility
 */
export const useResponsiveColumns = (columns: TableColumn[]) => {
  const [viewport, setViewport] = useState<'mobile' | 'tablet' | 'desktop'>('desktop')

  useEffect(() => {
    const updateViewport = () => {
      if (typeof window === 'undefined') return

      const width = window.innerWidth
      if (width < 768) {
        setViewport('mobile')
      } else if (width < 1024) {
        setViewport('tablet')
      } else {
        setViewport('desktop')
      }
    }

    updateViewport()
    window.addEventListener('resize', updateViewport)
    window.addEventListener('orientationchange', updateViewport)

    return () => {
      window.removeEventListener('resize', updateViewport)
      window.removeEventListener('orientationchange', updateViewport)
    }
  }, [])

  const visibleColumns = useMemo(() => {
    if (viewport === 'desktop') {
      return columns.filter(col => col.visible)
    }

    const responsive = DEFAULT_RESPONSIVE_CONFIG
    const config = viewport === 'mobile' ? responsive.mobile : responsive.tablet
    const hiddenKeys = config.hiddenColumns

    return columns
      .filter(col => col.visible && !hiddenKeys.includes(col.key))
      .sort((a, b) => a.priority - b.priority)
      .slice(0, config.maxColumns)
  }, [columns, viewport])

  return {
    visibleColumns,
    viewport,
    isDesktop: viewport === 'desktop',
    isTablet: viewport === 'tablet',
    isMobile: viewport === 'mobile'
  }
}