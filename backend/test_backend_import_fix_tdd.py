#!/usr/bin/env python3
"""
TDD test to verify backend server can start with the fixed imports.

After refactoring ApiUsageMetrics to MarketDataUsageMetrics, the backend
server was failing to start due to import errors in main.py.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock


class TestBackendImportFix:
    """Test that backend imports work correctly after model refactor."""

    def test_models_init_imports_new_model(self):
        """
        Test that src.models.__init__.py imports the new MarketDataUsageMetrics model.

        This test should pass after we fix the models/__init__.py import.
        """
        try:
            from src.models import MarketDataUsageMetrics
            assert MarketDataUsageMetrics is not None
            assert hasattr(MarketDataUsageMetrics, '__tablename__')
            assert MarketDataUsageMetrics.__tablename__ == "market_data_usage_metrics"
        except ImportError as e:
            pytest.fail(f"Failed to import MarketDataUsageMetrics from src.models: {e}")

    def test_models_init_does_not_import_old_model(self):
        """
        Test that src.models.__init__.py does not try to import the old ApiUsageMetrics.

        This ensures we've properly removed references to the old model.
        """
        import src.models

        # Check that the old model name is not in the module's attributes
        assert not hasattr(src.models, 'ApiUsageMetrics')

        # Check that MarketDataUsageMetrics is available instead
        assert hasattr(src.models, 'MarketDataUsageMetrics')

    def test_main_py_imports_correct_module_name(self):
        """
        Test that main.py imports the correct module name.

        This test verifies the import statement in main.py uses the new module name.
        """
        # Read the main.py file to check the import line
        with open('/Users/seaton/Documents/src/portfolio-manager/backend/src/main.py', 'r') as f:
            content = f.read()

        # Should import the new module name
        assert 'market_data_usage_metrics' in content

        # Should not import the old module name
        assert 'market_data_api_usage_metrics' not in content

    @pytest.mark.asyncio
    async def test_lifespan_function_can_import_models(self):
        """
        Test that the lifespan function in main.py can import all models without errors.

        This simulates what happens when the FastAPI app starts up.
        """
        # Mock the database engine to avoid actual database operations
        with patch('src.main.engine') as mock_engine, \
             patch('src.main.Base') as mock_base:

            mock_base.metadata.create_all = MagicMock()

            try:
                # Import the models that are used in the lifespan function
                from src.models import user, portfolio, stock, transaction, holding, news_notice
                from src.models import market_data_provider, realtime_price_history, portfolio_valuation
                from src.models import sse_connection, poll_interval_config, market_data_usage_metrics

                # If we get here without ImportError, the test passes
                assert True

            except ImportError as e:
                pytest.fail(f"Lifespan import failed: {e}")

    def test_direct_import_works(self):
        """
        Test that we can directly import from the new module file.

        This verifies the actual module file exists and is importable.
        """
        try:
            from src.models.market_data_usage_metrics import MarketDataUsageMetrics

            # Verify it's the correct class
            assert MarketDataUsageMetrics.__name__ == 'MarketDataUsageMetrics'
            assert MarketDataUsageMetrics.__tablename__ == 'market_data_usage_metrics'

        except ImportError as e:
            pytest.fail(f"Direct import failed: {e}")

    def test_old_module_file_does_not_exist(self):
        """
        Test that the old module file has been renamed/removed.

        This ensures we've properly renamed the file as part of the refactor.
        """
        import os

        old_file_path = '/Users/seaton/Documents/src/portfolio-manager/backend/src/models/market_data_api_usage_metrics.py'
        new_file_path = '/Users/seaton/Documents/src/portfolio-manager/backend/src/models/market_data_usage_metrics.py'

        # Old file should not exist
        assert not os.path.exists(old_file_path), "Old module file still exists"

        # New file should exist
        assert os.path.exists(new_file_path), "New module file does not exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])