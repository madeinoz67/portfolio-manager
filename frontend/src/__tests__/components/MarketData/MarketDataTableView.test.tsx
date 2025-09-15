import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MarketDataTableView } from '@/components/MarketData/MarketDataTableView';
import { PriceResponse } from '@/types/marketData';

const mockPriceData: Record<string, PriceResponse> = {
  CBA: {
    symbol: 'CBA',
    price: 169.97,
    currency: 'AUD',
    opening_price: 168.50,
    previous_close: 168.20,
    high_price: 170.15,
    low_price: 168.00,
    volume: 1250000,
    market_cap: 289500000000,
    fetched_at: '2025-01-15T14:30:00Z',
    provider: 'yahoo',
    cached: false,
    trend: {
      change: 1.77,
      change_percent: 1.05,
      direction: 'up'
    }
  },
  BHP: {
    symbol: 'BHP',
    price: 40.81,
    currency: 'AUD',
    opening_price: 40.65,
    previous_close: 40.70,
    high_price: 41.05,
    low_price: 40.45,
    volume: 3500000,
    market_cap: 195000000000,
    fetched_at: '2025-01-15T14:30:00Z',
    provider: 'yahoo',
    cached: false,
    trend: {
      change: 0.11,
      change_percent: 0.27,
      direction: 'up'
    }
  }
};

describe('MarketDataTableView', () => {
  const mockOnRemoveSymbol = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders empty state when no data provided', () => {
    render(
      <MarketDataTableView
        symbols={[]}
        priceData={{}}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    expect(screen.getByText(/no stocks to display/i)).toBeInTheDocument();
  });

  it('renders table with stock data', () => {
    render(
      <MarketDataTableView
        symbols={['CBA', 'BHP']}
        priceData={mockPriceData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('CBA')).toBeInTheDocument();
    expect(screen.getByText('BHP')).toBeInTheDocument();
    expect(screen.getByText('$169.97')).toBeInTheDocument();
    expect(screen.getByText('$40.81')).toBeInTheDocument();
  });

  it('displays trend indicators correctly', () => {
    render(
      <MarketDataTableView
        symbols={['CBA']}
        priceData={mockPriceData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    expect(screen.getByText('+$1.77')).toBeInTheDocument();
    expect(screen.getByText('+1.05%')).toBeInTheDocument();
  });

  it('shows loading state for symbols without price data', () => {
    render(
      <MarketDataTableView
        symbols={['CBA', 'ANZ']}
        priceData={mockPriceData}
        loading={true}
      />
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('calls onRemoveSymbol when remove button is clicked', () => {
    render(
      <MarketDataTableView
        symbols={['CBA']}
        priceData={mockPriceData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    const removeButton = screen.getByRole('button', { name: /remove cba/i });
    fireEvent.click(removeButton);
    expect(mockOnRemoveSymbol).toHaveBeenCalledWith('CBA');
  });

  it('displays all required columns', () => {
    render(
      <MarketDataTableView
        symbols={['CBA']}
        priceData={mockPriceData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    expect(screen.getByText('Symbol')).toBeInTheDocument();
    expect(screen.getByText('Price')).toBeInTheDocument();
    expect(screen.getByText('Change')).toBeInTheDocument();
    expect(screen.getByText('Change %')).toBeInTheDocument();
    expect(screen.getByText('Volume')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
  });

  it('formats volume correctly', () => {
    render(
      <MarketDataTableView
        symbols={['CBA']}
        priceData={mockPriceData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    expect(screen.getByText('1.3M')).toBeInTheDocument();
  });

  it('shows cached indicator when data is cached', () => {
    const cachedData = {
      ...mockPriceData,
      CBA: { ...mockPriceData.CBA, cached: true }
    };

    render(
      <MarketDataTableView
        symbols={['CBA']}
        priceData={cachedData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    expect(screen.getByText('C')).toBeInTheDocument();
  });
});