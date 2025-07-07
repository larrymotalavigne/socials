"""
Unit tests for security utilities.

This module tests input validation, rate limiting, audit logging,
encryption, and other security features.
"""

import pytest
import time
import json
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, Any

from utils.security import (
    InputValidator,
    RateLimiter,
    AuditLogger,
    EncryptionManager,
    ValidationRule,
    RateLimitConfig,
    AuditLogEntry,
    require_validation,
    rate_limit,
    audit_log,
    get_input_validator,
    get_rate_limiter,
    get_audit_logger,
    get_encryption_manager
)


class TestValidationRule:
    """Test cases for ValidationRule dataclass."""

    def test_validation_rule_creation(self):
        """Test creating a ValidationRule instance."""
        rule = ValidationRule(
            name="test_rule",
            pattern=r"^[a-z]+$",
            min_length=1,
            max_length=10,
            error_message="Test validation failed"
        )
        
        assert rule.name == "test_rule"
        assert rule.pattern == r"^[a-z]+$"
        assert rule.min_length == 1
        assert rule.max_length == 10
        assert rule.error_message == "Test validation failed"

    def test_validation_rule_defaults(self):
        """Test ValidationRule with default values."""
        rule = ValidationRule(name="simple_rule")
        
        assert rule.name == "simple_rule"
        assert rule.pattern is None
        assert rule.min_length is None
        assert rule.max_length is None
        assert rule.error_message == "Validation failed"


