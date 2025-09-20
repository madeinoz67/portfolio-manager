'use client';

import React, { useState, useEffect } from 'react';
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
import { formatDistanceToNow } from 'date-fns';

interface AdapterMetrics {
  adapter_id: string;
  provider_name: string;
  display_name: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;
  average_response_time_ms: number;
  total_cost: number;
  requests_today: number;
  requests_this_hour: number;
  last_request_at?: string;
  last_success_at?: string;
  last_failure_at?: string;
  current_status: 'healthy' | 'degraded' | 'down';
  uptime_percentage: number;
  rate_limit_hits: number;
  error_rate_24h: number;
  p95_response_time_ms: number;
  daily_cost: number;
  monthly_cost_estimate: number;
}

interface AdapterMetricsViewProps {
  adapterId: string;
  onClose?: () => void;
}

const AdapterMetricsView: React.FC<AdapterMetricsViewProps> = ({
  adapterId,
  onClose,
}) => {
  const [metrics, setMetrics] = useState<AdapterMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const response = await fetch(
        `/api/v1/admin/adapters/${adapterId}/metrics?timeRange=${timeRange}`,
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
      setMetrics(data);
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

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      healthy: { variant: 'default' as const, icon: CheckCircle, color: 'text-green-600' },
      degraded: { variant: 'secondary' as const, icon: AlertTriangle, color: 'text-yellow-600' },
      down: { variant: 'destructive' as const, icon: AlertTriangle, color: 'text-red-600' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.down;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className={`w-3 h-3 ${config.color}`} />
        {status.charAt(0).toUpperCase() + status.slice(1)}
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

  if (!metrics) {
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
                {metrics.display_name} Metrics
              </CardTitle>
              <CardDescription>
                Performance and usage metrics for {metrics.provider_name}
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
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
                Auto Refresh
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
                {getStatusBadge(metrics.current_status)}
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {formatPercentage(metrics.uptime_percentage)}
                </p>
                <p className="text-xs text-gray-500">Uptime</p>
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
                  {metrics.success_rate >= 95 ? (
                    <TrendingUp className="w-4 h-4 text-green-600" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-600" />
                  )}
                  <span className={`text-sm ${metrics.success_rate >= 95 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercentage(metrics.success_rate)}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {metrics.successful_requests}
                </p>
                <p className="text-xs text-gray-500">
                  of {metrics.total_requests} requests
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
                  <span className="text-sm text-blue-600">
                    P95: {formatResponseTime(metrics.p95_response_time_ms)}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {formatResponseTime(metrics.average_response_time_ms)}
                </p>
                <p className="text-xs text-gray-500">Average</p>
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
                    Est. Monthly: {formatCurrency(metrics.monthly_cost_estimate)}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(metrics.daily_cost)}
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
              <span className="text-sm font-medium">Requests Today</span>
              <span className="text-lg font-semibold">{metrics.requests_today}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Requests This Hour</span>
              <span className="text-lg font-semibold">{metrics.requests_this_hour}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Failed Requests</span>
              <span className="text-lg font-semibold text-red-600">
                {metrics.failed_requests}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Rate Limit Hits</span>
              <span className="text-lg font-semibold text-yellow-600">
                {metrics.rate_limit_hits}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">24h Error Rate</span>
              <span className={`text-lg font-semibold ${metrics.error_rate_24h > 5 ? 'text-red-600' : 'text-green-600'}`}>
                {formatPercentage(metrics.error_rate_24h)}
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
              <span className="text-sm font-medium">Total Cost</span>
              <span className="text-lg font-semibold">{formatCurrency(metrics.total_cost)}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Daily Cost</span>
              <span className="text-lg font-semibold">{formatCurrency(metrics.daily_cost)}</span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Monthly Estimate</span>
              <span className="text-lg font-semibold text-blue-600">
                {formatCurrency(metrics.monthly_cost_estimate)}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Cost per Request</span>
              <span className="text-lg font-semibold">
                {metrics.total_requests > 0
                  ? formatCurrency(metrics.total_cost / metrics.total_requests)
                  : formatCurrency(0)
                }
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
          {metrics.last_request_at && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Last Request</span>
              <span className="text-sm text-gray-600">
                {formatDistanceToNow(new Date(metrics.last_request_at), { addSuffix: true })}
              </span>
            </div>
          )}

          {metrics.last_success_at && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Last Success</span>
              <span className="text-sm text-green-600">
                {formatDistanceToNow(new Date(metrics.last_success_at), { addSuffix: true })}
              </span>
            </div>
          )}

          {metrics.last_failure_at && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Last Failure</span>
              <span className="text-sm text-red-600">
                {formatDistanceToNow(new Date(metrics.last_failure_at), { addSuffix: true })}
              </span>
            </div>
          )}

          {!metrics.last_request_at && !metrics.last_success_at && !metrics.last_failure_at && (
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