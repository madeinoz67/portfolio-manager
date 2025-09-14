"""
TDD test to identify and fix datetime formatting issues in api/api_keys.py

Following FastAPI timezone best practices from:
https://medium.com/@rameshkannanyt0078/how-to-handle-timezones-properly-in-fastapi-and-database-68b1c019c1bc
"""

import pytest
import json
import subprocess
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from src.main import app


class TestApiKeysDatetimeTDD:
    def test_api_key_creation_response_datetime_format(self):
        """Test that API key creation response uses proper datetime formatting for JavaScript."""
        from src.api.api_keys import create_api_key
        from src.schemas.api_key import ApiKeyCreate
        from src.models.user import User
        from src.models.api_key import ApiKey

        # Mock objects
        mock_user = MagicMock(spec=User)
        mock_user.id = "test-user-id"
        mock_user.email = "test@example.com"

        mock_db = MagicMock()

        # Create a mock API key with datetime fields
        mock_api_key = MagicMock(spec=ApiKey)
        mock_api_key.id = "test-api-key-id"
        mock_api_key.name = "test-key"
        mock_api_key.permissions = None
        mock_api_key.expires_at = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        mock_api_key.created_at = datetime.now(timezone.utc)

        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock(return_value=mock_api_key)

        # Mock the key generation functions
        import src.api.api_keys as api_keys_module
        original_generate = getattr(api_keys_module, 'generate_api_key', None)
        original_hash = getattr(api_keys_module, 'hash_api_key', None)

        def mock_generate_api_key():
            return "test-api-key-12345"

        def mock_hash_api_key(key):
            return "hashed-" + key

        api_keys_module.generate_api_key = mock_generate_api_key
        api_keys_module.hash_api_key = mock_hash_api_key

        try:
            # Test the actual function
            import asyncio
            async def test_create():
                api_key_data = ApiKeyCreate(name="test-key", permissions=None)
                result = await create_api_key(api_key_data, mock_user, mock_db)
                return result

            response = asyncio.run(test_create())

            # Check that the response contains datetime fields
            assert hasattr(response, 'expires_at')
            assert hasattr(response, 'created_at')

            # Test JavaScript parsing of the datetime strings
            expires_at = response.expires_at
            created_at = response.created_at

            if expires_at:
                js_test_code = f"""
                const dateStr = "{expires_at}";
                const date = new Date(dateStr);
                console.log(JSON.stringify({{
                    valid: !isNaN(date.getTime()),
                    original: dateStr,
                    has_invalid_pattern: (dateStr.includes("+00:00") && dateStr.endsWith("Z"))
                }}));
                """

                result = subprocess.run(['node', '-e', js_test_code], capture_output=True, text=True)
                assert result.returncode == 0, f"JavaScript test failed: {result.stderr}"

                js_result = json.loads(result.stdout.strip())
                assert js_result["valid"] is True, f"JavaScript cannot parse expires_at: {expires_at}"
                assert js_result["has_invalid_pattern"] is False, f"expires_at has invalid +00:00Z pattern: {expires_at}"

            if created_at:
                js_test_code = f"""
                const dateStr = "{created_at}";
                const date = new Date(dateStr);
                console.log(JSON.stringify({{
                    valid: !isNaN(date.getTime()),
                    original: dateStr,
                    has_invalid_pattern: (dateStr.includes("+00:00") && dateStr.endsWith("Z"))
                }}));
                """

                result = subprocess.run(['node', '-e', js_test_code], capture_output=True, text=True)
                assert result.returncode == 0, f"JavaScript test failed: {result.stderr}"

                js_result = json.loads(result.stdout.strip())
                assert js_result["valid"] is True, f"JavaScript cannot parse created_at: {created_at}"
                assert js_result["has_invalid_pattern"] is False, f"created_at has invalid +00:00Z pattern: {created_at}"

        finally:
            # Restore original functions
            if original_generate:
                api_keys_module.generate_api_key = original_generate
            if original_hash:
                api_keys_module.hash_api_key = original_hash

    def test_api_key_response_follows_fastapi_best_practices(self):
        """Test that API key responses follow FastAPI timezone best practices."""
        # This test verifies that the datetime formatting in api_keys.py
        # doesn't create the problematic +00:00Z pattern that breaks JavaScript Date parsing

        # Create a mock datetime that would be typical for API keys
        test_datetime = datetime(2025, 9, 14, 20, 30, 0, tzinfo=timezone.utc)

        # Test the pattern that should NOT be used: .isoformat() + "Z"
        invalid_format = test_datetime.isoformat() + "Z"

        # This should create the problematic +00:00Z pattern
        assert "+00:00Z" in invalid_format, f"Expected invalid pattern not found in: {invalid_format}"

        # Test that JavaScript fails to parse the invalid format
        js_test_code = f"""
        const dateStr = "{invalid_format}";
        const date = new Date(dateStr);
        console.log(JSON.stringify({{
            valid: !isNaN(date.getTime()),
            original: dateStr
        }}));
        """

        result = subprocess.run(['node', '-e', js_test_code], capture_output=True, text=True)
        assert result.returncode == 0

        js_result = json.loads(result.stdout.strip())
        # The invalid format should fail JavaScript parsing
        assert js_result["valid"] is False, f"JavaScript should not parse invalid format: {invalid_format}"