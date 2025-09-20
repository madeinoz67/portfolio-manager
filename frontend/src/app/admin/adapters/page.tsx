'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import AdapterList from '@/components/Admin/Adapters/AdapterList';
import AdapterConfigForm from '@/components/Admin/Adapters/AdapterConfigForm';
import AdapterMetricsView from '@/components/Admin/Adapters/AdapterMetricsView';
import AdapterHealthStatus from '@/components/Admin/Adapters/AdapterHealthStatus';
import { AdapterConfiguration } from '@/types/adapters';

type ViewMode = 'list' | 'create' | 'edit' | 'metrics' | 'health';

const AdminAdaptersPage: React.FC = () => {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedAdapter, setSelectedAdapter] = useState<AdapterConfiguration | null>(null);
  const [selectedAdapterId, setSelectedAdapterId] = useState<string | null>(null);

  const handleCreateAdapter = () => {
    setSelectedAdapter(null);
    setViewMode('create');
  };

  const handleEditAdapter = (adapter: AdapterConfiguration) => {
    setSelectedAdapter(adapter);
    setViewMode('edit');
  };

  const handleViewMetrics = (adapterId: string) => {
    setSelectedAdapterId(adapterId);
    setViewMode('metrics');
  };

  const handleViewHealth = (adapterId: string) => {
    setSelectedAdapterId(adapterId);
    setViewMode('health');
  };

  const handleDeleteAdapter = (adapterId: string) => {
    // Deletion is handled by the AdapterList component
    // Just refresh the list by staying in list mode
    setViewMode('list');
  };

  const handleFormSuccess = () => {
    // Return to list view after successful create/edit
    setViewMode('list');
    setSelectedAdapter(null);
  };

  const handleFormCancel = () => {
    // Return to list view on cancel
    setViewMode('list');
    setSelectedAdapter(null);
  };

  const handleClose = () => {
    // Return to list view from metrics/health view
    setViewMode('list');
    setSelectedAdapterId(null);
  };

  const renderContent = () => {
    switch (viewMode) {
      case 'create':
        return (
          <AdapterConfigForm
            mode="create"
            onSuccess={handleFormSuccess}
            onCancel={handleFormCancel}
          />
        );

      case 'edit':
        return (
          <AdapterConfigForm
            mode="edit"
            adapter={selectedAdapter}
            onSuccess={handleFormSuccess}
            onCancel={handleFormCancel}
          />
        );

      case 'metrics':
        return selectedAdapterId ? (
          <AdapterMetricsView
            adapterId={selectedAdapterId}
            onClose={handleClose}
          />
        ) : null;

      case 'health':
        return selectedAdapterId ? (
          <AdapterHealthStatus
            adapterId={selectedAdapterId}
            onClose={handleClose}
          />
        ) : null;

      case 'list':
      default:
        return (
          <AdapterList
            onCreateAdapter={handleCreateAdapter}
            onEditAdapter={handleEditAdapter}
            onDeleteAdapter={handleDeleteAdapter}
            onViewMetrics={handleViewMetrics}
          />
        );
    }
  };

  return (
    <div className="container mx-auto px-4 py-6 max-w-7xl">
      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Market Data Adapters
            </h1>
            <p className="text-gray-600 mt-1">
              Manage market data provider configurations and monitoring
            </p>
          </div>

          {/* Breadcrumb */}
          <nav className="flex items-center space-x-2 text-sm text-gray-500">
            <button
              onClick={() => router.push('/admin')}
              className="hover:text-gray-700 transition-colors"
            >
              Admin
            </button>
            <span>/</span>
            {viewMode !== 'list' && (
              <>
                <button
                  onClick={() => setViewMode('list')}
                  className="hover:text-gray-700 transition-colors"
                >
                  Adapters
                </button>
                <span>/</span>
              </>
            )}
            <span className="text-gray-900 font-medium">
              {viewMode === 'create' && 'Create Adapter'}
              {viewMode === 'edit' && 'Edit Adapter'}
              {viewMode === 'metrics' && 'Adapter Metrics'}
              {viewMode === 'health' && 'Health Status'}
              {viewMode === 'list' && 'Adapters'}
            </span>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-6">
        {renderContent()}
      </div>
    </div>
  );
};

export default AdminAdaptersPage;