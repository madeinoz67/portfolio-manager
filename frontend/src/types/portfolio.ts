export interface Portfolio {
  id: string
  name: string
  description?: string

  // Portfolio value
  total_value: string

  // Daily P&L - movement from previous close to current price
  daily_change: string
  daily_change_percent: string

  // Unrealized P&L - total gain/loss from purchase cost to current value
  unrealized_gain_loss: string
  unrealized_gain_loss_percent: string

  created_at: string
  updated_at: string
  price_last_updated?: string
}

export interface CreatePortfolioData {
  name: string
  description: string
}