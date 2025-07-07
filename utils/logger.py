"""
Centralized logging system for AI Instagram Publisher.

This module provides structured logging with rotation, performance tracking,
and integration with the configuration system.
"""

import logging
import logging.handlers
import sys
import time
import functools
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import json

# Import config with fallback to avoid circular imports
try:
    from config import get_config, ConfigurationError
except ImportError:
    # Fallback for circular import issues
    get_config = None
    ConfigurationError = Exception


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, use_json=False):
        """Initialize formatter with optional JSON mode."""
        super().__init__(fmt, datefmt, style, validate)
        self.use_json = use_json
        self._formatting = False  # Guard against recursion

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        # Guard against recursion
        if self._formatting:
            return super().format(record)

        self._formatting = True
        try:
            # If JSON mode is disabled, use standard formatting
            if not self.use_json:
                return super().format(record)

            # Create base log data for JSON format
            log_data = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }

            # Add extra fields if present
            if hasattr(record, 'extra_data'):
                log_data.update(record.extra_data)

            # Add exception info if present
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)

            # Return JSON format
            return json.dumps(log_data, default=str)

        except Exception:
            # Fallback to standard format on any error
            return super().format(record)
        finally:
            self._formatting = False


class PerformanceLogger:
    """Logger for performance tracking."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_execution_time(self, func_name: str, execution_time: float, **kwargs):
        """Log function execution time."""
        self.logger.info(
            f"Performance: {func_name} executed in {execution_time:.4f}s",
            extra={'extra_data': {
                'performance': True,
                'function': func_name,
                'execution_time': execution_time,
                **kwargs
            }}
        )

    def log_api_call(self, api_name: str, endpoint: str, response_time: float, 
                     status_code: Optional[int] = None, **kwargs):
        """Log API call performance."""
        self.logger.info(
            f"API Call: {api_name} {endpoint} - {response_time:.4f}s",
            extra={'extra_data': {
                'api_call': True,
                'api_name': api_name,
                'endpoint': endpoint,
                'response_time': response_time,
                'status_code': status_code,
                **kwargs
            }}
        )


class LoggerManager:
    """Manager for centralized logging configuration."""

    def __init__(self):
        self._loggers: Dict[str, logging.Logger] = {}
        self._configured = False
        self._performance_logger: Optional[PerformanceLogger] = None

    def setup_logging(self):
        """Set up logging configuration based on app config."""
        if self._configured:
            return

        # Set configured flag immediately to prevent recursion
        self._configured = True

        try:
            if get_config is not None:
                config = get_config()
                log_config = config.logging

                # Configure root logger
                root_logger = logging.getLogger()
                root_logger.setLevel(getattr(logging, log_config.level.upper()))

                # Clear existing handlers
                root_logger.handlers.clear()

                # Create formatter with JSON mode for production
                use_json = config.environment.value != 'development'
                formatter = StructuredFormatter(log_config.format, use_json=use_json)

                # Console handler
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                console_handler.setLevel(getattr(logging, log_config.level.upper()))
                root_logger.addHandler(console_handler)

                # File handler with rotation if file path is specified
                if log_config.file_path:
                    file_path = Path(log_config.file_path)
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    file_handler = logging.handlers.RotatingFileHandler(
                        filename=file_path,
                        maxBytes=log_config.max_file_size,
                        backupCount=log_config.backup_count,
                        encoding='utf-8'
                    )
                    file_handler.setFormatter(formatter)
                    file_handler.setLevel(getattr(logging, log_config.level.upper()))
                    root_logger.addHandler(file_handler)

                # Set up performance logger
                perf_logger = self.get_logger('performance')
                self._performance_logger = PerformanceLogger(perf_logger)

                # Log successful setup
                setup_logger = self.get_logger('logger_manager')
                setup_logger.info(
                    f"Logging configured - Level: {log_config.level}, "
                    f"File: {log_config.file_path or 'Console only'}, "
                    f"Environment: {config.environment.value}"
                )
            else:
                raise ConfigurationError("Configuration system not available")

        except (ConfigurationError, Exception) as e:
            # Fallback logging setup with simple formatter
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            root_logger.handlers.clear()

            # Use simple formatter for fallback to avoid recursion
            simple_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(simple_formatter)
            console_handler.setLevel(logging.INFO)
            root_logger.addHandler(console_handler)

            fallback_logger = logging.getLogger('logger_manager')
            fallback_logger.warning(f"Using fallback logging due to config error: {e}")

            # Set up basic performance logger
            perf_logger = self.get_logger('performance')
            self._performance_logger = PerformanceLogger(perf_logger)

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the given name."""
        if not self._configured:
            self.setup_logging()

        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger

        return self._loggers[name]

    @property
    def performance(self) -> PerformanceLogger:
        """Get performance logger."""
        if not self._configured:
            self.setup_logging()
        return self._performance_logger

    def log_config_status(self):
        """Log current configuration status."""
        status_logger = self.get_logger('config_status')

        try:
            if get_config is not None:
                config = get_config()
                status_logger.info("Configuration Status:", extra={'extra_data': {
                    'environment': config.environment.value,
                    'debug_mode': config.debug,
                    'openai_configured': bool(config.openai.api_key),
                    'instagram_configured': bool(config.instagram.access_token),
                    'telegram_configured': bool(config.telegram.bot_token),
                    'scheduling_enabled': config.scheduling.enabled,
                    'log_level': config.logging.level,
                    'log_file': config.logging.file_path
                }})
            else:
                status_logger.warning("Configuration system not available - using fallback logging")

        except (ConfigurationError, Exception) as e:
            status_logger.error(f"Configuration error: {e}")


