/**
 * API client for adapter management operations
 */

import { AdapterConfiguration, CreateAdapterRequest, UpdateAdapterRequest } from '@/types/adapters';

export interface AdapterMetrics {
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

export interface AdapterHealth {
  adapter_id: string;
  provider_name: string;
  display_name: string;
  overall_status: 'healthy' | 'degraded' | 'down';
  last_check_at: string;
  uptime_percentage: number;
  checks: HealthCheck[];
  next_check_in: number;
  check_interval: number;
  consecutive_failures: number;
  last_success_at?: string;
  last_failure_at?: string;
}

export interface HealthCheck {
  check_type: string;
  status: 'healthy' | 'warning' | 'critical';
  message: string;
  response_time_ms?: number;
  checked_at: string;
  details?: Record<string, any>;
}

export interface ProviderRegistry {
  providers: {
    [key: string]: {
      name: string;
      display_name: string;
      description: string;
      required_config: string[];
      optional_config: string[];
      supports_bulk: boolean;
      rate_limits: {
        requests_per_minute?: number;
        requests_per_day?: number;
        symbols_per_request?: number;
      };
    };
  };
}

class AdaptersApiClient {
  private baseUrl = '/api/v1/admin/adapters';

  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `Request failed: ${response.status} ${response.statusText}`;

      try {
        const errorData = await response.json();
        if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch {
        // Ignore JSON parsing errors, use default message
      }

      throw new Error(errorMessage);
    }

    return response.json();
  }

  /**
   * Fetch all adapter configurations
   */
  async getAdapters(): Promise<AdapterConfiguration[]> {
    const response = await fetch(this.baseUrl, {
      headers: await this.getAuthHeaders(),
    });

    return this.handleResponse<AdapterConfiguration[]>(response);
  }

  /**
   * Fetch a specific adapter configuration by ID
   */
  async getAdapter(id: string): Promise<AdapterConfiguration> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      headers: await this.getAuthHeaders(),
    });

    return this.handleResponse<AdapterConfiguration>(response);
  }

  /**
   * Create a new adapter configuration
   */
  async createAdapter(data: CreateAdapterRequest): Promise<AdapterConfiguration> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<AdapterConfiguration>(response);
  }

  /**
   * Update an existing adapter configuration
   */
  async updateAdapter(id: string, data: UpdateAdapterRequest): Promise<AdapterConfiguration> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PUT',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<AdapterConfiguration>(response);
  }

  /**
   * Delete an adapter configuration
   */
  async deleteAdapter(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to delete adapter: ${response.status} ${response.statusText}`);
    }
  }

  /**
   * Fetch adapter metrics
   */
  async getAdapterMetrics(id: string, timeRange: string = '24h'): Promise<AdapterMetrics> {
    const response = await fetch(`${this.baseUrl}/${id}/metrics?timeRange=${timeRange}`, {
      headers: await this.getAuthHeaders(),
    });

    return this.handleResponse<AdapterMetrics>(response);
  }

  /**
   * Fetch adapter health status
   */
  async getAdapterHealth(id: string): Promise<AdapterHealth> {
    const response = await fetch(`${this.baseUrl}/${id}/health`, {
      headers: await this.getAuthHeaders(),
    });

    return this.handleResponse<AdapterHealth>(response);
  }

  /**
   * Trigger a health check for an adapter
   */
  async triggerHealthCheck(id: string): Promise<AdapterHealth> {
    const response = await fetch(`${this.baseUrl}/${id}/health`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    });

    return this.handleResponse<AdapterHealth>(response);
  }

  /**
   * Fetch provider registry information
   */
  async getProviderRegistry(): Promise<ProviderRegistry> {
    const response = await fetch(`${this.baseUrl}/registry`, {
      headers: await this.getAuthHeaders(),
    });

    return this.handleResponse<ProviderRegistry>(response);
  }

  /**
   * Test adapter connectivity
   */
  async testAdapter(data: CreateAdapterRequest | UpdateAdapterRequest): Promise<{
    success: boolean;
    message: string;
    response_time_ms?: number;
    error_details?: string;
  }> {
    const response = await fetch(`${this.baseUrl}/test`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<{
      success: boolean;
      message: string;
      response_time_ms?: number;
      error_details?: string;
    }>(response);
  }

  /**
   * Validate adapter configuration
   */
  async validateAdapter(data: CreateAdapterRequest | UpdateAdapterRequest): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    const response = await fetch(`${this.baseUrl}/validate`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    return this.handleResponse<{
      valid: boolean;
      errors: string[];
      warnings: string[];
    }>(response);
  }

  /**
   * Get adapter activity logs
   */
  async getAdapterActivity(id: string, limit: number = 50): Promise<{
    activities: Array<{
      id: string;
      activity_type: string;
      description: string;
      status: string;
      timestamp: string;
      metadata?: Record<string, any>;
    }>;
    total: number;
  }> {
    const response = await fetch(`${this.baseUrl}/${id}/activity?limit=${limit}`, {
      headers: await this.getAuthHeaders(),
    });

    return this.handleResponse<{
      activities: Array<{
        id: string;
        activity_type: string;
        description: string;
        status: string;
        timestamp: string;
        metadata?: Record<string, any>;
      }>;
      total: number;
    }>(response);
  }

  /**
   * Bulk update adapter statuses
   */
  async bulkUpdateAdapters(updates: Array<{
    id: string;
    is_active?: boolean;
    priority?: number;
  }>): Promise<{
    updated: number;
    errors: Array<{
      id: string;
      error: string;
    }>;
  }> {
    const response = await fetch(`${this.baseUrl}/bulk-update`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ updates }),
    });

    return this.handleResponse<{
      updated: number;
      errors: Array<{
        id: string;
        error: string;
      }>;
    }>(response);
  }

  /**
   * Export adapter configurations
   */
  async exportAdapters(format: 'json' | 'yaml' = 'json'): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/export?format=${format}`, {
      headers: await this.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to export adapters: ${response.status} ${response.statusText}`);
    }

    return response.blob();
  }

  /**
   * Import adapter configurations
   */
  async importAdapters(file: File, overwrite: boolean = false): Promise<{
    imported: number;
    updated: number;
    errors: Array<{
      adapter: string;
      error: string;
    }>;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('overwrite', overwrite.toString());

    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${this.baseUrl}/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    return this.handleResponse<{
      imported: number;
      updated: number;
      errors: Array<{
        adapter: string;
        error: string;
      }>;
    }>(response);
  }
}

// Export singleton instance
export const adaptersApi = new AdaptersApiClient();
export default adaptersApi;