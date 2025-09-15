import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MarketDataViewToggle } from '@/components/MarketData/MarketDataViewToggle';

describe('MarketDataViewToggle', () => {
  const mockOnViewChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders with default tiles view selected', () => {
    render(
      <MarketDataViewToggle
        currentView="tiles"
        onViewChange={mockOnViewChange}
      />
    );

    expect(screen.getByRole('button', { name: /tiles view/i })).toHaveClass('bg-blue-500');
    expect(screen.getByRole('button', { name: /table view/i })).not.toHaveClass('bg-blue-500');
  });

  it('renders with table view selected', () => {
    render(
      <MarketDataViewToggle
        currentView="table"
        onViewChange={mockOnViewChange}
      />
    );

    expect(screen.getByRole('button', { name: /table view/i })).toHaveClass('bg-blue-500');
    expect(screen.getByRole('button', { name: /tiles view/i })).not.toHaveClass('bg-blue-500');
  });

  it('calls onViewChange when tiles button is clicked', () => {
    render(
      <MarketDataViewToggle
        currentView="table"
        onViewChange={mockOnViewChange}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /tiles view/i }));
    expect(mockOnViewChange).toHaveBeenCalledWith('tiles');
  });

  it('calls onViewChange when table button is clicked', () => {
    render(
      <MarketDataViewToggle
        currentView="tiles"
        onViewChange={mockOnViewChange}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /table view/i }));
    expect(mockOnViewChange).toHaveBeenCalledWith('table');
  });

  it('has proper accessibility attributes', () => {
    render(
      <MarketDataViewToggle
        currentView="tiles"
        onViewChange={mockOnViewChange}
      />
    );

    expect(screen.getByRole('group', { name: /view selection/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /tiles view/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: /table view/i })).toHaveAttribute('aria-pressed', 'false');
  });
});