// Portfolio View Toggle Integration Tests - Feature 004: Tile/Table View Toggle
// These tests MUST FAIL before implementation (TDD Red phase)

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import PortfoliosPage from '@/app/portfolios/page'
import { usePortfolios } from '@/hooks/usePortfolios'
import { usePortfolioView } from '@/hooks/usePortfolioView'
import {
  createMockPortfolios,
  setupPortfolioViewTest,
  waitForViewTransition
} from '@/__tests__/utils/portfolioViewTestUtils'

// Mock the hooks
jest.mock('@/hooks/usePortfolios')
jest.mock('@/hooks/usePortfolioView')
jest.mock('@/components/ui/Toast', () => ({
  useToast: () => ({
    addToast: jest.fn()
  })
}))

const mockUsePortfolios = usePortfolios as jest.MockedFunction<typeof usePortfolios>
const mockUsePortfolioView = usePortfolioView as jest.MockedFunction<typeof usePortfolioView>

describe('Portfolio View Toggle Integration', () => {
  const mockPortfolios = createMockPortfolios(5)
  const testSetup = setupPortfolioViewTest()

  beforeEach(() => {
    testSetup.cleanup()
    jest.clearAllMocks()

    // Mock usePortfolios hook
    mockUsePortfolios.mockReturnValue({
      portfolios: mockPortfolios,
      loading: false,
      error: null,
      createPortfolio: jest.fn(),
      updatePortfolio: jest.fn(),
      deletePortfolio: jest.fn(),
      fetchPortfolios: jest.fn()
    })

    // Mock initial usePortfolioView state
    mockUsePortfolioView.mockReturnValue({
      viewMode: 'tiles',
      tableColumns: testSetup.mockViewState.tableConfig.columns,
      toggleViewMode: jest.fn(),
      setViewMode: jest.fn(),
      updateTableColumns: jest.fn(),
      resetConfiguration: jest.fn(),
      isLoaded: true
    })
  })

  afterEach(() => {
    testSetup.cleanup()
  })

  describe('View Toggle Integration', () => {
    it('should display view toggle control on portfolios page', () => {
      render(<PortfoliosPage />)

      // Should show view toggle component
      expect(screen.getByRole('button', { name: /tiles/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /table/i })).toBeInTheDocument()

      // Tiles should be initially selected
      expect(screen.getByRole('button', { name: /tiles/i })).toHaveAttribute('aria-pressed', 'true')
      expect(screen.getByRole('button', { name: /table/i })).toHaveAttribute('aria-pressed', 'false')
    })

    it('should render portfolios in tile view by default', () => {
      render(<PortfoliosPage />)

      // Should show portfolio cards (tile view)
      expect(screen.getAllByTestId('portfolio-card')).toHaveLength(mockPortfolios.length)

      // Should not show table
      expect(screen.queryByRole('table')).not.toBeInTheDocument()
    })

    it('should switch to table view when table button is clicked', async () => {
      const mockToggleViewMode = jest.fn()

      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'tiles',
        toggleViewMode: mockToggleViewMode,
        setViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      render(<PortfoliosPage />)

      // Click table view button
      fireEvent.click(screen.getByRole('button', { name: /table/i }))

      // Should call view mode change
      expect(mockToggleViewMode).toHaveBeenCalledTimes(1)
    })

    it('should render portfolios in table view when mode is table', () => {
      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'table',
        toggleViewMode: jest.fn(),
        setViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      render(<PortfoliosPage />)

      // Should show table
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /portfolio name/i })).toBeInTheDocument()

      // Should show portfolio data in table rows
      expect(screen.getAllByRole('row')).toHaveLength(mockPortfolios.length + 1) // +1 for header

      // Should not show portfolio cards
      expect(screen.queryByTestId('portfolio-card')).not.toBeInTheDocument()
    })

    it('should preserve search functionality in both views', async () => {
      const { rerender } = render(<PortfoliosPage />)

      // Search in tile view
      const searchInput = screen.getByPlaceholderText(/search portfolios/i)
      fireEvent.change(searchInput, { target: { value: 'Portfolio 1' } })

      await waitFor(() => {
        expect(screen.getByText('Portfolio 1')).toBeInTheDocument()
        expect(screen.queryByText('Portfolio 2')).not.toBeInTheDocument()
      })

      // Switch to table view with search active
      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'table',
        toggleViewMode: jest.fn(),
        setViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      rerender(<PortfoliosPage />)

      // Should still show filtered results in table view
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getByText('Portfolio 1')).toBeInTheDocument()
      expect(screen.queryByText('Portfolio 2')).not.toBeInTheDocument()
    })

    it('should preserve sort functionality in both views', () => {
      const { rerender } = render(<PortfoliosPage />)

      // Set sort in tile view
      const sortDropdown = screen.getByDisplayValue(/name/i)
      fireEvent.change(sortDropdown, { target: { value: 'value' } })

      // Switch to table view
      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'table',
        toggleViewMode: jest.fn(),
        setViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      rerender(<PortfoliosPage />)

      // Sort setting should be preserved
      expect(screen.getByDisplayValue(/value/i)).toBeInTheDocument()
    })
  })

  describe('View Transition Animation', () => {
    it('should show loading state during view transition', async () => {
      const mockSetViewMode = jest.fn()

      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'tiles',
        setViewMode: mockSetViewMode,
        toggleViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      render(<PortfoliosPage />)

      // Click table view
      fireEvent.click(screen.getByRole('button', { name: /table/i }))

      // Should show transition loading state
      expect(screen.getByTestId('view-transition-loading')).toBeInTheDocument()

      // Wait for transition to complete
      await waitForViewTransition()

      expect(screen.queryByTestId('view-transition-loading')).not.toBeInTheDocument()
    })

    it('should complete view transition within performance target', async () => {
      const startTime = performance.now()

      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'table',
        toggleViewMode: jest.fn(),
        setViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      render(<PortfoliosPage />)

      const endTime = performance.now()
      const renderTime = endTime - startTime

      // Should render within performance target (300ms from plan.md)
      expect(renderTime).toBeLessThan(300)
    })
  })

  describe('View Persistence', () => {
    it('should load user preference on page mount', () => {
      // Mock persisted table view preference
      testSetup.mockLocalStorage.setItem(
        'portfolio-view-preferences',
        JSON.stringify({
          viewMode: 'table',
          timestamp: Date.now(),
          version: '1.0.0'
        })
      )

      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'table', // Loaded from persistence
        toggleViewMode: jest.fn(),
        setViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      render(<PortfoliosPage />)

      // Should start in table view based on persisted preference
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /table/i })).toHaveAttribute('aria-pressed', 'true')
    })

    it('should save view preference when changed', () => {
      const mockSetViewMode = jest.fn()

      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'tiles',
        setViewMode: mockSetViewMode,
        toggleViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      render(<PortfoliosPage />)

      fireEvent.click(screen.getByRole('button', { name: /table/i }))

      expect(mockSetViewMode).toHaveBeenCalledWith('table')
    })
  })

  describe('Error Handling', () => {
    it('should handle portfolios loading error in both views', () => {
      mockUsePortfolios.mockReturnValue({
        portfolios: [],
        loading: false,
        error: 'Failed to load portfolios',
        createPortfolio: jest.fn(),
        updatePortfolio: jest.fn(),
        deletePortfolio: jest.fn(),
        fetchPortfolios: jest.fn()
      })

      const { rerender } = render(<PortfoliosPage />)

      // Should show error in tile view
      expect(screen.getByText(/failed to load portfolios/i)).toBeInTheDocument()

      // Switch to table view
      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'table',
        toggleViewMode: jest.fn(),
        setViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      rerender(<PortfoliosPage />)

      // Should still show error in table view
      expect(screen.getByText(/failed to load portfolios/i)).toBeInTheDocument()
    })

    it('should handle view preference loading failure gracefully', () => {
      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        isLoaded: false, // Loading failed
        viewMode: 'tiles', // Fallback to default
        toggleViewMode: jest.fn(),
        setViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn()
      })

      render(<PortfoliosPage />)

      // Should render with default view mode
      expect(screen.getAllByTestId('portfolio-card')).toHaveLength(mockPortfolios.length)
      expect(screen.getByRole('button', { name: /tiles/i })).toHaveAttribute('aria-pressed', 'true')
    })

    it('should disable view toggle during loading states', () => {
      mockUsePortfolios.mockReturnValue({
        portfolios: [],
        loading: true,
        error: null,
        createPortfolio: jest.fn(),
        updatePortfolio: jest.fn(),
        deletePortfolio: jest.fn(),
        fetchPortfolios: jest.fn()
      })

      render(<PortfoliosPage />)

      // View toggle should be disabled during loading
      expect(screen.getByRole('button', { name: /tiles/i })).toBeDisabled()
      expect(screen.getByRole('button', { name: /table/i })).toBeDisabled()
    })
  })

  describe('Accessibility Integration', () => {
    it('should maintain focus management during view transitions', async () => {
      render(<PortfoliosPage />)

      const tableButton = screen.getByRole('button', { name: /table/i })

      // Focus the table button
      tableButton.focus()
      expect(tableButton).toHaveFocus()

      // Click to change view
      fireEvent.click(tableButton)

      // Focus should remain on the toggle after transition
      await waitForViewTransition()
      expect(tableButton).toHaveFocus()
    })

    it('should announce view changes to screen readers', () => {
      render(<PortfoliosPage />)

      // Should have aria-live region for announcements
      expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument()

      // Click table view
      fireEvent.click(screen.getByRole('button', { name: /table/i }))

      // Should announce the view change
      expect(screen.getByRole('status', { hidden: true })).toHaveTextContent(/table view/i)
    })

    it('should support keyboard navigation between views', () => {
      render(<PortfoliosPage />)

      const tableButton = screen.getByRole('button', { name: /table/i })

      // Should respond to keyboard activation
      tableButton.focus()
      fireEvent.keyDown(tableButton, { key: 'Enter', code: 'Enter' })

      // Should trigger view change
      expect(mockUsePortfolioView().setViewMode).toHaveBeenCalled()
    })
  })

  describe('Mobile Integration', () => {
    it('should render view toggle appropriately on mobile', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', { value: 600, writable: true })

      render(<PortfoliosPage />)

      // View toggle should still be accessible on mobile
      expect(screen.getByRole('button', { name: /tiles/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /table/i })).toBeInTheDocument()

      // Should have mobile-appropriate styling
      const toggleContainer = screen.getByRole('button', { name: /tiles/i }).parentElement
      expect(toggleContainer).toHaveClass(expect.stringMatching(/mobile|sm|responsive/))
    })

    it('should handle table horizontal scroll on mobile', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', { value: 600, writable: true })

      mockUsePortfolioView.mockReturnValue({
        ...testSetup.mockViewState,
        viewMode: 'table',
        toggleViewMode: jest.fn(),
        setViewMode: jest.fn(),
        updateTableColumns: jest.fn(),
        resetConfiguration: jest.fn(),
        isLoaded: true
      })

      render(<PortfoliosPage />)

      const table = screen.getByRole('table')
      expect(table).toHaveClass(expect.stringMatching(/overflow-x|scroll/))
    })
  })
})