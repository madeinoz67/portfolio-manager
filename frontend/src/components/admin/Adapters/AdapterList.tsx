'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Trash2,
  Edit,
  Eye,
  Activity,
  Search,
  RefreshCw,
  Filter,
  BarChart3,
  Zap
} from 'lucide-react';
import { useAdapters, useProviderRegistry } from '@/hooks/useAdapters';
import { AdapterConfiguration } from '@/types/adapters';
import { adaptersApi, AdapterMetrics } from '@/services/adapters-api';
import { formatDistanceToNow, format } from 'date-fns';

interface AdapterListProps {
  onEditAdapter?: (adapter: AdapterConfiguration) => void;
  onDeleteAdapter?: (adapterId: string) => void;
  onViewMetrics?: (adapterId: string) => void;
  onViewHealth?: (adapterId: string) => void;
}

const AdapterList: React.FC<AdapterListProps> = ({
  onEditAdapter,
  onDeleteAdapter,
  onViewMetrics,
  onViewHealth,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [providerFilter, setProviderFilter] = useState<string>('all');

  const {
    adapters,
    loading,
    error,
    fetchAdapters,
    deleteAdapter,
    updateAdapter,
  } = useAdapters();

  const {
    registry,
    loading: registryLoading,
    error: registryError,
  } = useProviderRegistry();

  const router = useRouter();

  // State for adapter metrics
  const [adapterMetrics, setAdapterMetrics] = useState<Record<string, AdapterMetrics>>({});
  const [metricsLoading, setMetricsLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchAdapters();
  }, []);

  // Fetch metrics for all adapters
  useEffect(() => {
    const fetchAllMetrics = async () => {
      for (const adapter of adapters) {
        try {
          setMetricsLoading(prev => ({ ...prev, [adapter.id]: true }));
          const metrics = await adaptersApi.getAdapterMetrics(adapter.id);
          console.log(`Metrics received for adapter ${adapter.id}:`, metrics);
          console.log(`requests_today for ${adapter.id}:`, metrics.requests_today);
          setAdapterMetrics(prev => ({ ...prev, [adapter.id]: metrics }));
        } catch (error) {
          console.error(`Failed to fetch metrics for adapter ${adapter.id}:`, error);
        } finally {
          setMetricsLoading(prev => ({ ...prev, [adapter.id]: false }));
        }
      }
    };

    if (adapters.length > 0) {
      fetchAllMetrics();
    }
  }, [adapters]);

  const handleRefresh = () => {
    fetchAdapters();
  };

  const handleDelete = async (adapterId: string) => {
    if (window.confirm('Are you sure you want to delete this adapter? This action cannot be undone.')) {
      try {
        await deleteAdapter(adapterId);
        if (onDeleteAdapter) {
          onDeleteAdapter(adapterId);
        }
      } catch (error) {
        console.error('Failed to delete adapter:', error);
      }
    }
  };

  // Filter adapters based on search and filters
  const filteredAdapters = adapters.filter((adapter) => {
    const matchesSearch =
      adapter.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      adapter.provider_name.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' ||
      (statusFilter === 'active' && adapter.is_active) ||
      (statusFilter === 'inactive' && !adapter.is_active);

    const matchesProvider = providerFilter === 'all' ||
      adapter.provider_name === providerFilter;

    return matchesSearch && matchesStatus && matchesProvider;
  });

  // Get unique provider names for filter dropdown
  const uniqueProviders = Array.from(
    new Set(adapters.map(adapter => adapter.provider_name))
  );

  const getStatusBadge = (isActive: boolean) => {
    return (
      <Badge variant={isActive ? 'default' : 'secondary'}>
        {isActive ? 'Active' : 'Inactive'}
      </Badge>
    );
  };

  const getProviderDisplayName = (providerName: string) => {
    const displayNames: Record<string, string> = {
      'alpha_vantage': 'Alpha Vantage',
      'yfinance': 'Yahoo Finance',
      'yahoo_finance': 'Yahoo Finance',
      'iex_cloud': 'IEX Cloud',
      'polygon': 'Polygon',
      'finnhub': 'Finnhub'
    };
    return displayNames[providerName] || providerName;
  };

  // Get real usage data from metrics and registry
  const getUsageData = (adapterId: string, isActive: boolean, providerName: string) => {
    if (!isActive) {
      return { used: 0, limit: 0, percentage: 0 };
    }

    const metrics = adapterMetrics[adapterId];
    if (!metrics) {
      console.log(`No metrics found for adapter ${adapterId}`);
      return { used: 0, limit: 0, percentage: 0 };
    }

    // Get daily limit from provider registry
    const provider = registry?.providers?.[providerName];
    const dailyLimit = provider?.rate_limits?.requests_per_day || 0;

    const used = metrics.requests_today || 0;
    const percentage = dailyLimit > 0 ? (used / dailyLimit) * 100 : 0;

    console.log(`Usage data for ${adapterId}: used=${used}, dailyLimit=${dailyLimit}, percentage=${percentage}`);
    console.log(`Full metrics object:`, metrics);

    return { used, limit: dailyLimit, percentage: Math.min(percentage, 100) };
  };

  // Get real cost data from metrics
  const getCostData = (adapterId: string) => {
    const metrics = adapterMetrics[adapterId];
    if (!metrics) {
      return { perCall: 0.0000, monthly: 0.00 };
    }

    // Use real cost data from metrics
    const perCall = metrics.total_requests > 0 ? metrics.total_cost / metrics.total_requests : 0;
    const monthly = metrics.monthly_cost_estimate || 0;

    return { perCall, monthly };
  };

  // Check if provider supports bulk operations from registry
  const supportsBulk = (providerName: string) => {
    if (!registry?.providers) return false;
    const provider = registry.providers[providerName];
    return provider?.supports_bulk || false;
  };

  // Get provider capabilities from registry
  const getProviderCapabilities = (providerName: string) => {
    if (!registry?.providers) return [];
    const provider = registry.providers[providerName];
    if (!provider) return [];

    const capabilities = [];
    if (provider.supports_bulk) capabilities.push('Bulk Queries');
    if (provider.rate_limits?.requests_per_day && provider.rate_limits.requests_per_day > 1000) {
      capabilities.push('High Volume');
    }
    capabilities.push('Real-time Data');

    return capabilities;
  };

  const handleToggleStatus = async (adapterId: string, currentStatus: boolean) => {
    console.log('handleToggleStatus called:', { adapterId, currentStatus, newStatus: !currentStatus });
    try {
      console.log('Calling updateAdapter...');
      await updateAdapter(adapterId, { is_active: !currentStatus });
      console.log('updateAdapter completed successfully');
      // The updateAdapter hook already updates the state, no need to fetch again
    } catch (error) {
      console.error('Failed to toggle adapter status:', error);
      // On error, refresh to get the current state
      await fetchAdapters();
    }
  };

  const handleAdapterClick = (adapterId: string) => {
    router.push(`/admin/adapters/${adapterId}`);
  };

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <p>Error loading adapters: {error}</p>
            <Button onClick={handleRefresh} className="mt-4">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl font-semibold text-gray-900">Data Providers</CardTitle>
            <CardDescription>
              Manage your market data provider configurations and usage
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleRefresh} variant="outline" size="sm">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search adapters by name or provider..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>

            <Select value={providerFilter} onValueChange={setProviderFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Providers</SelectItem>
                {uniqueProviders.map(provider => (
                  <SelectItem key={provider} value={provider}>
                    {getProviderDisplayName(provider)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 mx-auto animate-spin text-blue-600 mb-2" />
            <p className="text-gray-600">Loading adapters...</p>
          </div>
        ) : filteredAdapters.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600 mb-4">
              {adapters.length === 0
                ? 'No adapters configured yet'
                : 'No adapters match your current filters'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-b border-gray-200">
                  <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider py-3">
                    Provider
                  </TableHead>
                  <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider py-3">
                    Status
                  </TableHead>
                  <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider py-3">
                    Monthly API Calls
                  </TableHead>
                  <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider py-3">
                    Last Update
                  </TableHead>
                  <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider py-3">
                    Cost
                  </TableHead>
                  <TableHead className="text-xs font-medium text-gray-500 uppercase tracking-wider py-3">
                    Actions
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAdapters.map((adapter) => {
                  const usageData = getUsageData(adapter.id, adapter.is_active, adapter.provider_name);
                  const costData = getCostData(adapter.id);
                  const hasBulk = supportsBulk(adapter.provider_name);
                  const capabilities = getProviderCapabilities(adapter.provider_name);
                  const metrics = adapterMetrics[adapter.id];
                  const isMetricsLoading = metricsLoading[adapter.id];

                  return (
                    <TableRow
                      key={adapter.id}
                      className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleAdapterClick(adapter.id)}
                    >
                      {/* Provider Column */}
                      <TableCell className="py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                            <BarChart3 className="w-5 h-5 text-blue-600" />
                          </div>
                          <div>
                            <div className="font-medium text-gray-900">
                              {getProviderDisplayName(adapter.provider_name)}
                            </div>
                            <div className="text-sm text-gray-500 space-y-1">
                              <div>
                                {adapter.provider_name}
                                {hasBulk && (
                                  <Badge variant="secondary" className="ml-2 text-xs">
                                    <Zap className="w-3 h-3 mr-1" />
                                    Bulk Enabled
                                  </Badge>
                                )}
                              </div>
                              <div className="flex flex-wrap gap-1">
                                {capabilities.slice(0, 2).map((capability, index) => (
                                  <Badge key={index} variant="outline" className="text-xs px-1 py-0">
                                    {capability}
                                  </Badge>
                                ))}
                                {capabilities.length > 2 && (
                                  <Badge variant="outline" className="text-xs px-1 py-0">
                                    +{capabilities.length - 2} more
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </TableCell>

                      {/* Status Column */}
                      <TableCell className="py-4">
                        <div className="flex items-center gap-3">
                          <Badge
                            variant={adapter.is_active ? 'default' : 'secondary'}
                            className={adapter.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}
                          >
                            {adapter.is_active ? 'active' : 'inactive'}
                          </Badge>
                          {adapter.is_active && (
                            <span className="text-sm text-gray-500">
                              {adapter.provider_name === 'alpha_vantage' ? 'Disabled' : ''}
                            </span>
                          )}
                        </div>
                      </TableCell>

                      {/* Usage Column */}
                      <TableCell className="py-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="font-medium">
                              {isMetricsLoading ? 'Loading...' : `${usageData.used.toLocaleString()} / ${usageData.limit > 0 ? usageData.limit.toLocaleString() : 'Unlimited'}`}
                            </span>
                            <span className="text-gray-500">
                              {isMetricsLoading ? '—' : usageData.limit > 0 ? `${usageData.percentage.toFixed(1)}% used` : 'No limit'}
                            </span>
                          </div>
                          <Progress
                            value={usageData.percentage}
                            className="h-2 bg-gray-200"
                          />
                        </div>
                      </TableCell>

                      {/* Last Update Column */}
                      <TableCell className="py-4">
                        <div className="text-sm">
                          <div className="text-gray-900">
                            {metrics?.last_success_at
                              ? format(new Date(metrics.last_success_at), 'dd/MM/yyyy, h:mm:ss a')
                              : '—'
                            }
                          </div>
                          <div className="text-gray-500">
                            {isMetricsLoading
                              ? 'Loading...'
                              : `Calls today: ${usageData.used}`
                            }
                          </div>
                        </div>
                      </TableCell>

                      {/* Cost Column */}
                      <TableCell className="py-4">
                        <div className="text-sm">
                          <div className="text-gray-900 font-medium">
                            ${costData.perCall.toFixed(4)}/call
                          </div>
                          <div className="text-gray-500">
                            Monthly: ${costData.monthly.toFixed(2)}
                          </div>
                        </div>
                      </TableCell>

                      {/* Actions Column */}
                      <TableCell className="py-4" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-3">
                          <Switch
                            checked={adapter.is_active}
                            onCheckedChange={() => handleToggleStatus(adapter.id, adapter.is_active)}
                            className="data-[state=checked]:bg-green-600"
                          />
                          <span className="text-sm font-medium text-gray-700">
                            {adapter.is_active ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Results summary */}
        {!loading && filteredAdapters.length > 0 && (
          <div className="mt-4 text-sm text-gray-600 text-center">
            Showing {filteredAdapters.length} of {adapters.length} adapters
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AdapterList;