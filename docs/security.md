# Security Guide

## 📋 Overview

AI Socials implements comprehensive security measures to protect your data, API keys, and content. This guide covers all security features, best practices, and configuration options.

## 🛡️ Security Architecture

### Security Layers

```
AI Socials Security Architecture
├── 🔐 Input Security
│   ├── Input Validation & Sanitization
│   ├── Content Moderation
│   └── Prompt Safety Checks
├── 🔑 Authentication & Authorization
│   ├── API Key Management
│   ├── Token Validation
│   └── Access Control
├── 🚦 Rate Limiting & Abuse Prevention
│   ├── Request Rate Limiting
│   ├── Burst Protection
│   └── IP-based Blocking
├── 📊 Audit & Monitoring
│   ├── Security Event Logging
│   ├── Audit Trails
│   └── Anomaly Detection
└── 🔒 Data Protection
    ├── Encryption at Rest
    ├── Secure Configuration
    └── Sensitive Data Handling
```

## 🔐 Input Security

### Input Validation

AI Socials validates all user inputs to prevent injection attacks and ensure data integrity.

#### Validation Rules

```python
from utils.security import get_input_validator

validator = get_input_validator()

# Validate prompt input
result = validator.validate("user prompt here", "prompt")
if result['valid']:
    safe_prompt = result['sanitized_value']
else:
    print(f"Validation failed: {result['error']}")
```

**Built-in Validation Rules:**

| Rule Type | Purpose | Restrictions |
|-----------|---------|--------------|
| `prompt` | Content prompts | 1-2000 chars, no special chars |
| `api_key` | API keys | 20-200 chars, alphanumeric |
| `user_id` | User identifiers | Alphanumeric, underscore, hyphen |
| `filename` | File names | Valid filename chars only |
| `hashtag` | Social hashtags | Must start with #, alphanumeric |
| `url` | URLs | Valid HTTP/HTTPS format |
| `email` | Email addresses | Valid email format |

#### Custom Validation

```python
from utils.security import ValidationRule

# Create custom validation rule
custom_rule = ValidationRule(
    name="custom_field",
    min_length=5,
    max_length=100,
    pattern=r'^[a-zA-Z0-9_]+$',
    forbidden_chars='<>{}[]',
    error_message="Invalid custom field format"
)

# Add to validator
validator.rules['custom_field'] = custom_rule

# Use custom validation
result = validator.validate("user_input", "custom_field")
```

### Input Sanitization

All inputs are automatically sanitized to remove potentially dangerous content:

```python
# Automatic sanitization
sanitized = validator.sanitize("user<script>alert('xss')</script>input", "prompt")
# Result: "userinput" (script tags removed)

# Manual sanitization
from utils.security import get_input_validator
validator = get_input_validator()

# Remove HTML tags
clean_text = validator.sanitize("<b>Bold text</b>", "prompt")
# Result: "Bold text"

# Normalize whitespace
normalized = validator.sanitize("text   with    spaces", "prompt")
# Result: "text with spaces"
```

### Content Moderation

AI Socials includes content moderation to prevent inappropriate content generation:

```python
from generator import get_caption_generator

caption_gen = get_caption_generator()

# Content is automatically moderated
result = caption_gen.generate_caption(
    prompt="family-friendly content",
    style="engaging"
)

# Inappropriate prompts are rejected
try:
    result = caption_gen.generate_caption(
        prompt="inappropriate content",
        style="engaging"
    )
except ContentGenerationError as e:
    print(f"Content moderation blocked: {e.message}")
```

## 🔑 Authentication & Authorization

### API Key Management

#### Secure Storage

```python
# Store API keys in environment variables
import os
from dotenv import load_dotenv

load_dotenv()

# Never hardcode API keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')

# Validate key format
if not OPENAI_API_KEY or not OPENAI_API_KEY.startswith('sk-'):
    raise ConfigurationError("Invalid OpenAI API key format")
```

#### Key Rotation

```bash
# 1. Generate new API key from provider
# 2. Update environment variable
export OPENAI_API_KEY=new_api_key_here

# 3. Restart application
python main.py --validate-only

# 4. Revoke old key from provider dashboard
```

#### Key Validation

```python
from config import get_config

config = get_config()

# API keys are validated on startup
if not config.openai.api_key:
    raise ConfigurationError("OpenAI API key required")

# Test key validity
from main import AISocials
app = AISocials()
if not app.validate_setup():
    print("❌ API key validation failed")
```

