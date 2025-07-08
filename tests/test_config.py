"""
Unit tests for configuration management system.

This module tests the configuration loading, validation, and error handling
to ensure proper configuration management across different environments.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from typing import Dict, Any

from config import (
    ConfigManager,
    AppConfig,
    OpenAIConfig,
    OllamaConfig,
    InstagramConfig,
    TelegramConfig,
    SchedulingConfig,
    LoggingConfig,
    ContentConfig,
    Environment,
    ConfigurationError,
    get_config
)


class TestConfigManager:
    """Test cases for ConfigManager class."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.config_manager = ConfigManager()
        # Clear any cached config
        self.config_manager._config = None

    def test_get_env_with_default(self):
        """Test getting environment variable with default value."""
        with patch.dict(os.environ, {}, clear=True):
            result = _get_env("TEST_VAR", "default_value")
            assert result == "default_value"

    def test_get_env_with_existing_value(self):
        """Test getting existing environment variable."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = _get_env("TEST_VAR", "default_value")
            assert result == "test_value"

    def test_get_env_required_missing(self):
        """Test getting required environment variable that's missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError, match="Required environment variable 'TEST_VAR' is not set"):
                _get_env("TEST_VAR", required=True)

    def test_get_bool_env_true_values(self):
        """Test boolean environment variable parsing for true values."""
        true_values = ["true", "True", "TRUE", "1", "yes", "YES", "on", "ON"]
        for value in true_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                result = _get_bool_env("TEST_BOOL")
                assert result is True, f"Failed for value: {value}"

    def test_get_bool_env_false_values(self):
        """Test boolean environment variable parsing for false values."""
        false_values = ["false", "False", "FALSE", "0", "no", "NO", "off", "OFF", ""]
        for value in false_values:
            with patch.dict(os.environ, {"TEST_BOOL": value}):
                result = _get_bool_env("TEST_BOOL")
                assert result is False, f"Failed for value: {value}"

    def test_get_int_env_valid(self):
        """Test integer environment variable parsing with valid values."""
        with patch.dict(os.environ, {"TEST_INT": "42"}):
            result = _get_int_env("TEST_INT", 0)
            assert result == 42

    def test_get_int_env_invalid(self):
        """Test integer environment variable parsing with invalid values."""
        with patch.dict(os.environ, {"TEST_INT": "not_a_number"}):
            with pytest.raises(ConfigurationError, match="must be an integer"):
                _get_int_env("TEST_INT", 0)

    def test_get_float_env_valid(self):
        """Test float environment variable parsing with valid values."""
        with patch.dict(os.environ, {"TEST_FLOAT": "3.14"}):
            result = _get_float_env("TEST_FLOAT", 0.0)
            assert result == 3.14

    def test_get_float_env_invalid(self):
        """Test float environment variable parsing with invalid values."""
        with patch.dict(os.environ, {"TEST_FLOAT": "not_a_number"}):
            with pytest.raises(ConfigurationError, match="must be a float"):
                _get_float_env("TEST_FLOAT", 0.0)

    def test_get_list_env(self):
        """Test list environment variable parsing."""
        with patch.dict(os.environ, {"TEST_LIST": "item1,item2,item3"}):
            result = _get_list_env("TEST_LIST", [])
            assert result == ["item1", "item2", "item3"]

    def test_get_list_env_with_spaces(self):
        """Test list environment variable parsing with spaces."""
        with patch.dict(os.environ, {"TEST_LIST": "item1, item2 , item3"}):
            result = _get_list_env("TEST_LIST", [])
            assert result == ["item1", "item2", "item3"]

    def test_load_config_minimal(self):
        """Test loading configuration with minimal required settings."""
        env_vars = {
            "OPENAI_API_KEY": "test_key",
            "ENVIRONMENT": "development"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.config_manager.load_config()
            
            assert isinstance(config, AppConfig)
            assert config.environment == Environment.DEVELOPMENT
            assert config.openai.api_key == "test_key"
            assert config.debug is False

    def test_load_config_complete(self):
        """Test loading configuration with all settings."""
        env_vars = {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "OPENAI_API_KEY": "test_openai_key",
            "OPENAI_MODEL_CHAT": "gpt-4",
            "OPENAI_MODEL_IMAGE": "dall-e-3",
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_MODEL": "llama2",
            "INSTAGRAM_ACCESS_TOKEN": "test_instagram_token",
            "INSTAGRAM_USER_ID": "test_user_id",
            "TELEGRAM_BOT_TOKEN": "test_telegram_token",
            "TELEGRAM_CHAT_ID": "test_chat_id",
            "CAPTION_GENERATOR": "ollama",
            "CONTENT_OUTPUT_DIR": "/tmp/test_output",
            "CONTENT_HASHTAG_COUNT": "15"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = self.config_manager.load_config()
            
            assert config.environment == Environment.PRODUCTION
            assert config.debug is False
            assert config.openai.api_key == "test_openai_key"
            assert config.ollama.model == "llama2"
            assert config.instagram.access_token == "test_instagram_token"
            assert config.telegram.bot_token == "test_telegram_token"
            assert config.caption_generator == "ollama"
            assert config.content.hashtag_count == 15

    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        env_vars = {
            "OPENAI_API_KEY": "test_key",
            "ENVIRONMENT": "development"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            result = self.config_manager.validate_config()
            
            assert result["valid"] is True
            assert result["environment"] == "development"
            assert result["openai_configured"] is True

    def test_validate_config_invalid(self):
        """Test configuration validation with invalid config."""
        with patch.dict(os.environ, {}, clear=True):
            result = self.config_manager.validate_config()
            
            assert result["valid"] is False
            assert "error" in result


class TestConfigClasses:
    """Test cases for configuration data classes."""

    def test_openai_config_valid(self):
        """Test OpenAI configuration with valid data."""
        config = OpenAIConfig(
            api_key="test_key",
            model_chat="gpt-4",
            model_image="dall-e-3"
        )
        assert config.api_key == "test_key"
        assert config.model_chat == "gpt-4"
        assert config.model_image == "dall-e-3"

    def test_openai_config_empty_key(self):
        """Test OpenAI configuration with empty API key."""
        with pytest.raises(ConfigurationError, match="OpenAI API key is required"):
            OpenAIConfig(api_key="")

    def test_ollama_config_valid(self):
        """Test Ollama configuration with valid data."""
        config = OllamaConfig(
            base_url="http://localhost:11434",
            model="llama2"
        )
        assert config.base_url == "http://localhost:11434"
        assert config.model == "llama2"

    def test_ollama_config_invalid_url(self):
        """Test Ollama configuration with invalid URL."""
        with pytest.raises(ConfigurationError, match="must start with http"):
            OllamaConfig(base_url="invalid_url")

    def test_instagram_config_valid(self):
        """Test Instagram configuration with valid data."""
        config = InstagramConfig(
            access_token="test_token",
            user_id="test_user_id"
        )
        assert config.access_token == "test_token"
        assert config.user_id == "test_user_id"

    def test_instagram_config_missing_user_id(self):
        """Test Instagram configuration with missing user ID."""
        with pytest.raises(ConfigurationError, match="user_id is required"):
            InstagramConfig(access_token="test_token", user_id=None)

    def test_telegram_config_valid(self):
        """Test Telegram configuration with valid data."""
        config = TelegramConfig(
            bot_token="test_token",
            chat_id="test_chat_id"
        )
        assert config.bot_token == "test_token"
        assert config.chat_id == "test_chat_id"

    def test_telegram_config_missing_chat_id(self):
        """Test Telegram configuration with missing chat ID."""
        with pytest.raises(ConfigurationError, match="chat_id is required"):
            TelegramConfig(bot_token="test_token", chat_id=None)

    def test_scheduling_config_valid(self):
        """Test scheduling configuration with valid data."""
        config = SchedulingConfig(
            enabled=True,
            interval_hours=12,
            max_posts_per_day=5
        )
        assert config.enabled is True
        assert config.interval_hours == 12
        assert config.max_posts_per_day == 5

    def test_scheduling_config_invalid_interval(self):
        """Test scheduling configuration with invalid interval."""
        with pytest.raises(ConfigurationError, match="interval must be positive"):
            SchedulingConfig(interval_hours=0)

    def test_logging_config_valid(self):
        """Test logging configuration with valid data."""
        config = LoggingConfig(
            level="DEBUG",
            file_path="/tmp/test.log"
        )
        assert config.level == "DEBUG"
        assert config.file_path == "/tmp/test.log"

    def test_logging_config_invalid_level(self):
        """Test logging configuration with invalid level."""
        with pytest.raises(ConfigurationError, match="Invalid log level"):
            LoggingConfig(level="INVALID")

    def test_content_config_valid(self):
        """Test content configuration with valid data."""
        config = ContentConfig(
            output_directory="/tmp/test",
            max_caption_length=2000,
            hashtag_count=15
        )
        assert config.output_directory == "/tmp/test"
        assert config.max_caption_length == 2000
        assert config.hashtag_count == 15

    def test_content_config_invalid_caption_length(self):
        """Test content configuration with invalid caption length."""
        with pytest.raises(ConfigurationError, match="Instagram caption limit"):
            ContentConfig(max_caption_length=3000)

    def test_app_config_valid(self):
        """Test app configuration with valid data."""
        openai_config = OpenAIConfig(api_key="test_key")
        ollama_config = OllamaConfig()
        instagram_config = InstagramConfig()
        telegram_config = TelegramConfig()
        scheduling_config = SchedulingConfig()
        logging_config = LoggingConfig()
        content_config = ContentConfig()
        
        config = AppConfig(
            environment=Environment.DEVELOPMENT,
            openai=openai_config,
            ollama=ollama_config,
            instagram=instagram_config,
            telegram=telegram_config,
            scheduling=scheduling_config,
            logging=logging_config,
            content=content_config,
            caption_generator="openai"
        )
        
        assert config.environment == Environment.DEVELOPMENT
        assert config.caption_generator == "openai"

    def test_app_config_invalid_caption_generator(self):
        """Test app configuration with invalid caption generator."""
        openai_config = OpenAIConfig(api_key="test_key")
        ollama_config = OllamaConfig()
        instagram_config = InstagramConfig()
        telegram_config = TelegramConfig()
        scheduling_config = SchedulingConfig()
        logging_config = LoggingConfig()
        content_config = ContentConfig()
        
        with pytest.raises(ConfigurationError, match="must be either 'openai' or 'ollama'"):
            AppConfig(
                environment=Environment.DEVELOPMENT,
                openai=openai_config,
                ollama=ollama_config,
                instagram=instagram_config,
                telegram=telegram_config,
                scheduling=scheduling_config,
                logging=logging_config,
                content=content_config,
                caption_generator="invalid"
            )


class TestEnvironmentEnum:
    """Test cases for Environment enum."""

    def test_environment_values(self):
        """Test environment enum values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"

    def test_environment_from_string(self):
        """Test creating environment from string."""
        assert Environment("development") == Environment.DEVELOPMENT
        assert Environment("staging") == Environment.STAGING
        assert Environment("production") == Environment.PRODUCTION


@pytest.fixture
def mock_env_file():
    """Fixture providing mock .env file content."""
    return """
ENVIRONMENT=development
DEBUG=true
OPENAI_API_KEY=test_openai_key
OLLAMA_MODEL=llama2
INSTAGRAM_ACCESS_TOKEN=test_instagram_token
INSTAGRAM_USER_ID=test_user_id
CAPTION_GENERATOR=openai
"""


class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_load_from_env_file(self, mock_env_file):
        """Test loading configuration from .env file."""
        with patch("builtins.open", mock_open(read_data=mock_env_file)):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("dotenv.load_dotenv") as mock_load_dotenv:
                    config_manager = ConfigManager(".env")
                    mock_load_dotenv.assert_called()

    def test_get_config_singleton(self):
        """Test that get_config returns the same instance."""
        env_vars = {
            "OPENAI_API_KEY": "test_key",
            "ENVIRONMENT": "development"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config1 = get_config()
            config2 = get_config()
            
            # Should be the same instance due to caching
            assert config1 is config2

    def test_reload_config(self):
        """Test configuration reloading."""
        config_manager = ConfigManager()
        
        # Load initial config
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key1", "ENVIRONMENT": "development"}):
            config1 = config_manager.load_config()
            assert config1.openai.api_key == "key1"
        
        # Reload with different values
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key2", "ENVIRONMENT": "production"}):
            config2 = config_manager.reload_config()
            assert config2.openai.api_key == "key2"
            assert config2.environment == Environment.PRODUCTION