class TestInputValidator:
    """Test cases for InputValidator class."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.validator = InputValidator()

    def test_validator_initialization(self):
        """Test InputValidator initialization."""
        assert self.validator.rules is not None
        assert 'prompt' in self.validator.rules
        assert 'api_key' in self.validator.rules
        assert 'user_id' in self.validator.rules

    def test_validate_prompt_valid(self):
        """Test prompt validation with valid input."""
        result = self.validator.validate("This is a valid prompt", "prompt")
        
        assert result['valid'] is True
        assert 'sanitized_value' in result

    def test_validate_prompt_too_short(self):
        """Test prompt validation with too short input."""
        result = self.validator.validate("", "prompt")
        
        assert result['valid'] is False
        assert "too short" in result['error']

    def test_validate_prompt_too_long(self):
        """Test prompt validation with too long input."""
        long_prompt = "a" * 2001
        result = self.validator.validate(long_prompt, "prompt")
        
        assert result['valid'] is False
        assert "too long" in result['error']

    def test_validate_prompt_forbidden_chars(self):
        """Test prompt validation with forbidden characters."""
        result = self.validator.validate("This has <script> tags", "prompt")
        
        assert result['valid'] is False
        assert "forbidden characters" in result['error']

    def test_validate_api_key_valid(self):
        """Test API key validation with valid input."""
        result = self.validator.validate("sk-1234567890abcdef1234567890abcdef", "api_key")
        
        assert result['valid'] is True

    def test_validate_api_key_invalid_pattern(self):
        """Test API key validation with invalid pattern."""
        result = self.validator.validate("invalid@key#format", "api_key")
        
        assert result['valid'] is False
        assert "Invalid API key format" in result['error']

    def test_validate_user_id_valid(self):
        """Test user ID validation with valid input."""
        result = self.validator.validate("user_123", "user_id")
        
        assert result['valid'] is True

    def test_validate_user_id_invalid(self):
        """Test user ID validation with invalid characters."""
        result = self.validator.validate("user@123", "user_id")
        
        assert result['valid'] is False

    def test_validate_hashtag_valid(self):
        """Test hashtag validation with valid input."""
        result = self.validator.validate("#nature", "hashtag")
        
        assert result['valid'] is True

    def test_validate_hashtag_invalid(self):
        """Test hashtag validation with invalid input."""
        result = self.validator.validate("#nature-photography", "hashtag")
        
        assert result['valid'] is False

    def test_validate_url_valid(self):
        """Test URL validation with valid input."""
        result = self.validator.validate("https://example.com/path", "url")
        
        assert result['valid'] is True

    def test_validate_url_invalid(self):
        """Test URL validation with invalid input."""
        result = self.validator.validate("not-a-url", "url")
        
        assert result['valid'] is False

    def test_validate_email_valid(self):
        """Test email validation with valid input."""
        result = self.validator.validate("user@example.com", "email")
        
        assert result['valid'] is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid input."""
        result = self.validator.validate("invalid-email", "email")
        
        assert result['valid'] is False

    def test_validate_unknown_rule(self):
        """Test validation with unknown rule."""
        result = self.validator.validate("test", "unknown_rule")
        
        assert result['valid'] is False
        assert "Unknown validation rule" in result['error']

    def test_validate_non_string_input(self):
        """Test validation with non-string input."""
        result = self.validator.validate(123, "prompt")
        
        assert result['valid'] is False
        assert "must be a string" in result['error']

    def test_sanitize_prompt(self):
        """Test prompt sanitization."""
        dirty_input = "  <script>alert('xss')</script>  Test prompt  "
        sanitized = self.validator.sanitize(dirty_input, "prompt")
        
        assert "<script>" not in sanitized
        assert "Test prompt" in sanitized
        assert not sanitized.startswith(" ")
        assert not sanitized.endswith(" ")

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        dirty_filename = "test<file>name.txt"
        sanitized = self.validator.sanitize(dirty_filename, "filename")
        
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert "test_file_name.txt" == sanitized

    def test_sanitize_hashtag(self):
        """Test hashtag sanitization."""
        dirty_hashtag = "nature-photography"
        sanitized = self.validator.sanitize(dirty_hashtag, "hashtag")
        
        assert sanitized.startswith("#")
        assert "-" not in sanitized

    def test_validate_multiple_valid(self):
        """Test multiple field validation with valid data."""
        data = {
            'prompt': 'Valid prompt',
            'user_id': 'user123'
        }
        rules = {
            'prompt': 'prompt',
            'user_id': 'user_id'
        }
        
        result = self.validator.validate_multiple(data, rules)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert 'prompt' in result['sanitized']
        assert 'user_id' in result['sanitized']

    def test_validate_multiple_invalid(self):
        """Test multiple field validation with invalid data."""
        data = {
            'prompt': '',  # Too short
            'user_id': 'user@123'  # Invalid characters
        }
        rules = {
            'prompt': 'prompt',
            'user_id': 'user_id'
        }
        
        result = self.validator.validate_multiple(data, rules)
        
        assert result['valid'] is False
        assert 'prompt' in result['errors']
        assert 'user_id' in result['errors']


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.limiter = RateLimiter()

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        assert self.limiter._configs is not None
        assert 'api_general' in self.limiter._configs
        assert 'api_generation' in self.limiter._configs

    def test_is_allowed_first_request(self):
        """Test rate limiting for first request."""
        result = self.limiter.is_allowed("test_user", "api_general")
        
        assert result['allowed'] is True
        assert result['current_requests'] == 1
        assert 'remaining_requests' in result

    def test_is_allowed_within_limit(self):
        """Test rate limiting within allowed limit."""
        identifier = "test_user_2"
        
        # Make several requests within limit
        for i in range(5):
            result = self.limiter.is_allowed(identifier, "api_general")
            assert result['allowed'] is True

    def test_is_allowed_exceed_limit(self):
        """Test rate limiting when exceeding limit."""
        # Create a custom limit for testing
        test_config = RateLimitConfig(max_requests=2, time_window=3600)
        self.limiter.add_custom_limit("test_limit", test_config)
        
        identifier = "test_user_3"
        
        # First two requests should be allowed
        result1 = self.limiter.is_allowed(identifier, "test_limit")
        assert result1['allowed'] is True
        
        result2 = self.limiter.is_allowed(identifier, "test_limit")
        assert result2['allowed'] is True
        
        # Third request should be blocked
        result3 = self.limiter.is_allowed(identifier, "test_limit")
        assert result3['allowed'] is False
        assert "Rate limit exceeded" in result3['error']

    def test_is_allowed_burst_limit(self):
        """Test burst limit functionality."""
        # Create a config with burst limit
        test_config = RateLimitConfig(max_requests=100, time_window=3600, burst_limit=3)
        self.limiter.add_custom_limit("burst_test", test_config)
        
        identifier = "burst_user"
        
        # First three requests should be allowed
        for i in range(3):
            result = self.limiter.is_allowed(identifier, "burst_test")
            assert result['allowed'] is True
        
        # Fourth request should hit burst limit
        result = self.limiter.is_allowed(identifier, "burst_test")
        assert result['allowed'] is False
        assert "Burst limit exceeded" in result['error']

    def test_is_allowed_unknown_limit_type(self):
        """Test rate limiting with unknown limit type."""
        result = self.limiter.is_allowed("test_user", "unknown_limit")
        
        assert result['allowed'] is True
        assert "Unknown limit type" in result['error']

    def test_reset_limit(self):
        """Test resetting rate limit for identifier."""
        identifier = "reset_test_user"
        
        # Make a request
        self.limiter.is_allowed(identifier, "api_general")
        
        # Reset the limit
        self.limiter.reset_limit(identifier)
        
        # Should be able to make requests again
        result = self.limiter.is_allowed(identifier, "api_general")
        assert result['allowed'] is True

    def test_get_stats(self):
        """Test getting rate limiter statistics."""
        # Make some requests
        self.limiter.is_allowed("user1", "api_general")
        self.limiter.is_allowed("user2", "api_general")
        
        stats = self.limiter.get_stats()
        
        assert 'active_limits' in stats
        assert 'blocked_identifiers' in stats
        assert 'total_identifiers' in stats
        assert 'limit_types' in stats


class TestAuditLogger:
    """Test cases for AuditLogger class."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.audit_logger = AuditLogger(self.temp_file.name)

    def teardown_method(self):
        """Clean up after each test."""
        try:
            os.unlink(self.temp_file.name)
        except FileNotFoundError:
            pass

    def test_audit_logger_initialization(self):
        """Test AuditLogger initialization."""
        assert self.audit_logger.log_file == self.temp_file.name
        assert self.audit_logger.audit_logger is not None

    def test_log_action_basic(self):
        """Test basic action logging."""
        self.audit_logger.log_action(
            action="test_action",
            resource="test_resource",
            user_id="test_user",
            success=True
        )
        
        # Check if log was written
        with open(self.temp_file.name, 'r') as f:
            log_content = f.read()
            assert "test_action" in log_content
            assert "test_resource" in log_content
            assert "test_user" in log_content

    def test_log_action_with_details(self):
        """Test action logging with details."""
        details = {"key": "value", "number": 42}
        
        self.audit_logger.log_action(
            action="detailed_action",
            resource="detailed_resource",
            user_id="detail_user",
            details=details,
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0",
            risk_level="medium"
        )
        
        with open(self.temp_file.name, 'r') as f:
            log_content = f.read()
            log_data = json.loads(log_content.split(' - AUDIT - ')[1])
            
            assert log_data['action'] == "detailed_action"
            assert log_data['details']['key'] == "value"
            assert log_data['ip_address'] == "192.168.1.1"
            assert log_data['risk_level'] == "medium"

    def test_log_security_event(self):
        """Test security event logging."""
        self.audit_logger.log_security_event(
            event_type="suspicious_activity",
            description="Multiple failed login attempts",
            user_id="suspect_user",
            ip_address="192.168.1.100"
        )
        
        with open(self.temp_file.name, 'r') as f:
            log_content = f.read()
            assert "security_event_suspicious_activity" in log_content
            assert "Multiple failed login attempts" in log_content

    def test_log_api_access(self):
        """Test API access logging."""
        self.audit_logger.log_api_access(
            endpoint="/api/generate",
            method="POST",
            user_id="api_user",
            ip_address="192.168.1.50",
            response_code=200,
            details={"request_size": 1024}
        )
        
        with open(self.temp_file.name, 'r') as f:
            log_content = f.read()
            log_data = json.loads(log_content.split(' - AUDIT - ')[1])
            
            assert log_data['action'] == "api_access_post"
            assert log_data['details']['endpoint'] == "/api/generate"
            assert log_data['details']['response_code'] == 200


class TestEncryptionManager:
    """Test cases for EncryptionManager class."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.encryption_manager = EncryptionManager()

    def test_encryption_manager_initialization(self):
        """Test EncryptionManager initialization."""
        assert self.encryption_manager.key is not None
        assert self.encryption_manager.fernet is not None

    def test_encrypt_decrypt_string(self):
        """Test string encryption and decryption."""
        original_data = "This is sensitive data"
        
        encrypted = self.encryption_manager.encrypt(original_data)
        decrypted = self.encryption_manager.decrypt(encrypted)
        
        assert encrypted != original_data
        assert decrypted == original_data

    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        original_data = {"api_key": "secret123", "user_id": "user456"}
        
        encrypted = self.encryption_manager.encrypt_dict(original_data)
        decrypted = self.encryption_manager.decrypt_dict(encrypted)
        
        assert encrypted != str(original_data)
        assert decrypted == original_data

    def test_hash_data(self):
        """Test data hashing."""
        data = "password123"
        
        hash_result = self.encryption_manager.hash_data(data)
        
        assert 'hash' in hash_result
        assert 'salt' in hash_result
        assert hash_result['hash'] != data

    def test_verify_hash_correct(self):
        """Test hash verification with correct data."""
        data = "password123"
        hash_result = self.encryption_manager.hash_data(data)
        
        is_valid = self.encryption_manager.verify_hash(
            data, hash_result['hash'], hash_result['salt']
        )
        
        assert is_valid is True

    def test_verify_hash_incorrect(self):
        """Test hash verification with incorrect data."""
        data = "password123"
        wrong_data = "wrongpassword"
        hash_result = self.encryption_manager.hash_data(data)
        
        is_valid = self.encryption_manager.verify_hash(
            wrong_data, hash_result['hash'], hash_result['salt']
        )
        
        assert is_valid is False

    def test_derive_key_from_password(self):
        """Test key derivation from password."""
        password = "mypassword"
        salt = b"testsalt12345678"
        
        key = self.encryption_manager.derive_key_from_password(password, salt)
        
        assert key is not None
        assert len(key) > 0

    def test_encryption_with_custom_key(self):
        """Test encryption with custom key."""
        from cryptography.fernet import Fernet
        custom_key = Fernet.generate_key()
        
        custom_manager = EncryptionManager(custom_key)
        
        data = "test data"
        encrypted = custom_manager.encrypt(data)
        decrypted = custom_manager.decrypt(encrypted)
        
        assert decrypted == data


