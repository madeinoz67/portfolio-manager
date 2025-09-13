export type TransactionType = 'BUY' | 'SELL' | 'DIVIDEND' | 'STOCK_SPLIT' | 'REVERSE_SPLIT' | 'TRANSFER_IN' | 'TRANSFER_OUT' | 'SPIN_OFF' | 'MERGER' | 'BONUS_SHARES'

export type SourceType = 'MANUAL' | 'IMPORTED' | 'EMAIL'

export interface Stock {
  id: string
  symbol: string
  company_name: string
  exchange?: string
  sector?: string
  market_cap?: string
  current_price?: string
}

export interface Transaction {
  id: string
  stock: Stock
  transaction_type: TransactionType
  quantity: string
  price_per_share: string
  total_amount: string
  fees: string
  transaction_date: string
  source_type: SourceType
  notes?: string
  is_verified: boolean
  processed_date: string
}

export interface TransactionCreate {
  stock_symbol: string
  transaction_type: TransactionType
  quantity: number
  price_per_share: number
  fees?: number
  transaction_date: string
  notes?: string
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
  limit: number
  offset: number
}