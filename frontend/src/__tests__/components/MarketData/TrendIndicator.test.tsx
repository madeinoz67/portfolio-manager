import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TrendIndicator } from '@/components/MarketData/TrendIndicator';
import { TrendData } from '@/types/marketData';

describe('TrendIndicator', () => {
  const mockUpTrend: TrendData = {
    trend: 'up',
    change: 1.50,
    change_percent: 2.5
  };

  const mockDownTrend: TrendData = {
    trend: 'down',
    change: -0.75,
    change_percent: -1.2
  };

  const mockNeutralTrend: TrendData = {
    trend: 'neutral',
    change: 0.00,
    change_percent: 0.0
  };

  it('renders without trend data', () => {
    render(<TrendIndicator />);
    expect(screen.getByText('No trend data')).toBeInTheDocument();
  });

  it('displays diagonal up-right arrow for positive trends without background', () => {
    render(<TrendIndicator trend={mockUpTrend} />);

    // Should show diagonal up-right arrow for positive trend WITHOUT rounded background
    const upArrow = screen.getByLabelText('Upward trend');
    expect(upArrow).toBeInTheDocument();

    // Should be an SVG element
    expect(upArrow.tagName).toBe('svg');
    expect(upArrow).toHaveAttribute('viewBox', '0 0 16 16');

    // Check for diagonal up-right path (M3 13L13 3 with arrow head)
    const path = upArrow.querySelector('path');
    expect(path).toHaveAttribute('d', 'M3 13L13 3M13 3H7M13 3V9');
  });

  it('displays diagonal down-right arrow for negative trends without background', () => {
    render(<TrendIndicator trend={mockDownTrend} />);

    // Should show diagonal down-right arrow for negative trend WITHOUT rounded background
    const downArrow = screen.getByLabelText('Downward trend');
    expect(downArrow).toBeInTheDocument();

    // Should be an SVG element
    expect(downArrow.tagName).toBe('svg');
    expect(downArrow).toHaveAttribute('viewBox', '0 0 16 16');

    // Check for diagonal down-right path (M3 3L13 13 with arrow head)
    const path = downArrow.querySelector('path');
    expect(path).toHaveAttribute('d', 'M3 3L13 13M13 13H7M13 13V7');
  });

  it('displays neutral indicator for neutral trends without background', () => {
    render(<TrendIndicator trend={mockNeutralTrend} />);

    // Should show horizontal line for neutral trend WITHOUT rounded background
    const neutralIndicator = screen.getByLabelText('Neutral trend');
    expect(neutralIndicator).toBeInTheDocument();

    // Should be an SVG element
    expect(neutralIndicator.tagName).toBe('svg');
    expect(neutralIndicator).toHaveAttribute('viewBox', '0 0 20 20');

    // Check for horizontal line path
    const path = neutralIndicator.querySelector('path');
    expect(path).toHaveAttribute('d', 'M3 10h14v2H3z');
  });

  it('applies correct colors for trend directions', () => {
    const { rerender } = render(<TrendIndicator trend={mockUpTrend} />);

    // Check up trend container color (green)
    const container = screen.getByLabelText('Upward trend').closest('div');
    expect(container).toHaveClass('text-green-600');

    // Check down trend container color (red)
    rerender(<TrendIndicator trend={mockDownTrend} />);
    const downContainer = screen.getByLabelText('Downward trend').closest('div');
    expect(downContainer).toHaveClass('text-red-600');

    // Check neutral trend container color (gray)
    rerender(<TrendIndicator trend={mockNeutralTrend} />);
    const neutralContainer = screen.getByLabelText('Neutral trend').closest('div');
    expect(neutralContainer).toHaveClass('text-gray-600');
  });

  it('displays change and percentage values', () => {
    render(<TrendIndicator trend={mockUpTrend} />);

    expect(screen.getByText('+1.50')).toBeInTheDocument();
    expect(screen.getByText('(+2.50%)')).toBeInTheDocument();
  });

  it('handles negative change values correctly', () => {
    render(<TrendIndicator trend={mockDownTrend} />);

    expect(screen.getByText('-0.75')).toBeInTheDocument();
    expect(screen.getByText('(-1.20%)')).toBeInTheDocument();
  });

  it('supports different sizes', () => {
    const { rerender } = render(<TrendIndicator trend={mockUpTrend} size="sm" />);

    // Small size should have smaller icon
    let svg = screen.getByLabelText('Upward trend');
    expect(svg).toHaveClass('w-3', 'h-3');

    // Large size should have larger icon
    rerender(<TrendIndicator trend={mockUpTrend} size="lg" />);
    svg = screen.getByLabelText('Upward trend');
    expect(svg).toHaveClass('w-5', 'h-5');
  });

  it('supports hiding icon, change, or percentage', () => {
    render(
      <TrendIndicator
        trend={mockUpTrend}
        showIcon={false}
        showChange={false}
        showPercentage={false}
      />
    );

    // Should not show arrow icon
    expect(screen.queryByLabelText('Upward trend')).not.toBeInTheDocument();

    // Should not show change or percentage
    expect(screen.queryByText('+1.50')).not.toBeInTheDocument();
    expect(screen.queryByText('(+2.50%)')).not.toBeInTheDocument();
  });
});