### Access Control

#### Environment-based Access

```python
import os
from config import get_config

# Production environment restrictions
if os.getenv('ENVIRONMENT') == 'production':
    # Stricter validation in production
    config = get_config()
    
    # Require all security features
    if not config.security.audit_logging:
        raise ConfigurationError("Audit logging required in production")
    
    if not config.security.rate_limiting:
        raise ConfigurationError("Rate limiting required in production")
```

#### Service-specific Authorization

```python
# Instagram publishing requires specific permissions
from publisher.instagram_publisher import get_instagram_publisher

try:
    publisher = get_instagram_publisher()
    
    # Test authorization
    result = publisher.test_connection()
    if not result['connected']:
        raise AuthenticationError("Instagram authorization failed")
        
except AuthenticationError as e:
    print(f"Authorization error: {e.message}")
```

## 🚦 Rate Limiting & Abuse Prevention

### Rate Limiting Configuration

```python
from utils.security import get_rate_limiter, RateLimitConfig

# Get rate limiter
limiter = get_rate_limiter()

# Check if request is allowed
result = limiter.is_allowed("user_123", "api_generation")
if result['allowed']:
    # Process request
    pass
else:
    print(f"Rate limit exceeded: {result['error']}")
    print(f"Retry after: {result['retry_after']} seconds")
```

#### Default Rate Limits

| Limit Type | Max Requests | Time Window | Burst Limit |
|------------|--------------|-------------|-------------|
| `api_general` | 100 | 1 hour | - |
| `api_generation` | 20 | 1 hour | 5 |
| `api_publishing` | 10 | 1 hour | - |
| `login_attempts` | 5 | 15 minutes | - |
| `content_moderation` | 1000 | 1 hour | - |

#### Custom Rate Limits

```python
# Add custom rate limit
custom_config = RateLimitConfig(
    max_requests=50,
    time_window=3600,  # 1 hour
    burst_limit=10,
    block_duration=1800  # 30 minutes
)

limiter.add_custom_limit("custom_api", custom_config)

# Use custom limit
result = limiter.is_allowed("user_123", "custom_api")
```

### Abuse Prevention

#### Automatic Blocking

```python
# Users are automatically blocked after exceeding limits
result = limiter.is_allowed("abusive_user", "api_generation")

if not result['allowed']:
    print(f"User blocked until: {result.get('blocked_until')}")
    print(f"Reason: {result['error']}")
```

#### Manual Blocking

```python
# Manually block a user
limiter._blocked["suspicious_user"] = datetime.now() + timedelta(hours=24)

# Reset limits for a user
limiter.reset_limit("user_123")
```

### Rate Limiting Decorators

```python
from utils.security import rate_limit

@rate_limit(limit_type="api_generation")
def generate_content_with_limit(prompt):
    """Generate content with automatic rate limiting."""
    app = AISocials()
    return app.generate_content(prompt=prompt)

# Usage
try:
    result = generate_content_with_limit("test prompt")
except Exception as e:
    if "Rate limit exceeded" in str(e):
        print("Please wait before making another request")
```

## 📊 Audit & Monitoring

### Audit Logging

All security-relevant events are logged for audit purposes:

```python
from utils.security import get_audit_logger

auditor = get_audit_logger()

# Log security events
auditor.log_action(
    action="content_generation",
    resource="ai_content",
    user_id="user_123",
    details={"prompt": "sunset image"},
    success=True,
    risk_level="low"
)

# Log high-risk events
auditor.log_security_event(
    event_type="suspicious_activity",
    description="Multiple failed login attempts",
    user_id="user_456",
    ip_address="192.168.1.100",
    details={"attempts": 5}
)
```

#### Audit Log Format

```json
{
    "timestamp": "2024-01-01T12:00:00Z",
    "user_id": "user_123",
    "action": "content_generation",
    "resource": "ai_content",
    "details": {
        "prompt": "sunset image",
        "model": "dall-e-3"
    },
    "ip_address": "192.168.1.100",
    "user_agent": "AI-Socials/1.0",
    "success": true,
    "risk_level": "low"
}
```

### Security Monitoring

#### Real-time Monitoring

```python
from utils.security import get_rate_limiter, get_audit_logger

def security_dashboard():
    """Get security monitoring dashboard data."""
    limiter = get_rate_limiter()
    
    # Rate limiting stats
    rate_stats = limiter.get_stats()
    
    # Error statistics
    from utils.exceptions import get_error_stats
    error_stats = get_error_stats()
    
    return {
        'active_rate_limits': rate_stats['active_limits'],
        'blocked_users': rate_stats['blocked_identifiers'],
        'security_errors': error_stats.get('authentication:AuthenticationError', 0),
        'validation_errors': error_stats.get('validation:ValidationError', 0)
    }

# Monitor security status
dashboard = security_dashboard()
print(f"🚨 Security Dashboard:")
print(f"Active rate limits: {dashboard['active_rate_limits']}")
print(f"Blocked users: {dashboard['blocked_users']}")
```

#### Anomaly Detection

```python
def detect_anomalies():
    """Detect security anomalies."""
    anomalies = []
    
    # Check for unusual error rates
    error_stats = get_error_stats()
    total_errors = sum(error_stats.values())
    
    if total_errors > 100:  # Threshold
        anomalies.append({
            'type': 'high_error_rate',
            'severity': 'medium',
            'details': f'Total errors: {total_errors}'
        })
    
    # Check for blocked users
    limiter = get_rate_limiter()
    stats = limiter.get_stats()
    
    if stats['blocked_identifiers'] > 10:  # Threshold
        anomalies.append({
            'type': 'high_blocked_users',
            'severity': 'high',
            'details': f'Blocked users: {stats["blocked_identifiers"]}'
        })
    
    return anomalies

# Check for anomalies
anomalies = detect_anomalies()
for anomaly in anomalies:
    print(f"🚨 {anomaly['severity'].upper()}: {anomaly['type']}")
```

## 🔒 Data Protection

### Encryption

#### Sensitive Data Encryption

```python
from utils.security import get_encryption_manager

# Get encryption manager
encryption = get_encryption_manager()

# Encrypt sensitive data
sensitive_data = "user_api_key_here"
encrypted = encryption.encrypt(sensitive_data)

# Store encrypted data
with open('encrypted_data.txt', 'w') as f:
    f.write(encrypted)

# Decrypt when needed
decrypted = encryption.decrypt(encrypted)
```

#### Configuration Encryption

```python
# Encrypt configuration data
config_data = {
    'api_keys': {
        'openai': 'sk-...',
        'instagram': 'token...'
    },
    'settings': {
        'debug': False
    }
}

encrypted_config = encryption.encrypt_dict(config_data)

# Save encrypted configuration
with open('config.encrypted', 'w') as f:
    f.write(encrypted_config)

# Load and decrypt
with open('config.encrypted', 'r') as f:
    encrypted_data = f.read()

decrypted_config = encryption.decrypt_dict(encrypted_data)
```

### Secure Configuration

#### Environment Variables

```bash
# Use secure environment variables
export OPENAI_API_KEY="sk-your-secure-key"
export INSTAGRAM_ACCESS_TOKEN="your-secure-token"

# Set restrictive permissions on .env file
chmod 600 .env

# Never commit .env to version control
echo ".env" >> .gitignore
```

#### Configuration Validation

```python
from config import config_manager

# Validate configuration security
validation = config_manager.validate_config()

if not validation['valid']:
    print("❌ Configuration validation failed:")
    for error in validation['errors']:
        print(f"  - {error}")

# Check for security requirements
if not validation.get('secure_keys'):
    print("⚠️  Warning: Using placeholder API keys")

if not validation.get('encryption_enabled'):
    print("⚠️  Warning: Encryption not enabled")
```

### Data Handling

#### Sensitive Data Masking

```python
def mask_sensitive_data(data, field_name):
    """Mask sensitive data for logging."""
    if field_name in ['api_key', 'token', 'password']:
        if len(data) > 8:
            return data[:4] + '*' * (len(data) - 8) + data[-4:]
        else:
            return '*' * len(data)
    return data

# Example usage
api_key = "sk-1234567890abcdef"
masked = mask_sensitive_data(api_key, 'api_key')
print(f"API Key: {masked}")  # Output: sk-1****cdef
```

#### Secure Logging

```python
from utils.logger import get_logger

logger = get_logger(__name__)

# Log without exposing sensitive data
def secure_log_api_call(api_name, key, success):
    """Log API call without exposing key."""
    masked_key = mask_sensitive_data(key, 'api_key')
    
    logger.info(
        f"API call to {api_name}",
        extra={'extra_data': {
            'api_name': api_name,
            'key_prefix': masked_key,
            'success': success
        }}
    )

# Usage
secure_log_api_call("OpenAI", "sk-1234567890abcdef", True)
```

