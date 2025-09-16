/**
 * TDD tests for Analytics page formatting and display.
 * Tests percentage formatting with 2 decimal places for best performer.
 */

import { render, screen } from '@testing-library/react';
import { jest } from '@jest/globals';
import Analytics from '../../app/analytics/page';
import { AuthContext } from '../../contexts/AuthContext';
import { ThemeProvider } from '../../contexts/ThemeContext';
import type { User } from '../../types/auth';

// Mock the required hooks and modules
jest.mock('next/navigation', () => ({
  useSearchParams: () => ({
    get: jest.fn(() => null),
  }),
}));

jest.mock('../../hooks/usePortfolios', () => ({
  usePortfolios: () => ({
    portfolios: [
      {
        id: 'portfolio-1',
        name: 'Best Portfolio',
        description: 'Test portfolio',
        total_value: '10000.00',
        daily_change: '100.00',
        daily_change_percent: '1.034248921158983492020001369',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      },
      {
        id: 'portfolio-2',
        name: 'Other Portfolio',
        description: 'Test portfolio 2',
        total_value: '5000.00',
        daily_change: '25.00',
        daily_change_percent: '0.5',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      }
    ],
    loading: false,
    error: null,
  }),
}));

// Mock chart components
jest.mock('../../components/analytics/PerformanceChart', () => {
  return function MockPerformanceChart() {
    return <div data-testid="performance-chart">Performance Chart</div>;
  };
});

jest.mock('../../components/analytics/AssetAllocationChart', () => {
  return function MockAssetAllocationChart() {
    return <div data-testid="asset-allocation-chart">Asset Allocation Chart</div>;
  };
});

jest.mock('../../components/analytics/PortfolioComparison', () => {
  return function MockPortfolioComparison() {
    return <div data-testid="portfolio-comparison">Portfolio Comparison</div>;
  };
});

jest.mock('../../components/analytics/TimeRangeSelector', () => {
  return function MockTimeRangeSelector({ selected, onSelect }: any) {
    return <div data-testid="time-range-selector">Time Range: {selected}</div>;
  };
});

const mockUser: User = {
  id: '123',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  role: 'USER',
};

const mockAuthContext = {
  user: mockUser,
  login: jest.fn(),
  logout: jest.fn(),
  isLoading: false,
};

describe('Analytics Page Formatting', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => null),
        setItem: jest.fn(),
      },
      writable: true,
    });
    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    });
  });

  const renderWithAuth = (component: React.ReactElement) => {
    return render(
      <ThemeProvider>
        <AuthContext.Provider value={mockAuthContext}>
          {component}
        </AuthContext.Provider>
      </ThemeProvider>
    );
  };

  it('should format best performer percentage with exactly 2 decimal places', () => {
    renderWithAuth(<Analytics />);

    // Should show the best performer with properly formatted percentage
    expect(screen.getByText('Best Performer')).toBeInTheDocument();

    // Should format the long decimal to 2 decimal places
    expect(screen.getByText('1.03%')).toBeInTheDocument();

    // Should NOT show the long decimal
    expect(screen.queryByText(/1\.034248921158983492020001369/)).not.toBeInTheDocument();
  });
});