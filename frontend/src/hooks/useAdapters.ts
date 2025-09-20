/**
 * React hooks for adapter management state
 */

import { useState, useEffect, useCallback } from 'react';
import {
  AdapterConfiguration,
  CreateAdapterRequest,
  UpdateAdapterRequest
} from '@/types/adapters';
import {
  adaptersApi,
  AdapterMetrics,
  AdapterHealth,
  ProviderRegistry
} from '@/services/adapters-api';

export interface UseAdaptersResult {
  adapters: AdapterConfiguration[];
  loading: boolean;
  error: string | null;
  fetchAdapters: () => Promise<void>;
  createAdapter: (data: CreateAdapterRequest) => Promise<AdapterConfiguration>;
  updateAdapter: (id: string, data: UpdateAdapterRequest) => Promise<AdapterConfiguration>;
  deleteAdapter: (id: string) => Promise<void>;
  refreshAdapters: () => Promise<void>;
}

export interface UseAdapterResult {
  adapter: AdapterConfiguration | null;
  loading: boolean;
  error: string | null;
  fetchAdapter: () => Promise<void>;
  updateAdapter: (data: UpdateAdapterRequest) => Promise<AdapterConfiguration>;
  deleteAdapter: () => Promise<void>;
  refreshAdapter: () => Promise<void>;
}

export interface UseAdapterMetricsResult {
  metrics: AdapterMetrics | null;
  loading: boolean;
  error: string | null;
  fetchMetrics: (timeRange?: string) => Promise<void>;
  refreshMetrics: () => Promise<void>;
}

export interface UseAdapterHealthResult {
  health: AdapterHealth | null;
  loading: boolean;
  error: string | null;
  fetchHealth: () => Promise<void>;
  triggerHealthCheck: () => Promise<void>;
  refreshHealth: () => Promise<void>;
}

export interface UseProviderRegistryResult {
  registry: ProviderRegistry | null;
  loading: boolean;
  error: string | null;
  fetchRegistry: () => Promise<void>;
}

/**
 * Hook for managing multiple adapters
 */
