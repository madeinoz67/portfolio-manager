'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Activity,
  Shield,
  Settings,
  BarChart3,
  RefreshCw,
} from 'lucide-react';
import AdapterConfigForm from '@/components/admin/Adapters/AdapterConfigForm';
import AdapterMetricsView from '@/components/admin/Adapters/AdapterMetricsView';
import AdapterHealthStatus from '@/components/admin/Adapters/AdapterHealthStatus';
import { AdapterConfiguration } from '@/types/adapters';
import { formatDistanceToNow } from 'date-fns';

type ViewMode = 'overview' | 'edit';

const AdapterDetailPage: React.FC = () => {
  const router = useRouter();
  const params = useParams();
  const adapterId = params.id as string;

  const [adapter, setAdapter] = useState<AdapterConfiguration | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('overview');
  const [activeTab, setActiveTab] = useState('overview');

  const fetchAdapter = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/admin/adapters/${adapterId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Adapter not found');
        }
        throw new Error(`Failed to fetch adapter: ${response.statusText}`);
      }

      const data = await response.json();
      setAdapter(data);
    } catch (err) {
      console.error('Error fetching adapter:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch adapter');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!adapter) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete the adapter "${adapter.display_name}"? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/admin/adapters/${adapterId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete adapter: ${response.statusText}`);
      }

      // Redirect to adapters list after successful deletion
      router.push('/admin/adapters');
    } catch (err) {
      console.error('Error deleting adapter:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete adapter');
    }
  };

  const handleEditSuccess = () => {
    setViewMode('overview');
    fetchAdapter(); // Refresh adapter data
  };

  const handleEditCancel = () => {
    setViewMode('overview');
  };

  useEffect(() => {
    if (adapterId) {
      fetchAdapter();
    }
  }, [adapterId]);

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

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading adapter details...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-red-600">
              <p className="mb-4">{error}</p>
              <div className="space-x-2">
                <Button onClick={fetchAdapter} variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
                <Button
                  onClick={() => router.push('/admin/adapters')}
                  variant="outline"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Adapters
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!adapter) {
    return (
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <Card>
          <CardContent className="p-6">
            <div className="text-center text-gray-600">
              <p>Adapter not found</p>
              <Button
                onClick={() => router.push('/admin/adapters')}
                className="mt-4"
                variant="outline"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Adapters
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (viewMode === 'edit') {
    return (
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="mb-6">
          <Button
            onClick={handleEditCancel}
            variant="outline"
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Overview
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">
            Edit Adapter: {adapter.display_name}
          </h1>
        </div>

        <AdapterConfigForm
          mode="edit"
          adapter={adapter}
          onSuccess={handleEditSuccess}
          onCancel={handleEditCancel}
        />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <Button
          onClick={() => router.push('/admin/adapters')}
          variant="outline"
          className="mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Adapters
        </Button>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              {adapter.display_name}
              {getStatusBadge(adapter.is_active)}
            </h1>
            <p className="text-gray-600 mt-1">
              {getProviderDisplayName(adapter.provider_name)} adapter configuration
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={() => setViewMode('edit')}
              variant="outline"
              size="sm"
            >
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </Button>

            <Button
              onClick={handleDelete}
              variant="outline"
              size="sm"
              className="text-red-600 hover:text-red-700 border-red-200 hover:border-red-300"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="metrics" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Metrics
          </TabsTrigger>
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            Health
          </TabsTrigger>
          <TabsTrigger value="activity" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Activity
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Configuration Details */}
          <Card>
            <CardHeader>
              <CardTitle>Configuration Details</CardTitle>
              <CardDescription>
                Current adapter configuration and settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Provider</label>
                  <p className="text-lg font-semibold">
                    {getProviderDisplayName(adapter.provider_name)}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Display Name</label>
                  <p className="text-lg font-semibold">{adapter.display_name}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Status</label>
                  <div className="mt-1">
                    {getStatusBadge(adapter.is_active)}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Priority</label>
                  <p className="text-lg font-semibold">{adapter.priority}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Created</label>
                  <p className="text-lg">
                    {formatDistanceToNow(new Date(adapter.created_at), { addSuffix: true })}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Last Updated</label>
                  <p className="text-lg">
                    {formatDistanceToNow(new Date(adapter.updated_at), { addSuffix: true })}
                  </p>
                </div>
              </div>

              {adapter.description && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Description</label>
                  <p className="text-gray-800 mt-1">{adapter.description}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Provider Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Provider Settings</CardTitle>
              <CardDescription>
                Provider-specific configuration parameters
              </CardDescription>
            </CardHeader>
            <CardContent>
              {adapter.config && Object.keys(adapter.config).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(adapter.config).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center">
                      <span className="font-medium text-gray-700 capitalize">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className="text-gray-600">
                        {key.toLowerCase().includes('key') || key.toLowerCase().includes('secret')
                          ? '••••••••'
                          : String(value)
                        }
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No additional configuration parameters</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics">
          <AdapterMetricsView adapterId={adapter.id} />
        </TabsContent>

        <TabsContent value="health">
          <AdapterHealthStatus adapterId={adapter.id} />
        </TabsContent>

        <TabsContent value="activity">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Recent adapter operations and events
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-gray-500 py-8">
                <Activity className="w-8 h-8 mx-auto mb-2" />
                <p>Activity logs will be displayed here</p>
                <p className="text-sm">Feature coming soon</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdapterDetailPage;