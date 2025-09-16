/**
 * TDD tests for PortfolioCard component formatting and display.
 * Tests percentage formatting with 2 decimal places.
 */

import { render, screen } from '@testing-library/react';
import { jest } from '@jest/globals';
import PortfolioCard from '../../components/Portfolio/PortfolioCard';
import { AuthContext } from '../../contexts/AuthContext';
import type { User } from '../../types/auth';

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

describe('PortfolioCard Formatting', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithAuth = (component: React.ReactElement) => {
    return render(
      <AuthContext.Provider value={mockAuthContext}>
        {component}
      </AuthContext.Provider>
    );
  };

  it('should format percentage with exactly 2 decimal places for very precise decimals', () => {
    const mockPortfolio = {
      id: 'portfolio-123',
      name: 'Test Portfolio',
      description: 'Test portfolio',
      total_value: '14604.00',
      daily_change: '5.00',
      daily_change_percent: '0.034248921158983492020001369',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    };

    renderWithAuth(<PortfolioCard portfolio={mockPortfolio} />);

    // Should show percentage with exactly 2 decimal places
    expect(screen.getByText('(0.03%)')).toBeInTheDocument();

    // Should NOT show the long decimal
    expect(screen.queryByText(/0\.034248921158983492020001369/)).not.toBeInTheDocument();
  });

  it('should format percentage with exactly 2 decimal places for whole numbers', () => {
    const mockPortfolio = {
      id: 'portfolio-123',
      name: 'Test Portfolio',
      description: 'Test portfolio',
      total_value: '10000.00',
      daily_change: '100.00',
      daily_change_percent: '1.0',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    };

    renderWithAuth(<PortfolioCard portfolio={mockPortfolio} />);

    // Should show percentage with exactly 2 decimal places
    expect(screen.getByText('(1.00%)')).toBeInTheDocument();
  });

  it('should format negative percentage with exactly 2 decimal places', () => {
    const mockPortfolio = {
      id: 'portfolio-123',
      name: 'Test Portfolio',
      description: 'Test portfolio',
      total_value: '9950.00',
      daily_change: '-50.00',
      daily_change_percent: '-0.5025',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    };

    renderWithAuth(<PortfolioCard portfolio={mockPortfolio} />);

    // Should show negative percentage with exactly 2 decimal places
    expect(screen.getByText('(-0.50%)')).toBeInTheDocument();
  });

  it('should format zero percentage correctly', () => {
    const mockPortfolio = {
      id: 'portfolio-123',
      name: 'Test Portfolio',
      description: 'Test portfolio',
      total_value: '10000.00',
      daily_change: '0.00',
      daily_change_percent: '0',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
    };

    renderWithAuth(<PortfolioCard portfolio={mockPortfolio} />);

    // Should show zero percentage with exactly 2 decimal places
    expect(screen.getByText('(0.00%)')).toBeInTheDocument();
  });
});