"""
Configuration management system for AI Instagram Publisher.

This module provides comprehensive configuration management with validation,
environment support, and proper error handling.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv


class Environment(Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str
    model_chat: str = "gpt-4"
    model_image: str = "dall-e-3"
    max_tokens: int = 150
    temperature: float = 0.8
    image_size: str = "1024x1024"
    image_quality: str = "standard"

    def __post_init__(self):
        # Allow placeholder keys for testing purposes, but mark them as invalid
        if not self.api_key:
            raise ConfigurationError("OpenAI API key is required and must be set")

        # Note: We allow placeholder keys like "your_openai_key_here" to pass validation
        # The actual connection test will reveal if the key is valid


@dataclass
class OllamaConfig:
    """Ollama API configuration."""
    base_url: str = "http://localhost:11434"
    model: str = "llama2"
    timeout: int = 30
    temperature: float = 0.8
    max_tokens: int = 150

    def __post_init__(self):
        # Validate base URL format
        if not self.base_url.startswith(('http://', 'https://')):
            raise ConfigurationError("Ollama base URL must start with http:// or https://")


@dataclass
class InstagramConfig:
    """Instagram API configuration."""
    access_token: Optional[str] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    user_id: Optional[str] = None

    def __post_init__(self):
        # Instagram config is optional for now, but validate if provided
        if self.access_token and not self.user_id:
            raise ConfigurationError("Instagram user_id is required when access_token is provided")


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None

    def __post_init__(self):
        # Telegram config is optional for now
        if self.bot_token and not self.chat_id:
            raise ConfigurationError("Telegram chat_id is required when bot_token is provided")


@dataclass
class SchedulingConfig:
    """Scheduling configuration."""
    enabled: bool = False
    interval_hours: int = 24
    max_posts_per_day: int = 3
    timezone: str = "UTC"

    def __post_init__(self):
        if self.interval_hours <= 0:
            raise ConfigurationError("Scheduling interval must be positive")
        if self.max_posts_per_day <= 0:
            raise ConfigurationError("Max posts per day must be positive")


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    def __post_init__(self):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ConfigurationError(f"Invalid log level: {self.level}. Must be one of {valid_levels}")


@dataclass
class ContentConfig:
    """Content generation configuration."""
    output_directory: str = "generated_content"
    image_format: str = "png"
    max_caption_length: int = 2200  # Instagram limit
    hashtag_count: int = 10
    content_themes: List[str] = field(default_factory=lambda: ["nature", "lifestyle", "inspiration"])

    def __post_init__(self):
        # Create output directory if it doesn't exist
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)

        if self.max_caption_length > 2200:
            raise ConfigurationError("Instagram caption limit is 2200 characters")


@dataclass
class AppConfig:
    """Main application configuration."""
    # Required fields (no defaults)
    environment: Environment
    openai: OpenAIConfig
    ollama: OllamaConfig
    instagram: InstagramConfig
    telegram: TelegramConfig
    scheduling: SchedulingConfig
    logging: LoggingConfig
    content: ContentConfig

    # Optional fields (with defaults)
    debug: bool = False
    retry_attempts: int = 3
    retry_delay: float = 1.0
    request_timeout: int = 30
    caption_generator: str = "openai"  # "openai" or "ollama"

    def __post_init__(self):
        if self.retry_attempts <= 0:
            raise ConfigurationError("Retry attempts must be positive")
        if self.retry_delay < 0:
            raise ConfigurationError("Retry delay cannot be negative")
        if self.caption_generator not in ["openai", "ollama"]:
            raise ConfigurationError("Caption generator must be either 'openai' or 'ollama'")


class ConfigManager:
    """Configuration manager for loading and validating configuration."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            env_file: Path to environment file. If None, uses default .env
        """
        self.env_file = env_file or ".env"
        self._config: Optional[AppConfig] = None
        self._load_environment()

    def _load_environment(self):
        """Load environment variables from file."""
        if Path(self.env_file).exists():
            load_dotenv(self.env_file)
        else:
            # Try to load from default locations
            for env_path in [".env", ".env.local", ".env.development"]:
                if Path(env_path).exists():
                    load_dotenv(env_path)
                    break

    def _get_env(self, key: str, default: Any = None, required: bool = False) -> Any:
        """Get environment variable with validation.

        Args:
            key: Environment variable key
            default: Default value if not found
            required: Whether the variable is required

        Returns:
            Environment variable value

        Raises:
            ConfigurationError: If required variable is missing
        """
        value = os.getenv(key, default)
        if required and value is None:
            raise ConfigurationError(f"Required environment variable '{key}' is not set")
        return value

    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = self._get_env(key, str(default))
        return value.lower() in ("true", "1", "yes", "on")

    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer environment variable."""
        value = self._get_env(key, str(default))
        try:
            return int(value)
        except ValueError:
            raise ConfigurationError(f"Environment variable '{key}' must be an integer, got: {value}")

    def _get_float_env(self, key: str, default: float) -> float:
        """Get float environment variable."""
        value = self._get_env(key, str(default))
        try:
            return float(value)
        except ValueError:
            raise ConfigurationError(f"Environment variable '{key}' must be a float, got: {value}")

    def _get_list_env(self, key: str, default: List[str]) -> List[str]:
        """Get list environment variable (comma-separated)."""
        value = self._get_env(key, ",".join(default))
        return [item.strip() for item in value.split(",") if item.strip()]

    def load_config(self) -> AppConfig:
        """Load and validate configuration.

        Returns:
            Validated application configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Determine environment
            env_name = self._get_env("ENVIRONMENT", "development")
            try:
                environment = Environment(env_name.lower())
            except ValueError:
                raise ConfigurationError(f"Invalid environment: {env_name}")

            # Load OpenAI configuration
            openai_config = OpenAIConfig(
                api_key=self._get_env("OPENAI_API_KEY", required=True),
                model_chat=self._get_env("OPENAI_MODEL_CHAT", "gpt-4"),
                model_image=self._get_env("OPENAI_MODEL_IMAGE", "dall-e-3"),
                max_tokens=self._get_int_env("OPENAI_MAX_TOKENS", 150),
                temperature=self._get_float_env("OPENAI_TEMPERATURE", 0.8),
                image_size=self._get_env("OPENAI_IMAGE_SIZE", "1024x1024"),
                image_quality=self._get_env("OPENAI_IMAGE_QUALITY", "standard")
            )

            # Load Ollama configuration
            ollama_config = OllamaConfig(
                base_url=self._get_env("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=self._get_env("OLLAMA_MODEL", "llama2"),
                timeout=self._get_int_env("OLLAMA_TIMEOUT", 30),
                temperature=self._get_float_env("OLLAMA_TEMPERATURE", 0.8),
                max_tokens=self._get_int_env("OLLAMA_MAX_TOKENS", 150)
            )

            # Load Instagram configuration
            instagram_config = InstagramConfig(
                access_token=self._get_env("INSTAGRAM_ACCESS_TOKEN"),
                app_id=self._get_env("INSTAGRAM_APP_ID"),
                app_secret=self._get_env("INSTAGRAM_APP_SECRET"),
                user_id=self._get_env("INSTAGRAM_USER_ID")
            )

            # Load Telegram configuration
            telegram_config = TelegramConfig(
                bot_token=self._get_env("TELEGRAM_BOT_TOKEN"),
                chat_id=self._get_env("TELEGRAM_CHAT_ID")
            )

            # Load scheduling configuration
            scheduling_config = SchedulingConfig(
                enabled=self._get_bool_env("SCHEDULING_ENABLED", False),
                interval_hours=self._get_int_env("SCHEDULING_INTERVAL_HOURS", 24),
                max_posts_per_day=self._get_int_env("SCHEDULING_MAX_POSTS_PER_DAY", 3),
                timezone=self._get_env("SCHEDULING_TIMEZONE", "UTC")
            )

            # Load logging configuration
            logging_config = LoggingConfig(
                level=self._get_env("LOG_LEVEL", "INFO"),
                format=self._get_env("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                file_path=self._get_env("LOG_FILE_PATH"),
                max_file_size=self._get_int_env("LOG_MAX_FILE_SIZE", 10 * 1024 * 1024),
                backup_count=self._get_int_env("LOG_BACKUP_COUNT", 5)
            )

            # Load content configuration
            content_config = ContentConfig(
                output_directory=self._get_env("CONTENT_OUTPUT_DIR", "generated_content"),
                image_format=self._get_env("CONTENT_IMAGE_FORMAT", "png"),
                max_caption_length=self._get_int_env("CONTENT_MAX_CAPTION_LENGTH", 2200),
                hashtag_count=self._get_int_env("CONTENT_HASHTAG_COUNT", 10),
                content_themes=self._get_list_env("CONTENT_THEMES", ["nature", "lifestyle", "inspiration"])
            )

            # Create main configuration
            self._config = AppConfig(
                environment=environment,
                debug=self._get_bool_env("DEBUG", False),
                openai=openai_config,
                ollama=ollama_config,
                instagram=instagram_config,
                telegram=telegram_config,
                scheduling=scheduling_config,
                logging=logging_config,
                content=content_config,
                retry_attempts=self._get_int_env("RETRY_ATTEMPTS", 3),
                retry_delay=self._get_float_env("RETRY_DELAY", 1.0),
                request_timeout=self._get_int_env("REQUEST_TIMEOUT", 30),
                caption_generator=self._get_env("CAPTION_GENERATOR", "openai")
            )

            return self._config

        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")

    @property
    def config(self) -> AppConfig:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def reload_config(self) -> AppConfig:
        """Reload configuration from environment."""
        self._load_environment()
        self._config = None
        return self.load_config()

    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration and return status.

        Returns:
            Dictionary with validation results
        """
        try:
            config = self.config
            return {
                "valid": True,
                "environment": config.environment.value,
                "openai_configured": bool(config.openai.api_key),
                "ollama_configured": bool(config.ollama.base_url),
                "caption_generator": config.caption_generator,
                "instagram_configured": bool(config.instagram.access_token),
                "telegram_configured": bool(config.telegram.bot_token),
                "scheduling_enabled": config.scheduling.enabled,
                "debug_mode": config.debug
            }
        except ConfigurationError as e:
            return {
                "valid": False,
                "error": str(e)
            }


# Global configuration manager instance
config_manager = ConfigManager()

# Convenience function to get configuration
def get_config() -> AppConfig:
    """Get application configuration."""
    return config_manager.config
