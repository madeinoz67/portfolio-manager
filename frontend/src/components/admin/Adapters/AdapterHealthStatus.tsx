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
import { Progress } from '@/components/ui/progress';
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Clock,
  Zap,
  Shield,
  Activity,
  Wifi,
  Server,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface HealthCheck {
  check_type: string;
  status: 'healthy' | 'warning' | 'critical';
  message: string;
  response_time_ms?: number;
  checked_at: string;
  details?: Record<string, any>;
}

interface AdapterHealth {
  adapter_id: string;
  provider_name: string;
  display_name: string;
  overall_status: 'healthy' | 'degraded' | 'down';
  last_check_at: string;
  uptime_percentage: number;
  checks: HealthCheck[];
  next_check_in: number; // seconds until next check
  check_interval: number; // check interval in seconds
  consecutive_failures: number;
  last_success_at?: string;
  last_failure_at?: string;
}

interface AdapterHealthStatusProps {
  adapterId: string;
  onClose?: () => void;
  compact?: boolean;
}

const AdapterHealthStatus: React.FC<AdapterHealthStatusProps> = ({
  adapterId,
  onClose,
  compact = false,
}) => {
  const [health, setHealth] = useState<AdapterHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggeringCheck, setTriggeringCheck] = useState(false);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      const response = await fetch(
        `/api/v1/admin/adapters/${adapterId}/health`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch health status: ${response.statusText}`);
      }

      const data = await response.json();
      setHealth(data);
    } catch (err) {
      console.error('Error fetching adapter health:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch health status');
    } finally {
      setLoading(false);
    }
  };

  const triggerHealthCheck = async () => {
    try {
      setTriggeringCheck(true);

      const token = localStorage.getItem('token');
      const response = await fetch(
        `/api/v1/admin/adapters/${adapterId}/health`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to trigger health check: ${response.statusText}`);
      }

      // Refresh health data after triggering check
      setTimeout(fetchHealth, 2000); // Wait 2 seconds for check to complete
    } catch (err) {
      console.error('Error triggering health check:', err);
      setError(err instanceof Error ? err.message : 'Failed to trigger health check');
    } finally {
      setTriggeringCheck(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, [adapterId]);

  useEffect(() => {
    // Auto-refresh health status every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [adapterId]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'warning':
      case 'degraded':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      case 'critical':
      case 'down':
        return <XCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      healthy: { variant: 'default' as const, color: 'bg-green-100 text-green-800' },
      warning: { variant: 'secondary' as const, color: 'bg-yellow-100 text-yellow-800' },
      degraded: { variant: 'secondary' as const, color: 'bg-yellow-100 text-yellow-800' },
      critical: { variant: 'destructive' as const, color: 'bg-red-100 text-red-800' },
      down: { variant: 'destructive' as const, color: 'bg-red-100 text-red-800' },
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.critical;

    return (
      <Badge variant={config.variant} className={`${config.color} flex items-center gap-1`}>
        {getStatusIcon(status)}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getCheckIcon = (checkType: string) => {
    switch (checkType) {
      case 'connectivity':
        return <Wifi className="w-4 h-4" />;
      case 'authentication':
        return <Shield className="w-4 h-4" />;
      case 'api_response':
        return <Server className="w-4 h-4" />;
      case 'rate_limit':
        return <Zap className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const formatResponseTime = (ms: number) => {
    if (ms < 1000) {
      return `${ms.toFixed(0)}ms`;
    }
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatNextCheck = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds}s`;
    }
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <Card className={compact ? 'h-32' : ''}>
        <CardContent className="p-6">
          <div className="text-center py-4">
            <RefreshCw className="w-6 h-6 mx-auto animate-spin text-blue-600 mb-2" />
            <p className="text-sm text-gray-600">Loading health status...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={compact ? 'h-32' : ''}>
        <CardContent className="p-6">
          <div className="text-center text-red-600">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2" />
            <p className="text-sm">Error: {error}</p>
            <Button onClick={fetchHealth} className="mt-2" variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!health) {
    return (
      <Card className={compact ? 'h-32' : ''}>
        <CardContent className="p-6">
          <div className="text-center text-gray-600">
            <Activity className="w-6 h-6 mx-auto mb-2" />
            <p className="text-sm">No health data available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (compact) {
    return (
      <Card className="h-32">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {getStatusIcon(health.overall_status)}
              <span className="font-medium text-sm">{health.display_name}</span>
            </div>
            {getStatusBadge(health.overall_status)}
          </div>

          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-600">
              <span>Uptime</span>
              <span>{health.uptime_percentage.toFixed(1)}%</span>
            </div>
            <Progress value={health.uptime_percentage} className="h-1" />

            <div className="flex justify-between text-xs text-gray-500">
              <span>Last check</span>
              <span>
                {formatDistanceToNow(new Date(health.last_check_at), { addSuffix: true })}
              </span>
            </div>
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
                {health.display_name} Health Status
              </CardTitle>
              <CardDescription>
                Real-time health monitoring for {health.provider_name}
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={triggerHealthCheck}
                disabled={triggeringCheck}
                variant="outline"
                size="sm"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${triggeringCheck ? 'animate-spin' : ''}`} />
                {triggeringCheck ? 'Checking...' : 'Check Now'}
              </Button>

              <Button onClick={fetchHealth} variant="outline" size="sm">
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

      {/* Overall Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overall Status</p>
                {getStatusBadge(health.overall_status)}
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {health.uptime_percentage.toFixed(1)}%
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
                <p className="text-sm font-medium text-gray-600">Last Check</p>
                <div className="flex items-center gap-1 mt-1">
                  <Clock className="w-4 h-4 text-blue-600" />
                  <span className="text-sm text-blue-600">
                    {formatDistanceToNow(new Date(health.last_check_at), { addSuffix: true })}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-gray-900">
                  {formatNextCheck(health.next_check_in)}
                </p>
                <p className="text-xs text-gray-500">Next check</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Failures</p>
                <div className="flex items-center gap-1 mt-1">
                  <AlertTriangle className={`w-4 h-4 ${health.consecutive_failures > 0 ? 'text-red-600' : 'text-gray-400'}`} />
                  <span className={`text-sm ${health.consecutive_failures > 0 ? 'text-red-600' : 'text-gray-600'}`}>
                    Consecutive
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-2xl font-bold ${health.consecutive_failures > 0 ? 'text-red-600' : 'text-gray-900'}`}>
                  {health.consecutive_failures}
                </p>
                <p className="text-xs text-gray-500">Failures</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Health Checks */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Health Checks</CardTitle>
          <CardDescription>Individual component health status</CardDescription>
        </CardHeader>
        <CardContent>
          {health.checks.length === 0 ? (
            <div className="text-center text-gray-500 py-4">
              No health checks configured
            </div>
          ) : (
            <div className="space-y-3">
              {health.checks.map((check, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {getCheckIcon(check.check_type)}
                    <div>
                      <p className="font-medium capitalize">
                        {check.check_type.replace('_', ' ')}
                      </p>
                      <p className="text-sm text-gray-600">{check.message}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    {check.response_time_ms && (
                      <div className="text-right text-sm">
                        <p className="font-medium">{formatResponseTime(check.response_time_ms)}</p>
                        <p className="text-gray-500">Response</p>
                      </div>
                    )}

                    <div className="text-right text-sm">
                      <p className="text-gray-500">
                        {formatDistanceToNow(new Date(check.checked_at), { addSuffix: true })}
                      </p>
                    </div>

                    {getStatusBadge(check.status)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Activity</CardTitle>
          <CardDescription>Latest success and failure timestamps</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {health.last_success_at && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                Last Success
              </span>
              <span className="text-sm text-green-600">
                {formatDistanceToNow(new Date(health.last_success_at), { addSuffix: true })}
              </span>
            </div>
          )}

          {health.last_failure_at && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium flex items-center gap-2">
                <XCircle className="w-4 h-4 text-red-600" />
                Last Failure
              </span>
              <span className="text-sm text-red-600">
                {formatDistanceToNow(new Date(health.last_failure_at), { addSuffix: true })}
              </span>
            </div>
          )}

          <div className="flex justify-between items-center">
            <span className="text-sm font-medium flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" />
              Check Interval
            </span>
            <span className="text-sm text-blue-600">
              Every {Math.floor(health.check_interval / 60)} minutes
            </span>
          </div>

          {!health.last_success_at && !health.last_failure_at && (
            <div className="text-center text-gray-500 py-4">
              No recent activity recorded
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdapterHealthStatus;