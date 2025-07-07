# Configuration Reference

## 📋 Overview

The AI Instagram Publisher uses a comprehensive configuration system that supports multiple environments, secure credential management, and fine-tuned control over all aspects of content generation and publishing.

## 🏗️ Configuration Architecture

### Configuration Hierarchy
1. **Environment Variables** (highest priority)
2. **`.env` file** (development/local)
3. **Default values** (fallback)

### Environment Support
- **Development**: Local development with debug features
- **Staging**: Pre-production testing environment
- **Production**: Live deployment with optimized settings

## ⚙️ Core Configuration

### Application Settings

```bash
# Environment Configuration
ENVIRONMENT=development  # development, staging, production
DEBUG=true              # Enable debug mode and verbose logging
```

**ENVIRONMENT Options:**
- `development`: Local development with debug features enabled
- `staging`: Pre-production environment for testing
- `production`: Optimized for live deployment

**DEBUG Effects:**
- Enables verbose logging
- Shows detailed error messages
- Activates development-specific features

### Content Generation

```bash
# Caption Generator Selection
CAPTION_GENERATOR=openai  # openai or ollama

# Content Output Configuration
CONTENT_OUTPUT_DIR=generated_content
CONTENT_IMAGE_FORMAT=png
CONTENT_MAX_CAPTION_LENGTH=2200  # Instagram limit
CONTENT_HASHTAG_COUNT=10
CONTENT_THEMES=nature,lifestyle,inspiration
```

**Configuration Details:**

| Setting | Options | Default | Description |
|---------|---------|---------|-------------|
| `CAPTION_GENERATOR` | `openai`, `ollama` | `openai` | AI model for caption generation |
| `CONTENT_OUTPUT_DIR` | Any valid path | `generated_content` | Directory for generated content |
| `CONTENT_IMAGE_FORMAT` | `png`, `jpg`, `webp` | `png` | Output image format |
| `CONTENT_MAX_CAPTION_LENGTH` | 1-2200 | `2200` | Maximum caption length (Instagram limit) |
| `CONTENT_HASHTAG_COUNT` | 1-30 | `10` | Number of hashtags to generate |
| `CONTENT_THEMES` | Comma-separated list | `nature,lifestyle,inspiration` | Available content themes |

## 🤖 AI Model Configuration

### OpenAI Settings

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration
OPENAI_MODEL_CHAT=gpt-4           # Chat model for captions
OPENAI_MODEL_IMAGE=dall-e-3       # Image generation model
OPENAI_TEMPERATURE=0.8            # Creativity level (0.0-2.0)
OPENAI_MAX_TOKENS=150             # Maximum response length

# Image Generation
OPENAI_IMAGE_SIZE=1024x1024       # Image dimensions
OPENAI_IMAGE_QUALITY=standard     # Image quality level
```

**Model Options:**

| Setting | Available Options | Recommended |
|---------|------------------|-------------|
| `OPENAI_MODEL_CHAT` | `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo` | `gpt-4` |
| `OPENAI_MODEL_IMAGE` | `dall-e-2`, `dall-e-3` | `dall-e-3` |
| `OPENAI_IMAGE_SIZE` | `1024x1024`, `1792x1024`, `1024x1792` | `1024x1024` |
| `OPENAI_IMAGE_QUALITY` | `standard`, `hd` | `standard` |

**Temperature Guidelines:**
- `0.0-0.3`: Very focused and deterministic
- `0.4-0.7`: Balanced creativity and consistency
- `0.8-1.2`: Creative and varied (recommended)
- `1.3-2.0`: Highly creative but potentially inconsistent

### Ollama Settings

```bash
# Ollama Configuration (for local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=30
OLLAMA_TEMPERATURE=0.8
OLLAMA_MAX_TOKENS=150
```

**Ollama Models:**
- `llama2`: General-purpose model (7B, 13B, 70B variants)
- `codellama`: Code-focused model
- `mistral`: Fast and efficient model
- `neural-chat`: Conversation-optimized model

**Setup Requirements:**
1. Install Ollama locally
2. Pull desired model: `ollama pull llama2`
3. Start service: `ollama serve`

## 📱 Social Media Integration

### Instagram Configuration

```bash
# Instagram Graph API
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
INSTAGRAM_USER_ID=your_instagram_user_id
```

**Setup Process:**
1. Create Facebook Developer App
2. Add Instagram Graph API product
3. Generate long-lived access token
4. Convert Instagram account to Business account

**Token Types:**
- **Short-lived**: Valid for 1 hour
- **Long-lived**: Valid for 60 days (recommended)
- **Page Access Token**: For business accounts

### Telegram Integration

```bash
# Telegram Bot (for content review)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

**Setup Process:**
1. Create bot with @BotFather
2. Get bot token
3. Add bot to chat/channel
4. Get chat ID using bot API

## 📊 Logging Configuration

```bash
# Logging Settings
LOG_LEVEL=INFO                    # Logging verbosity
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE_PATH=logs/app.log        # Log file location
LOG_MAX_FILE_SIZE=10485760        # 10MB max file size
LOG_BACKUP_COUNT=5                # Number of backup files
```

**Log Levels:**
- `DEBUG`: Detailed information for debugging
- `INFO`: General information about application flow
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical errors that may stop the application

**Log Rotation:**
- Automatic rotation when file reaches max size
- Keeps specified number of backup files
- Compressed backup files to save space

## 🔒 Security Configuration

