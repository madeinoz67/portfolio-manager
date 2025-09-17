// ViewToggle Component Contract Tests - Feature 004: Tile/Table View Toggle
// These tests MUST FAIL before implementation (TDD Red phase)

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import ViewToggle from '@/components/Portfolio/ViewToggle'
import { ViewToggleProps, ViewMode } from '@/types/portfolioView'
import { createMockEventHandlers } from '@/__tests__/utils/portfolioViewTestUtils'

describe('ViewToggle Component Contract', () => {
  const mockHandlers = createMockEventHandlers()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('should render with tiles view mode selected', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      // Should show both toggle options
      expect(screen.getByRole('button', { name: /tiles/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /table/i })).toBeInTheDocument()

      // Tiles should be selected/active
      expect(screen.getByRole('button', { name: /tiles/i })).toHaveAttribute('aria-pressed', 'true')
      expect(screen.getByRole('button', { name: /table/i })).toHaveAttribute('aria-pressed', 'false')
    })

    it('should render with table view mode selected', () => {
      const props: ViewToggleProps = {
        viewMode: 'table',
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      // Table should be selected/active
      expect(screen.getByRole('button', { name: /table/i })).toHaveAttribute('aria-pressed', 'true')
      expect(screen.getByRole('button', { name: /tiles/i })).toHaveAttribute('aria-pressed', 'false')
    })

    it('should apply custom className when provided', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange,
        className: 'custom-toggle-class'
      }

      const { container } = render(<ViewToggle {...props} />)
      expect(container.firstChild).toHaveClass('custom-toggle-class')
    })

    it('should handle disabled state', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange,
        disabled: true
      }

      render(<ViewToggle {...props} />)

      expect(screen.getByRole('button', { name: /tiles/i })).toBeDisabled()
      expect(screen.getByRole('button', { name: /table/i })).toBeDisabled()
    })
  })

  describe('Size Variants', () => {
    it.each(['sm', 'md', 'lg'] as const)('should render %s size variant', (size) => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange,
        size
      }

      render(<ViewToggle {...props} />)

      // Should apply size-specific classes (exact classes depend on implementation)
      const toggleContainer = screen.getByRole('button', { name: /tiles/i }).parentElement
      expect(toggleContainer).toHaveClass(expect.stringMatching(size))
    })

    it('should default to medium size when size not specified', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      // Should have medium size styling (exact implementation dependent)
      const toggleContainer = screen.getByRole('button', { name: /tiles/i }).parentElement
      expect(toggleContainer).toHaveClass(expect.stringMatching(/md|medium|default/))
    })
  })

  describe('User Interactions', () => {
    it('should call onViewModeChange when tiles button is clicked', () => {
      const props: ViewToggleProps = {
        viewMode: 'table', // Start with table mode
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      fireEvent.click(screen.getByRole('button', { name: /tiles/i }))

      expect(mockHandlers.onViewModeChange).toHaveBeenCalledTimes(1)
      expect(mockHandlers.onViewModeChange).toHaveBeenCalledWith('tiles')
    })

    it('should call onViewModeChange when table button is clicked', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles', // Start with tiles mode
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      fireEvent.click(screen.getByRole('button', { name: /table/i }))

      expect(mockHandlers.onViewModeChange).toHaveBeenCalledTimes(1)
      expect(mockHandlers.onViewModeChange).toHaveBeenCalledWith('table')
    })

    it('should not call onViewModeChange when clicking already active button', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      // Click the already active tiles button
      fireEvent.click(screen.getByRole('button', { name: /tiles/i }))

      expect(mockHandlers.onViewModeChange).not.toHaveBeenCalled()
    })

    it('should not respond to clicks when disabled', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange,
        disabled: true
      }

      render(<ViewToggle {...props} />)

      fireEvent.click(screen.getByRole('button', { name: /table/i }))

      expect(mockHandlers.onViewModeChange).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      const tilesButton = screen.getByRole('button', { name: /tiles/i })
      const tableButton = screen.getByRole('button', { name: /table/i })

      // Should have proper roles and labels
      expect(tilesButton).toHaveAttribute('role', 'button')
      expect(tableButton).toHaveAttribute('role', 'button')

      // Should have pressed states
      expect(tilesButton).toHaveAttribute('aria-pressed', 'true')
      expect(tableButton).toHaveAttribute('aria-pressed', 'false')

      // Should have accessible names
      expect(tilesButton).toHaveAccessibleName(/tiles/i)
      expect(tableButton).toHaveAccessibleName(/table/i)
    })

    it('should support keyboard navigation', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      const tableButton = screen.getByRole('button', { name: /table/i })

      // Should be focusable and respond to keyboard events
      tableButton.focus()
      expect(tableButton).toHaveFocus()

      // Should trigger change on Enter key
      fireEvent.keyDown(tableButton, { key: 'Enter', code: 'Enter' })
      expect(mockHandlers.onViewModeChange).toHaveBeenCalledWith('table')

      // Should trigger change on Space key
      jest.clearAllMocks()
      fireEvent.keyDown(tableButton, { key: ' ', code: 'Space' })
      expect(mockHandlers.onViewModeChange).toHaveBeenCalledWith('table')
    })

    it('should announce view mode changes to screen readers', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange
      }

      const { rerender } = render(<ViewToggle {...props} />)

      // Change to table view
      rerender(<ViewToggle {...props} viewMode="table" />)

      // Should have updated aria-pressed states
      expect(screen.getByRole('button', { name: /tiles/i })).toHaveAttribute('aria-pressed', 'false')
      expect(screen.getByRole('button', { name: /table/i })).toHaveAttribute('aria-pressed', 'true')
    })
  })

  describe('Visual Feedback', () => {
    it('should apply active styling to selected view mode', () => {
      const props: ViewToggleProps = {
        viewMode: 'table',
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      const tilesButton = screen.getByRole('button', { name: /tiles/i })
      const tableButton = screen.getByRole('button', { name: /table/i })

      // Active button should have active styling
      expect(tableButton).toHaveClass(expect.stringMatching(/active|selected|pressed/))
      expect(tilesButton).not.toHaveClass(expect.stringMatching(/active|selected|pressed/))
    })

    it('should show hover states for interactive elements', () => {
      const props: ViewToggleProps = {
        viewMode: 'tiles',
        onViewModeChange: mockHandlers.onViewModeChange
      }

      render(<ViewToggle {...props} />)

      const tableButton = screen.getByRole('button', { name: /table/i })

      // Should support hover interactions (implementation specific)
      fireEvent.mouseEnter(tableButton)
      expect(tableButton).toHaveClass(expect.stringMatching(/hover|focus/))

      fireEvent.mouseLeave(tableButton)
      expect(tableButton).not.toHaveClass(expect.stringMatching(/hover/))
    })
  })

  describe('Props Validation', () => {
    it('should handle valid viewMode values', () => {
      const validModes: ViewMode[] = ['tiles', 'table']

      validModes.forEach(mode => {
        const props: ViewToggleProps = {
          viewMode: mode,
          onViewModeChange: mockHandlers.onViewModeChange
        }

        expect(() => render(<ViewToggle {...props} />)).not.toThrow()
      })
    })

    it('should require onViewModeChange callback', () => {
      const props = {
        viewMode: 'tiles' as ViewMode
        // Missing onViewModeChange - should cause error or warning
      }

      // This test validates that the component properly handles missing required props
      expect(() => render(<ViewToggle {...props} />)).toThrow()
    })
  })
})