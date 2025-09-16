export interface Portfolio {
  id: string
  name: string
  description?: string
  total_value: string
  daily_change: string
  daily_change_percent: string
  created_at: string
  updated_at: string
  price_last_updated?: string
}

export interface CreatePortfolioData {
  name: string
  description: string
}