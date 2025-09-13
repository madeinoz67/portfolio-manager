"""
Integration tests for transaction CRUD operations using TDD approach.

Tests cover:
- Transaction creation with different types (BUY, SELL, DIVIDEND, etc.)
- Transaction updating (partial and full updates)
- Transaction deletion
- Business logic validation for transaction categories
- Error handling for invalid operations
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models.transaction import TransactionType
from tests.conftest import TestData


class TestTransactionCRUD:
    """Test transaction CRUD operations with different transaction types."""

    def test_create_buy_transaction(self, client: TestClient, test_data: TestData):
        """Test creating a BUY transaction."""
        transaction_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "BUY",
            "quantity": "100.0",
            "price_per_share": "150.50",
            "fees": "9.99",
            "transaction_date": str(date.today()),
            "notes": "Initial purchase"
        }
        
        response = client.post(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions",
            json=transaction_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "BUY"
        assert data["quantity"] == "100.0000"
        assert data["price_per_share"] == "150.5000"
        assert data["total_amount"] == "15059.99"  # 100 * 150.50 + 9.99

    def test_create_dividend_transaction(self, client: TestClient, test_data: TestData):
        """Test creating a DIVIDEND transaction."""
        transaction_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "DIVIDEND",
            "quantity": "0.0",  # Dividends don't affect quantity
            "price_per_share": "2.50",  # Dividend per share
            "fees": "0.00",
            "transaction_date": str(date.today()),
            "notes": "Quarterly dividend payment"
        }
        
        response = client.post(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions",
            json=transaction_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "DIVIDEND"
        assert data["quantity"] == "0.0000"
        assert data["price_per_share"] == "2.5000"

    def test_create_stock_split_transaction(self, client: TestClient, test_data: TestData):
        """Test creating a STOCK_SPLIT transaction."""
        transaction_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "STOCK_SPLIT",
            "quantity": "100.0",  # Additional shares from split
            "price_per_share": "0.00",  # No cost basis for splits
            "fees": "0.00",
            "transaction_date": str(date.today()),
            "notes": "2:1 stock split"
        }
        
        response = client.post(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions",
            json=transaction_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "STOCK_SPLIT"
        assert data["price_per_share"] == "0.0000"

    def test_update_transaction_partial(self, client: TestClient, test_data: TestData):
        """Test partially updating a transaction."""
        # First create a transaction
        transaction_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "BUY",
            "quantity": "100.0",
            "price_per_share": "150.00",
            "fees": "9.99",
            "transaction_date": str(date.today()),
            "notes": "Original transaction"
        }
        
        create_response = client.post(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions",
            json=transaction_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        assert create_response.status_code == 201
        transaction_id = create_response.json()["id"]
        
        # Now update only the quantity and notes
        update_data = {
            "quantity": "120.0",
            "notes": "Updated quantity"
        }
        
        response = client.put(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{transaction_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == "120.0000"
        assert data["notes"] == "Updated quantity"
        assert data["price_per_share"] == "150.0000"  # Unchanged
        assert data["transaction_type"] == "BUY"  # Unchanged

    def test_update_transaction_stock_symbol(self, client: TestClient, test_data: TestData):
        """Test updating transaction stock symbol."""
        # Create transaction
        transaction_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "BUY",
            "quantity": "100.0",
            "price_per_share": "150.00",
            "fees": "9.99",
            "transaction_date": str(date.today())
        }
        
        create_response = client.post(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions",
            json=transaction_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        transaction_id = create_response.json()["id"]
        
        # Update to different stock
        update_data = {"stock_symbol": "MSFT"}
        
        response = client.put(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{transaction_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["stock"]["symbol"] == "MSFT"

    def test_delete_transaction(self, client: TestClient, test_data: TestData):
        """Test deleting a transaction."""
        # Create transaction
        transaction_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "BUY",
            "quantity": "100.0",
            "price_per_share": "150.00",
            "fees": "9.99",
            "transaction_date": str(date.today())
        }
        
        create_response = client.post(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions",
            json=transaction_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        transaction_id = create_response.json()["id"]
        
        # Delete the transaction
        response = client.delete(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        
        assert response.status_code == 204
        
        # Verify transaction is deleted
        get_response = client.get(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        assert get_response.status_code == 404

    def test_update_nonexistent_transaction(self, client: TestClient, test_data: TestData):
        """Test updating a transaction that doesn't exist."""
        fake_transaction_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"quantity": "50.0"}
        
        response = client.put(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{fake_transaction_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        
        assert response.status_code == 404

    def test_delete_nonexistent_transaction(self, client: TestClient, test_data: TestData):
        """Test deleting a transaction that doesn't exist."""
        fake_transaction_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.delete(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{fake_transaction_id}",
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        
        assert response.status_code == 404

    def test_update_transaction_validation_errors(self, client: TestClient, test_data: TestData):
        """Test validation errors when updating transactions."""
        # Create transaction
        transaction_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "BUY",
            "quantity": "100.0",
            "price_per_share": "150.00",
            "fees": "9.99",
            "transaction_date": str(date.today())
        }
        
        create_response = client.post(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions",
            json=transaction_data,
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        transaction_id = create_response.json()["id"]
        
        # Test negative quantity
        response = client.put(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{transaction_id}",
            json={"quantity": "-10.0"},
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        assert response.status_code == 422
        
        # Test negative price
        response = client.put(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{transaction_id}",
            json={"price_per_share": "-50.0"},
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        assert response.status_code == 422
        
        # Test future date
        future_date = date.today() + timedelta(days=1)
        response = client.put(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{transaction_id}",
            json={"transaction_date": str(future_date)},
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        assert response.status_code == 422

    def test_transaction_type_categorization(self, client: TestClient, test_data: TestData):
        """Test creating transactions with all supported types."""
        transaction_types = [
            ("BUY", "100.0", "150.00"),
            ("SELL", "50.0", "155.00"),
            ("DIVIDEND", "0.0", "2.50"),
            ("STOCK_SPLIT", "100.0", "0.00"),
            ("REVERSE_SPLIT", "0.0", "0.00"),
            ("TRANSFER_IN", "25.0", "140.00"),
            ("TRANSFER_OUT", "25.0", "140.00"),
            ("SPIN_OFF", "10.0", "0.00"),
            ("MERGER", "0.0", "180.00"),
            ("BONUS_SHARES", "5.0", "0.00")
        ]
        
        for trans_type, quantity, price in transaction_types:
            transaction_data = {
                "stock_symbol": "AAPL",
                "transaction_type": trans_type,
                "quantity": quantity,
                "price_per_share": price,
                "fees": "0.00",
                "transaction_date": str(date.today()),
                "notes": f"Test {trans_type} transaction"
            }
            
            response = client.post(
                f"/api/v1/portfolios/{test_data.portfolio.id}/transactions",
                json=transaction_data,
                headers={"Authorization": f"Bearer {test_data.access_token}"}
            )
            
            assert response.status_code == 201, f"Failed to create {trans_type} transaction"
            data = response.json()
            assert data["transaction_type"] == trans_type

    def test_unauthorized_transaction_operations(self, client: TestClient, test_data: TestData):
        """Test that unauthorized users cannot perform transaction operations."""
        transaction_data = {
            "stock_symbol": "AAPL",
            "transaction_type": "BUY",
            "quantity": "100.0",
            "price_per_share": "150.00",
            "fees": "9.99",
            "transaction_date": str(date.today())
        }
        
        # Test without auth token
        response = client.post(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions",
            json=transaction_data
        )
        assert response.status_code == 401
        
        # Test update without auth token
        fake_transaction_id = "00000000-0000-0000-0000-000000000000"
        response = client.put(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{fake_transaction_id}",
            json={"quantity": "50.0"}
        )
        assert response.status_code == 401
        
        # Test delete without auth token
        response = client.delete(
            f"/api/v1/portfolios/{test_data.portfolio.id}/transactions/{fake_transaction_id}"
        )
        assert response.status_code == 401

    def test_cross_portfolio_transaction_access(self, client: TestClient, test_data: TestData):
        """Test that users cannot access transactions from other portfolios."""
        # This test would require creating another user/portfolio
        # For now, we'll test with a fake portfolio ID
        fake_portfolio_id = "00000000-0000-0000-0000-000000000000"
        fake_transaction_id = "11111111-1111-1111-1111-111111111111"
        
        # Test accessing transaction from non-existent portfolio
        response = client.get(
            f"/api/v1/portfolios/{fake_portfolio_id}/transactions/{fake_transaction_id}",
            headers={"Authorization": f"Bearer {test_data.access_token}"}
        )
        assert response.status_code == 404