'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  BarChart3,
  DollarSign,
} from 'lucide-react';
import { getRelativeTime } from '@/utils/timezone';

interface CurrentMetrics {
  adapter_id: string;
  provider_name: string;
  is_healthy: boolean;
  is_active: boolean;
  last_check: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  avg_latency_ms: number;
  min_latency_ms: number;
  max_latency_ms: number;
  p95_latency_ms: number;
  requests_per_minute: number;
  rate_limit_remaining?: number;
  rate_limit_reset_time?: string;
  error_count_24h: number;
  last_error?: string;
  last_error_time?: string;
  circuit_breaker_state: string;
  circuit_breaker_failure_count: number;
  circuit_breaker_next_attempt?: string;
}

interface CostMetrics {
  daily_cost: number;
  daily_budget?: number;
  daily_budget_used_percent: number;
  monthly_cost: number;
  monthly_budget?: number;
  monthly_budget_used_percent: number;
  cost_per_request: number;
  cost_per_successful_request: number;
  budget_status: string;
  budget_remaining_daily?: number;
  budget_remaining_monthly?: number;
  cost_alerts: string[];
  projected_daily_cost?: number;
  projected_monthly_cost?: number;
}

interface AdapterMetrics {
  adapter_id: string;
  provider_name: string;
  current_metrics: CurrentMetrics;
  cost_metrics?: CostMetrics;
  historical_data?: any[];
  active_alerts: any[];
  last_updated: string;
}

interface AdapterMetricsViewProps {
  adapterId: string;
  onClose?: () => void;
}

