export interface Stock {
  symbol: string
  company_name: string
  current_price?: string
  sector?: string
  market_cap?: string
}

export interface StockSearchResult extends Stock {
  // Additional fields that might come from search API
  exchange?: string
  currency?: string
  last_updated?: string
}

export interface StockSuggestion {
  symbol: string
  company_name: string
}

export interface SearchFilters {
  sector?: string
  exchange?: string
  market_cap_min?: number
  market_cap_max?: number
  price_min?: number
  price_max?: number
}

export interface SearchOptions {
  limit?: number
  filters?: SearchFilters
}

export interface CachedSearchResult {
  query: string
  results: StockSearchResult[]
  timestamp: number
  filters?: SearchFilters
}