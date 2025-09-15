/**
 * Frontend tests for portfolio deletion functionality with confirmation.
 * Tests deletion modal, name verification, and API integration.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import PortfolioDeletionModal from '../../components/portfolio/PortfolioDeletionModal';
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

describe('PortfolioDeletionModal', () => {
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

  it('should render deletion modal with portfolio name and confirmation input', () => {
    renderWithAuth(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    expect(screen.getByRole('heading', { name: 'Delete Portfolio' })).toBeInTheDocument();
    expect(screen.getByText('My Test Portfolio')).toBeInTheDocument();
    expect(screen.getByText(/enter the portfolio name/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Portfolio name')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /delete portfolio/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeEnabled();
  });

  it('should enable delete button only when confirmation name matches exactly', async () => {
    renderWithAuth(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    const confirmationInput = screen.getByPlaceholderText('Portfolio name');
    const deleteButton = screen.getByRole('button', { name: /delete portfolio/i });

    // Initially disabled
    expect(deleteButton).toBeDisabled();

    // Partial match should not enable
    fireEvent.change(confirmationInput, { target: { value: 'My Test' } });
    expect(deleteButton).toBeDisabled();

    // Case mismatch should not enable
    fireEvent.change(confirmationInput, { target: { value: 'my test portfolio' } });
    expect(deleteButton).toBeDisabled();

    // Exact match should enable
    fireEvent.change(confirmationInput, { target: { value: 'My Test Portfolio' } });
    expect(deleteButton).toBeEnabled();
  });

  it('should call soft delete API when delete button is clicked', async () => {
    mockDeletePortfolio.mockResolvedValue({ success: true });
    const onDeleted = jest.fn();

    renderWithAuth(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={onDeleted}
      />
    );

    const confirmationInput = screen.getByPlaceholderText('Portfolio name');
    const deleteButton = screen.getByRole('button', { name: /delete portfolio/i });

    // Enter correct confirmation name
    fireEvent.change(confirmationInput, { target: { value: 'My Test Portfolio' } });

    // Click delete
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockDeletePortfolio).toHaveBeenCalledWith('portfolio-123', {
        confirmationName: 'My Test Portfolio',
      });
    });

    await waitFor(() => {
      expect(onDeleted).toHaveBeenCalled();
    });
  });

  it('should show hard delete option when enabled', async () => {
    renderWithAuth(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
        allowHardDelete={true}
      />
    );

    expect(screen.getByText(/permanently delete/i)).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /permanently delete/i })).toBeInTheDocument();
    expect(screen.getByText(/this action cannot be undone/i)).toBeInTheDocument();
  });

  it('should call hard delete API when hard delete is selected', async () => {
    mockHardDeletePortfolio.mockResolvedValue({ success: true });
    const onDeleted = jest.fn();

    renderWithAuth(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={onDeleted}
        allowHardDelete={true}
      />
    );

    const confirmationInput = screen.getByPlaceholderText('Portfolio name');
    const hardDeleteCheckbox = screen.getByRole('checkbox', { name: /permanently delete/i });
    const deleteButton = screen.getByRole('button', { name: /delete portfolio/i });

    // Enter correct confirmation name
    fireEvent.change(confirmationInput, { target: { value: 'My Test Portfolio' } });

    // Enable hard delete
    fireEvent.click(hardDeleteCheckbox);

    // Click delete
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockHardDeletePortfolio).toHaveBeenCalledWith('portfolio-123', {
        confirmationName: 'My Test Portfolio',
      });
    });

    await waitFor(() => {
      expect(onDeleted).toHaveBeenCalled();
    });
  });

  it('should display error message when deletion fails', async () => {
    mockDeletePortfolio.mockRejectedValue(new Error('Confirmation name does not match'));

    renderWithAuth(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    const confirmationInput = screen.getByPlaceholderText('Portfolio name');
    const deleteButton = screen.getByRole('button', { name: /delete portfolio/i });

    // Enter correct confirmation name
    fireEvent.change(confirmationInput, { target: { value: 'My Test Portfolio' } });

    // Click delete
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(screen.getByText(/confirmation name does not match/i)).toBeInTheDocument();
    });
  });

  it('should show loading state during deletion', async () => {
    // Mock a delayed response
    mockDeletePortfolio.mockImplementation(() =>
      new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    renderWithAuth(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    const confirmationInput = screen.getByPlaceholderText('Portfolio name');
    const deleteButton = screen.getByRole('button', { name: /delete portfolio/i });

    // Enter correct confirmation name
    fireEvent.change(confirmationInput, { target: { value: 'My Test Portfolio' } });

    // Click delete
    fireEvent.click(deleteButton);

    // Should show loading state
    expect(screen.getByText(/deleting/i)).toBeInTheDocument();
    expect(deleteButton).toBeDisabled();

    await waitFor(() => {
      expect(screen.queryByText(/deleting/i)).not.toBeInTheDocument();
    });
  });

  it('should close modal when cancel button is clicked', () => {
    const onClose = jest.fn();

    renderWithAuth(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={onClose}
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(onClose).toHaveBeenCalled();
  });

  it('should reset form when modal is reopened', () => {
    const { rerender } = renderWithAuth(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    const confirmationInput = screen.getByPlaceholderText('Portfolio name');

    // Enter some text
    fireEvent.change(confirmationInput, { target: { value: 'Some text' } });
    expect(confirmationInput).toHaveValue('Some text');

    // Close modal
    rerender(
      <PortfolioDeletionModal
        isOpen={false}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    // Reopen modal
    rerender(
      <PortfolioDeletionModal
        isOpen={true}
        onClose={jest.fn()}
        portfolio={mockPortfolio}
        onDeleted={jest.fn()}
      />
    );

    // Input should be reset
    const newInput = screen.getByPlaceholderText('Portfolio name');
    expect(newInput).toHaveValue('');
  });
});