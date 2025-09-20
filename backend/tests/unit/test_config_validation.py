"""
T062: Unit tests for configuration validation
Tests adapter configuration validation, encryption, and management.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from typing import Dict, Any, List
import json
import base64

from src.services.config_manager import (
    ConfigurationManager,
    ConfigValidator,
    CredentialEncryption,
    ConfigurationError,
    ValidationError,
    EncryptionError,
)
from src.schemas.adapter_schemas import (
    AdapterConfigurationCreate,
    AdapterConfigurationUpdate,
    ProviderConfig,
)


class TestConfigValidator:
    """Test the ConfigValidator class."""

    def test_validate_alpha_vantage_config_success(self):
        """Test successful Alpha Vantage configuration validation."""
        config = {
            "api_key": "ABCD1234567890",
            "base_url": "https://www.alphavantage.co/query",
            "timeout": 30,
            "requests_per_minute": 5
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("alpha_vantage", config)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_validate_alpha_vantage_config_missing_api_key(self):
        """Test Alpha Vantage configuration validation with missing API key."""
        config = {
            "base_url": "https://www.alphavantage.co/query",
            "timeout": 30
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("alpha_vantage", config)

        assert result.is_valid is False
        assert "api_key is required" in result.errors
        assert len(result.warnings) == 0

    def test_validate_alpha_vantage_config_invalid_api_key_format(self):
        """Test Alpha Vantage configuration validation with invalid API key format."""
        config = {
            "api_key": "short",  # Too short
            "base_url": "https://www.alphavantage.co/query"
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("alpha_vantage", config)

        assert result.is_valid is False
        assert "api_key must be at least 8 characters" in result.errors

    def test_validate_alpha_vantage_config_invalid_url(self):
        """Test Alpha Vantage configuration validation with invalid URL."""
        config = {
            "api_key": "ABCD1234567890",
            "base_url": "not-a-valid-url"
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("alpha_vantage", config)

        assert result.is_valid is False
        assert "base_url must be a valid URL" in result.errors

    def test_validate_yahoo_finance_config_success(self):
        """Test successful Yahoo Finance configuration validation."""
        config = {
            "base_url": "https://query1.finance.yahoo.com/v8/finance/chart",
            "timeout": 30,
            "max_retries": 3,
            "user_agent": "Custom User Agent"
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("yahoo_finance", config)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_yahoo_finance_config_warnings(self):
        """Test Yahoo Finance configuration validation with warnings."""
        config = {
            "timeout": 60,  # High timeout
            "max_retries": 10  # High retry count
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("yahoo_finance", config)

        assert result.is_valid is True
        assert "timeout is quite high" in result.warnings
        assert "max_retries is quite high" in result.warnings

    def test_validate_iex_cloud_config_success(self):
        """Test successful IEX Cloud configuration validation."""
        config = {
            "api_token": "pk_test_abc123def456",
            "base_url": "https://cloud.iexapis.com/stable",
            "sandbox": True
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("iex_cloud", config)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_iex_cloud_config_production_warning(self):
        """Test IEX Cloud configuration validation with production warning."""
        config = {
            "api_token": "sk_live_abc123def456",  # Live token
            "base_url": "https://cloud.iexapis.com/stable",
            "sandbox": False
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("iex_cloud", config)

        assert result.is_valid is True
        assert "Using live API token" in result.warnings

    def test_validate_polygon_config_success(self):
        """Test successful Polygon configuration validation."""
        config = {
            "api_key": "abc123def456ghi789",
            "base_url": "https://api.polygon.io",
            "tier": "basic"
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("polygon", config)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_finnhub_config_success(self):
        """Test successful Finnhub configuration validation."""
        config = {
            "api_key": "bq123abc456def789",
            "base_url": "https://finnhub.io/api/v1"
        }

        validator = ConfigValidator()
        result = validator.validate_provider_config("finnhub", config)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_unknown_provider(self):
        """Test validation of unknown provider."""
        config = {"any": "config"}

        validator = ConfigValidator()
        result = validator.validate_provider_config("unknown_provider", config)

        assert result.is_valid is False
        assert "Unknown provider" in result.errors

    def test_validate_common_config_fields(self):
        """Test validation of common configuration fields."""
        config = {
            "api_key": "valid_key",
            "timeout": -5,  # Invalid
            "max_retries": "not_a_number",  # Invalid type
            "requests_per_minute": 1000000  # Too high
        }

        validator = ConfigValidator()
        result = validator._validate_common_fields(config)

        assert result.is_valid is False
        assert "timeout must be positive" in result.errors
        assert "max_retries must be an integer" in result.errors
        assert "requests_per_minute is too high" in result.warnings

    def test_validate_required_fields(self):
        """Test validation of required fields."""
        config = {"optional_field": "value"}
        required_fields = ["required_field1", "required_field2"]

        validator = ConfigValidator()
        errors = validator._validate_required_fields(config, required_fields)

        assert "required_field1 is required" in errors
        assert "required_field2 is required" in errors

    def test_validate_url_format(self):
        """Test URL format validation."""
        validator = ConfigValidator()

        # Valid URLs
        assert validator._is_valid_url("https://api.example.com") is True
        assert validator._is_valid_url("http://localhost:8080") is True

        # Invalid URLs
        assert validator._is_valid_url("not-a-url") is False
        assert validator._is_valid_url("ftp://invalid-protocol.com") is False
        assert validator._is_valid_url("") is False

    def test_validate_api_key_format(self):
        """Test API key format validation."""
        validator = ConfigValidator()

        # Valid API keys
        assert validator._is_valid_api_key("abcd1234efgh5678") is True
        assert validator._is_valid_api_key("ABCD1234EFGH5678") is True

        # Invalid API keys
        assert validator._is_valid_api_key("short") is False
        assert validator._is_valid_api_key("") is False
        assert validator._is_valid_api_key("key with spaces") is False


class TestCredentialEncryption:
    """Test the CredentialEncryption class."""

    @pytest.fixture
    def encryption_key(self):
        """Generate a test encryption key."""
        from cryptography.fernet import Fernet
        return Fernet.generate_key()

    @pytest.fixture
    def credential_encryption(self, encryption_key):
        """Create CredentialEncryption instance with test key."""
        with patch.dict('os.environ', {'ENCRYPTION_KEY': base64.b64encode(encryption_key).decode()}):
            return CredentialEncryption()

    def test_encrypt_decrypt_round_trip(self, credential_encryption):
        """Test encryption and decryption round trip."""
        original_value = "sensitive_api_key_12345"

        encrypted = credential_encryption.encrypt(original_value)
        decrypted = credential_encryption.decrypt(encrypted)

        assert decrypted == original_value
        assert encrypted != original_value

    def test_encrypt_sensitive_fields(self, credential_encryption):
        """Test encryption of sensitive configuration fields."""
        config = {
            "api_key": "sensitive_key",
            "secret": "secret_value",
            "password": "password123",
            "non_sensitive": "normal_value"
        }

        encrypted_config = credential_encryption.encrypt_sensitive_fields(config)

        # Sensitive fields should be encrypted
        assert encrypted_config["api_key"] != config["api_key"]
        assert encrypted_config["secret"] != config["secret"]
        assert encrypted_config["password"] != config["password"]

        # Non-sensitive fields should remain unchanged
        assert encrypted_config["non_sensitive"] == config["non_sensitive"]

    def test_decrypt_sensitive_fields(self, credential_encryption):
        """Test decryption of sensitive configuration fields."""
        config = {
            "api_key": "sensitive_key",
            "secret": "secret_value",
            "password": "password123",
            "non_sensitive": "normal_value"
        }

        # Encrypt first
        encrypted_config = credential_encryption.encrypt_sensitive_fields(config)

        # Then decrypt
        decrypted_config = credential_encryption.decrypt_sensitive_fields(encrypted_config)

        # Should match original config
        assert decrypted_config == config

    def test_encrypt_empty_value(self, credential_encryption):
        """Test encryption of empty value."""
        encrypted = credential_encryption.encrypt("")
        decrypted = credential_encryption.decrypt(encrypted)

        assert decrypted == ""

    def test_encrypt_none_value(self, credential_encryption):
        """Test encryption of None value."""
        encrypted = credential_encryption.encrypt(None)
        assert encrypted is None

    def test_decrypt_invalid_data(self, credential_encryption):
        """Test decryption of invalid data."""
        with pytest.raises(EncryptionError):
            credential_encryption.decrypt("invalid_encrypted_data")

    def test_missing_encryption_key(self):
        """Test initialization without encryption key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(EncryptionError, match="ENCRYPTION_KEY environment variable not set"):
                CredentialEncryption()

    def test_invalid_encryption_key(self):
        """Test initialization with invalid encryption key."""
        with patch.dict('os.environ', {'ENCRYPTION_KEY': 'invalid_key'}):
            with pytest.raises(EncryptionError, match="Invalid encryption key format"):
                CredentialEncryption()


