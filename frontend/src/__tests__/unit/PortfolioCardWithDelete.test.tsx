/**
 * TDD tests for PortfolioCard component with delete functionality integration.
 * Testing the delete button, modal integration, and callback functionality.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import PortfolioCard from '../../components/Portfolio/PortfolioCard';
import { AuthContext } from '../../contexts/AuthContext';
import type { User } from '../../types/auth';

// Mock the portfolio API
jest.mock('../../services/portfolio', () => ({
  deletePortfolio: jest.fn(),
  hardDeletePortfolio: jest.fn(),
}));

const mockDeletePortfolio = jest.fn();
const mockHardDeletePortfolio = jest.fn();

// Mock portfolio service
jest.mock('../../services/portfolio', () => ({
  deletePortfolio: mockDeletePortfolio,
  hardDeletePortfolio: mockHardDeletePortfolio,
}));

// Get the mock router from global setup
const mockRouter = global.mockRouter;

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

const mockPortfolio = {
  id: 'portfolio-123',
  name: 'My Test Portfolio',
  description: 'Test portfolio for deletion',
  total_value: '10000.00',
  daily_change: '100.00',
  daily_change_percent: '1.0',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
};

describe('PortfolioCard with Delete Functionality', () => {
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

  it('should render portfolio card with delete button', () => {
    renderWithAuth(
      <PortfolioCard
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    expect(screen.getByText('My Test Portfolio')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /view details/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add trade/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
  });

  it('should show delete button with trash icon', () => {
    renderWithAuth(
      <PortfolioCard
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    expect(deleteButton).toBeInTheDocument();
    expect(deleteButton).toHaveClass('text-red-600');
  });

  it('should open deletion modal when delete button is clicked', () => {
    renderWithAuth(
      <PortfolioCard
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    // Modal should be open
    expect(screen.getByRole('heading', { name: 'Delete Portfolio' })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Portfolio name')).toBeInTheDocument();
  });

  it('should close modal when cancel is clicked', () => {
    renderWithAuth(
      <PortfolioCard
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    // Open modal
    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    // Close modal
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    // Modal should be closed
    expect(screen.queryByRole('heading', { name: 'Delete Portfolio' })).not.toBeInTheDocument();
  });

  it('should call onDeleted callback when portfolio is successfully deleted', async () => {
    mockDeletePortfolio.mockResolvedValue({ success: true });
    const onDeleted = jest.fn();

    renderWithAuth(
      <PortfolioCard
        portfolio={mockPortfolio}
        onDeleted={onDeleted}
      />
    );

    // Open modal
    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    // Enter confirmation name
    const confirmationInput = screen.getByPlaceholderText('Portfolio name');
    fireEvent.change(confirmationInput, { target: { value: 'My Test Portfolio' } });

    // Click delete
    const modalDeleteButton = screen.getByRole('button', { name: /delete portfolio/i });
    fireEvent.click(modalDeleteButton);

    await waitFor(() => {
      expect(mockDeletePortfolio).toHaveBeenCalledWith('portfolio-123', {
        confirmationName: 'My Test Portfolio',
      });
    });

    await waitFor(() => {
      expect(onDeleted).toHaveBeenCalled();
    });
  });

  it('should not show delete button when onDeleted callback is not provided', () => {
    renderWithAuth(
      <PortfolioCard
        portfolio={mockPortfolio}
      />
    );

    expect(screen.getByRole('button', { name: /view details/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add trade/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
  });

  it('should handle delete errors gracefully', async () => {
    mockDeletePortfolio.mockRejectedValue(new Error('Network error'));
    const onDeleted = jest.fn();

    renderWithAuth(
      <PortfolioCard
        portfolio={mockPortfolio}
        onDeleted={onDeleted}
      />
    );

    // Open modal
    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    // Enter confirmation name
    const confirmationInput = screen.getByPlaceholderText('Portfolio name');
    fireEvent.change(confirmationInput, { target: { value: 'My Test Portfolio' } });

    // Click delete
    const modalDeleteButton = screen.getByRole('button', { name: /delete portfolio/i });
    fireEvent.click(modalDeleteButton);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });

    // onDeleted should not be called on error
    expect(onDeleted).not.toHaveBeenCalled();
  });

  it('should display loading state during deletion', async () => {
    // Mock a delayed response
    mockDeletePortfolio.mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    renderWithAuth(
      <PortfolioCard
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    // Open modal
    const deleteButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(deleteButton);

    // Enter confirmation name
    const confirmationInput = screen.getByPlaceholderText('Portfolio name');
    fireEvent.change(confirmationInput, { target: { value: 'My Test Portfolio' } });

    // Click delete
    const modalDeleteButton = screen.getByRole('button', { name: /delete portfolio/i });
    fireEvent.click(modalDeleteButton);

    // Should show loading state
    expect(screen.getByText(/deleting/i)).toBeInTheDocument();
    expect(modalDeleteButton).toBeDisabled();

    await waitFor(() => {
      expect(screen.queryByText(/deleting/i)).not.toBeInTheDocument();
    });
  });
});