const AdapterMetricsView: React.FC<AdapterMetricsViewProps> = ({
  adapterId,
  onClose,
}) => {
  const { token, isAdmin } = useAuth();
  const [metricsData, setMetricsData] = useState<AdapterMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!token) {
        throw new Error('No authentication token available');
      }

      if (!isAdmin()) {
        throw new Error('Admin access required');
      }
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/admin/adapters/${adapterId}/metrics?timeRange=${timeRange}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.statusText}`);
      }

      const data = await response.json();
      setMetricsData(data);
    } catch (err) {
      console.error('Error fetching adapter metrics:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, [adapterId, timeRange]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(fetchMetrics, 30000); // Refresh every 30 seconds
    }
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [autoRefresh, adapterId, timeRange]);

  const getStatusBadge = (isHealthy: boolean) => {
    if (isHealthy) {
      return (
        <Badge variant="default" className="flex items-center gap-1">
          <CheckCircle className="w-3 h-3 text-green-600" />
          Healthy
        </Badge>
      );
    }
    return (
      <Badge variant="destructive" className="flex items-center gap-1">
        <AlertTriangle className="w-3 h-3 text-red-600" />
        Unhealthy
      </Badge>
    );
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const formatResponseTime = (ms: number) => {
    if (ms < 1000) {
      return `${ms.toFixed(0)}ms`;
    }
    return `${(ms / 1000).toFixed(1)}s`;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 mx-auto animate-spin text-blue-600 mb-2" />
            <p className="text-gray-600">Loading metrics...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
            <p>Error loading metrics: {error}</p>
            <Button onClick={fetchMetrics} className="mt-4" variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!metricsData) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-600">
            <BarChart3 className="w-8 h-8 mx-auto mb-2" />
            <p>No metrics available for this adapter</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                {metricsData.provider_name} Metrics
              </CardTitle>
              <CardDescription>
                Performance and usage metrics for adapter {metricsData.adapter_id}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">Last Hour</SelectItem>
                  <SelectItem value="24h">Last 24 Hours</SelectItem>
                  <SelectItem value="7d">Last 7 Days</SelectItem>
                  <SelectItem value="30d">Last 30 Days</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={autoRefresh ? 'bg-blue-50 border-blue-200' : ''}
                title={autoRefresh ? 'Auto refresh enabled (30s intervals) - click to disable' : 'Click to enable auto refresh every 30 seconds'}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
                {autoRefresh ? 'Auto ON' : 'Auto Refresh'}
              </Button>

              <Button onClick={fetchMetrics} variant="outline" size="sm">
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>

              {onClose && (
                <Button onClick={onClose} variant="outline" size="sm">
                  Close
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Status</p>
                {getStatusBadge(metricsData.current_metrics.is_healthy)}
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {metricsData.current_metrics.is_healthy ? '100%' : '0%'}
                </p>
                <p className="text-xs text-gray-500">Health</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <div className="flex items-center gap-1 mt-1">
                  {metricsData.current_metrics.success_rate >= 0.95 ? (
                    <TrendingUp className="w-4 h-4 text-green-600" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-600" />
                  )}
                  <span className={`text-sm ${metricsData.current_metrics.success_rate >= 0.95 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(metricsData.current_metrics.success_rate * 100)}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {metricsData.current_metrics.successful_requests}
                </p>
                <p className="text-xs text-gray-500">
                  of {metricsData.current_metrics.total_requests} requests
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Response Time</p>
                <div className="flex items-center gap-1 mt-1">
                  <Clock className="w-4 h-4 text-blue-600" />
                  <span className={`text-sm ${metricsData.current_metrics.p95_latency_ms === 0 ? 'text-amber-600' : 'text-blue-600'}`}>
                    P95: {formatResponseTime(metricsData.current_metrics.p95_latency_ms)}
                    {metricsData.current_metrics.p95_latency_ms === 0 && ' (no data)'}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-2xl font-bold ${metricsData.current_metrics.avg_latency_ms === 0 ? 'text-amber-600' : 'text-gray-900'}`}>
                  {formatResponseTime(metricsData.current_metrics.avg_latency_ms)}
                </p>
                <p className="text-xs text-gray-500">
                  {metricsData.current_metrics.avg_latency_ms === 0 ? 'No data' : 'Average'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Daily Cost</p>
                <div className="flex items-center gap-1 mt-1">
                  <DollarSign className="w-4 h-4 text-green-600" />
                  <span className="text-sm text-gray-500">
                    Est. Monthly: {formatCurrency(metricsData.cost_metrics?.projected_monthly_cost || 0)}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(metricsData.cost_metrics?.daily_cost || 0)}
                </p>
                <p className="text-xs text-gray-500">Today</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Request Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Request Statistics</CardTitle>
            <CardDescription>Request volume and error rates</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Requests per Minute</span>
              <span className="text-lg font-semibold">{metricsData.current_metrics.requests_per_minute || 0}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Circuit Breaker Failures</span>
              <span className="text-lg font-semibold">{metricsData.current_metrics.circuit_breaker_failure_count || 0}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Failed Requests</span>
              <span className="text-lg font-semibold text-red-600">
                {metricsData.current_metrics.failed_requests}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Rate Limit Remaining</span>
              <span className="text-lg font-semibold text-yellow-600">
                {metricsData.current_metrics.rate_limit_remaining || 'N/A'}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">24h Error Count</span>
              <span className={`text-lg font-semibold ${metricsData.current_metrics.error_count_24h > 5 ? 'text-red-600' : 'text-green-600'}`}>
                {metricsData.current_metrics.error_count_24h}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Cost Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Cost Analysis</CardTitle>
            <CardDescription>Usage costs and estimates</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Monthly Cost</span>
              <span className="text-lg font-semibold">{formatCurrency(metricsData.cost_metrics?.monthly_cost || 0)}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Daily Cost</span>
              <span className="text-lg font-semibold">{formatCurrency(metricsData.cost_metrics?.daily_cost || 0)}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Monthly Estimate</span>
              <span className="text-lg font-semibold text-blue-600">
                {formatCurrency(metricsData.cost_metrics?.projected_monthly_cost || metricsData.cost_metrics?.monthly_cost || 0)}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Cost per Request</span>
              <span className="text-lg font-semibold">
                {formatCurrency(metricsData.cost_metrics?.cost_per_request || 0)}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Activity</CardTitle>
          <CardDescription>Latest request timestamps</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {metricsData.last_updated && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Last Updated</span>
              <span className="text-sm text-gray-600">
                {getRelativeTime(metricsData.last_updated)}
              </span>
            </div>
          )}

          {metricsData.current_metrics.last_error_time && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Last Error</span>
              <span className="text-sm text-red-600">
                {getRelativeTime(metricsData.current_metrics.last_error_time)}
              </span>
            </div>
          )}

          {metricsData.current_metrics.circuit_breaker_state !== 'closed' && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Circuit Breaker</span>
              <span className="text-sm text-yellow-600">
                {metricsData.current_metrics.circuit_breaker_state}
              </span>
            </div>
          )}

          {!metricsData.last_updated && !metricsData.current_metrics.last_error_time && (
            <div className="text-center text-gray-500 py-4">
              No recent activity recorded
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdapterMetricsView;