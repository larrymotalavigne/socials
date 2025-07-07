# Troubleshooting Guide

## 📋 Overview

This guide helps you diagnose and resolve common issues with AI Socials. Issues are organized by category with step-by-step solutions.

## 🚨 Quick Diagnostics

### Health Check Commands

```bash
# Validate entire setup
python main.py --validate-only

# Test all API connections
python main.py --test-all

# Test specific services
python main.py --test-openai
python main.py --test-instagram
python main.py --test-caption-generators

# Check configuration
python -c "from config import get_config; print(get_config())"
```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
python main.py --prompt "test"

# Or set in .env file
echo "DEBUG=true" >> .env
```

## 🔧 Installation Issues

### Python Version Problems

**Problem:** `python: command not found` or version conflicts

**Solutions:**

```bash
# Check Python version
python --version
python3 --version

# Use specific Python version
python3.9 -m venv venv
python3.9 -m pip install -e .

# On Windows, try:
py -3.9 -m venv venv
```

**Problem:** `pip: command not found`

**Solutions:**

```bash
# Install pip
python -m ensurepip --upgrade

# On Ubuntu/Debian
sudo apt install python3-pip

# On macOS with Homebrew
brew install python
```

### Virtual Environment Issues

**Problem:** Virtual environment not activating

**Solutions:**

```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv

# Windows activation
venv\Scripts\activate.bat

# PowerShell activation
venv\Scripts\Activate.ps1

# macOS/Linux activation
source venv/bin/activate

# Verify activation
which python
```

**Problem:** `Permission denied` errors

**Solutions:**

```bash
# Fix permissions (macOS/Linux)
sudo chown -R $USER:$USER /path/to/ai-socials

# Windows: Run as Administrator
# Or change directory permissions
```

### Dependency Installation Problems

**Problem:** Package installation fails

**Solutions:**

```bash
# Update pip first
pip install --upgrade pip

# Clear pip cache
pip cache purge

# Install with verbose output
pip install -e . -v

# Force reinstall
pip install -e . --force-reinstall

# Install without cache
pip install -e . --no-cache-dir
```

**Problem:** Conflicting dependencies

**Solutions:**

```bash
# Check for conflicts
pip check

# Create fresh environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e .[dev,test]

# Use pip-tools for dependency resolution
pip install pip-tools
pip-compile requirements.in
```

## ⚙️ Configuration Issues

### Environment File Problems

**Problem:** `.env` file not found or not loading

**Solutions:**

```bash
# Check if .env exists
ls -la .env

# Copy from template
cp .env.example .env

# Verify environment loading
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"

# Check file permissions
chmod 600 .env
```

**Problem:** Environment variables not recognized

**Solutions:**

```bash
# Check variable names (case sensitive)
grep -n "OPENAI_API_KEY" .env

# Remove spaces around = sign
# Wrong: OPENAI_API_KEY = your_key
# Right: OPENAI_API_KEY=your_key

# Check for hidden characters
cat -A .env

# Reload environment
unset OPENAI_API_KEY
source .env  # Won't work directly
# Use: export $(cat .env | xargs)
```

### API Key Issues

**Problem:** "Invalid API key" errors

**Solutions:**

```bash
# Verify API key format
echo $OPENAI_API_KEY | wc -c  # Should be ~51 characters

# Test API key directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Check for extra spaces/newlines
echo "$OPENAI_API_KEY" | od -c

# Regenerate API key from OpenAI dashboard
```

**Problem:** Instagram API authentication fails

**Solutions:**

```bash
# Check token validity
curl -X GET \
  "https://graph.instagram.com/me?fields=id,username&access_token=$INSTAGRAM_ACCESS_TOKEN"

# Verify user ID matches
echo "Token User ID: $INSTAGRAM_USER_ID"

# Check token permissions
# Ensure token has instagram_basic, instagram_content_publish scopes

# Refresh long-lived token if expired
```

## 🤖 Content Generation Issues

### OpenAI API Problems

**Problem:** "Rate limit exceeded" errors

**Solutions:**

```bash
# Check current usage
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/usage

# Implement exponential backoff
python main.py --prompt "test" --retry-attempts 3

# Switch to different model
export OPENAI_MODEL_CHAT=gpt-3.5-turbo
```

**Problem:** Image generation fails

**Solutions:**

```bash
# Test image generation directly
python -c "
from generator import get_image_generator
gen = get_image_generator()
result = gen.generate_image('test image')
print(result)
"

# Check DALL-E model availability
export OPENAI_MODEL_IMAGE=dall-e-2  # Fallback

# Verify prompt content policy
# Avoid: violence, adult content, copyrighted material
```

**Problem:** Caption generation produces poor results

**Solutions:**

```bash
# Try different models
export OPENAI_MODEL_CHAT=gpt-4
export OPENAI_MODEL_CHAT=gpt-3.5-turbo

# Adjust temperature
export OPENAI_TEMPERATURE=0.7  # More focused
export OPENAI_TEMPERATURE=1.2  # More creative

# Test with simpler prompts
python main.py --prompt "sunset" --style casual
```

### Ollama Issues

**Problem:** Ollama connection fails

**Solutions:**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama service
ollama serve

# Check available models
ollama list

# Pull required model
ollama pull llama2

# Test model directly
ollama run llama2 "Hello world"

# Check Ollama logs
ollama logs
```

**Problem:** Ollama model not found

**Solutions:**

```bash
# List available models
ollama list

# Pull specific model
ollama pull llama2:7b
ollama pull mistral

# Update model name in config
export OLLAMA_MODEL=llama2:7b

# Check model size requirements
df -h  # Ensure enough disk space
```

## 📱 Publishing Issues

### Instagram Publishing Problems

**Problem:** "Media upload failed" errors

**Solutions:**

```bash
# Check image file
file /path/to/image.png
ls -la /path/to/image.png

# Verify image format
python -c "
from PIL import Image
img = Image.open('/path/to/image.png')
print(f'Format: {img.format}, Size: {img.size}, Mode: {img.mode}')
"

# Convert image if needed
python -c "
from PIL import Image
img = Image.open('/path/to/image.png')
img = img.convert('RGB')
img.save('/path/to/image_fixed.jpg', 'JPEG')
"

# Check file size (max 8MB for Instagram)
du -h /path/to/image.png
```

**Problem:** Caption too long error

**Solutions:**

```bash
# Check caption length
python -c "
caption = 'your caption here'
print(f'Length: {len(caption)} characters')
print(f'Max allowed: 2200 characters')
"

# Truncate caption
export CONTENT_MAX_CAPTION_LENGTH=2000

# Reduce hashtag count
export CONTENT_HASHTAG_COUNT=5
```

**Problem:** Instagram API rate limits

**Solutions:**

```bash
# Check rate limit status
python -c "
from publisher.instagram_publisher import get_instagram_publisher
pub = get_instagram_publisher()
result = pub.test_connection()
print(result)
"

# Wait before retrying
sleep 3600  # Wait 1 hour

# Implement publishing queue
# Use scheduler for delayed publishing
```

## 🔍 Review System Issues

### Telegram Bot Problems

**Problem:** Bot not responding

**Solutions:**

```bash
# Test bot token
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Check bot permissions
# Ensure bot can send messages to chat

# Verify chat ID
echo "Chat ID: $TELEGRAM_CHAT_ID"

# Test message sending
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
  -d "chat_id=$TELEGRAM_CHAT_ID&text=Test message"

# Check bot logs
python -c "
from reviewer.telegram_bot import get_telegram_bot
bot = get_telegram_bot()
print('Bot initialized successfully')
"
```

**Problem:** Review messages not appearing

**Solutions:**

```bash
# Check if bot is started
python -c "
import asyncio
from reviewer.telegram_bot import get_telegram_bot

async def test():
    bot = get_telegram_bot()
    await bot.start_bot()

asyncio.run(test())
"

# Verify webhook settings (if using webhooks)
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo"

# Check chat permissions
# Ensure bot is admin or has send permissions
```

## 📊 Performance Issues

### Slow Content Generation

**Problem:** Generation takes too long

**Solutions:**

```bash
# Enable performance logging
export DEBUG=true

# Check network connectivity
ping api.openai.com
ping graph.instagram.com

# Use faster models
export OPENAI_MODEL_CHAT=gpt-3.5-turbo
export OPENAI_MODEL_IMAGE=dall-e-2

# Reduce image quality
export OPENAI_IMAGE_QUALITY=standard
export OPENAI_IMAGE_SIZE=1024x1024

# Monitor resource usage
top -p $(pgrep -f python)
```

### Memory Issues

**Problem:** Out of memory errors

**Solutions:**

```bash
# Check memory usage
free -h
ps aux | grep python

# Reduce concurrent operations
# Avoid batch processing large datasets

# Clear cache
python -c "
import gc
gc.collect()
"

# Restart application periodically
# Implement memory monitoring
```

### Disk Space Issues

**Problem:** No space left on device

**Solutions:**

```bash
# Check disk usage
df -h
du -sh generated_content/

# Clean old generated content
find generated_content/ -type f -mtime +7 -delete

# Configure log rotation
# Check logs/ directory size
du -sh logs/

# Set up automatic cleanup
# Add to crontab:
# 0 2 * * * find /path/to/ai-socials/generated_content -mtime +7 -delete
```

## 🔒 Security Issues

### Permission Problems

**Problem:** File permission errors

**Solutions:**

```bash
# Fix file permissions
chmod 755 /path/to/ai-socials
chmod 644 /path/to/ai-socials/.env
chmod 755 /path/to/ai-socials/generated_content

# Fix ownership
sudo chown -R $USER:$USER /path/to/ai-socials

# Check SELinux (if applicable)
sestatus
# Disable temporarily: sudo setenforce 0
```

### API Security Issues

**Problem:** Suspicious API activity

**Solutions:**

```bash
# Rotate API keys immediately
# 1. Generate new OpenAI API key
# 2. Update .env file
# 3. Revoke old key

# Check audit logs
grep "security_event" logs/audit.log

# Review rate limiting
python -c "
from utils.security import get_rate_limiter
limiter = get_rate_limiter()
print(limiter.get_stats())
"

# Enable additional logging
export AUDIT_LOGGING=true
```

## 🐛 Common Error Messages

### "ModuleNotFoundError"

```bash
# Error: ModuleNotFoundError: No module named 'openai'
pip install -e .

# Error: ModuleNotFoundError: No module named 'config'
# Ensure you're in the project directory
cd /path/to/ai-socials
python main.py
```

### "ConfigurationError"

```bash
# Error: OpenAI API key is required
echo "OPENAI_API_KEY=your_key_here" >> .env

# Error: Invalid configuration
python main.py --validate-only
```

### "ContentGenerationError"

```bash
# Error: Failed to generate image
# Check OpenAI API status: https://status.openai.com/
# Verify API key and billing

# Error: Prompt violates content policy
# Modify prompt to avoid restricted content
```

### "PublishingError"

```bash
# Error: Instagram publisher not available
# Check Instagram API credentials
python main.py --test-instagram

# Error: Image file does not exist
ls -la /path/to/image.png
# Ensure image was generated successfully
```

## 🔧 Advanced Debugging

### Enable Verbose Logging

```python
# Add to main.py or create debug script
import logging
logging.basicConfig(level=logging.DEBUG)

from utils.logger import setup_logging
setup_logging()

# Run with debug
DEBUG=true python main.py --prompt "debug test"
```

### Network Debugging

```bash
# Test API connectivity
curl -v https://api.openai.com/v1/models
curl -v https://graph.instagram.com/v23.0/me

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Test DNS resolution
nslookup api.openai.com
nslookup graph.instagram.com
```

### Database/Storage Debugging

```bash
# Check SQLite database (for scheduler)
sqlite3 data/jobs.sqlite ".tables"
sqlite3 data/jobs.sqlite "SELECT * FROM apscheduler_jobs;"

# Check file system
ls -la generated_content/
ls -la logs/
ls -la data/
```

## 📞 Getting Help

### Before Asking for Help

1. **Check logs**: Look in `logs/` directory
2. **Run diagnostics**: Use `--validate-only` and `--test-all`
3. **Search issues**: Check GitHub issues for similar problems
4. **Try minimal example**: Test with simple prompts

### Information to Include

When reporting issues, include:

```bash
# System information
python --version
pip --version
uname -a  # Linux/macOS
systeminfo  # Windows

# Application information
python main.py --validate-only
pip list | grep -E "(openai|requests|python-dotenv)"

# Error logs
tail -50 logs/app.log
tail -20 logs/error.log

# Configuration (sanitized)
python -c "
from config import get_config
config = get_config()
print(f'Environment: {config.environment}')
print(f'Debug: {config.debug}')
print(f'OpenAI configured: {bool(config.openai.api_key)}')
"
```

### Support Channels

- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Check all docs/ files
- **Community**: Discord/Slack channels
- **Email**: Direct support for critical issues

## 🔄 Recovery Procedures

### Reset Configuration

```bash
# Backup current config
cp .env .env.backup

# Reset to defaults
cp .env.example .env
# Edit with your API keys

# Clear cached config
rm -rf __pycache__/
python -c "from config import config_manager; config_manager._config = None"
```

### Clean Installation

```bash
# Complete reset
rm -rf venv/
rm -rf __pycache__/
rm -rf *.egg-info/
rm -rf .pytest_cache/

# Fresh installation
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .[dev,test]

# Verify installation
python main.py --validate-only
```

### Data Recovery

```bash
# Backup generated content
cp -r generated_content/ generated_content_backup/

# Recover from logs
grep "Generated content" logs/app.log

# Check scheduler jobs
sqlite3 data/jobs.sqlite "SELECT * FROM apscheduler_jobs;"
```

---

## 📚 Related Documentation

- [Installation Guide](installation.md) - Setup instructions
- [Configuration Reference](configuration.md) - Configuration options
- [Usage Guide](usage.md) - How to use the application
- [API Documentation](api.md) - API reference
- [Development Guide](development.md) - Contributing guidelines

**Still having issues?** Contact our support team with the diagnostic information above!