## 🔧 Security Configuration

### Security Settings

```python
# config.py - Security configuration
@dataclass
class SecurityConfig:
    """Security configuration settings."""
    
    # Input validation
    input_validation_enabled: bool = True
    content_moderation_enabled: bool = True
    
    # Rate limiting
    rate_limiting_enabled: bool = True
    max_requests_per_hour: int = 100
    
    # Audit logging
    audit_logging_enabled: bool = True
    audit_log_file: str = "audit.log"
    
    # Encryption
    encryption_enabled: bool = True
    encryption_key_rotation_days: int = 90
    
    # API security
    api_key_validation_enabled: bool = True
    require_https: bool = True
```

### Environment-specific Security

```python
# Development environment
if config.environment == Environment.DEVELOPMENT:
    # Relaxed security for development
    config.security.rate_limiting_enabled = False
    config.security.content_moderation_enabled = False

# Production environment
elif config.environment == Environment.PRODUCTION:
    # Strict security for production
    config.security.rate_limiting_enabled = True
    config.security.audit_logging_enabled = True
    config.security.encryption_enabled = True
    config.security.require_https = True
```

## 🛡️ Security Best Practices

### API Key Security

1. **Never Hardcode Keys**
   ```python
   # ❌ Bad: Hardcoded key
   OPENAI_API_KEY = "sk-1234567890abcdef"
   
   # ✅ Good: Environment variable
   OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
   ```

2. **Use Key Rotation**
   ```bash
   # Rotate keys regularly (every 90 days)
   # 1. Generate new key
   # 2. Update environment
   # 3. Test application
   # 4. Revoke old key
   ```

3. **Validate Key Format**
   ```python
   def validate_openai_key(key):
       """Validate OpenAI API key format."""
       if not key or not key.startswith('sk-'):
           raise ConfigurationError("Invalid OpenAI API key format")
       if len(key) < 40:
           raise ConfigurationError("OpenAI API key too short")
   ```

### Input Security

1. **Always Validate Inputs**
   ```python
   @require_validation({'prompt': 'prompt', 'style': 'style'})
   def generate_content(prompt, style):
       """Generate content with validated inputs."""
       # Function implementation
   ```

2. **Sanitize User Content**
   ```python
   # Remove potentially dangerous content
   safe_prompt = validator.sanitize(user_prompt, "prompt")
   ```

3. **Use Content Moderation**
   ```python
   # Enable content moderation for all user inputs
   config.security.content_moderation_enabled = True
   ```

### Network Security

1. **Use HTTPS Only**
   ```python
   # Require HTTPS for all API calls
   if not url.startswith('https://'):
       raise SecurityError("HTTPS required for API calls")
   ```

2. **Validate SSL Certificates**
   ```python
   import requests
   
   # Verify SSL certificates
   response = requests.get(url, verify=True)
   ```

3. **Set Request Timeouts**
   ```python
   # Prevent hanging requests
   response = requests.get(url, timeout=30)
   ```

### Error Handling Security

1. **Don't Expose Sensitive Information**
   ```python
   try:
       result = api_call(api_key)
   except Exception as e:
       # Log full error internally
       logger.error(f"API call failed: {str(e)}")
       
       # Return generic error to user
       raise APIError("Service temporarily unavailable")
   ```

2. **Use Structured Error Handling**
   ```python
   from utils.exceptions import handle_exception
   
   try:
       risky_operation()
   except Exception as e:
       handle_exception(e, {"component": "content_generation"})
   ```

## 🔍 Security Testing

### Security Test Suite

```python
import pytest
from utils.security import get_input_validator, get_rate_limiter

class TestSecurity:
    """Security test suite."""
    
    def test_input_validation(self):
        """Test input validation."""
        validator = get_input_validator()
        
        # Test valid input
        result = validator.validate("valid prompt", "prompt")
        assert result['valid'] is True
        
        # Test invalid input
        result = validator.validate("<script>alert('xss')</script>", "prompt")
        assert result['valid'] is False
    
    def test_rate_limiting(self):
        """Test rate limiting."""
        limiter = get_rate_limiter()
        
        # Test normal usage
        result = limiter.is_allowed("test_user", "api_general")
        assert result['allowed'] is True
        
        # Test rate limit exceeded
        for _ in range(101):  # Exceed limit
            limiter.is_allowed("test_user", "api_general")
        
        result = limiter.is_allowed("test_user", "api_general")
        assert result['allowed'] is False
    
    def test_encryption(self):
        """Test encryption functionality."""
        from utils.security import get_encryption_manager
        
        encryption = get_encryption_manager()
        
        # Test string encryption
        original = "sensitive data"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original
```

