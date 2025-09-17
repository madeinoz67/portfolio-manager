// usePortfolioView Hook Contract Tests - Feature 004: Tile/Table View Toggle
// These tests MUST FAIL before implementation (TDD Red phase)

import { renderHook, act } from '@testing-library/react'
import { usePortfolioView } from '@/hooks/usePortfolioView'
import { ViewMode, UsePortfolioViewReturn } from '@/types/portfolioView'
import {
  createMockTableColumns,
  createMockLocalStorage,
  createMockPersistedState,
  TEST_CONSTANTS
} from '@/__tests__/utils/portfolioViewTestUtils'

// Mock localStorage for testing
const mockLocalStorage = createMockLocalStorage()
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
})

describe('usePortfolioView Hook Contract', () => {
  beforeEach(() => {
    mockLocalStorage.clear()
    jest.clearAllMocks()
  })

  describe('Initial State', () => {
    it('should initialize with default tile view mode', () => {
      const { result } = renderHook(() => usePortfolioView())

      expect(result.current.viewMode).toBe('tiles')
      expect(result.current.isLoaded).toBe(true)
      expect(result.current.tableColumns).toEqual(expect.arrayContaining([
        expect.objectContaining({ key: 'name', label: expect.any(String) })
      ]))
    })

    it('should load persisted preferences from localStorage', () => {
      const persistedState = createMockPersistedState({
        viewMode: 'table',
        timestamp: Date.now(),
        version: '1.0.0'
      })

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(persistedState))

      const { result } = renderHook(() => usePortfolioView())

      expect(result.current.viewMode).toBe('table')
      expect(result.current.isLoaded).toBe(true)
    })

    it('should handle corrupted localStorage data gracefully', () => {
      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, 'invalid-json')

      const { result } = renderHook(() => usePortfolioView())

      // Should fall back to default state
      expect(result.current.viewMode).toBe('tiles')
      expect(result.current.isLoaded).toBe(true)
    })

    it('should provide default table columns configuration', () => {
      const { result } = renderHook(() => usePortfolioView())

      const columns = result.current.tableColumns

      expect(columns).toHaveLength(expect.any(Number))
      expect(columns[0]).toHaveProperty('key')
      expect(columns[0]).toHaveProperty('label')
      expect(columns[0]).toHaveProperty('visible')
      expect(columns[0]).toHaveProperty('sortable')
      expect(columns[0]).toHaveProperty('priority')

      // Should include essential portfolio columns
      const columnKeys = columns.map(col => col.key)
      expect(columnKeys).toContain('name')
      expect(columnKeys).toContain('total_value')
      expect(columnKeys).toContain('daily_change')
    })
  })

  describe('View Mode Management', () => {
    it('should toggle between tiles and table view modes', () => {
      const { result } = renderHook(() => usePortfolioView())

      // Start with tiles
      expect(result.current.viewMode).toBe('tiles')

      // Toggle to table
      act(() => {
        result.current.toggleViewMode()
      })

      expect(result.current.viewMode).toBe('table')

      // Toggle back to tiles
      act(() => {
        result.current.toggleViewMode()
      })

      expect(result.current.viewMode).toBe('tiles')
    })

    it('should set specific view mode', () => {
      const { result } = renderHook(() => usePortfolioView())

      act(() => {
        result.current.setViewMode('table')
      })

      expect(result.current.viewMode).toBe('table')

      act(() => {
        result.current.setViewMode('tiles')
      })

      expect(result.current.viewMode).toBe('tiles')
    })

    it('should persist view mode changes to localStorage', () => {
      const { result } = renderHook(() => usePortfolioView())

      act(() => {
        result.current.setViewMode('table')
      })

      // Should save to localStorage
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        TEST_CONSTANTS.STORAGE_KEY,
        expect.stringContaining('"viewMode":"table"')
      )

      const savedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1])
      expect(savedData.viewMode).toBe('table')
      expect(savedData.timestamp).toBeCloseTo(Date.now(), -2) // Within 100ms
      expect(savedData.version).toBe('1.0.0')
    })

    it('should not persist invalid view modes', () => {
      const { result } = renderHook(() => usePortfolioView())

      // Try to set invalid view mode
      act(() => {
        // @ts-expect-error Testing invalid input
        result.current.setViewMode('invalid')
      })

      // Should remain unchanged and not persist
      expect(result.current.viewMode).toBe('tiles')
      expect(mockLocalStorage.setItem).not.toHaveBeenCalled()
    })
  })

  describe('Table Columns Management', () => {
    it('should update table columns configuration', () => {
      const { result } = renderHook(() => usePortfolioView())

      const newColumns = createMockTableColumns().slice(0, 3) // Only first 3 columns

      act(() => {
        result.current.updateTableColumns(newColumns)
      })

      expect(result.current.tableColumns).toEqual(newColumns)
    })

    it('should persist table column changes to localStorage', () => {
      const { result } = renderHook(() => usePortfolioView())

      const newColumns = createMockTableColumns().map(col => ({
        ...col,
        visible: col.key === 'name' || col.key === 'total_value' // Only show name and value
      }))

      act(() => {
        result.current.updateTableColumns(newColumns)
      })

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        TEST_CONSTANTS.STORAGE_KEY,
        expect.stringContaining('"tableColumns"')
      )

      const savedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1])
      expect(savedData.tableColumns).toBeDefined()
    })

    it('should validate table columns before updating', () => {
      const { result } = renderHook(() => usePortfolioView())

      const invalidColumns = [
        { key: 'invalid', label: '' } // Missing required fields
      ]

      act(() => {
        // @ts-expect-error Testing invalid input
        result.current.updateTableColumns(invalidColumns)
      })

      // Should not update with invalid columns
      expect(result.current.tableColumns).not.toEqual(invalidColumns)
    })

    it('should reset to default configuration', () => {
      const { result } = renderHook(() => usePortfolioView())

      // First modify the columns
      const modifiedColumns = createMockTableColumns().map(col => ({
        ...col,
        visible: false
      }))

      act(() => {
        result.current.updateTableColumns(modifiedColumns)
      })

      expect(result.current.tableColumns).toEqual(modifiedColumns)

      // Then reset
      act(() => {
        result.current.resetConfiguration()
      })

      // Should return to default state
      expect(result.current.viewMode).toBe('tiles')
      expect(result.current.tableColumns).not.toEqual(modifiedColumns)
      expect(result.current.tableColumns[0].visible).toBe(true) // Default should have visible columns
    })
  })

  describe('Persistence Integration', () => {
    it('should handle localStorage quota exceeded error', () => {
      const { result } = renderHook(() => usePortfolioView())

      // Mock localStorage.setItem to throw quota exceeded error
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('QuotaExceededError')
      })

      // Should not crash when localStorage is full
      expect(() => {
        act(() => {
          result.current.setViewMode('table')
        })
      }).not.toThrow()

      // View should still change even if persistence fails
      expect(result.current.viewMode).toBe('table')
    })

    it('should handle localStorage being unavailable', () => {
      // Mock localStorage to be undefined
      Object.defineProperty(window, 'localStorage', {
        value: undefined,
        writable: true
      })

      const { result } = renderHook(() => usePortfolioView())

      // Should still function without localStorage
      expect(result.current.viewMode).toBe('tiles')

      act(() => {
        result.current.toggleViewMode()
      })

      expect(result.current.viewMode).toBe('table')
    })

    it('should migrate old version data format', () => {
      const oldFormatData = {
        viewMode: 'table',
        // Missing version field - simulates old format
        timestamp: Date.now() - 86400000 // 24 hours old
      }

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(oldFormatData))

      const { result } = renderHook(() => usePortfolioView())

      // Should still load the view mode
      expect(result.current.viewMode).toBe('table')

      // Should update to new format on next save
      act(() => {
        result.current.setViewMode('tiles')
      })

      const savedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1])
      expect(savedData.version).toBe('1.0.0')
    })

    it('should expire old cached preferences', () => {
      const expiredState = createMockPersistedState({
        viewMode: 'table',
        timestamp: Date.now() - (30 * 24 * 60 * 60 * 1000), // 30 days old
        version: '1.0.0'
      })

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(expiredState))

      const { result } = renderHook(() => usePortfolioView())

      // Should fall back to default for expired data
      expect(result.current.viewMode).toBe('tiles')
    })
  })

  describe('Performance and Memory', () => {
    it('should not trigger unnecessary re-renders', () => {
      const { result, rerender } = renderHook(() => usePortfolioView())

      const firstRender = result.current
      rerender()
      const secondRender = result.current

      // Functions should be stable between renders (memoized)
      expect(firstRender.toggleViewMode).toBe(secondRender.toggleViewMode)
      expect(firstRender.setViewMode).toBe(secondRender.setViewMode)
      expect(firstRender.updateTableColumns).toBe(secondRender.updateTableColumns)
      expect(firstRender.resetConfiguration).toBe(secondRender.resetConfiguration)
    })

    it('should cleanup resources when unmounted', () => {
      const { unmount } = renderHook(() => usePortfolioView())

      // Should not throw when unmounting
      expect(() => unmount()).not.toThrow()
    })

    it('should handle rapid state changes efficiently', () => {
      const { result } = renderHook(() => usePortfolioView())

      // Rapidly toggle view mode
      act(() => {
        for (let i = 0; i < 10; i++) {
          result.current.toggleViewMode()
        }
      })

      // Should end up in correct final state
      expect(result.current.viewMode).toBe('tiles') // Even number of toggles

      // Should not spam localStorage calls
      expect(mockLocalStorage.setItem.mock.calls.length).toBeLessThan(11)
    })
  })

  describe('TypeScript Contract Compliance', () => {
    it('should return correct TypeScript types', () => {
      const { result } = renderHook(() => usePortfolioView())
      const hookReturn: UsePortfolioViewReturn = result.current

      // Type checks
      expect(typeof hookReturn.viewMode).toBe('string')
      expect(Array.isArray(hookReturn.tableColumns)).toBe(true)
      expect(typeof hookReturn.toggleViewMode).toBe('function')
      expect(typeof hookReturn.setViewMode).toBe('function')
      expect(typeof hookReturn.updateTableColumns).toBe('function')
      expect(typeof hookReturn.resetConfiguration).toBe('function')
      expect(typeof hookReturn.isLoaded).toBe('boolean')

      // ViewMode type constraint
      expect(['tiles', 'table']).toContain(hookReturn.viewMode)
    })

    it('should enforce table column structure', () => {
      const { result } = renderHook(() => usePortfolioView())

      result.current.tableColumns.forEach(column => {
        expect(column).toHaveProperty('key')
        expect(column).toHaveProperty('label')
        expect(column).toHaveProperty('visible')
        expect(column).toHaveProperty('sortable')
        expect(column).toHaveProperty('align')
        expect(column).toHaveProperty('priority')

        expect(typeof column.key).toBe('string')
        expect(typeof column.label).toBe('string')
        expect(typeof column.visible).toBe('boolean')
        expect(typeof column.sortable).toBe('boolean')
        expect(['left', 'center', 'right']).toContain(column.align)
        expect(typeof column.priority).toBe('number')
      })
    })
  })

  describe('Error Recovery', () => {
    it('should recover from localStorage corruption', () => {
      // First set valid data
      const validState = createMockPersistedState({ viewMode: 'table' })
      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(validState))

      const { result } = renderHook(() => usePortfolioView())
      expect(result.current.viewMode).toBe('table')

      // Corrupt the data
      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, 'corrupted-data')

      // Re-render should recover gracefully
      act(() => {
        result.current.resetConfiguration()
      })

      expect(result.current.viewMode).toBe('tiles')
    })

    it('should handle concurrent modifications', () => {
      const { result: hook1 } = renderHook(() => usePortfolioView())
      const { result: hook2 } = renderHook(() => usePortfolioView())

      // Simulate concurrent changes
      act(() => {
        hook1.current.setViewMode('table')
        hook2.current.setViewMode('tiles')
      })

      // Both hooks should be in consistent state
      expect(hook1.current.viewMode).toBe(hook2.current.viewMode)
    })
  })
})