class TestConfigurationManager:
    """Test the ConfigurationManager class."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def mock_encryption(self):
        """Mock credential encryption."""
        mock = Mock(spec=CredentialEncryption)
        mock.encrypt_sensitive_fields.return_value = {"encrypted": "config"}
        mock.decrypt_sensitive_fields.return_value = {"decrypted": "config"}
        return mock

    @pytest.fixture
    def config_manager(self, mock_db_session, mock_encryption):
        """Create ConfigurationManager with mocked dependencies."""
        return ConfigurationManager(
            db_session=mock_db_session,
            encryption=mock_encryption
        )

    @pytest.mark.asyncio
    async def test_create_configuration_success(self, config_manager):
        """Test successful configuration creation."""
        config_data = AdapterConfigurationCreate(
            provider_name="alpha_vantage",
            display_name="Test Alpha Vantage",
            config={"api_key": "test_key"},
            is_active=True,
            priority=1
        )

        # Mock database operations
        config_manager.db_session.add = Mock()
        config_manager.db_session.commit = Mock()
        config_manager.db_session.refresh = Mock()

        result = await config_manager.create_configuration(config_data)

        assert result is not None
        config_manager.encryption.encrypt_sensitive_fields.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_configuration_validation_error(self, config_manager):
        """Test configuration creation with validation error."""
        config_data = AdapterConfigurationCreate(
            provider_name="alpha_vantage",
            display_name="Test",
            config={"invalid": "config"},  # Missing required api_key
            is_active=True,
            priority=1
        )

        with pytest.raises(ValidationError):
            await config_manager.create_configuration(config_data)

    @pytest.mark.asyncio
    async def test_update_configuration_success(self, config_manager):
        """Test successful configuration update."""
        adapter_id = "adapter_123"
        update_data = AdapterConfigurationUpdate(
            display_name="Updated Name",
            config={"api_key": "new_key"},
            is_active=False
        )

        # Mock existing configuration
        existing_config = Mock()
        existing_config.id = adapter_id
        existing_config.provider_name = "alpha_vantage"
        config_manager.db_session.query.return_value.filter.return_value.first.return_value = existing_config

        result = await config_manager.update_configuration(adapter_id, update_data)

        assert result == existing_config
        config_manager.encryption.encrypt_sensitive_fields.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_configuration_not_found(self, config_manager):
        """Test configuration update when configuration not found."""
        adapter_id = "nonexistent"
        update_data = AdapterConfigurationUpdate(display_name="Updated")

        # Mock no configuration found
        config_manager.db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ConfigurationError, match="Configuration not found"):
            await config_manager.update_configuration(adapter_id, update_data)

    @pytest.mark.asyncio
    async def test_delete_configuration_success(self, config_manager):
        """Test successful configuration deletion."""
        adapter_id = "adapter_123"

        # Mock existing configuration
        existing_config = Mock()
        config_manager.db_session.query.return_value.filter.return_value.first.return_value = existing_config

        result = await config_manager.delete_configuration(adapter_id)

        assert result is True
        config_manager.db_session.delete.assert_called_once_with(existing_config)
        config_manager.db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_configuration_not_found(self, config_manager):
        """Test configuration deletion when configuration not found."""
        adapter_id = "nonexistent"

        # Mock no configuration found
        config_manager.db_session.query.return_value.filter.return_value.first.return_value = None

        result = await config_manager.delete_configuration(adapter_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_configuration_success(self, config_manager):
        """Test successful configuration retrieval."""
        adapter_id = "adapter_123"

        # Mock existing configuration
        existing_config = Mock()
        existing_config.config = {"encrypted": "config"}
        config_manager.db_session.query.return_value.filter.return_value.first.return_value = existing_config

        result = await config_manager.get_configuration(adapter_id)

        assert result == existing_config
        config_manager.encryption.decrypt_sensitive_fields.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_configuration_not_found(self, config_manager):
        """Test configuration retrieval when configuration not found."""
        adapter_id = "nonexistent"

        # Mock no configuration found
        config_manager.db_session.query.return_value.filter.return_value.first.return_value = None

        result = await config_manager.get_configuration(adapter_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_configurations(self, config_manager):
        """Test listing all configurations."""
        # Mock configurations
        config1 = Mock()
        config1.config = {"encrypted": "config1"}
        config2 = Mock()
        config2.config = {"encrypted": "config2"}

        config_manager.db_session.query.return_value.all.return_value = [config1, config2]

        result = await config_manager.list_configurations()

        assert len(result) == 2
        assert config_manager.encryption.decrypt_sensitive_fields.call_count == 2

    @pytest.mark.asyncio
    async def test_list_configurations_by_provider(self, config_manager):
        """Test listing configurations by provider."""
        provider_name = "alpha_vantage"

        # Mock configurations
        config1 = Mock()
        config1.config = {"encrypted": "config1"}

        config_manager.db_session.query.return_value.filter.return_value.all.return_value = [config1]

        result = await config_manager.list_configurations_by_provider(provider_name)

        assert len(result) == 1
        config_manager.encryption.decrypt_sensitive_fields.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_configuration_success(self, config_manager):
        """Test configuration testing."""
        config_data = {
            "provider_name": "alpha_vantage",
            "config": {"api_key": "test_key"}
        }

        # Mock adapter creation and testing
        with patch('src.services.adapters.registry.get_provider_registry') as mock_registry:
            mock_adapter = Mock()
            mock_adapter.validate_config = AsyncMock(return_value=True)
            mock_adapter.connect = AsyncMock(return_value=True)
            mock_adapter.disconnect = AsyncMock()

            mock_registry.return_value.create_adapter.return_value = mock_adapter

            result = await config_manager.test_configuration(config_data)

            assert result["success"] is True
            assert "Test successful" in result["message"]

    @pytest.mark.asyncio
    async def test_test_configuration_failure(self, config_manager):
        """Test configuration testing with failure."""
        config_data = {
            "provider_name": "alpha_vantage",
            "config": {"api_key": "invalid_key"}
        }

        # Mock adapter creation failure
        with patch('src.services.adapters.registry.get_provider_registry') as mock_registry:
            mock_adapter = Mock()
            mock_adapter.validate_config = AsyncMock(side_effect=Exception("Invalid config"))

            mock_registry.return_value.create_adapter.return_value = mock_adapter

            result = await config_manager.test_configuration(config_data)

            assert result["success"] is False
            assert "Invalid config" in result["message"]

    @pytest.mark.asyncio
    async def test_export_configurations(self, config_manager):
        """Test exporting configurations."""
        # Mock configurations
        config1 = Mock()
        config1.to_dict.return_value = {"id": "1", "provider": "alpha_vantage"}
        config2 = Mock()
        config2.to_dict.return_value = {"id": "2", "provider": "yahoo_finance"}

        config_manager.db_session.query.return_value.all.return_value = [config1, config2]

        result = await config_manager.export_configurations()

        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    @pytest.mark.asyncio
    async def test_import_configurations(self, config_manager):
        """Test importing configurations."""
        import_data = [
            {
                "provider_name": "alpha_vantage",
                "display_name": "Imported AV",
                "config": {"api_key": "imported_key"},
                "is_active": True,
                "priority": 1
            }
        ]

        # Mock successful creation
        config_manager.create_configuration = AsyncMock(return_value=Mock())

        result = await config_manager.import_configurations(import_data)

        assert result["imported"] == 1
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_validate_configuration_schema(self, config_manager):
        """Test configuration schema validation."""
        # Valid configuration
        valid_config = {
            "provider_name": "alpha_vantage",
            "display_name": "Test",
            "config": {"api_key": "test_key"},
            "is_active": True,
            "priority": 1
        }

        result = config_manager.validate_configuration_schema(valid_config)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

        # Invalid configuration
        invalid_config = {
            "provider_name": "alpha_vantage",
            # Missing required fields
        }

        result = config_manager.validate_configuration_schema(invalid_config)
        assert result["valid"] is False
        assert len(result["errors"]) > 0