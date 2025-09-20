/**
 * T063: Frontend component tests - AdapterConfigForm component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import '@testing-library/jest-dom';

import AdapterConfigForm from '../AdapterConfigForm';
import { useAdapters, useProviderRegistry, useAdapterTesting } from '@/hooks/useAdapters';
import { AdapterConfiguration } from '@/types/adapters';

// Mock the hooks
jest.mock('@/hooks/useAdapters');
const mockUseAdapters = useAdapters as jest.MockedFunction<typeof useAdapters>;
const mockUseProviderRegistry = useProviderRegistry as jest.MockedFunction<typeof useProviderRegistry>;
const mockUseAdapterTesting = useAdapterTesting as jest.MockedFunction<typeof useAdapterTesting>;

const mockAdapter: AdapterConfiguration = {
  id: 'adapter-1',
  provider_name: 'alpha_vantage',
  display_name: 'Test Alpha Vantage',
  description: 'Test adapter description',
  config: {
    api_key: 'test_api_key',
    base_url: 'https://www.alphavantage.co/query',
    timeout: 30,
  },
  is_active: true,
  priority: 1,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-02T00:00:00Z',
};

const mockRegistry = {
  providers: {
    alpha_vantage: {
      name: 'alpha_vantage',
      display_name: 'Alpha Vantage',
      description: 'Alpha Vantage market data provider',
      required_config: ['api_key'],
      optional_config: ['base_url', 'timeout'],
      supports_bulk: true,
      rate_limits: {
        requests_per_minute: 5,
        requests_per_day: 500,
      },
    },
    yahoo_finance: {
      name: 'yahoo_finance',
      display_name: 'Yahoo Finance',
      description: 'Yahoo Finance market data provider',
      required_config: [],
      optional_config: ['timeout', 'user_agent'],
      supports_bulk: true,
      rate_limits: {
        requests_per_minute: 60,
      },
    },
  },
};

describe('AdapterConfigForm', () => {
  const defaultProps = {
    mode: 'create' as const,
    onSuccess: jest.fn(),
    onCancel: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseAdapters.mockReturnValue({
      adapters: [],
      loading: false,
      error: null,
      fetchAdapters: jest.fn(),
      createAdapter: jest.fn().mockResolvedValue(mockAdapter),
      updateAdapter: jest.fn().mockResolvedValue(mockAdapter),
      deleteAdapter: jest.fn(),
      refreshAdapters: jest.fn(),
    });

    mockUseProviderRegistry.mockReturnValue({
      registry: mockRegistry,
      loading: false,
      error: null,
      fetchRegistry: jest.fn(),
    });

    mockUseAdapterTesting.mockReturnValue({
      testing: false,
      testResult: null,
      testAdapter: jest.fn(),
      validateAdapter: jest.fn(),
      clearTestResult: jest.fn(),
    });
  });

  describe('Create Mode', () => {
    it('renders create form correctly', () => {
      render(<AdapterConfigForm {...defaultProps} />);

      expect(screen.getByText('Create New Adapter')).toBeInTheDocument();
      expect(screen.getByText('Basic Configuration')).toBeInTheDocument();
      expect(screen.getByText('Provider Settings')).toBeInTheDocument();
      expect(screen.getByText('Advanced Settings')).toBeInTheDocument();
    });

    it('shows provider selection dropdown', () => {
      render(<AdapterConfigForm {...defaultProps} />);

      expect(screen.getByText('Select Provider')).toBeInTheDocument();
      fireEvent.click(screen.getByText('Select Provider'));

      expect(screen.getByText('Alpha Vantage')).toBeInTheDocument();
      expect(screen.getByText('Yahoo Finance')).toBeInTheDocument();
    });

    it('updates provider configuration when provider is selected', async () => {
      render(<AdapterConfigForm {...defaultProps} />);

      // Select Alpha Vantage provider
      fireEvent.click(screen.getByText('Select Provider'));
      fireEvent.click(screen.getByText('Alpha Vantage'));

      await waitFor(() => {
        expect(screen.getByLabelText('API Key *')).toBeInTheDocument();
        expect(screen.getByLabelText('Base URL')).toBeInTheDocument();
        expect(screen.getByLabelText('Timeout (seconds)')).toBeInTheDocument();
      });
    });

    it('validates required fields', async () => {
      render(<AdapterConfigForm {...defaultProps} />);

      // Try to submit without filling required fields
      const submitButton = screen.getByText('Create Adapter');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Display name is required')).toBeInTheDocument();
      });
    });

    it('creates adapter successfully', async () => {
      const mockCreateAdapter = jest.fn().mockResolvedValue(mockAdapter);
      mockUseAdapters.mockReturnValue({
        adapters: [],
        loading: false,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: mockCreateAdapter,
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterConfigForm {...defaultProps} />);

      // Fill form
      fireEvent.click(screen.getByText('Select Provider'));
      fireEvent.click(screen.getByText('Alpha Vantage'));

      await waitFor(() => {
        const displayNameInput = screen.getByLabelText('Display Name *');
        fireEvent.change(displayNameInput, { target: { value: 'Test Adapter' } });

        const apiKeyInput = screen.getByLabelText('API Key *');
        fireEvent.change(apiKeyInput, { target: { value: 'test_key_123' } });
      });

      // Submit form
      const submitButton = screen.getByText('Create Adapter');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockCreateAdapter).toHaveBeenCalledWith({
          provider_name: 'alpha_vantage',
          display_name: 'Test Adapter',
          description: '',
          config: {
            api_key: 'test_key_123',
            base_url: '',
            timeout: 30,
          },
          is_active: false,
          priority: 1,
        });
        expect(defaultProps.onSuccess).toHaveBeenCalled();
      });
    });
  });

  describe('Edit Mode', () => {
    const editProps = {
      mode: 'edit' as const,
      adapter: mockAdapter,
      onSuccess: jest.fn(),
      onCancel: jest.fn(),
    };

    it('renders edit form correctly', () => {
      render(<AdapterConfigForm {...editProps} />);

      expect(screen.getByText('Edit Adapter')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test Alpha Vantage')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Alpha Vantage')).toBeInTheDocument();
    });

    it('pre-fills form with adapter data', () => {
      render(<AdapterConfigForm {...editProps} />);

      expect(screen.getByDisplayValue('Test Alpha Vantage')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test adapter description')).toBeInTheDocument();
      expect(screen.getByDisplayValue('test_api_key')).toBeInTheDocument();
      expect(screen.getByDisplayValue('https://www.alphavantage.co/query')).toBeInTheDocument();

      const activeCheckbox = screen.getByLabelText('Active') as HTMLInputElement;
      expect(activeCheckbox.checked).toBe(true);
    });

    it('updates adapter successfully', async () => {
      const mockUpdateAdapter = jest.fn().mockResolvedValue(mockAdapter);
      mockUseAdapters.mockReturnValue({
        adapters: [],
        loading: false,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: jest.fn(),
        updateAdapter: mockUpdateAdapter,
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterConfigForm {...editProps} />);

      // Update display name
      const displayNameInput = screen.getByDisplayValue('Test Alpha Vantage');
      fireEvent.change(displayNameInput, { target: { value: 'Updated Adapter' } });

      // Submit form
      const submitButton = screen.getByText('Update Adapter');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockUpdateAdapter).toHaveBeenCalledWith('adapter-1', {
          display_name: 'Updated Adapter',
          description: 'Test adapter description',
          config: {
            api_key: 'test_api_key',
            base_url: 'https://www.alphavantage.co/query',
            timeout: 30,
          },
          is_active: true,
          priority: 1,
        });
        expect(editProps.onSuccess).toHaveBeenCalled();
      });
    });
  });

  describe('Tab Navigation', () => {
    it('switches between tabs correctly', () => {
      render(<AdapterConfigForm {...defaultProps} />);

      // Initially on Basic Configuration tab
      expect(screen.getByText('Display Name *')).toBeInTheDocument();

      // Click Provider Settings tab
      fireEvent.click(screen.getByText('Provider Settings'));
      expect(screen.getByText('Select a provider to configure settings')).toBeInTheDocument();

      // Click Advanced Settings tab
      fireEvent.click(screen.getByText('Advanced Settings'));
      expect(screen.getByText('Priority')).toBeInTheDocument();
    });
  });

  describe('Test Connection', () => {
    it('tests connection successfully', async () => {
      const mockTestAdapter = jest.fn().mockResolvedValue({
        success: true,
        message: 'Connection successful',
        response_time_ms: 120,
      });

      mockUseAdapterTesting.mockReturnValue({
        testing: false,
        testResult: null,
        testAdapter: mockTestAdapter,
        validateAdapter: jest.fn(),
        clearTestResult: jest.fn(),
      });

      render(<AdapterConfigForm {...defaultProps} />);

      // Fill required fields first
      fireEvent.click(screen.getByText('Select Provider'));
      fireEvent.click(screen.getByText('Alpha Vantage'));

      await waitFor(() => {
        const displayNameInput = screen.getByLabelText('Display Name *');
        fireEvent.change(displayNameInput, { target: { value: 'Test Adapter' } });

        const apiKeyInput = screen.getByLabelText('API Key *');
        fireEvent.change(apiKeyInput, { target: { value: 'test_key' } });
      });

      // Test connection
      const testButton = screen.getByText('Test Connection');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(mockTestAdapter).toHaveBeenCalled();
      });
    });

    it('shows test connection loading state', () => {
      mockUseAdapterTesting.mockReturnValue({
        testing: true,
        testResult: null,
        testAdapter: jest.fn(),
        validateAdapter: jest.fn(),
        clearTestResult: jest.fn(),
      });

      render(<AdapterConfigForm {...defaultProps} />);

      expect(screen.getByText('Testing...')).toBeInTheDocument();
    });

    it('displays test result', () => {
      mockUseAdapterTesting.mockReturnValue({
        testing: false,
        testResult: {
          success: true,
          message: 'Connection successful',
          response_time_ms: 120,
        },
        testAdapter: jest.fn(),
        validateAdapter: jest.fn(),
        clearTestResult: jest.fn(),
      });

      render(<AdapterConfigForm {...defaultProps} />);

      expect(screen.getByText('Connection successful')).toBeInTheDocument();
      expect(screen.getByText('Response time: 120ms')).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('shows validation errors for empty fields', async () => {
      render(<AdapterConfigForm {...defaultProps} />);

      const submitButton = screen.getByText('Create Adapter');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Display name is required')).toBeInTheDocument();
      });
    });

    it('validates display name length', async () => {
      render(<AdapterConfigForm {...defaultProps} />);

      const displayNameInput = screen.getByLabelText('Display Name *');
      fireEvent.change(displayNameInput, {
        target: { value: 'a'.repeat(101) } // Too long
      });

      const submitButton = screen.getByText('Create Adapter');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Display name too long')).toBeInTheDocument();
      });
    });

    it('validates priority range', async () => {
      render(<AdapterConfigForm {...defaultProps} />);

      // Go to Advanced Settings tab
      fireEvent.click(screen.getByText('Advanced Settings'));

      const priorityInput = screen.getByLabelText('Priority');
      fireEvent.change(priorityInput, { target: { value: '0' } }); // Below minimum

      const submitButton = screen.getByText('Create Adapter');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Priority must be at least 1')).toBeInTheDocument();
      });
    });
  });

  describe('Cancel Functionality', () => {
    it('calls onCancel when cancel button is clicked', () => {
      render(<AdapterConfigForm {...defaultProps} />);

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(defaultProps.onCancel).toHaveBeenCalled();
    });

    it('calls onCancel when close button is clicked', () => {
      render(<AdapterConfigForm {...defaultProps} />);

      const closeButton = screen.getByText('×');
      fireEvent.click(closeButton);

      expect(defaultProps.onCancel).toHaveBeenCalled();
    });
  });

  describe('Loading States', () => {
    it('shows loading state when creating adapter', () => {
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

      render(<AdapterConfigForm {...defaultProps} />);

      const submitButton = screen.getByText('Creating...');
      expect(submitButton).toBeDisabled();
    });

    it('shows loading state when updating adapter', () => {
      const editProps = {
        mode: 'edit' as const,
        adapter: mockAdapter,
        onSuccess: jest.fn(),
        onCancel: jest.fn(),
      };

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

      render(<AdapterConfigForm {...editProps} />);

      const submitButton = screen.getByText('Updating...');
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('displays error when creation fails', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      const mockCreateAdapter = jest.fn().mockRejectedValue(new Error('Creation failed'));

      mockUseAdapters.mockReturnValue({
        adapters: [],
        loading: false,
        error: null,
        fetchAdapters: jest.fn(),
        createAdapter: mockCreateAdapter,
        updateAdapter: jest.fn(),
        deleteAdapter: jest.fn(),
        refreshAdapters: jest.fn(),
      });

      render(<AdapterConfigForm {...defaultProps} />);

      // Fill and submit form
      fireEvent.click(screen.getByText('Select Provider'));
      fireEvent.click(screen.getByText('Alpha Vantage'));

      await waitFor(() => {
        const displayNameInput = screen.getByLabelText('Display Name *');
        fireEvent.change(displayNameInput, { target: { value: 'Test Adapter' } });

        const apiKeyInput = screen.getByLabelText('API Key *');
        fireEvent.change(apiKeyInput, { target: { value: 'test_key' } });
      });

      const submitButton = screen.getByText('Create Adapter');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Error creating adapter:', expect.any(Error));
      });

      consoleSpy.mockRestore();
    });

    it('displays provider registry loading error', () => {
      mockUseProviderRegistry.mockReturnValue({
        registry: null,
        loading: false,
        error: 'Failed to load providers',
        fetchRegistry: jest.fn(),
      });

      render(<AdapterConfigForm {...defaultProps} />);

      expect(screen.getByText('Error loading providers: Failed to load providers')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      render(<AdapterConfigForm {...defaultProps} />);

      expect(screen.getByLabelText('Display Name *')).toBeInTheDocument();
      expect(screen.getByLabelText('Description')).toBeInTheDocument();
      expect(screen.getByLabelText('Active')).toBeInTheDocument();
    });

    it('has proper button roles', () => {
      render(<AdapterConfigForm {...defaultProps} />);

      expect(screen.getByRole('button', { name: 'Create Adapter' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Test Connection' })).toBeInTheDocument();
    });

    it('has proper tab navigation', () => {
      render(<AdapterConfigForm {...defaultProps} />);

      const tabs = screen.getAllByRole('tab');
      expect(tabs).toHaveLength(3);
      expect(screen.getByRole('tabpanel')).toBeInTheDocument();
    });
  });

  describe('Provider-Specific Configuration', () => {
    it('shows different fields for different providers', async () => {
      render(<AdapterConfigForm {...defaultProps} />);

      // Select Yahoo Finance
      fireEvent.click(screen.getByText('Select Provider'));
      fireEvent.click(screen.getByText('Yahoo Finance'));

      await waitFor(() => {
        // Yahoo Finance shouldn't require API key
        expect(screen.queryByLabelText('API Key *')).not.toBeInTheDocument();
        expect(screen.getByLabelText('Timeout (seconds)')).toBeInTheDocument();
        expect(screen.getByLabelText('User Agent')).toBeInTheDocument();
      });
    });

    it('shows provider capabilities information', async () => {
      render(<AdapterConfigForm {...defaultProps} />);

      fireEvent.click(screen.getByText('Select Provider'));
      fireEvent.click(screen.getByText('Alpha Vantage'));

      await waitFor(() => {
        expect(screen.getByText('Alpha Vantage market data provider')).toBeInTheDocument();
        expect(screen.getByText('5 requests per minute')).toBeInTheDocument();
        expect(screen.getByText('500 requests per day')).toBeInTheDocument();
      });
    });
  });
});