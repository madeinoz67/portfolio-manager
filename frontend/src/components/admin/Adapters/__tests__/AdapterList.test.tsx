/**
 * T063: Frontend component tests - AdapterList component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import '@testing-library/jest-dom';

import AdapterList from '../AdapterList';
import { useAdapters } from '@/hooks/useAdapters';
import { AdapterConfiguration } from '@/types/adapters';

// Mock the useAdapters hook
jest.mock('@/hooks/useAdapters');
const mockUseAdapters = useAdapters as jest.MockedFunction<typeof useAdapters>;

// Mock date-fns
jest.mock('date-fns', () => ({
  formatDistanceToNow: jest.fn((date) => '2 hours ago'),
}));

const mockAdapters: AdapterConfiguration[] = [
  {
    id: 'adapter-1',
    provider_name: 'alpha_vantage',
    display_name: 'Alpha Vantage Primary',
    description: 'Primary Alpha Vantage adapter',
    config: { api_key: 'test_key' },
    is_active: true,
    priority: 1,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
  },
  {
    id: 'adapter-2',
    provider_name: 'yahoo_finance',
    display_name: 'Yahoo Finance Backup',
    description: 'Backup Yahoo Finance adapter',
    config: {},
    is_active: false,
    priority: 2,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
];

describe('AdapterList', () => {
  const defaultProps = {
    onCreateAdapter: jest.fn(),
    onEditAdapter: jest.fn(),
    onDeleteAdapter: jest.fn(),
    onViewMetrics: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAdapters.mockReturnValue({
      adapters: mockAdapters,
      loading: false,
      error: null,
      fetchAdapters: jest.fn(),
      createAdapter: jest.fn(),
      updateAdapter: jest.fn(),
      deleteAdapter: jest.fn(),
      refreshAdapters: jest.fn(),
    });
  });

  describe('Rendering', () => {
    it('renders adapter list with adapters', () => {
      render(<AdapterList {...defaultProps} />);

      expect(screen.getByText('Market Data Adapters')).toBeInTheDocument();
      expect(screen.getByText('Alpha Vantage Primary')).toBeInTheDocument();
      expect(screen.getByText('Yahoo Finance Backup')).toBeInTheDocument();
    });

    it('renders loading state', () => {
      mockUseAdapters.mockReturnValue({
        adapters: [],
        loading: true,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      expect(screen.getByText('Loading adapters...')).toBeInTheDocument();
    });

    it('renders error state', () => {
      mockUseAdapters.mockReturnValue({
        adapters: [],
        loading: false,
        error: 'Failed to fetch adapters',
        fetchAdapters: jest.fn(),
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      expect(screen.getByText('Error loading adapters: Failed to fetch adapters')).toBeInTheDocument();
    });

    it('renders empty state', () => {
      mockUseAdapters.mockReturnValue({
        adapters: [],
        loading: false,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      expect(screen.getByText('No adapters configured yet')).toBeInTheDocument();
    });
  });

  describe('Filtering and Search', () => {
    it('filters adapters by search term', async () => {
      render(<AdapterList {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search adapters by name or provider...');
      fireEvent.change(searchInput, { target: { value: 'Alpha' } });

      await waitFor(() => {
        expect(screen.getByText('Alpha Vantage Primary')).toBeInTheDocument();
        expect(screen.queryByText('Yahoo Finance Backup')).not.toBeInTheDocument();
      });
    });

    it('filters adapters by status', async () => {
      render(<AdapterList {...defaultProps} />);

      const statusFilter = screen.getByDisplayValue('All Status');
      fireEvent.click(statusFilter);

      const activeOption = screen.getByText('Active');
      fireEvent.click(activeOption);

      await waitFor(() => {
        expect(screen.getByText('Alpha Vantage Primary')).toBeInTheDocument();
        expect(screen.queryByText('Yahoo Finance Backup')).not.toBeInTheDocument();
      });
    });

    it('filters adapters by provider', async () => {
      render(<AdapterList {...defaultProps} />);

      const providerFilter = screen.getByDisplayValue('All Providers');
      fireEvent.click(providerFilter);

      const yahooOption = screen.getByText('Yahoo Finance');
      fireEvent.click(yahooOption);

      await waitFor(() => {
        expect(screen.queryByText('Alpha Vantage Primary')).not.toBeInTheDocument();
        expect(screen.getByText('Yahoo Finance Backup')).toBeInTheDocument();
      });
    });

    it('shows filtered results count', () => {
      render(<AdapterList {...defaultProps} />);

      expect(screen.getByText('Showing 2 of 2 adapters')).toBeInTheDocument();
    });
  });

  describe('Status Display', () => {
    it('displays active status correctly', () => {
      render(<AdapterList {...defaultProps} />);

      const activeRows = screen.getAllByText('Active');
      expect(activeRows).toHaveLength(1);
    });

    it('displays inactive status correctly', () => {
      render(<AdapterList {...defaultProps} />);

      const inactiveRows = screen.getAllByText('Inactive');
      expect(inactiveRows).toHaveLength(1);
    });

    it('displays provider names correctly', () => {
      render(<AdapterList {...defaultProps} />);

      expect(screen.getByText('Alpha Vantage')).toBeInTheDocument();
      expect(screen.getByText('Yahoo Finance')).toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    it('calls onCreateAdapter when add button is clicked', () => {
      render(<AdapterList {...defaultProps} />);

      const addButton = screen.getByText('Add Adapter');
      fireEvent.click(addButton);

      expect(defaultProps.onCreateAdapter).toHaveBeenCalledTimes(1);
    });

    it('calls onEditAdapter when edit button is clicked', () => {
      render(<AdapterList {...defaultProps} />);

      const editButtons = screen.getAllByTitle('Edit Adapter');
      fireEvent.click(editButtons[0]);

      expect(defaultProps.onEditAdapter).toHaveBeenCalledWith(mockAdapters[0]);
    });

    it('calls onViewMetrics when metrics button is clicked', () => {
      render(<AdapterList {...defaultProps} />);

      const metricsButtons = screen.getAllByTitle('View Metrics');
      fireEvent.click(metricsButtons[0]);

      expect(defaultProps.onViewMetrics).toHaveBeenCalledWith('adapter-1');
    });

    it('shows delete confirmation dialog', async () => {
      // Mock window.confirm
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
      const mockDeleteAdapter = jest.fn().mockResolvedValue(undefined);

      mockUseAdapters.mockReturnValue({
        adapters: mockAdapters,
        loading: false,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: mockDeleteAdapter,
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      const deleteButtons = screen.getAllByTitle('Delete Adapter');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalledWith(
          'Are you sure you want to delete this adapter? This action cannot be undone.'
        );
        expect(mockDeleteAdapter).toHaveBeenCalledWith('adapter-1');
        expect(defaultProps.onDeleteAdapter).toHaveBeenCalledWith('adapter-1');
      });

      confirmSpy.mockRestore();
    });

    it('does not delete when confirmation is cancelled', async () => {
      // Mock window.confirm to return false
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);
      const mockDeleteAdapter = jest.fn();

      mockUseAdapters.mockReturnValue({
        adapters: mockAdapters,
        loading: false,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: mockDeleteAdapter,
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      const deleteButtons = screen.getAllByTitle('Delete Adapter');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
        expect(mockDeleteAdapter).not.toHaveBeenCalled();
        expect(defaultProps.onDeleteAdapter).not.toHaveBeenCalled();
      });

      confirmSpy.mockRestore();
    });
  });

  describe('Refresh Functionality', () => {
    it('calls fetchAdapters on mount', () => {
      const mockFetchAdapters = jest.fn();

      mockUseAdapters.mockReturnValue({
        adapters: mockAdapters,
        loading: false,
        error: null,
        fetchAdapters: mockFetchAdapters,
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      expect(mockFetchAdapters).toHaveBeenCalledTimes(1);
    });

    it('calls fetchAdapters when refresh button is clicked', () => {
      const mockFetchAdapters = jest.fn();

      mockUseAdapters.mockReturnValue({
        adapters: mockAdapters,
        loading: false,
        error: null,
        fetchAdapters: mockFetchAdapters,
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      expect(mockFetchAdapters).toHaveBeenCalledTimes(2); // Once on mount, once on click
    });

    it('shows loading state on refresh button when loading', () => {
      mockUseAdapters.mockReturnValue({
        adapters: mockAdapters,
        loading: true,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      const refreshIcon = document.querySelector('.animate-spin');
      expect(refreshIcon).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper table structure', () => {
      render(<AdapterList {...defaultProps} />);

      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getAllByRole('columnheader')).toHaveLength(6);
      expect(screen.getAllByRole('row')).toHaveLength(3); // Header + 2 data rows
    });

    it('has accessible button labels', () => {
      render(<AdapterList {...defaultProps} />);

      expect(screen.getByTitle('Edit Adapter')).toBeInTheDocument();
      expect(screen.getByTitle('Delete Adapter')).toBeInTheDocument();
      expect(screen.getByTitle('View Metrics')).toBeInTheDocument();
      expect(screen.getByTitle('View Details')).toBeInTheDocument();
    });

    it('has proper form labels', () => {
      render(<AdapterList {...defaultProps} />);

      expect(screen.getByPlaceholderText('Search adapters by name or provider...')).toBeInTheDocument();
    });
  });

  describe('Date Formatting', () => {
    it('formats relative dates correctly', () => {
      render(<AdapterList {...defaultProps} />);

      // Check that formatDistanceToNow is called and results are displayed
      const relativeTimes = screen.getAllByText('2 hours ago');
      expect(relativeTimes.length).toBeGreaterThan(0);
    });
  });

  describe('Provider Name Display', () => {
    it('displays provider display names correctly', () => {
      render(<AdapterList {...defaultProps} />);

      expect(screen.getByText('Alpha Vantage')).toBeInTheDocument();
      expect(screen.getByText('Yahoo Finance')).toBeInTheDocument();
    });

    it('handles unknown provider names', () => {
      const adaptersWithUnknown = [
        ...mockAdapters,
        {
          id: 'adapter-3',
          provider_name: 'unknown_provider',
          display_name: 'Unknown Provider',
          description: '',
          config: {},
          is_active: true,
          priority: 3,
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
        },
      ];

      mockUseAdapters.mockReturnValue({
        adapters: adaptersWithUnknown,
        loading: false,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      expect(screen.getByText('unknown_provider')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('handles delete error gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
      const mockDeleteAdapter = jest.fn().mockRejectedValue(new Error('Delete failed'));

      mockUseAdapters.mockReturnValue({
        adapters: mockAdapters,
        loading: false,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: mockDeleteAdapter,
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      const deleteButtons = screen.getAllByTitle('Delete Adapter');
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to delete adapter:', expect.any(Error));
      });

      confirmSpy.mockRestore();
      consoleSpy.mockRestore();
    });

    it('shows try again button in error state', () => {
      const mockFetchAdapters = jest.fn();

      mockUseAdapters.mockReturnValue({
        adapters: [],
        loading: false,
        error: 'Network error',
        fetchAdapters: mockFetchAdapters,
        createAdapter: jest.fn(),
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterList {...defaultProps} />);

      const tryAgainButton = screen.getByText('Try Again');
      fireEvent.click(tryAgainButton);

      expect(mockFetchAdapters).toHaveBeenCalled();
    });
  });
});