class TestSecurityDecorators:
    """Test cases for security decorators."""

    def test_require_validation_decorator_valid(self):
        """Test require_validation decorator with valid input."""
        @require_validation({'prompt': 'prompt'})
        def test_function(prompt):
            return f"Processed: {prompt}"
        
        result = test_function("Valid prompt")
        assert "Processed:" in result

    def test_require_validation_decorator_invalid(self):
        """Test require_validation decorator with invalid input."""
        @require_validation({'prompt': 'prompt'})
        def test_function(prompt):
            return f"Processed: {prompt}"
        
        with pytest.raises(ValueError, match="Validation failed"):
            test_function("")  # Empty prompt should fail

    def test_rate_limit_decorator_allowed(self):
        """Test rate_limit decorator when request is allowed."""
        @rate_limit('api_general')
        def test_function(user_id):
            return f"Success for {user_id}"
        
        result = test_function("test_user")
        assert "Success for test_user" == result

    def test_audit_log_decorator_success(self):
        """Test audit_log decorator for successful operation."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.close()
            
            try:
                @audit_log('test_action', 'test_resource')
                def test_function(data):
                    return f"Processed: {data}"
                
                result = test_function("test_data")
                assert "Processed: test_data" == result
                
            finally:
                try:
                    os.unlink(temp_file.name)
                except FileNotFoundError:
                    pass

    def test_audit_log_decorator_failure(self):
        """Test audit_log decorator for failed operation."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.close()
            
            try:
                @audit_log('test_action', 'test_resource')
                def test_function():
                    raise ValueError("Test error")
                
                with pytest.raises(ValueError, match="Test error"):
                    test_function()
                    
            finally:
                try:
                    os.unlink(temp_file.name)
                except FileNotFoundError:
                    pass