# Global logger manager instance
logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    return logger_manager.get_logger(name)


def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance."""
    return logger_manager.performance


def log_execution_time(func: Callable = None, *, logger_name: Optional[str] = None):
    """Decorator to log function execution time.

    Args:
        func: Function to decorate
        logger_name: Custom logger name (defaults to function's module)

    Returns:
        Decorated function
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Get logger
            log_name = logger_name or f.__module__
            logger = get_logger(log_name)

            try:
                logger.debug(f"Starting execution: {f.__name__}")
                result = f(*args, **kwargs)

                execution_time = time.time() - start_time
                logger_manager.performance.log_execution_time(
                    f.__name__, 
                    execution_time,
                    module=f.__module__,
                    success=True
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Error in {f.__name__}: {str(e)}")
                logger_manager.performance.log_execution_time(
                    f.__name__, 
                    execution_time,
                    module=f.__module__,
                    success=False,
                    error=str(e)
                )
                raise

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def log_api_call(api_name: str, endpoint: str = ""):
    """Decorator to log API call performance.

    Args:
        api_name: Name of the API (e.g., 'OpenAI', 'Instagram')
        endpoint: API endpoint or method name

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger = get_logger(func.__module__)

            try:
                logger.debug(f"API Call: {api_name} {endpoint or func.__name__}")
                result = f(*args, **kwargs)

                response_time = time.time() - start_time
                logger_manager.performance.log_api_call(
                    api_name,
                    endpoint or func.__name__,
                    response_time,
                    success=True
                )

                return result

            except Exception as e:
                response_time = time.time() - start_time
                logger.error(f"API Error: {api_name} {endpoint or func.__name__}: {str(e)}")
                logger_manager.performance.log_api_call(
                    api_name,
                    endpoint or func.__name__,
                    response_time,
                    success=False,
                    error=str(e)
                )
                raise

        return wrapper
    return decorator


def setup_logging():
    """Initialize logging system."""
    logger_manager.setup_logging()
    # Note: log_config_status() is called separately to avoid recursion


# Note: Logging setup is now done explicitly by the application
# to avoid recursion issues during module import
