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
    cached: false,
    trend: {
      trend: 'up',
      change: 1.77,
      change_percent: 1.05
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
    cached: false,
    trend: {
      trend: 'up',
      change: 0.11,
      change_percent: 0.27
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

  it('displays all required columns including trend', () => {
    render(
      <MarketDataTableView
        symbols={['CBA']}
        priceData={mockPriceData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    expect(screen.getByText('Symbol')).toBeInTheDocument();
    expect(screen.getByText('Price')).toBeInTheDocument();
    expect(screen.getByText('Trend')).toBeInTheDocument();
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

  it('displays up trend indicator for positive trends', () => {
    render(
      <MarketDataTableView
        symbols={['CBA']}
        priceData={mockPriceData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    // Should show up arrow for positive trend with rounded background
    const upArrow = screen.getByLabelText('Up trend');
    expect(upArrow).toBeInTheDocument();
    expect(upArrow).toHaveClass('rounded-full');
    expect(upArrow).toHaveClass('bg-green-100');
  });

  it('displays down trend indicator for negative trends', () => {
    const negativeData = {
      AAPL: {
        symbol: 'AAPL',
        price: 150.00,
        currency: 'USD',
        fetched_at: '2025-01-15T14:30:00Z',
        cached: false,
        trend: {
          trend: 'down' as const,
          change: -2.50,
          change_percent: -1.64
        }
      }
    };

    render(
      <MarketDataTableView
        symbols={['AAPL']}
        priceData={negativeData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    // Should show down arrow for negative trend with rounded background
    const downArrow = screen.getByLabelText('Down trend');
    expect(downArrow).toBeInTheDocument();
    expect(downArrow).toHaveClass('rounded-full');
    expect(downArrow).toHaveClass('bg-red-100');
  });

  it('displays neutral trend indicator when no trend data', () => {
    const neutralData = {
      MSFT: {
        symbol: 'MSFT',
        price: 300.00,
        currency: 'USD',
        fetched_at: '2025-01-15T14:30:00Z',
        cached: false
        // No trend data
      }
    };

    render(
      <MarketDataTableView
        symbols={['MSFT']}
        priceData={neutralData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    // Should show neutral indicator with rounded background
    const neutralIndicator = screen.getByLabelText('No trend data');
    expect(neutralIndicator).toBeInTheDocument();
    expect(neutralIndicator).toHaveClass('rounded-full');
    expect(neutralIndicator).toHaveClass('bg-gray-100');
  });

  it('colors change and change% columns based on trend direction', () => {
    const mixedData = {
      UP_STOCK: {
        symbol: 'UP_STOCK',
        price: 100.00,
        currency: 'USD',
        fetched_at: '2025-01-15T14:30:00Z',
        cached: false,
        trend: {
          trend: 'up' as const,
          change: 2.50,
          change_percent: 2.5
        }
      },
      DOWN_STOCK: {
        symbol: 'DOWN_STOCK',
        price: 80.00,
        currency: 'USD',
        fetched_at: '2025-01-15T14:30:00Z',
        cached: false,
        trend: {
          trend: 'down' as const,
          change: -1.50,
          change_percent: -1.84
        }
      }
    };

    render(
      <MarketDataTableView
        symbols={['UP_STOCK', 'DOWN_STOCK']}
        priceData={mixedData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    // Check positive change colors (green)
    expect(screen.getByText('+$2.50')).toBeInTheDocument();
    expect(screen.getByText('+2.50%')).toBeInTheDocument();

    // Find the cells containing the positive change values and check their colors
    const posChangeCell = screen.getByText('+$2.50').closest('td');
    const posPercentCell = screen.getByText('+2.50%').closest('td');
    expect(posChangeCell).toHaveClass('text-green-600');
    expect(posPercentCell).toHaveClass('text-green-600');

    // Check negative change colors (red)
    expect(screen.getByText('-$1.50')).toBeInTheDocument();
    expect(screen.getByText('-1.84%')).toBeInTheDocument();

    // Find the cells containing the negative change values and check their colors
    const negChangeCell = screen.getByText('-$1.50').closest('td');
    const negPercentCell = screen.getByText('-1.84%').closest('td');
    expect(negChangeCell).toHaveClass('text-red-600');
    expect(negPercentCell).toHaveClass('text-red-600');
  });

  it('displays neutral/zero changes with grey color', () => {
    const neutralData = {
      NEUTRAL_STOCK: {
        symbol: 'NEUTRAL_STOCK',
        price: 50.00,
        currency: 'USD',
        fetched_at: '2025-01-15T14:30:00Z',
        cached: false,
        trend: {
          trend: 'neutral' as const,
          change: 0.00,
          change_percent: 0.00
        }
      }
    };

    render(
      <MarketDataTableView
        symbols={['NEUTRAL_STOCK']}
        priceData={neutralData}
        onRemoveSymbol={mockOnRemoveSymbol}
      />
    );

    // Check neutral change colors (grey)
    expect(screen.getByText('$0.00')).toBeInTheDocument();
    expect(screen.getByText('0.00%')).toBeInTheDocument();

    // Find the cells containing the neutral change values and check their colors
    const neutralChangeCell = screen.getByText('$0.00').closest('td');
    const neutralPercentCell = screen.getByText('0.00%').closest('td');
    expect(neutralChangeCell).toHaveClass('text-gray-600');
    expect(neutralPercentCell).toHaveClass('text-gray-600');
  });
});