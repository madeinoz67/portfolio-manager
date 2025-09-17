// Portfolio View Persistence Integration Tests - Feature 004: Tile/Table View Toggle
// These tests MUST FAIL before implementation (TDD Red phase)

import React from 'react'
import { renderHook, act } from '@testing-library/react'
import { usePortfolioView } from '@/hooks/usePortfolioView'
import { ViewMode, PersistedViewState } from '@/types/portfolioView'
import {
  createMockLocalStorage,
  createMockPersistedState,
  createMockTableColumns,
  TEST_CONSTANTS
} from '@/__tests__/utils/portfolioViewTestUtils'

// Mock localStorage for testing
const mockLocalStorage = createMockLocalStorage()
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
})

describe('Portfolio View Persistence Integration', () => {
  beforeEach(() => {
    mockLocalStorage.clear()
    jest.clearAllMocks()
  })

  describe('Initial Load Persistence', () => {
    it('should load default state when no persistence exists', () => {
      const { result } = renderHook(() => usePortfolioView())

      expect(result.current.viewMode).toBe('tiles')
      expect(result.current.isLoaded).toBe(true)
      expect(result.current.tableColumns).toHaveLength(expect.any(Number))
    })

    it('should load persisted view mode on initialization', () => {
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

    it('should load persisted table column configuration', () => {
      const customColumns = createMockTableColumns().map(col => ({
        ...col,
        visible: col.key === 'name' || col.key === 'total_value' // Only 2 columns visible
      }))

      const persistedState = createMockPersistedState({
        viewMode: 'table',
        tableColumns: customColumns,
        timestamp: Date.now(),
        version: '1.0.0'
      })

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(persistedState))

      const { result } = renderHook(() => usePortfolioView())

      expect(result.current.tableColumns).toEqual(
        expect.arrayContaining(customColumns)
      )

      // Should have only 2 visible columns
      const visibleColumns = result.current.tableColumns.filter(col => col.visible)
      expect(visibleColumns).toHaveLength(2)
    })

    it('should handle corrupted localStorage gracefully', () => {
      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, 'invalid-json-data')

      const { result } = renderHook(() => usePortfolioView())

      // Should fall back to defaults
      expect(result.current.viewMode).toBe('tiles')
      expect(result.current.isLoaded).toBe(true)
      expect(result.current.tableColumns).toHaveLength(expect.any(Number))
    })

    it('should handle partially corrupted data', () => {
      const partiallyCorrupted = {
        viewMode: 'table',
        // Missing required fields
        timestamp: 'invalid-timestamp',
        version: null
      }

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(partiallyCorrupted))

      const { result } = renderHook(() => usePortfolioView())

      // Should extract valid data and use defaults for invalid
      expect(result.current.viewMode).toBe('table') // Valid data preserved
      expect(result.current.isLoaded).toBe(true)
    })
  })

  describe('Save Persistence', () => {
    it('should persist view mode changes', () => {
      const { result } = renderHook(() => usePortfolioView())

      act(() => {
        result.current.setViewMode('table')
      })

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        TEST_CONSTANTS.STORAGE_KEY,
        expect.stringContaining('"viewMode":"table"')
      )

      const savedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1])
      expect(savedData.viewMode).toBe('table')
      expect(savedData.timestamp).toBeCloseTo(Date.now(), -2)
      expect(savedData.version).toBe('1.0.0')
    })

    it('should persist table column changes', () => {
      const { result } = renderHook(() => usePortfolioView())

      const modifiedColumns = createMockTableColumns().map(col => ({
        ...col,
        width: col.key === 'name' ? '300px' : undefined
      }))

      act(() => {
        result.current.updateTableColumns(modifiedColumns)
      })

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        TEST_CONSTANTS.STORAGE_KEY,
        expect.stringContaining('"tableColumns"')
      )

      const savedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1])
      expect(savedData.tableColumns).toBeDefined()
    })

    it('should debounce rapid changes to prevent localStorage spam', async () => {
      const { result } = renderHook(() => usePortfolioView())

      // Rapid changes
      act(() => {
        result.current.toggleViewMode()
        result.current.toggleViewMode()
        result.current.toggleViewMode()
        result.current.toggleViewMode()
      })

      // Should not save every single change
      expect(mockLocalStorage.setItem.mock.calls.length).toBeLessThan(4)
    })

    it('should handle localStorage quota exceeded error', () => {
      const { result } = renderHook(() => usePortfolioView())

      // Mock quota exceeded error
      mockLocalStorage.setItem.mockImplementation(() => {
        const error = new Error('QuotaExceededError')
        error.name = 'QuotaExceededError'
        throw error
      })

      // Should not crash when localStorage is full
      expect(() => {
        act(() => {
          result.current.setViewMode('table')
        })
      }).not.toThrow()

      // State should still update even if persistence fails
      expect(result.current.viewMode).toBe('table')
    })

    it('should handle localStorage being disabled/unavailable', () => {
      // Mock localStorage as unavailable
      Object.defineProperty(window, 'localStorage', {
        value: undefined,
        writable: true
      })

      const { result } = renderHook(() => usePortfolioView())

      // Should still function without localStorage
      expect(result.current.viewMode).toBe('tiles')

      act(() => {
        result.current.setViewMode('table')
      })

      expect(result.current.viewMode).toBe('table')
    })
  })

  describe('Version Migration', () => {
    it('should migrate old version data format', () => {
      const oldVersionData = {
        viewMode: 'table',
        columns: [ // Old format
          { name: 'Portfolio Name', visible: true },
          { name: 'Value', visible: false }
        ],
        timestamp: Date.now(),
        // Missing version field
      }

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(oldVersionData))

      const { result } = renderHook(() => usePortfolioView())

      // Should load the view mode from old format
      expect(result.current.viewMode).toBe('table')

      // Should save in new format on next change
      act(() => {
        result.current.setViewMode('tiles')
      })

      const savedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1])
      expect(savedData.version).toBe('1.0.0')
      expect(savedData.tableColumns).toBeDefined() // New format
      expect(savedData.columns).toBeUndefined() // Old format removed
    })

    it('should handle future version compatibility', () => {
      const futureVersionData = createMockPersistedState({
        viewMode: 'table',
        version: '2.0.0', // Future version
        timestamp: Date.now(),
        newFutureField: 'some-data' // Unknown field
      })

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(futureVersionData))

      const { result } = renderHook(() => usePortfolioView())

      // Should still load known fields
      expect(result.current.viewMode).toBe('table')
      expect(result.current.isLoaded).toBe(true)
    })

    it('should preserve unrecognized fields during save', () => {
      const dataWithExtra = {
        ...createMockPersistedState(),
        customField: 'preserve-me',
        userPreference: { theme: 'dark' }
      }

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(dataWithExtra))

      const { result } = renderHook(() => usePortfolioView())

      act(() => {
        result.current.setViewMode('table')
      })

      const savedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1])
      expect(savedData.customField).toBe('preserve-me')
      expect(savedData.userPreference).toEqual({ theme: 'dark' })
    })
  })

  describe('Data Expiration', () => {
    it('should expire old cached preferences', () => {
      const expiredData = createMockPersistedState({
        viewMode: 'table',
        timestamp: Date.now() - (31 * 24 * 60 * 60 * 1000), // 31 days old
        version: '1.0.0'
      })

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(expiredData))

      const { result } = renderHook(() => usePortfolioView())

      // Should fall back to defaults for expired data
      expect(result.current.viewMode).toBe('tiles')
      expect(result.current.isLoaded).toBe(true)

      // Should clean up expired data
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith(TEST_CONSTANTS.STORAGE_KEY)
    })

    it('should preserve fresh data within expiration window', () => {
      const freshData = createMockPersistedState({
        viewMode: 'table',
        timestamp: Date.now() - (7 * 24 * 60 * 60 * 1000), // 7 days old
        version: '1.0.0'
      })

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(freshData))

      const { result } = renderHook(() => usePortfolioView())

      // Should preserve fresh data
      expect(result.current.viewMode).toBe('table')
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled()
    })

    it('should update timestamp on save to extend expiration', () => {
      const oldData = createMockPersistedState({
        viewMode: 'table',
        timestamp: Date.now() - (20 * 24 * 60 * 60 * 1000), // 20 days old
        version: '1.0.0'
      })

      mockLocalStorage.setItem(TEST_CONSTANTS.STORAGE_KEY, JSON.stringify(oldData))

      const { result } = renderHook(() => usePortfolioView())

      // Make a change to trigger save
      act(() => {
        result.current.toggleViewMode()
      })

      const savedData = JSON.parse(mockLocalStorage.setItem.mock.calls[0][1])
      expect(savedData.timestamp).toBeCloseTo(Date.now(), -2) // Fresh timestamp
    })
  })

  describe('Cross-Tab Synchronization', () => {
    it('should listen for storage changes from other tabs', () => {
      const { result } = renderHook(() => usePortfolioView())

      expect(result.current.viewMode).toBe('tiles')

      // Simulate another tab changing the preference
      const newData = createMockPersistedState({
        viewMode: 'table',
        timestamp: Date.now(),
        version: '1.0.0'
      })

      // Trigger storage event (simulates change from another tab)
      window.dispatchEvent(new StorageEvent('storage', {
        key: TEST_CONSTANTS.STORAGE_KEY,
        newValue: JSON.stringify(newData),
        oldValue: null,
        storageArea: localStorage
      }))

      // Should update to reflect change from other tab
      expect(result.current.viewMode).toBe('table')
    })

    it('should ignore invalid storage events', () => {
      const { result } = renderHook(() => usePortfolioView())

      const originalViewMode = result.current.viewMode

      // Send invalid storage event
      window.dispatchEvent(new StorageEvent('storage', {
        key: TEST_CONSTANTS.STORAGE_KEY,
        newValue: 'invalid-json',
        oldValue: null,
        storageArea: localStorage
      }))

      // Should ignore invalid data and maintain current state
      expect(result.current.viewMode).toBe(originalViewMode)
    })

    it('should handle rapid cross-tab changes', () => {
      const { result } = renderHook(() => usePortfolioView())

      // Simulate rapid changes from multiple tabs
      const changes = ['table', 'tiles', 'table', 'tiles']

      changes.forEach(viewMode => {
        const data = createMockPersistedState({
          viewMode: viewMode as ViewMode,
          timestamp: Date.now(),
          version: '1.0.0'
        })

        window.dispatchEvent(new StorageEvent('storage', {
          key: TEST_CONSTANTS.STORAGE_KEY,
          newValue: JSON.stringify(data),
          oldValue: null,
          storageArea: localStorage
        }))
      })

      // Should end up in final state
      expect(result.current.viewMode).toBe('tiles')
    })
  })

  describe('Cleanup and Memory Management', () => {
    it('should cleanup storage listeners on unmount', () => {
      const { unmount } = renderHook(() => usePortfolioView())

      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener')

      unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'storage',
        expect.any(Function)
      )

      removeEventListenerSpy.mockRestore()
    })

    it('should not leak memory with repeated mount/unmount', () => {
      const initialListenerCount = window.addEventListener.mock?.calls?.length || 0

      // Mount and unmount multiple times
      for (let i = 0; i < 5; i++) {
        const { unmount } = renderHook(() => usePortfolioView())
        unmount()
      }

      // Should not accumulate listeners
      const finalListenerCount = window.addEventListener.mock?.calls?.length || 0
      expect(finalListenerCount - initialListenerCount).toBeLessThanOrEqual(1)
    })
  })
})