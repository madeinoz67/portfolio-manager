'use client';

import React, { useState, useEffect } from 'react';
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
  Plus,
  RefreshCw,
  Filter
} from 'lucide-react';
import { useAdapters } from '@/hooks/useAdapters';
import { AdapterConfiguration } from '@/types/adapters';
import { formatDistanceToNow } from 'date-fns';

interface AdapterListProps {
  onCreateAdapter?: () => void;
  onEditAdapter?: (adapter: AdapterConfiguration) => void;
  onDeleteAdapter?: (adapterId: string) => void;
  onViewMetrics?: (adapterId: string) => void;
}

const AdapterList: React.FC<AdapterListProps> = ({
  onCreateAdapter,
  onEditAdapter,
  onDeleteAdapter,
  onViewMetrics,
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
  } = useAdapters();

  useEffect(() => {
    fetchAdapters();
  }, []);

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
      'yahoo_finance': 'Yahoo Finance',
      'iex_cloud': 'IEX Cloud',
      'polygon': 'Polygon',
      'finnhub': 'Finnhub'
    };
    return displayNames[providerName] || providerName;
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
            <CardTitle>Market Data Adapters</CardTitle>
            <CardDescription>
              Manage market data provider configurations and monitoring
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleRefresh} variant="outline" size="sm">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            {onCreateAdapter && (
              <Button onClick={onCreateAdapter} size="sm">
                <Plus className="w-4 h-4 mr-2" />
                Add Adapter
              </Button>
            )}
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
            {adapters.length === 0 && onCreateAdapter && (
              <Button onClick={onCreateAdapter}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Adapter
              </Button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Provider</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAdapters.map((adapter) => (
                  <TableRow key={adapter.id}>
                    <TableCell className="font-medium">
                      {adapter.display_name}
                    </TableCell>
                    <TableCell>
                      {getProviderDisplayName(adapter.provider_name)}
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(adapter.is_active)}
                    </TableCell>
                    <TableCell className="text-gray-600">
                      {formatDistanceToNow(new Date(adapter.created_at), {
                        addSuffix: true
                      })}
                    </TableCell>
                    <TableCell className="text-gray-600">
                      {formatDistanceToNow(new Date(adapter.updated_at), {
                        addSuffix: true
                      })}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-2">
                        {onViewMetrics && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onViewMetrics(adapter.id)}
                            title="View Metrics"
                          >
                            <Activity className="w-4 h-4" />
                          </Button>
                        )}

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {/* View details */}}
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>

                        {onEditAdapter && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onEditAdapter(adapter)}
                            title="Edit Adapter"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                        )}

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(adapter.id)}
                          className="text-red-600 hover:text-red-700"
                          title="Delete Adapter"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
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