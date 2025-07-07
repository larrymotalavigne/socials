"""
Custom exception classes and error handling framework for AI Instagram Publisher.

This module provides structured error handling with proper categorization,
retry mechanisms, and error reporting.
"""

import time
import functools
from typing import Optional, Dict, Any, Callable, Type, Union
from enum import Enum

from utils.logger import get_logger


class ErrorCategory(Enum):
    """Categories of errors for better handling and reporting."""
    CONFIGURATION = "configuration"
    API_ERROR = "api_error"
    CONTENT_GENERATION = "content_generation"
    PUBLISHING = "publishing"
    SCHEDULING = "scheduling"
    VALIDATION = "validation"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    SYSTEM = "system"


class BaseAppException(Exception):
    """Base exception class for all application-specific exceptions."""
    
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.details = details or {}
        self.original_exception = original_exception
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/reporting."""
        return {
            'type': self.__class__.__name__,
            'message': self.message,
            'category': self.category.value,
            'details': self.details,
            'timestamp': self.timestamp,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }


class ConfigurationError(BaseAppException):
    """Raised when there's a configuration-related error."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        super().__init__(
            message, 
            ErrorCategory.CONFIGURATION, 
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class APIError(BaseAppException):
    """Raised when there's an API-related error."""
    
    def __init__(
        self, 
        message: str, 
        api_name: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = {
            'api_name': api_name,
            'status_code': status_code,
            'response_data': response_data
        }
        details.update(kwargs.get('details', {}))
        
        super().__init__(
            message, 
            ErrorCategory.API_ERROR, 
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class OpenAIError(APIError):
    """Raised when there's an OpenAI API error."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, api_name="OpenAI", **kwargs)


class InstagramError(APIError):
    """Raised when there's an Instagram API error."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, api_name="Instagram", **kwargs)


class TelegramError(APIError):
    """Raised when there's a Telegram API error."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, api_name="Telegram", **kwargs)


class ContentGenerationError(BaseAppException):
    """Raised when content generation fails."""
    
    def __init__(self, message: str, content_type: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if content_type:
            details['content_type'] = content_type
        
        super().__init__(
            message, 
            ErrorCategory.CONTENT_GENERATION, 
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class PublishingError(BaseAppException):
    """Raised when publishing fails."""
    
    def __init__(self, message: str, platform: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if platform:
            details['platform'] = platform
        
        super().__init__(
            message, 
            ErrorCategory.PUBLISHING, 
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class SchedulingError(BaseAppException):
    """Raised when scheduling operations fail."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, 
            ErrorCategory.SCHEDULING, 
            details=kwargs.get('details', {}),
            original_exception=kwargs.get('original_exception')
        )


class ValidationError(BaseAppException):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        
        super().__init__(
            message, 
            ErrorCategory.VALIDATION, 
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class NetworkError(BaseAppException):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, 
            ErrorCategory.NETWORK, 
            details=kwargs.get('details', {}),
            original_exception=kwargs.get('original_exception')
        )


class AuthenticationError(BaseAppException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, service: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if service:
            details['service'] = service
        
        super().__init__(
            message, 
            ErrorCategory.AUTHENTICATION, 
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class RateLimitError(BaseAppException):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self, 
        message: str, 
        service: Optional[str] = None,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if service:
            details['service'] = service
        if retry_after:
            details['retry_after'] = retry_after
        
        super().__init__(
            message, 
            ErrorCategory.RATE_LIMIT, 
            details=details,
            original_exception=kwargs.get('original_exception')
        )


class SystemError(BaseAppException):
    """Raised when system-level errors occur."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message, 
            ErrorCategory.SYSTEM, 
            details=kwargs.get('details', {}),
            original_exception=kwargs.get('original_exception')
        )


class ErrorHandler:
    """Global error handler for the application."""
    
    def __init__(self):
        self.logger = get_logger('error_handler')
        self._error_counts: Dict[str, int] = {}
    
    def handle_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Handle an exception with proper logging and categorization."""
        context = context or {}
        
        if isinstance(exception, BaseAppException):
            self._handle_app_exception(exception, context)
        else:
            self._handle_generic_exception(exception, context)
    
    def _handle_app_exception(self, exception: BaseAppException, context: Dict[str, Any]):
        """Handle application-specific exceptions."""
        error_data = exception.to_dict()
        error_data.update(context)
        
        # Count errors by type
        error_key = f"{exception.category.value}:{exception.__class__.__name__}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        
        # Log based on category
        if exception.category in [ErrorCategory.SYSTEM, ErrorCategory.API_ERROR]:
            self.logger.error(
                f"[{exception.category.value.upper()}] {exception.message}",
                extra={'extra_data': error_data}
            )
        elif exception.category == ErrorCategory.CONFIGURATION:
            self.logger.critical(
                f"[CONFIGURATION] {exception.message}",
                extra={'extra_data': error_data}
            )
        else:
            self.logger.warning(
                f"[{exception.category.value.upper()}] {exception.message}",
                extra={'extra_data': error_data}
            )
    
    def _handle_generic_exception(self, exception: Exception, context: Dict[str, Any]):
        """Handle generic Python exceptions."""
        error_data = {
            'type': exception.__class__.__name__,
            'message': str(exception),
            'category': 'unknown',
            'context': context
        }
        
        self.logger.error(
            f"[UNHANDLED] {exception.__class__.__name__}: {str(exception)}",
            extra={'extra_data': error_data},
            exc_info=True
        )
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics."""
        return self._error_counts.copy()


class RetryConfig:
    """Configuration for retry mechanisms."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def retry_on_exception(
    exceptions: Union[Type[Exception], tuple] = Exception,
    retry_config: Optional[RetryConfig] = None,
    logger_name: Optional[str] = None
):
    """Decorator to retry function calls on specific exceptions.
    
    Args:
        exceptions: Exception type(s) to retry on
        retry_config: Retry configuration
        logger_name: Custom logger name
        
    Returns:
        Decorated function
    """
    if retry_config is None:
        retry_config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            
            for attempt in range(retry_config.max_attempts):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    if attempt == retry_config.max_attempts - 1:
                        logger.error(
                            f"Function {func.__name__} failed after {retry_config.max_attempts} attempts",
                            extra={'extra_data': {
                                'function': func.__name__,
                                'attempts': retry_config.max_attempts,
                                'final_error': str(e)
                            }}
                        )
                        raise
                    
                    # Calculate delay
                    delay = min(
                        retry_config.base_delay * (retry_config.exponential_base ** attempt),
                        retry_config.max_delay
                    )
                    
                    if retry_config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{retry_config.max_attempts}), "
                        f"retrying in {delay:.2f}s: {str(e)}",
                        extra={'extra_data': {
                            'function': func.__name__,
                            'attempt': attempt + 1,
                            'max_attempts': retry_config.max_attempts,
                            'delay': delay,
                            'error': str(e)
                        }}
                    )
                    
                    time.sleep(delay)
        
        return wrapper
    return decorator


# Global error handler instance
error_handler = ErrorHandler()


def handle_exception(exception: Exception, context: Optional[Dict[str, Any]] = None):
    """Handle an exception using the global error handler."""
    error_handler.handle_exception(exception, context)


def get_error_stats() -> Dict[str, int]:
    """Get global error statistics."""
    return error_handler.get_error_stats()