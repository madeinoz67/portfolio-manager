export type ProviderType = 'alpha_vantage' | 'yahoo_finance' | 'iex_cloud' | 'finnhub' | 'twelvedata'

export interface AdapterConfiguration {
  id: string
  provider_name: string
  display_name: string
  is_active: boolean
  priority: number
  config_data: Record<string, any>
  created_at: string
  updated_at: string
}

export interface AdapterHealth {
  provider_id: string
  status: 'healthy' | 'degraded' | 'unhealthy'
  response_time_ms?: number
  error_message?: string
  checked_at: string
}

export interface AdapterMetrics {
  provider_id: string
  metric_type: string
  metric_value: number
  recorded_at: string
}

export interface CreateAdapterRequest {
  provider_name: string
  display_name: string
  is_active: boolean
  priority: number
  config_data: Record<string, any>
}

export interface UpdateAdapterRequest {
  display_name?: string
  is_active?: boolean
  priority?: number
  config_data?: Record<string, any>
}