class TestSecurityUtilities:
    """Test cases for security utility functions."""

    def test_get_input_validator_singleton(self):
        """Test that get_input_validator returns the same instance."""
        validator1 = get_input_validator()
        validator2 = get_input_validator()
        
        assert validator1 is validator2
        assert isinstance(validator1, InputValidator)

    def test_get_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns the same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        assert limiter1 is limiter2
        assert isinstance(limiter1, RateLimiter)

    def test_get_audit_logger_singleton(self):
        """Test that get_audit_logger returns the same instance."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        
        assert logger1 is logger2
        assert isinstance(logger1, AuditLogger)

    def test_get_encryption_manager_singleton(self):
        """Test that get_encryption_manager returns the same instance."""
        manager1 = get_encryption_manager()
        manager2 = get_encryption_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, EncryptionManager)


class TestSecurityIntegration:
    """Integration tests for security components."""

    def test_full_security_workflow(self):
        """Test complete security workflow."""
        # Initialize components
        validator = InputValidator()
        limiter = RateLimiter()
        
        # Validate input
        validation_result = validator.validate("test_prompt", "prompt")
        assert validation_result['valid'] is True
        
        # Check rate limit
        rate_result = limiter.is_allowed("integration_user", "api_general")
        assert rate_result['allowed'] is True
        
        # Process would happen here
        
        # Log the action
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.close()
            
            try:
                auditor = AuditLogger(temp_file.name)
                auditor.log_action(
                    action="integration_test",
                    resource="test_resource",
                    user_id="integration_user",
                    success=True
                )
                
                # Verify log was written
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                    assert "integration_test" in log_content
                    
            finally:
                try:
                    os.unlink(temp_file.name)
                except FileNotFoundError:
                    pass

    def test_security_with_encryption(self):
        """Test security workflow with encryption."""
        validator = InputValidator()
        encryption_manager = EncryptionManager()
        
        # Validate and sanitize sensitive data
        api_key = "sk-1234567890abcdef1234567890abcdef"
        validation_result = validator.validate(api_key, "api_key")
        assert validation_result['valid'] is True
        
        # Encrypt the validated data
        encrypted_key = encryption_manager.encrypt(validation_result['sanitized_value'])
        
        # Decrypt and verify
        decrypted_key = encryption_manager.decrypt(encrypted_key)
        assert decrypted_key == validation_result['sanitized_value']

    def test_rate_limiting_with_validation(self):
        """Test rate limiting combined with input validation."""
        validator = InputValidator()
        limiter = RateLimiter()
        
        # Create custom limit for testing
        test_config = RateLimitConfig(max_requests=2, time_window=3600)
        limiter.add_custom_limit("validation_test", test_config)
        
        user_id = "validation_user"
        
        # First request - should pass validation and rate limit
        prompt1 = "First valid prompt"
        validation1 = validator.validate(prompt1, "prompt")
        rate1 = limiter.is_allowed(user_id, "validation_test")
        
        assert validation1['valid'] is True
        assert rate1['allowed'] is True
        
        # Second request - should pass validation and rate limit
        prompt2 = "Second valid prompt"
        validation2 = validator.validate(prompt2, "prompt")
        rate2 = limiter.is_allowed(user_id, "validation_test")
        
        assert validation2['valid'] is True
        assert rate2['allowed'] is True
        
        # Third request - should pass validation but fail rate limit
        prompt3 = "Third valid prompt"
        validation3 = validator.validate(prompt3, "prompt")
        rate3 = limiter.is_allowed(user_id, "validation_test")
        
        assert validation3['valid'] is True
        assert rate3['allowed'] is False


@pytest.fixture
def temp_audit_file():
    """Fixture providing temporary audit log file."""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    yield temp_file.name
    try:
        os.unlink(temp_file.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_validation_data():
    """Fixture providing sample data for validation testing."""
    return {
        'valid_prompt': 'This is a valid prompt for testing',
        'invalid_prompt': '',
        'valid_api_key': 'sk-1234567890abcdef1234567890abcdef',
        'invalid_api_key': 'invalid@key',
        'valid_user_id': 'user_123',
        'invalid_user_id': 'user@123'
    }


class TestSecurityFixtures:
    """Test cases using fixtures for consistent test data."""

    def test_validation_with_fixtures(self, sample_validation_data):
        """Test validation using fixture data."""
        validator = InputValidator()
        
        # Test valid data
        result = validator.validate(sample_validation_data['valid_prompt'], 'prompt')
        assert result['valid'] is True
        
        result = validator.validate(sample_validation_data['valid_api_key'], 'api_key')
        assert result['valid'] is True
        
        # Test invalid data
        result = validator.validate(sample_validation_data['invalid_prompt'], 'prompt')
        assert result['valid'] is False
        
        result = validator.validate(sample_validation_data['invalid_api_key'], 'api_key')
        assert result['valid'] is False

    def test_audit_logging_with_fixture(self, temp_audit_file):
        """Test audit logging using fixture file."""
        auditor = AuditLogger(temp_audit_file)
        
        auditor.log_action(
            action="fixture_test",
            resource="fixture_resource",
            user_id="fixture_user"
        )
        
        with open(temp_audit_file, 'r') as f:
            log_content = f.read()
            assert "fixture_test" in log_content
            assert "fixture_resource" in log_content