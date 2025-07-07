# API Documentation

## 📋 Overview

AI Socials provides a comprehensive API for content generation, publishing, and management. This document covers all available APIs, endpoints, and integration methods.

## 🏗️ API Architecture

### Core Components

```
AI Socials API
├── 🧠 Content Generation API
│   ├── Image Generation
│   ├── Caption Generation
│   └── Content Enhancement
├── 📱 Publishing API
│   ├── Instagram Publishing
│   ├── Content Validation
│   └── Publishing Pipeline
├── 🔍 Review API
│   ├── Content Review
│   ├── Approval Workflow
│   └── Review Management
├── ⚙️ Configuration API
│   ├── Settings Management
│   ├── API Key Management
│   └── Environment Configuration
└── 📊 Monitoring API
    ├── Performance Metrics
    ├── Error Tracking
    └── Usage Statistics
```

## 🤖 Content Generation API

### Image Generation

#### Generate Image

**Method:** `POST`  
**Endpoint:** `/api/v1/generate/image`

```python
from generator import get_image_generator

# Initialize generator
image_gen = get_image_generator()

# Generate image
result = image_gen.generate_image(
    prompt="a beautiful sunset over mountains",
    size="1024x1024",
    quality="standard",
    style="natural"
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Image generation prompt |
| `size` | string | No | Image dimensions (default: "1024x1024") |
| `quality` | string | No | Image quality: "standard" or "hd" |
| `style` | string | No | Image style preference |

**Response:**

```json
{
    "success": true,
    "image_path": "/path/to/generated/image.png",
    "metadata": {
        "model": "dall-e-3",
        "size": "1024x1024",
        "quality": "standard",
        "prompt": "a beautiful sunset over mountains",
        "file_size": 1024000,
        "created_at": "2024-01-01T12:00:00Z"
    }
}
```

**Error Response:**

```json
{
    "success": false,
    "error": "ContentGenerationError",
    "message": "Failed to generate image",
    "details": {
        "error_code": "OPENAI_API_ERROR",
        "retry_after": 60
    }
}
```

### Caption Generation

#### Generate Caption

**Method:** `POST`  
**Endpoint:** `/api/v1/generate/caption`

```python
from generator import get_caption_generator

# Initialize generator
caption_gen = get_caption_generator()