### Penetration Testing

```python
def test_injection_attacks():
    """Test for injection vulnerabilities."""
    validator = get_input_validator()
    
    # SQL injection attempts
    sql_payloads = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--"
    ]
    
    for payload in sql_payloads:
        result = validator.validate(payload, "prompt")
        assert not result['valid'], f"SQL injection not blocked: {payload}"
    
    # XSS attempts
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>"
    ]
    
    for payload in xss_payloads:
        result = validator.validate(payload, "prompt")
        assert not result['valid'], f"XSS not blocked: {payload}"

def test_rate_limit_bypass():
    """Test rate limit bypass attempts."""
    limiter = get_rate_limiter()
    
    # Test different user agents
    user_agents = ["bot1", "bot2", "bot3"]
    
    for agent in user_agents:
        for _ in range(101):  # Try to exceed limit
            result = limiter.is_allowed(agent, "api_general")
        
        # Should be blocked
        result = limiter.is_allowed(agent, "api_general")
        assert not result['allowed'], f"Rate limit bypass detected: {agent}"
```

## 🚨 Incident Response

### Security Incident Handling

1. **Immediate Response**
   ```python
   def handle_security_incident(incident_type, details):
       """Handle security incident."""
       auditor = get_audit_logger()
       
       # Log incident
       auditor.log_security_event(
           event_type=incident_type,
           description=f"Security incident: {incident_type}",
           details=details,
           risk_level="critical"
       )
       
       # Alert administrators
       send_security_alert(incident_type, details)
       
       # Take protective action
       if incident_type == "api_key_compromise":
           revoke_compromised_keys()
       elif incident_type == "rate_limit_abuse":
           block_abusive_users()
   ```

2. **Key Compromise Response**
   ```bash
   # If API key is compromised:
   # 1. Immediately revoke the key
   # 2. Generate new key
   # 3. Update configuration
   # 4. Restart services
   # 5. Monitor for unauthorized usage
   ```

3. **Data Breach Response**
   ```python
   def handle_data_breach():
       """Handle potential data breach."""
       # 1. Isolate affected systems
       # 2. Assess scope of breach
       # 3. Notify stakeholders
       # 4. Implement containment measures
       # 5. Begin forensic analysis
   ```

### Security Monitoring Alerts

```python
def setup_security_alerts():
    """Set up automated security alerts."""
    
    # Monitor for suspicious activity
    def check_suspicious_activity():
        error_stats = get_error_stats()
        auth_errors = error_stats.get('authentication:AuthenticationError', 0)
        
        if auth_errors > 10:  # Threshold
            send_alert("High authentication failure rate detected")
    
    # Monitor rate limiting
    def check_rate_limiting():
        limiter = get_rate_limiter()
        stats = limiter.get_stats()
        
        if stats['blocked_identifiers'] > 20:  # Threshold
            send_alert("Unusual rate limiting activity detected")
    
    # Schedule monitoring
    import schedule
    schedule.every(5).minutes.do(check_suspicious_activity)
    schedule.every(5).minutes.do(check_rate_limiting)
```

## 📚 Security Compliance

### Security Standards

AI Socials follows industry security standards:

- **OWASP Top 10**: Protection against common web vulnerabilities
- **NIST Cybersecurity Framework**: Comprehensive security approach
- **ISO 27001**: Information security management
- **SOC 2**: Security and availability controls

### Compliance Checklist

- [ ] Input validation for all user inputs
- [ ] API keys stored securely in environment variables
- [ ] Rate limiting implemented and configured
- [ ] Audit logging enabled for all security events
- [ ] Encryption enabled for sensitive data
- [ ] HTTPS required for all API communications
- [ ] Error messages don't expose sensitive information
- [ ] Security testing included in CI/CD pipeline
- [ ] Incident response procedures documented
- [ ] Regular security assessments conducted

---

## 📞 Security Support

For security-related questions and incident reporting:

- **Security Issues**: security@ai-socials.com
- **Vulnerability Reports**: Use responsible disclosure
- **Documentation**: Check other guides for implementation details
- **Emergency**: Contact security team immediately for critical issues

**Found a security vulnerability?** Please report it responsibly through our security contact channels.