```bash
# Security Settings
RETRY_ATTEMPTS=3                  # API retry attempts
RETRY_DELAY=1.0                   # Delay between retries (seconds)
REQUEST_TIMEOUT=30                # Request timeout (seconds)
```

**Rate Limiting:**
- Built-in rate limiting for API calls
- Configurable limits per endpoint
- Automatic backoff on rate limit hits

**Input Validation:**
- Automatic sanitization of all inputs
- Validation rules for prompts, filenames, etc.
- Protection against injection attacks

## ⏰ Scheduling Configuration

```bash
# Scheduling Settings
SCHEDULING_ENABLED=false          # Enable automatic scheduling
SCHEDULING_INTERVAL_HOURS=24      # Hours between posts
SCHEDULING_MAX_POSTS_PER_DAY=3    # Maximum daily posts
SCHEDULING_TIMEZONE=UTC           # Timezone for scheduling
```

**Scheduling Features:**
- Cron-like scheduling with flexible intervals
- Daily, weekly, or custom scheduling patterns
- Timezone-aware scheduling
- Automatic content generation and posting

## 🌍 Environment-Specific Configurations

### Development Environment

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
OPENAI_MODEL_CHAT=gpt-3.5-turbo  # Cost-effective for development
CONTENT_OUTPUT_DIR=dev_content
SCHEDULING_ENABLED=false
```

### Staging Environment

```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
OPENAI_MODEL_CHAT=gpt-4
CONTENT_OUTPUT_DIR=staging_content
SCHEDULING_ENABLED=true
SCHEDULING_INTERVAL_HOURS=48      # Less frequent posting
```

### Production Environment

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
OPENAI_MODEL_CHAT=gpt-4
OPENAI_IMAGE_QUALITY=hd
CONTENT_OUTPUT_DIR=/var/app/content
SCHEDULING_ENABLED=true
LOG_FILE_PATH=/var/log/socials/app.log
```

## 🔧 Advanced Configuration

### Performance Tuning

```bash
# Performance Settings
REQUEST_TIMEOUT=60                # Longer timeout for complex requests
OPENAI_MAX_TOKENS=300            # More detailed captions
CONTENT_HASHTAG_COUNT=15         # More hashtags for reach
```

### Content Quality

```bash
# Quality Settings
OPENAI_TEMPERATURE=0.7           # Balanced creativity
OPENAI_IMAGE_QUALITY=hd          # High-quality images
CONTENT_MAX_CAPTION_LENGTH=1500  # Optimal engagement length
```

### Security Hardening

```bash
# Security Hardening
RETRY_ATTEMPTS=2                 # Fewer retries to prevent abuse
REQUEST_TIMEOUT=15               # Shorter timeout
LOG_LEVEL=ERROR                  # Minimal logging for security
```

## 📝 Configuration Validation

### Automatic Validation

The application automatically validates configuration on startup:

```python
# Configuration validation
config_status = config_manager.validate_config()
if not config_status['valid']:
    print(f"Configuration error: {config_status['error']}")
    exit(1)
```

### Manual Validation

```bash
# Validate configuration
python main.py --validate-only

# Test specific components
python main.py --test-openai
python main.py --test-instagram
python main.py --test-caption-generators
```

## 🔄 Dynamic Configuration

### Runtime Configuration Changes

```python
# Change caption generator at runtime
python main.py --caption-generator ollama --prompt "test"

# Override image settings
python main.py --image-size 1792x1024 --image-quality hd
```

### Configuration Reloading

```python
# Reload configuration without restart
from config import config_manager
config_manager.reload_config()
```

## 📋 Configuration Templates

### Minimal Configuration

```bash
# Minimal .env for basic functionality
OPENAI_API_KEY=your_key_here
ENVIRONMENT=development
DEBUG=true
```

### Complete Configuration

```bash
# Complete .env with all options
# Copy from .env.example and customize
cp .env.example .env
```

### Docker Configuration

```yaml
# docker-compose.yml environment
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - ENVIRONMENT=production
  - DEBUG=false
  - LOG_LEVEL=INFO
  - CONTENT_OUTPUT_DIR=/app/content
```

## 🚨 Security Best Practices

### API Key Management

1. **Never commit API keys to version control**
2. **Use environment variables or secure vaults**
3. **Rotate keys regularly**
4. **Use least-privilege access**

### Environment Separation

1. **Separate configurations for each environment**
2. **Different API keys for dev/staging/production**
3. **Environment-specific resource limits**

### Access Control

1. **Restrict file permissions on .env files**
2. **Use secure credential storage in production**
3. **Implement proper authentication for web interfaces**

## 🔍 Troubleshooting Configuration

### Common Issues

#### Invalid API Key
```bash
# Test API key validity
python -c "
from config import get_config
config = get_config()
print(f'OpenAI key configured: {bool(config.openai.api_key)}')
"
```

#### Missing Environment Variables
```bash
# Check required variables
python main.py --validate-only
```

#### Configuration Conflicts
```bash
# Clear cached configuration
rm -rf __pycache__
python main.py --validate-only
```

### Debug Configuration

```bash
# Enable debug mode for detailed configuration info
DEBUG=true python main.py --validate-only
```

## 📚 Related Documentation

- [Installation Guide](installation.md) - Setup instructions
- [Usage Guide](usage.md) - How to use the application
- [Security Guide](security.md) - Security best practices
- [Troubleshooting](troubleshooting.md) - Common issues and solutions