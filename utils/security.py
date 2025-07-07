"""
Security utilities for AI Socials.

This module provides comprehensive security features including:
- Input validation and sanitization
- Rate limiting and abuse prevention
- Audit logging for sensitive operations
- API key management and rotation
- Encryption utilities for sensitive data
"""

import re
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from functools import wraps
from dataclasses import dataclass, field
from pathlib import Path
import json
import logging
from collections import defaultdict, deque

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from utils.logger import get_logger


@dataclass
class ValidationRule:
    """Represents a validation rule for input validation."""
    name: str
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_chars: Optional[str] = None
    forbidden_chars: Optional[str] = None
    custom_validator: Optional[Callable[[str], bool]] = None
    error_message: str = "Validation failed"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_requests: int
    time_window: int  # seconds
    burst_limit: Optional[int] = None
    block_duration: int = 300  # 5 minutes default


@dataclass
class AuditLogEntry:
    """Represents an audit log entry."""
    timestamp: datetime
    user_id: Optional[str]
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    risk_level: str = "low"  # low, medium, high, critical


class InputValidator:
    """Comprehensive input validation and sanitization."""

    def __init__(self):
        """Initialize the input validator with default rules."""
        self.logger = get_logger(__name__)
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Set up default validation rules."""
        self.rules = {
            'prompt': ValidationRule(
                name='prompt',
                min_length=1,
                max_length=2000,
                forbidden_chars='<>{}[]|\\`',
                error_message="Prompt must be 1-2000 characters and not contain special characters"
            ),
            'api_key': ValidationRule(
                name='api_key',
                pattern=r'^[a-zA-Z0-9\-_\.]+$',
                min_length=20,
                max_length=200,
                error_message="Invalid API key format"
            ),
            'user_id': ValidationRule(
                name='user_id',
                pattern=r'^[a-zA-Z0-9_\-]+$',
                min_length=1,
                max_length=100,
                error_message="User ID must be alphanumeric with underscores and hyphens only"
            ),
            'filename': ValidationRule(
                name='filename',
                pattern=r'^[a-zA-Z0-9_\-\.]+$',
                max_length=255,
                forbidden_chars='<>:"/\\|?*',
                error_message="Invalid filename format"
            ),
            'hashtag': ValidationRule(
                name='hashtag',
                pattern=r'^#[a-zA-Z0-9_]+$',
                min_length=2,
                max_length=100,
                error_message="Hashtag must start with # and contain only alphanumeric characters and underscores"
            ),
            'url': ValidationRule(
                name='url',
                pattern=r'^https?://[^\s<>"{}|\\^`\[\]]+$',
                max_length=2048,
                error_message="Invalid URL format"
            ),
            'email': ValidationRule(
                name='email',
                pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                max_length=254,
                error_message="Invalid email format"
            )
        }

    def validate(self, value: str, rule_name: str) -> Dict[str, Any]:
        """
        Validate input against a specific rule.

        Args:
            value: The value to validate
            rule_name: Name of the validation rule to apply

        Returns:
            Dictionary with validation results
        """
        if rule_name not in self.rules:
            return {'valid': False, 'error': f"Unknown validation rule: {rule_name}"}

        rule = self.rules[rule_name]

        try:
            # Check if value is string
            if not isinstance(value, str):
                return {'valid': False, 'error': "Value must be a string"}

            # Length validation
            if rule.min_length is not None and len(value) < rule.min_length:
                return {'valid': False, 'error': f"Value too short (minimum {rule.min_length} characters)"}

            if rule.max_length is not None and len(value) > rule.max_length:
                return {'valid': False, 'error': f"Value too long (maximum {rule.max_length} characters)"}

            # Pattern validation
            if rule.pattern and not re.match(rule.pattern, value):
                return {'valid': False, 'error': rule.error_message}

            # Forbidden characters
            if rule.forbidden_chars and any(char in value for char in rule.forbidden_chars):
                return {'valid': False, 'error': f"Value contains forbidden characters: {rule.forbidden_chars}"}

            # Allowed characters
            if rule.allowed_chars and not all(char in rule.allowed_chars for char in value):
                return {'valid': False, 'error': f"Value contains characters not in allowed set: {rule.allowed_chars}"}

            # Custom validator
            if rule.custom_validator and not rule.custom_validator(value):
                return {'valid': False, 'error': rule.error_message}

            return {'valid': True, 'sanitized_value': self.sanitize(value, rule_name)}

        except Exception as e:
            self.logger.error(f"Validation error for rule {rule_name}: {str(e)}")
            return {'valid': False, 'error': f"Validation error: {str(e)}"}

    def sanitize(self, value: str, rule_name: str) -> str:
        """
        Sanitize input value based on rule.

        Args:
            value: The value to sanitize
            rule_name: Name of the validation rule

        Returns:
            Sanitized value
        """
        if not isinstance(value, str):
            return str(value)

        # Basic sanitization
        sanitized = value.strip()

        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # Rule-specific sanitization
        if rule_name == 'prompt':
            # Remove potentially dangerous HTML/script tags
            sanitized = re.sub(r'<[^>]*>', '', sanitized)
            # Remove control characters except newlines and tabs
            sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

        elif rule_name == 'filename':
            # Replace invalid filename characters
            sanitized = re.sub(r'[<>:"/\\|?*]', '_', sanitized)
            # Remove leading/trailing dots and spaces
            sanitized = sanitized.strip('. ')

        elif rule_name == 'hashtag':
            # Ensure hashtag format
            if not sanitized.startswith('#'):
                sanitized = '#' + sanitized
            # Remove invalid characters
            sanitized = re.sub(r'[^#a-zA-Z0-9_]', '', sanitized)

        return sanitized

    def validate_multiple(self, data: Dict[str, str], rules: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate multiple values against their respective rules.

        Args:
            data: Dictionary of field names to values
            rules: Dictionary of field names to rule names

        Returns:
            Dictionary with validation results for all fields
        """
        results = {'valid': True, 'errors': {}, 'sanitized': {}}

        for field, value in data.items():
            if field in rules:
                result = self.validate(value, rules[field])
                if not result['valid']:
                    results['valid'] = False
                    results['errors'][field] = result['error']
                else:
                    results['sanitized'][field] = result['sanitized_value']

        return results