# Generate caption
result = caption_gen.generate_caption(
    prompt="a beautiful sunset over mountains",
    style="engaging",
    theme="nature",
    hashtag_count=10
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Content description prompt |
| `style` | string | No | Caption style (default: "engaging") |
| `theme` | string | No | Content theme for hashtags |
| `hashtag_count` | integer | No | Number of hashtags (default: 10) |
| `max_length` | integer | No | Maximum caption length |

**Response:**

```json
{
    "success": true,
    "full_caption": "🌅 Witnessing nature's masterpiece...",
    "main_caption": "Witnessing nature's masterpiece as the sun sets behind majestic mountains.",
    "hashtags": ["#sunset", "#mountains", "#nature"],
    "metadata": {
        "style": "engaging",
        "theme": "nature",
        "word_count": 45,
        "character_count": 280,
        "hashtag_count": 10,
        "model": "gpt-4",
        "created_at": "2024-01-01T12:00:00Z"
    }
}
```

### Content Enhancement

#### Enhance Content

```python
from main import AISocials

# Initialize application
app = AISocials()

# Generate complete content
result = app.generate_content(
    prompt="a beautiful sunset over mountains",
    style="engaging",
    theme="nature",
    image_options={
        "size": "1024x1024",
        "quality": "hd"
    }
)
```

**Response:**

```json
{
    "success": true,
    "image": {
        "image_path": "/path/to/image.png",
        "metadata": {...}
    },
    "caption": {
        "full_caption": "🌅 Witnessing nature's masterpiece...",
        "metadata": {...}
    },
    "content_id": "content_abc123",
    "created_at": "2024-01-01T12:00:00Z"
}
```

## 📱 Publishing API

### Instagram Publishing

#### Publish Post

```python
from publisher.instagram_publisher import get_instagram_publisher

# Initialize publisher
publisher = get_instagram_publisher()

# Publish content
result = publisher.publish_post(
    image_path="/path/to/image.png",
    caption="Your amazing caption here #hashtags",
    verify_post=True
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_path` | string | Yes | Path to image file |
| `caption` | string | Yes | Post caption text |
| `verify_post` | boolean | No | Verify post after publishing |

**Response:**

```json
{
    "success": true,
    "post_id": "instagram_post_id",
    "media_id": "instagram_media_id",
    "permalink": "https://instagram.com/p/...",
    "metadata": {
        "image_path": "/path/to/image.png",
        "caption": "Your amazing caption...",
        "caption_length": 280,
        "image_size": 1024000,
        "published_at": "2024-01-01T12:00:00Z",
        "verified": true
    }
}
```

#### Test Connection

```python
# Test Instagram API connection
result = publisher.test_connection()
```

**Response:**

```json
{
    "connected": true,
    "user_id": "instagram_user_id",
    "username": "your_username",
    "account_type": "BUSINESS",
    "message": "Instagram API connection successful"
}
```

## 🔍 Review API

### Content Review

#### Submit for Review

```python
from reviewer.telegram_bot import submit_content_for_review

# Submit content for review
review_id = await submit_content_for_review(
    content_type="instagram_post",
    image_path="/path/to/image.png",
    caption="Your caption here",
    metadata={"theme": "nature"},
    callback=approval_callback
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_type` | string | Yes | Type of content |
| `image_path` | string | No | Path to image file |
| `caption` | string | No | Caption text |
| `metadata` | object | No | Additional metadata |
| `callback` | function | No | Approval callback function |

**Response:**

```json
{
    "success": true,
    "review_id": "review_abc123",
    "status": "pending",
    "created_at": "2024-01-01T12:00:00Z"
}
```

#### Get Review Status

```python
from reviewer.telegram_bot import get_telegram_bot

bot = get_telegram_bot()
review = bot.reviews.get("review_abc123")
```

**Response:**

```json
{
    "review_id": "review_abc123",
    "status": "approved",
    "content_type": "instagram_post",
    "created_at": "2024-01-01T12:00:00Z",
    "reviewed_at": "2024-01-01T12:05:00Z",
    "reviewer_id": "telegram_user_id",
    "reviewer_username": "reviewer_name",
    "modifications": {}
}
```

## ⚙️ Configuration API

### Settings Management

#### Get Configuration

```python
from config import get_config

# Get current configuration
config = get_config()

# Access specific settings
openai_config = config.openai
instagram_config = config.instagram
content_config = config.content
```

#### Validate Configuration

```python
from config import config_manager

# Validate configuration
status = config_manager.validate_config()
```

**Response:**

```json
{
    "valid": true,
    "openai_configured": true,
    "instagram_configured": true,
    "telegram_configured": false,
    "errors": [],
    "warnings": ["Telegram not configured"]
}
```

### Environment Management

#### Switch Environment

```python
import os
from config import config_manager

# Switch to production
os.environ['ENVIRONMENT'] = 'production'
config_manager._config = None  # Clear cache
config = get_config()
```

## 📊 Monitoring API

### Performance Metrics

#### Get Performance Stats

```python
from utils.logger import get_logger

logger = get_logger(__name__)
# Performance metrics are automatically logged
```

#### Get Error Statistics

```python
from utils.exceptions import get_error_stats

# Get error statistics
stats = get_error_stats()
```

**Response:**

```json
{
    "api_error:OpenAIError": 2,
    "validation:ValidationError": 1,
    "publishing:InstagramError": 0
}
```

### Rate Limiting

#### Check Rate Limits

```python
from utils.security import get_rate_limiter

limiter = get_rate_limiter()
result = limiter.is_allowed("user_123", "api_generation")
```

**Response:**

```json
{
    "allowed": true,
    "current_requests": 5,
    "max_requests": 20,
    "remaining_requests": 15,
    "reset_time": "2024-01-01T13:00:00Z"
}
```

## 🔧 Scheduling API

### Job Management

#### Schedule Content Generation

```python
from scheduler import schedule_content_generation

# Schedule regular content generation
job_id = schedule_content_generation(
    prompt="daily nature content",
    interval_hours=24,
    style="engaging",
    theme="nature"
)
```

#### Schedule Publishing

```python
from scheduler import schedule_instagram_publishing
from datetime import datetime, timedelta

# Schedule publishing
publish_time = datetime.now() + timedelta(hours=2)
job_id = schedule_instagram_publishing(
    image_path="/path/to/image.png",
    caption="Scheduled post caption",
    publish_time=publish_time
)
```

#### Manage Jobs

```python
from scheduler import get_scheduler

scheduler = get_scheduler()

# List all jobs
jobs = scheduler.get_all_jobs()

# Get job info
job_info = scheduler.get_job_info(job_id)

# Remove job
scheduler.remove_job(job_id)
```

## 🔒 Security API

### Input Validation

```python
from utils.security import get_input_validator

validator = get_input_validator()

# Validate input
result = validator.validate("user input", "prompt")
```

**Response:**

```json
{
    "valid": true,
    "sanitized_value": "cleaned user input"
}
```

### Audit Logging

```python
from utils.security import get_audit_logger

auditor = get_audit_logger()

# Log security event
auditor.log_action(
    action="content_generation",
    resource="ai_content",
    user_id="user_123",
    details={"prompt": "sunset image"},
    success=True,
    risk_level="low"
)
```

## 🧪 Testing API

### Connection Testing

#### Test All Services

```python
from main import AISocials

app = AISocials()

# Test OpenAI connection
openai_result = app.test_openai_connection()

# Test Instagram connection
instagram_result = app.test_instagram_connection()

# Test caption generators
from generator import test_caption_generators
caption_results = test_caption_generators()
```

## 📚 SDK Usage Examples

### Basic Content Generation

```python
#!/usr/bin/env python3
"""Basic content generation example."""

from main import AISocials

def main():
    # Initialize application
    app = AISocials()
    
    # Generate content
    result = app.generate_content(
        prompt="a serene lake at dawn",
        style="inspirational",
        theme="nature"
    )
    
    if result.get('success'):
        print(f"✅ Image: {result['image']['image_path']}")
        print(f"✅ Caption: {result['caption']['full_caption']}")
    else:
        print(f"❌ Error: {result.get('error')}")

if __name__ == "__main__":
    main()
```

### Automated Publishing Pipeline

```python
#!/usr/bin/env python3
"""Automated publishing pipeline example."""

import asyncio
from main import AISocials
from reviewer.telegram_bot import submit_content_for_review

async def publishing_pipeline():
    app = AISocials()
    
    # Generate content
    content = app.generate_content(
        prompt="motivational quote with sunrise",
        style="inspirational"
    )
    
    if not content.get('success'):
        return
    
    # Submit for review
    review_id = await submit_content_for_review(
        content_type="instagram_post",
        image_path=content['image']['image_path'],
        caption=content['caption']['full_caption'],
        callback=publish_approved_content
    )
    
    print(f"Content submitted for review: {review_id}")

async def publish_approved_content(review, status):
    """Callback for approved content."""
    if status.value == "approved":
        app = AISocials()
        result = app.publish_content(
            image_path=review.image_path,
            caption=review.caption
        )
        print(f"Published: {result.get('post_id')}")

if __name__ == "__main__":
    asyncio.run(publishing_pipeline())
```

### Batch Content Generation

```python
#!/usr/bin/env python3
"""Batch content generation example."""

from main import AISocials
from concurrent.futures import ThreadPoolExecutor
import json

def generate_single_content(prompt_data):
    """Generate content for a single prompt."""
    app = AISocials()
    
    result = app.generate_content(
        prompt=prompt_data['prompt'],
        style=prompt_data.get('style', 'engaging'),
        theme=prompt_data.get('theme')
    )
    
    return {
        'prompt': prompt_data['prompt'],
        'result': result
    }

def batch_generate():
    """Generate multiple pieces of content in parallel."""
    prompts = [
        {'prompt': 'sunrise over ocean', 'style': 'peaceful', 'theme': 'nature'},
        {'prompt': 'city skyline at night', 'style': 'dynamic', 'theme': 'urban'},
        {'prompt': 'mountain hiking trail', 'style': 'adventurous', 'theme': 'outdoor'}
    ]
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(generate_single_content, prompts))
    
    # Save results
    with open('batch_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Generated {len(results)} pieces of content")

if __name__ == "__main__":
    batch_generate()
```

## 🔧 Error Handling

### Exception Types

```python
from utils.exceptions import (
    ContentGenerationError,
    PublishingError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    InstagramError,
    OpenAIError,
    TelegramError
)

try:
    result = app.generate_content(prompt="test")
except ContentGenerationError as e:
    print(f"Content generation failed: {e.message}")
    print(f"Error category: {e.category.value}")
    print(f"Details: {e.details}")
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Field: {e.details.get('field')}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e.message}")
    print(f"Retry after: {e.details.get('retry_after')} seconds")
```

### Retry Mechanisms

```python
from utils.exceptions import retry_on_exception, RetryConfig

@retry_on_exception(
    exceptions=(OpenAIError, NetworkError),
    retry_config=RetryConfig(max_attempts=3, base_delay=2.0)
)
def robust_content_generation(prompt):
    app = AISocials()
    return app.generate_content(prompt=prompt)
```

## 📈 Performance Optimization

### Caching

```python
# Content caching is automatic
result = app.generate_content(prompt="cached prompt")
# Subsequent calls with same prompt will use cache
```

### Async Operations

```python
import asyncio

async def async_content_pipeline():
    # Use async operations for I/O bound tasks
    tasks = [
        submit_content_for_review(...),
        # Other async operations
    ]
    
    results = await asyncio.gather(*tasks)
    return results
```

## 🔗 Integration Examples

### Flask Web Application

```python
from flask import Flask, request, jsonify
from main import AISocials

app = Flask(__name__)
ai_socials = AISocials()

@app.route('/api/generate', methods=['POST'])
def generate_content():
    data = request.json
    
    try:
        result = ai_socials.generate_content(
            prompt=data['prompt'],
            style=data.get('style', 'engaging')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI Application

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import AISocials

app = FastAPI()
ai_socials = AISocials()

class ContentRequest(BaseModel):
    prompt: str
    style: str = "engaging"
    theme: str = None

@app.post("/api/generate")
async def generate_content(request: ContentRequest):
    try:
        result = ai_socials.generate_content(
            prompt=request.prompt,
            style=request.style,
            theme=request.theme
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 📚 API Reference Summary

### Core Classes

| Class | Description | Module |
|-------|-------------|---------|
| `AISocials` | Main application orchestrator | `main` |
| `CaptionGenerator` | OpenAI caption generation | `generator.caption_generator` |
| `OllamaCaptionGenerator` | Ollama caption generation | `generator.ollama_caption_generator` |
| `ImageGenerator` | OpenAI image generation | `generator.image_generator` |
| `InstagramPublisher` | Instagram publishing | `publisher.instagram_publisher` |
| `TelegramReviewBot` | Telegram review bot | `reviewer.telegram_bot` |
| `ContentScheduler` | Job scheduling | `scheduler.scheduler` |

### Configuration Classes

| Class | Description | Module |
|-------|-------------|---------|
| `Config` | Main configuration | `config` |
| `OpenAIConfig` | OpenAI settings | `config` |
| `InstagramConfig` | Instagram settings | `config` |
| `TelegramConfig` | Telegram settings | `config` |

### Utility Classes

| Class | Description | Module |
|-------|-------------|---------|
| `InputValidator` | Input validation | `utils.security` |
| `RateLimiter` | Rate limiting | `utils.security` |
| `AuditLogger` | Audit logging | `utils.security` |
| `EncryptionManager` | Data encryption | `utils.security` |

---

## 📞 Support

For API support and questions:

- **Documentation**: Check [Usage Guide](usage.md) for examples
- **GitHub Issues**: Report API bugs and feature requests
- **Community**: Join our developer community
- **Email**: Contact our API support team

**Ready to integrate?** Check out the [Usage Guide](usage.md) for more examples and best practices!