export const useAdapters = (): UseAdaptersResult => {
  const [adapters, setAdapters] = useState<AdapterConfiguration[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAdapters = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adaptersApi.getAdapters();
      setAdapters(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch adapters';
      setError(errorMessage);
      console.error('Error fetching adapters:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const createAdapter = useCallback(async (data: CreateAdapterRequest): Promise<AdapterConfiguration> => {
    try {
      setError(null);
      const newAdapter = await adaptersApi.createAdapter(data);
      setAdapters(prev => [...prev, newAdapter]);
      return newAdapter;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create adapter';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const updateAdapter = useCallback(async (id: string, data: UpdateAdapterRequest): Promise<AdapterConfiguration> => {
    try {
      setError(null);
      const updatedAdapter = await adaptersApi.updateAdapter(id, data);
      setAdapters(prev => prev.map(adapter =>
        adapter.id === id ? updatedAdapter : adapter
      ));
      return updatedAdapter;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update adapter';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const deleteAdapter = useCallback(async (id: string): Promise<void> => {
    try {
      setError(null);
      await adaptersApi.deleteAdapter(id);
      setAdapters(prev => prev.filter(adapter => adapter.id !== id));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete adapter';
      setError(errorMessage);
      throw err;
    }
  }, []);

  const refreshAdapters = useCallback(async () => {
    await fetchAdapters();
  }, [fetchAdapters]);

  return {
    adapters,
    loading,
    error,
    fetchAdapters,
    createAdapter,
    updateAdapter,
    deleteAdapter,
    refreshAdapters,
  };
};

/**
 * Hook for managing a single adapter
 */
export const useAdapter = (id: string): UseAdapterResult => {
  const [adapter, setAdapter] = useState<AdapterConfiguration | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAdapter = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);
      const data = await adaptersApi.getAdapter(id);
      setAdapter(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch adapter';
      setError(errorMessage);
      console.error('Error fetching adapter:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  const updateAdapter = useCallback(async (data: UpdateAdapterRequest): Promise<AdapterConfiguration> => {
    if (!id) {
      throw new Error('No adapter ID provided');
    }

    try {
      setError(null);
      const updatedAdapter = await adaptersApi.updateAdapter(id, data);
      setAdapter(updatedAdapter);
      return updatedAdapter;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update adapter';
      setError(errorMessage);
      throw err;
    }
  }, [id]);

  const deleteAdapter = useCallback(async (): Promise<void> => {
    if (!id) {
      throw new Error('No adapter ID provided');
    }

    try {
      setError(null);
      await adaptersApi.deleteAdapter(id);
      setAdapter(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete adapter';
      setError(errorMessage);
      throw err;
    }
  }, [id]);

  const refreshAdapter = useCallback(async () => {
    await fetchAdapter();
  }, [fetchAdapter]);

  useEffect(() => {
    fetchAdapter();
  }, [fetchAdapter]);

  return {
    adapter,
    loading,
    error,
    fetchAdapter,
    updateAdapter,
    deleteAdapter,
    refreshAdapter,
  };
};

/**
 * Hook for adapter metrics
 */
export const useAdapterMetrics = (adapterId: string): UseAdapterMetricsResult => {
  const [metrics, setMetrics] = useState<AdapterMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async (timeRange: string = '24h') => {
    if (!adapterId) return;

    try {
      setLoading(true);
      setError(null);
      const data = await adaptersApi.getAdapterMetrics(adapterId, timeRange);
      setMetrics(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch metrics';
      setError(errorMessage);
      console.error('Error fetching adapter metrics:', err);
    } finally {
      setLoading(false);
    }
  }, [adapterId]);

  const refreshMetrics = useCallback(async () => {
    await fetchMetrics();
  }, [fetchMetrics]);

  return {
    metrics,
    loading,
    error,
    fetchMetrics,
    refreshMetrics,
  };
};

/**
 * Hook for adapter health status
 */
export const useAdapterHealth = (adapterId: string): UseAdapterHealthResult => {
  const [health, setHealth] = useState<AdapterHealth | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    if (!adapterId) return;

    try {
      setLoading(true);
      setError(null);
      const data = await adaptersApi.getAdapterHealth(adapterId);
      setHealth(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch health status';
      setError(errorMessage);
      console.error('Error fetching adapter health:', err);
    } finally {
      setLoading(false);
    }
  }, [adapterId]);

  const triggerHealthCheck = useCallback(async () => {
    if (!adapterId) return;

    try {
      setError(null);
      const data = await adaptersApi.triggerHealthCheck(adapterId);
      setHealth(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to trigger health check';
      setError(errorMessage);
      throw err;
    }
  }, [adapterId]);

  const refreshHealth = useCallback(async () => {
    await fetchHealth();
  }, [fetchHealth]);

  return {
    health,
    loading,
    error,
    fetchHealth,
    triggerHealthCheck,
    refreshHealth,
  };
};

/**
 * Hook for provider registry
 */
export const useProviderRegistry = (): UseProviderRegistryResult => {
  const [registry, setRegistry] = useState<ProviderRegistry | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRegistry = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adaptersApi.getProviderRegistry();
      setRegistry(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch provider registry';
      setError(errorMessage);
      console.error('Error fetching provider registry:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRegistry();
  }, [fetchRegistry]);

  return {
    registry,
    loading,
    error,
    fetchRegistry,
  };
};

/**
 * Hook for adapter testing and validation
 */
export const useAdapterTesting = () => {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    response_time_ms?: number;
    error_details?: string;
  } | null>(null);

  const testAdapter = useCallback(async (data: CreateAdapterRequest | UpdateAdapterRequest) => {
    try {
      setTesting(true);
      const result = await adaptersApi.testAdapter(data);
      setTestResult(result);
      return result;
    } catch (err) {
      const errorResult = {
        success: false,
        message: err instanceof Error ? err.message : 'Test failed',
        error_details: err instanceof Error ? err.message : undefined,
      };
      setTestResult(errorResult);
      throw err;
    } finally {
      setTesting(false);
    }
  }, []);

  const validateAdapter = useCallback(async (data: CreateAdapterRequest | UpdateAdapterRequest) => {
    try {
      return await adaptersApi.validateAdapter(data);
    } catch (err) {
      return {
        valid: false,
        errors: [err instanceof Error ? err.message : 'Validation failed'],
        warnings: [],
      };
    }
  }, []);

  return {
    testing,
    testResult,
    testAdapter,
    validateAdapter,
    clearTestResult: () => setTestResult(null),
  };
};

/**
 * Hook for adapter bulk operations
 */
export const useAdapterBulkOperations = () => {
  const [processing, setProcessing] = useState(false);

  const bulkUpdateAdapters = useCallback(async (updates: Array<{
    id: string;
    is_active?: boolean;
    priority?: number;
  }>) => {
    try {
      setProcessing(true);
      return await adaptersApi.bulkUpdateAdapters(updates);
    } catch (err) {
      throw err;
    } finally {
      setProcessing(false);
    }
  }, []);

  const exportAdapters = useCallback(async (format: 'json' | 'yaml' = 'json') => {
    try {
      setProcessing(true);
      const blob = await adaptersApi.exportAdapters(format);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `adapters-export.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      return blob;
    } catch (err) {
      throw err;
    } finally {
      setProcessing(false);
    }
  }, []);

  const importAdapters = useCallback(async (file: File, overwrite: boolean = false) => {
    try {
      setProcessing(true);
      return await adaptersApi.importAdapters(file, overwrite);
    } catch (err) {
      throw err;
    } finally {
      setProcessing(false);
    }
  }, []);

  return {
    processing,
    bulkUpdateAdapters,
    exportAdapters,
    importAdapters,
  };
};