class RateLimiter:
    """Rate limiting and abuse prevention system."""

    def __init__(self):
        """Initialize the rate limiter."""
        self.logger = get_logger(__name__)
        self._requests: Dict[str, deque] = defaultdict(deque)
        self._blocked: Dict[str, datetime] = {}
        self._configs: Dict[str, RateLimitConfig] = {}
        self._setup_default_limits()

    def _setup_default_limits(self):
        """Set up default rate limits."""
        self._configs = {
            'api_general': RateLimitConfig(max_requests=100, time_window=3600),  # 100/hour
            'api_generation': RateLimitConfig(max_requests=20, time_window=3600, burst_limit=5),  # 20/hour, 5 burst
            'api_publishing': RateLimitConfig(max_requests=10, time_window=3600),  # 10/hour
            'login_attempts': RateLimitConfig(max_requests=5, time_window=900, block_duration=1800),  # 5/15min, block 30min
            'content_moderation': RateLimitConfig(max_requests=1000, time_window=3600),  # 1000/hour
        }

    def is_allowed(self, identifier: str, limit_type: str = 'api_general') -> Dict[str, Any]:
        """
        Check if request is allowed under rate limit.

        Args:
            identifier: Unique identifier (IP, user ID, API key, etc.)
            limit_type: Type of rate limit to apply

        Returns:
            Dictionary with rate limit status
        """
        if limit_type not in self._configs:
            return {'allowed': True, 'error': f"Unknown limit type: {limit_type}"}

        config = self._configs[limit_type]
        now = datetime.now()

        # Check if currently blocked
        if identifier in self._blocked:
            if now < self._blocked[identifier]:
                remaining_time = (self._blocked[identifier] - now).total_seconds()
                return {
                    'allowed': False,
                    'error': 'Rate limit exceeded - temporarily blocked',
                    'retry_after': remaining_time,
                    'blocked_until': self._blocked[identifier].isoformat()
                }
            else:
                # Block expired, remove it
                del self._blocked[identifier]

        # Clean old requests
        cutoff_time = now - timedelta(seconds=config.time_window)
        request_times = self._requests[identifier]

        while request_times and request_times[0] < cutoff_time:
            request_times.popleft()

        # Check rate limit
        current_requests = len(request_times)

        if current_requests >= config.max_requests:
            # Block the identifier
            self._blocked[identifier] = now + timedelta(seconds=config.block_duration)

            self.logger.warning(
                f"Rate limit exceeded for {identifier}",
                extra={'extra_data': {
                    'identifier': identifier,
                    'limit_type': limit_type,
                    'current_requests': current_requests,
                    'max_requests': config.max_requests,
                    'blocked_until': self._blocked[identifier].isoformat()
                }}
            )

            return {
                'allowed': False,
                'error': 'Rate limit exceeded',
                'current_requests': current_requests,
                'max_requests': config.max_requests,
                'retry_after': config.block_duration,
                'blocked_until': self._blocked[identifier].isoformat()
            }

        # Check burst limit if configured
        if config.burst_limit:
            recent_cutoff = now - timedelta(seconds=60)  # Last minute
            recent_requests = sum(1 for req_time in request_times if req_time > recent_cutoff)

            if recent_requests >= config.burst_limit:
                return {
                    'allowed': False,
                    'error': 'Burst limit exceeded',
                    'current_requests': recent_requests,
                    'burst_limit': config.burst_limit,
                    'retry_after': 60
                }

        # Allow request and record it
        request_times.append(now)

        return {
            'allowed': True,
            'current_requests': current_requests + 1,
            'max_requests': config.max_requests,
            'remaining_requests': config.max_requests - current_requests - 1,
            'reset_time': (now + timedelta(seconds=config.time_window)).isoformat()
        }

    def add_custom_limit(self, name: str, config: RateLimitConfig):
        """Add a custom rate limit configuration."""
        self._configs[name] = config
        self.logger.info(f"Added custom rate limit: {name}")

    def reset_limit(self, identifier: str):
        """Reset rate limit for a specific identifier."""
        if identifier in self._requests:
            del self._requests[identifier]
        if identifier in self._blocked:
            del self._blocked[identifier]
        self.logger.info(f"Reset rate limit for: {identifier}")

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        now = datetime.now()
        active_limits = len(self._requests)
        blocked_count = len([b for b in self._blocked.values() if b > now])

        return {
            'active_limits': active_limits,
            'blocked_identifiers': blocked_count,
            'total_identifiers': len(self._requests),
            'limit_types': list(self._configs.keys())
        }


