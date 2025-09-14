"""
TDD tests for bulk updates toggle functionality on provider detail page.

This implements the bulk updates toggle feature using Test-Driven Development:
1. Write failing tests that define the expected behavior
2. Implement minimal code to make tests pass
3. Refactor and improve
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.api.admin import toggle_provider_bulk_updates, get_provider_bulk_update_status
from src.models.market_data_provider import MarketDataProvider
from src.models.user import User, UserRole


class TestBulkUpdatesToggleTDD:
    """TDD tests for bulk updates toggle functionality."""

    @pytest.fixture
    def admin_user(self):
        """Create an admin user for testing."""
        user = User(
            email="admin@test.com",
            password_hash="hashed",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True
        )
        return user

    @pytest.fixture
    def sample_provider(self):
        """Create a sample market data provider."""
        provider = MarketDataProvider(
            name="yfinance",
            display_name="Yahoo Finance",
            is_enabled=True,
            priority=1
        )
        provider.id = 1
        return provider

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        mock_session = MagicMock(spec=Session)
        return mock_session

    @pytest.mark.asyncio
    async def test_toggle_provider_bulk_updates_enable(self, admin_user, sample_provider, mock_db_session):
        """Test enabling bulk updates for a provider."""
        # Arrange
        provider_id = "yfinance"
        enable_bulk_updates = True

        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_provider
        mock_db_session.commit.return_value = None

        # This test should fail initially because the function doesn't exist yet
        try:
            # Act
            result = await toggle_provider_bulk_updates(
                provider_id=provider_id,
                enable_bulk_updates=enable_bulk_updates,
                current_admin=admin_user,
                db=mock_db_session
            )

            # Assert
            assert result["success"] is True
            assert result["provider_id"] == provider_id
            assert result["bulk_updates_enabled"] is True
            assert "message" in result

            # Verify the provider's bulk update setting was updated
            mock_db_session.commit.assert_called_once()

        except ImportError:
            # This is expected on first run - the function doesn't exist yet
            pytest.fail("toggle_provider_bulk_updates function not implemented yet - this test should fail first in TDD")

    @pytest.mark.asyncio
    async def test_toggle_provider_bulk_updates_disable(self, admin_user, sample_provider, mock_db_session):
        """Test disabling bulk updates for a provider."""
        # Arrange
        provider_id = "yfinance"
        enable_bulk_updates = False

        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_provider
        mock_db_session.commit.return_value = None

        try:
            # Act
            result = await toggle_provider_bulk_updates(
                provider_id=provider_id,
                enable_bulk_updates=enable_bulk_updates,
                current_admin=admin_user,
                db=mock_db_session
            )

            # Assert
            assert result["success"] is True
            assert result["provider_id"] == provider_id
            assert result["bulk_updates_enabled"] is False
            assert "message" in result

        except ImportError:
            pytest.fail("toggle_provider_bulk_updates function not implemented yet")

    @pytest.mark.asyncio
    async def test_toggle_provider_bulk_updates_provider_not_found(self, admin_user, mock_db_session):
        """Test toggling bulk updates for non-existent provider."""
        # Arrange
        provider_id = "nonexistent"
        enable_bulk_updates = True

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        try:
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await toggle_provider_bulk_updates(
                    provider_id=provider_id,
                    enable_bulk_updates=enable_bulk_updates,
                    current_admin=admin_user,
                    db=mock_db_session
                )

            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail).lower()

        except ImportError:
            pytest.fail("toggle_provider_bulk_updates function not implemented yet")

    @pytest.mark.asyncio
    async def test_get_provider_bulk_update_status(self, sample_provider, mock_db_session):
        """Test getting current bulk update status for a provider."""
        # Arrange
        provider_id = "yfinance"
        sample_provider.config = {"bulk_updates_enabled": True}

        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_provider

        try:
            # Act
            result = await get_provider_bulk_update_status(
                provider_id=provider_id,
                db=mock_db_session
            )

            # Assert
            assert result["provider_id"] == provider_id
            assert result["bulk_updates_enabled"] is True
            assert result["provider_name"] == sample_provider.display_name

        except ImportError:
            pytest.fail("get_provider_bulk_update_status function not implemented yet")

    @pytest.mark.asyncio
    async def test_bulk_updates_toggle_requires_admin_role(self, mock_db_session):
        """Test that bulk updates toggle requires admin role."""
        # Arrange
        regular_user = User(
            email="user@test.com",
            password_hash="hashed",
            first_name="Regular",
            last_name="User",
            role=UserRole.USER,  # Not admin
            is_active=True
        )

        provider_id = "yfinance"
        enable_bulk_updates = True

        try:
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await toggle_provider_bulk_updates(
                    provider_id=provider_id,
                    enable_bulk_updates=enable_bulk_updates,
                    current_admin=regular_user,  # Should fail with non-admin user
                    db=mock_db_session
                )

            assert exc_info.value.status_code == 403
            assert "admin" in str(exc_info.value.detail).lower()

        except ImportError:
            pytest.fail("toggle_provider_bulk_updates function not implemented yet")

    def test_provider_model_supports_bulk_updates_config(self, sample_provider):
        """Test that provider model can store bulk updates configuration."""
        # This test ensures the MarketDataProvider model can store bulk update settings

        # Test setting bulk updates config
        sample_provider.config = {"bulk_updates_enabled": True}
        assert sample_provider.config["bulk_updates_enabled"] is True

        # Test updating bulk updates config
        sample_provider.config = {"bulk_updates_enabled": False, "other_setting": "value"}
        assert sample_provider.config["bulk_updates_enabled"] is False
        assert sample_provider.config["other_setting"] == "value"