class AuditLogger:
    """Audit logging system for sensitive operations."""

    def __init__(self, log_file: Optional[str] = None):
        """Initialize the audit logger."""
        self.logger = get_logger(__name__)
        self.log_file = log_file or "audit.log"
        self._setup_audit_logger()

    def _setup_audit_logger(self):
        """Set up dedicated audit logger."""
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.setLevel(logging.INFO)

        # Create file handler for audit logs
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)

    def log_action(
        self,
        action: str,
        resource: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        risk_level: str = "low"
    ):
        """
        Log an audit event.

        Args:
            action: Action performed (e.g., 'login', 'generate_content', 'publish_post')
            resource: Resource affected (e.g., 'user_account', 'instagram_post')
            user_id: User identifier
            details: Additional details about the action
            ip_address: IP address of the request
            user_agent: User agent string
            success: Whether the action was successful
            risk_level: Risk level (low, medium, high, critical)
        """
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            resource=resource,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            risk_level=risk_level
        )

        # Log to audit file
        audit_data = {
            'timestamp': entry.timestamp.isoformat(),
            'user_id': entry.user_id,
            'action': entry.action,
            'resource': entry.resource,
            'details': entry.details,
            'ip_address': entry.ip_address,
            'user_agent': entry.user_agent,
            'success': entry.success,
            'risk_level': entry.risk_level
        }

        self.audit_logger.info(json.dumps(audit_data))

        # Log to main logger based on risk level
        log_message = f"AUDIT: {action} on {resource} by {user_id or 'anonymous'}"

        if risk_level == "critical":
            self.logger.critical(log_message, extra={'extra_data': audit_data})
        elif risk_level == "high":
            self.logger.error(log_message, extra={'extra_data': audit_data})
        elif risk_level == "medium":
            self.logger.warning(log_message, extra={'extra_data': audit_data})
        else:
            self.logger.info(log_message, extra={'extra_data': audit_data})

    def log_security_event(
        self,
        event_type: str,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a security-related event."""
        self.log_action(
            action=f"security_event_{event_type}",
            resource="security",
            user_id=user_id,
            details={
                'event_type': event_type,
                'description': description,
                **(details or {})
            },
            ip_address=ip_address,
            success=False,
            risk_level="high"
        )

    def log_api_access(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        response_code: int = 200,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log API access."""
        self.log_action(
            action=f"api_access_{method.lower()}",
            resource=f"api_endpoint_{endpoint}",
            user_id=user_id,
            details={
                'endpoint': endpoint,
                'method': method,
                'response_code': response_code,
                **(details or {})
            },
            ip_address=ip_address,
            success=200 <= response_code < 400,
            risk_level="low" if 200 <= response_code < 400 else "medium"
        )


class EncryptionManager:
    """Encryption utilities for sensitive data."""

    def __init__(self, key: Optional[bytes] = None):
        """Initialize encryption manager."""
        self.logger = get_logger(__name__)
        if key:
            self.key = key
        else:
            self.key = self._generate_key()
        self.fernet = Fernet(self.key)

    def _generate_key(self) -> bytes:
        """Generate a new encryption key."""
        return Fernet.generate_key()

    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive encryption key from password."""
        if salt is None:
            salt = secrets.token_bytes(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            raise

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt dictionary data."""
        json_data = json.dumps(data)
        return self.encrypt(json_data)

    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt dictionary data."""
        json_data = self.decrypt(encrypted_data)
        return json.loads(json_data)

    def hash_data(self, data: str, salt: Optional[str] = None) -> Dict[str, str]:
        """Create secure hash of data."""
        if salt is None:
            salt = secrets.token_hex(16)

        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return {
            'hash': hash_obj.hex(),
            'salt': salt
        }

    def verify_hash(self, data: str, hash_value: str, salt: str) -> bool:
        """Verify data against hash."""
        computed_hash = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return hmac.compare_digest(computed_hash.hex(), hash_value)


# Decorators for security
def require_validation(rules: Dict[str, str]):
    """Decorator to validate function arguments."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            validator = InputValidator()

            # Get function signature to map args to parameter names
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate specified arguments
            for param_name, rule_name in rules.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if isinstance(value, str):
                        result = validator.validate(value, rule_name)
                        if not result['valid']:
                            raise ValueError(f"Validation failed for {param_name}: {result['error']}")
                        # Replace with sanitized value
                        bound_args.arguments[param_name] = result['sanitized_value']

            return func(*bound_args.args, **bound_args.kwargs)
        return wrapper
    return decorator


def rate_limit(limit_type: str = 'api_general', identifier_func: Optional[Callable] = None):
    """Decorator to apply rate limiting."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = RateLimiter()

            # Determine identifier
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                # Default to first argument or 'default'
                identifier = str(args[0]) if args else 'default'

            # Check rate limit
            result = limiter.is_allowed(identifier, limit_type)
            if not result['allowed']:
                raise Exception(f"Rate limit exceeded: {result['error']}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def audit_log(action: str, resource: str, risk_level: str = "low"):
    """Decorator to automatically log function calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auditor = AuditLogger()

            # Extract user_id if available
            user_id = kwargs.get('user_id') or (args[0] if args and hasattr(args[0], 'user_id') else None)

            try:
                result = func(*args, **kwargs)
                auditor.log_action(
                    action=action,
                    resource=resource,
                    user_id=str(user_id) if user_id else None,
                    details={'function': func.__name__, 'args_count': len(args)},
                    success=True,
                    risk_level=risk_level
                )
                return result
            except Exception as e:
                auditor.log_action(
                    action=action,
                    resource=resource,
                    user_id=str(user_id) if user_id else None,
                    details={'function': func.__name__, 'error': str(e)},
                    success=False,
                    risk_level="high"
                )
                raise
        return wrapper
    return decorator


# Global instances
_input_validator = None
_rate_limiter = None
_audit_logger = None
_encryption_manager = None


def get_input_validator() -> InputValidator:
    """Get global input validator instance."""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
