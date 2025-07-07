# Usage Guide

## 📋 Overview

This guide provides comprehensive examples and instructions for using AI Socials to generate and publish social media content. Whether you're a beginner or advanced user, you'll find practical examples and best practices here.

## 🚀 Quick Start

### Basic Content Generation

```bash
# Generate content with a simple prompt
python main.py --prompt "a beautiful sunset over mountains"

# Generate with specific style
python main.py --prompt "coffee shop morning" --style professional

# Generate with theme for better hashtags
python main.py --prompt "yoga session" --style inspirational --theme wellness
```

### Command Line Options

```bash
# Basic usage
python main.py --prompt "your content description"

# Advanced options
python main.py \
  --prompt "mountain hiking adventure" \
  --style adventurous \
  --theme outdoor \
  --image-size 1024x1024 \
  --image-quality hd \
  --caption-generator openai \
  --output-dir custom_output \
  --publish
```

## 🎨 Content Generation

### Image Generation

#### Basic Image Generation

```python
from generator import get_image_generator

# Initialize generator
image_gen = get_image_generator()

# Generate image
result = image_gen.generate_image(
    prompt="a serene lake at sunrise with mountains in background",
    size="1024x1024",
    quality="standard"
)

if result.get('success'):
    print(f"Image saved to: {result['image_path']}")
else:
    print(f"Error: {result.get('error')}")
```

#### Advanced Image Options

```python
# High-quality landscape image
result = image_gen.generate_image(
    prompt="dramatic landscape with storm clouds",
    size="1792x1024",  # Landscape format
    quality="hd",       # High definition
    style="photographic"
)

# Portrait format for people
result = image_gen.generate_image(
    prompt="professional headshot of a business person",
    size="1024x1792",  # Portrait format
    quality="hd"
)

# Square format for social media
result = image_gen.generate_image(
    prompt="minimalist product photography",
    size="1024x1024",  # Square format
    quality="standard"
)
```

### Caption Generation

#### Basic Caption Generation

```python
from generator import get_caption_generator

# Initialize generator
caption_gen = get_caption_generator()

# Generate caption
result = caption_gen.generate_caption(
    prompt="sunset over mountains",
    style="engaging",
    hashtag_count=10
)

if result.get('success'):
    print("Caption:", result['full_caption'])
    print("Hashtags:", result['hashtags'])
else:
    print(f"Error: {result.get('error')}")
```

#### Caption Styles

```python
# Professional style
result = caption_gen.generate_caption(
    prompt="business meeting",
    style="professional",
    max_length=150
)

# Casual and fun
result = caption_gen.generate_caption(
    prompt="weekend brunch",
    style="casual",
    hashtag_count=15
)

# Inspirational content
result = caption_gen.generate_caption(
    prompt="morning workout",
    style="inspirational",
    theme="fitness"
)

# Educational content
result = caption_gen.generate_caption(
    prompt="cooking tutorial",
    style="educational",
    theme="food"
)

# Storytelling approach
result = caption_gen.generate_caption(
    prompt="travel adventure",
    style="storytelling",
    theme="travel"
)
```

### Complete Content Generation

```python
from main import AISocials

# Initialize application
app = AISocials()

# Generate complete content package
result = app.generate_content(
    prompt="cozy coffee shop on a rainy day",
    style="engaging",
    theme="lifestyle",
    image_options={
        "size": "1024x1024",
        "quality": "hd"
    }
)

if result.get('success'):
    # Access generated content
    image_path = result['image']['image_path']
    caption = result['caption']['full_caption']
    hashtags = result['caption']['hashtags']
    
    print(f"✅ Image: {image_path}")
    print(f"✅ Caption: {caption}")
    print(f"✅ Hashtags: {', '.join(hashtags)}")
else:
    print(f"❌ Error: {result.get('error')}")
```

## 📱 Publishing Content

### Instagram Publishing

#### Basic Publishing

```python
from publisher.instagram_publisher import get_instagram_publisher

# Initialize publisher
publisher = get_instagram_publisher()

# Publish content
result = publisher.publish_post(
    image_path="/path/to/image.png",
    caption="Your amazing caption with #hashtags",
    verify_post=True
)

if result.get('success'):
    print(f"✅ Published! Post ID: {result['post_id']}")
    print(f"🔗 URL: {result['permalink']}")
else:
    print(f"❌ Publishing failed: {result.get('error')}")
```

#### Publishing with Generated Content

```python
from main import AISocials

app = AISocials()

# Generate and publish in one flow
result = app.generate_content(
    prompt="morning coffee ritual",
    style="cozy",
    theme="lifestyle"
)

if result.get('success'):
    # Publish to Instagram
    publish_result = app.publish_content(
        image_path=result['image']['image_path'],
        caption=result['caption']['full_caption'],
        verify_post=True
    )
    
    if publish_result.get('success'):
        print(f"🎉 Content published successfully!")
        print(f"📸 Post ID: {publish_result['post_id']}")
    else:
        print(f"❌ Publishing failed: {publish_result.get('error')}")
```

### Testing Connections

```python
# Test Instagram connection
result = publisher.test_connection()
if result['connected']:
    print(f"✅ Connected as @{result['username']}")
else:
    print(f"❌ Connection failed: {result['error']}")

# Test OpenAI connection
from main import AISocials
app = AISocials()
if app.validate_setup():
    print("✅ All systems ready!")
else:
    print("❌ Setup validation failed")
```

## 🔍 Content Review System

### Telegram Bot Review

#### Setting Up Review

```python
import asyncio
from reviewer.telegram_bot import submit_content_for_review

async def review_workflow():
    # Generate content
    app = AISocials()
    content = app.generate_content(
        prompt="peaceful garden scene",
        style="serene"
    )
    
    if content.get('success'):
        # Submit for review
        review_id = await submit_content_for_review(
            content_type="instagram_post",
            image_path=content['image']['image_path'],
            caption=content['caption']['full_caption'],
            metadata={"theme": "nature"},
            callback=handle_approval
        )
        
        print(f"📋 Content submitted for review: {review_id}")

async def handle_approval(review, status):
    """Handle approval callback."""
    if status.value == "approved":
        # Publish approved content
        app = AISocials()
        result = app.publish_content(
            image_path=review.image_path,
            caption=review.caption
        )
        print(f"✅ Published approved content: {result.get('post_id')}")
    elif status.value == "rejected":
        print("❌ Content was rejected")
    elif status.value == "modified":
        print(f"✏️ Content was modified: {review.caption}")

# Run the workflow
asyncio.run(review_workflow())
```

#### Manual Review Check

```python
from reviewer.telegram_bot import get_telegram_bot

# Get bot instance
bot = get_telegram_bot()

# Check pending reviews
pending = [r for r in bot.reviews.values() if r.status.value == "pending"]
print(f"📋 Pending reviews: {len(pending)}")

# Get review statistics
stats = bot._get_review_statistics()
print(f"📊 Approval rate: {stats['approval_rate']:.1f}%")
print(f"📊 Total processed: {stats['total_processed']}")
```

## ⏰ Scheduling Content

### Basic Scheduling

```python
from scheduler import schedule_content_generation, get_scheduler

# Schedule daily content generation
job_id = schedule_content_generation(
    prompt="daily inspiration quote",
    interval_hours=24,
    style="inspirational",
    theme="motivation"
)

print(f"📅 Scheduled job: {job_id}")
```

### Advanced Scheduling

```python
from scheduler import schedule_instagram_publishing, get_scheduler
from datetime import datetime, timedelta

# Schedule specific post
publish_time = datetime.now() + timedelta(hours=2)
job_id = schedule_instagram_publishing(
    image_path="/path/to/image.png",
    caption="Scheduled post caption #scheduled",
    publish_time=publish_time
)

# Manage scheduled jobs
scheduler = get_scheduler()

# List all jobs
jobs = scheduler.get_all_jobs()
print(f"📅 Active jobs: {len(jobs)}")

# Get job details
job_info = scheduler.get_job_info(job_id)
if job_info:
    print(f"Next run: {job_info['next_run']}")

# Remove job
scheduler.remove_job(job_id)
```

### Scheduling Patterns

```python
# Daily content at 9 AM
from scheduler import get_scheduler
from datetime import time

scheduler = get_scheduler()

# Using cron-style scheduling
job_id = scheduler.add_job(
    function=generate_daily_content,
    job_type=JobType.CONTENT_GENERATION,
    trigger_type="cron",
    hour=9,
    minute=0
)

# Weekly content on Mondays
job_id = scheduler.add_job(
    function=generate_weekly_content,
    job_type=JobType.CONTENT_GENERATION,
    trigger_type="cron",
    day_of_week=0,  # Monday
    hour=10,
    minute=0
)

# Interval-based scheduling
job_id = scheduler.add_job(
    function=generate_content,
    job_type=JobType.CONTENT_GENERATION,
    trigger_type="interval",
    hours=6  # Every 6 hours
)
```

## 🎯 Advanced Usage Patterns

### Batch Content Generation

```python
from main import AISocials
from concurrent.futures import ThreadPoolExecutor
import json

def generate_content_batch(prompts):
    """Generate multiple pieces of content in parallel."""
    app = AISocials()
    
    def generate_single(prompt_data):
        return app.generate_content(
            prompt=prompt_data['prompt'],
            style=prompt_data.get('style', 'engaging'),
            theme=prompt_data.get('theme')
        )
    
    # Use thread pool for parallel generation
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(generate_single, prompts))
    
    return results

# Example usage
prompts = [
    {'prompt': 'sunrise over ocean', 'style': 'peaceful', 'theme': 'nature'},
    {'prompt': 'busy city street', 'style': 'dynamic', 'theme': 'urban'},
    {'prompt': 'cozy reading nook', 'style': 'warm', 'theme': 'lifestyle'}
]

results = generate_content_batch(prompts)

# Save results
with open('batch_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print(f"Generated {len(results)} pieces of content")
```

### Content Campaigns

```python
class ContentCampaign:
    """Manage a series of related content."""
    
    def __init__(self, theme, style="engaging"):
        self.theme = theme
        self.style = style
        self.app = AISocials()
        self.content_pieces = []
    
    def add_content_idea(self, prompt, scheduled_time=None):
        """Add content idea to campaign."""
        self.content_pieces.append({
            'prompt': prompt,
            'scheduled_time': scheduled_time,
            'generated': False
        })
    
    def generate_all(self):
        """Generate all content in campaign."""
        for piece in self.content_pieces:
            if not piece['generated']:
                result = self.app.generate_content(
                    prompt=piece['prompt'],
                    style=self.style,
                    theme=self.theme
                )
                piece['result'] = result
                piece['generated'] = True
    
    def schedule_publishing(self):
        """Schedule all content for publishing."""
        from scheduler import schedule_instagram_publishing
        
        for piece in self.content_pieces:
            if piece['generated'] and piece['scheduled_time']:
                job_id = schedule_instagram_publishing(
                    image_path=piece['result']['image']['image_path'],
                    caption=piece['result']['caption']['full_caption'],
                    publish_time=piece['scheduled_time']
                )
                piece['job_id'] = job_id

# Example campaign
campaign = ContentCampaign(theme="fitness", style="motivational")

# Add content ideas
from datetime import datetime, timedelta
base_time = datetime.now() + timedelta(days=1)

campaign.add_content_idea(
    "morning workout routine",
    scheduled_time=base_time
)
campaign.add_content_idea(
    "healthy breakfast prep",
    scheduled_time=base_time + timedelta(hours=8)
)
campaign.add_content_idea(
    "evening yoga session",
    scheduled_time=base_time + timedelta(hours=16)
)

# Generate and schedule
campaign.generate_all()
campaign.schedule_publishing()
```

### A/B Testing Content

```python
class ContentABTest:
    """A/B test different content variations."""
    
    def __init__(self, base_prompt):
        self.base_prompt = base_prompt
        self.variations = []
        self.app = AISocials()
    
    def add_variation(self, style, theme=None):
        """Add a content variation."""
        self.variations.append({
            'style': style,
            'theme': theme,
            'content': None,
            'performance': None
        })
    
    def generate_variations(self):
        """Generate all variations."""
        for variation in self.variations:
            result = self.app.generate_content(
                prompt=self.base_prompt,
                style=variation['style'],
                theme=variation['theme']
            )
            variation['content'] = result
    
    def publish_variation(self, index):
        """Publish a specific variation."""
        if index < len(self.variations):
            variation = self.variations[index]
            if variation['content']:
                result = self.app.publish_content(
                    image_path=variation['content']['image']['image_path'],
                    caption=variation['content']['caption']['full_caption']
                )
                variation['post_id'] = result.get('post_id')
                return result

# Example A/B test
ab_test = ContentABTest("coffee shop atmosphere")

# Add variations
ab_test.add_variation(style="cozy", theme="lifestyle")
ab_test.add_variation(style="professional", theme="business")
ab_test.add_variation(style="artistic", theme="creativity")

# Generate all variations
ab_test.generate_variations()

# Publish variation A
result_a = ab_test.publish_variation(0)
print(f"Published variation A: {result_a.get('post_id')}")
```

## 🔧 Configuration Examples

### Environment-Specific Usage

```python
import os
from config import get_config

# Development environment
os.environ['ENVIRONMENT'] = 'development'
os.environ['DEBUG'] = 'true'
config = get_config()

# Use faster, cheaper models for development
app = AISocials()
result = app.generate_content(
    prompt="test content",
    style="casual"
)

# Production environment
os.environ['ENVIRONMENT'] = 'production'
os.environ['DEBUG'] = 'false'
config = get_config()

# Use high-quality models for production
app = AISocials()
result = app.generate_content(
    prompt="premium content",
    style="professional",
    image_options={
        "quality": "hd",
        "size": "1792x1024"
    }
)
```

### Custom Configuration

```python
# Custom output directory
os.environ['CONTENT_OUTPUT_DIR'] = '/custom/path/content'

# Custom model selection
os.environ['OPENAI_MODEL_CHAT'] = 'gpt-4'
os.environ['OPENAI_MODEL_IMAGE'] = 'dall-e-3'

# Custom caption settings
os.environ['CONTENT_MAX_CAPTION_LENGTH'] = '1500'
os.environ['CONTENT_HASHTAG_COUNT'] = '15'

# Use Ollama for captions
os.environ['CAPTION_GENERATOR'] = 'ollama'
os.environ['OLLAMA_MODEL'] = 'llama2:13b'
```

## 🧪 Testing and Validation

### Content Quality Testing

```python
def test_content_quality(prompt, min_quality_score=0.7):
    """Test content generation quality."""
    app = AISocials()
    
    # Generate content
    result = app.generate_content(prompt=prompt)
    
    if not result.get('success'):
        return False, "Generation failed"
    
    # Check image quality
    image_path = result['image']['image_path']
    if not os.path.exists(image_path):
        return False, "Image file not found"
    
    # Check caption quality
    caption = result['caption']['full_caption']
    if len(caption) < 50:
        return False, "Caption too short"
    
    if len(result['caption']['hashtags']) < 5:
        return False, "Not enough hashtags"
    
    return True, "Quality check passed"

# Test various prompts
test_prompts = [
    "beautiful landscape",
    "modern architecture",
    "delicious food",
    "happy people"
]

for prompt in test_prompts:
    passed, message = test_content_quality(prompt)
    print(f"{'✅' if passed else '❌'} {prompt}: {message}")
```

### Performance Testing

```python
import time
from statistics import mean

def benchmark_generation(prompt, iterations=5):
    """Benchmark content generation performance."""
    app = AISocials()
    times = []
    
    for i in range(iterations):
        start_time = time.time()
        
        result = app.generate_content(prompt=prompt)
        
        end_time = time.time()
        generation_time = end_time - start_time
        times.append(generation_time)
        
        print(f"Iteration {i+1}: {generation_time:.2f}s")
    
    avg_time = mean(times)
    print(f"Average generation time: {avg_time:.2f}s")
    
    return avg_time

# Benchmark different scenarios
print("🔬 Benchmarking content generation...")
benchmark_generation("simple landscape", iterations=3)
benchmark_generation("complex scene with multiple elements", iterations=3)
```

## 📊 Monitoring and Analytics

### Usage Statistics

```python
from utils.exceptions import get_error_stats
from utils.security import get_rate_limiter

def get_usage_stats():
    """Get application usage statistics."""
    # Error statistics
    error_stats = get_error_stats()
    
    # Rate limiting statistics
    rate_limiter = get_rate_limiter()
    rate_stats = rate_limiter.get_stats()
    
    # Content generation statistics
    # (This would be implemented with actual metrics collection)
    
    return {
        'errors': error_stats,
        'rate_limiting': rate_stats,
        'uptime': "99.9%",  # Example
        'total_content_generated': 1234,  # Example
        'total_posts_published': 567  # Example
    }

# Display statistics
stats = get_usage_stats()
print("📊 Usage Statistics:")
print(f"Total errors: {sum(stats['errors'].values())}")
print(f"Active rate limits: {stats['rate_limiting']['active_limits']}")
```

### Health Monitoring

```python
def health_check():
    """Perform comprehensive health check."""
    app = AISocials()
    
    checks = {
        'configuration': False,
        'openai_connection': False,
        'instagram_connection': False,
        'file_system': False
    }
    
    # Configuration check
    try:
        if app.validate_setup():
            checks['configuration'] = True
    except Exception:
        pass
    
    # OpenAI connection check
    try:
        # Test with minimal request
        result = app.generate_content(prompt="test", style="casual")
        if result.get('success'):
            checks['openai_connection'] = True
    except Exception:
        pass
    
    # Instagram connection check
    try:
        if app.instagram_publisher:
            result = app.instagram_publisher.test_connection()
            if result.get('connected'):
                checks['instagram_connection'] = True
    except Exception:
        pass
    
    # File system check
    try:
        import tempfile
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"test")
            checks['file_system'] = True
    except Exception:
        pass
    
    return checks

# Run health check
health = health_check()
print("🏥 Health Check:")
for check, status in health.items():
    print(f"{'✅' if status else '❌'} {check}")
```

## 🎨 Creative Usage Examples

### Themed Content Series

```python
def create_themed_series(theme, count=7):
    """Create a week's worth of themed content."""
    app = AISocials()
    
    # Define prompts for the theme
    theme_prompts = {
        'nature': [
            'sunrise over mountains',
            'peaceful forest path',
            'ocean waves at sunset',
            'wildflower meadow',
            'starry night sky',
            'morning dew on leaves',
            'rainbow after storm'
        ],
        'food': [
            'fresh breakfast spread',
            'colorful salad bowl',
            'homemade pasta dish',
            'artisan coffee setup',
            'dessert presentation',
            'farmers market produce',
            'cozy dinner setting'
        ]
    }
    
    prompts = theme_prompts.get(theme, [f"{theme} content {i}" for i in range(count)])
    
    series_content = []
    for i, prompt in enumerate(prompts[:count]):
        result = app.generate_content(
            prompt=prompt,
            style="engaging",
            theme=theme
        )
        
        if result.get('success'):
            series_content.append({
                'day': i + 1,
                'prompt': prompt,
                'content': result
            })
    
    return series_content

# Create nature series
nature_series = create_themed_series('nature', count=7)
print(f"Created {len(nature_series)} pieces for nature series")
```

### Seasonal Content

```python
from datetime import datetime

def get_seasonal_prompt():
    """Get season-appropriate content prompt."""
    month = datetime.now().month
    
    seasonal_prompts = {
        'spring': [
            'cherry blossoms in bloom',
            'spring garden awakening',
            'fresh green leaves',
            'spring rain shower'
        ],
        'summer': [
            'beach day vibes',
            'summer picnic setup',
            'ice cream on hot day',
            'outdoor adventure'
        ],
        'autumn': [
            'colorful fall leaves',
            'cozy sweater weather',
            'pumpkin spice everything',
            'harvest season'
        ],
        'winter': [
            'snow-covered landscape',
            'warm fireplace scene',
            'hot cocoa moment',
            'winter wonderland'
        ]
    }
    
    if month in [3, 4, 5]:
        season = 'spring'
    elif month in [6, 7, 8]:
        season = 'summer'
    elif month in [9, 10, 11]:
        season = 'autumn'
    else:
        season = 'winter'
    
    import random
    return random.choice(seasonal_prompts[season])

# Generate seasonal content
seasonal_prompt = get_seasonal_prompt()
app = AISocials()
result = app.generate_content(
    prompt=seasonal_prompt,
    style="seasonal",
    theme="nature"
)
```

## 📚 Best Practices

### Content Quality

1. **Use Descriptive Prompts**
   ```python
   # Good: Specific and descriptive
   prompt = "golden hour portrait of a smiling woman in a sunflower field"
   
   # Avoid: Too vague
   prompt = "person outside"
   ```

2. **Match Style to Content**
   ```python
   # Business content
   app.generate_content(prompt="office meeting", style="professional")
   
   # Personal content
   app.generate_content(prompt="weekend brunch", style="casual")
   
   # Motivational content
   app.generate_content(prompt="morning workout", style="inspirational")
   ```

3. **Use Themes for Better Hashtags**
   ```python
   # Theme helps generate relevant hashtags
   app.generate_content(
       prompt="yoga session",
       style="peaceful",
       theme="wellness"  # Generates wellness-related hashtags
   )
   ```

### Performance Optimization

1. **Batch Operations**
   ```python
   # Generate multiple pieces efficiently
   prompts = ["prompt1", "prompt2", "prompt3"]
   results = []
   
   for prompt in prompts:
       result = app.generate_content(prompt=prompt)
       results.append(result)
       time.sleep(1)  # Rate limiting
   ```

2. **Error Handling**
   ```python
   try:
       result = app.generate_content(prompt="complex prompt")
   except ContentGenerationError as e:
       print(f"Generation failed: {e.message}")
       # Fallback to simpler prompt
       result = app.generate_content(prompt="simple fallback")
   ```

3. **Resource Management**
   ```python
   # Clean up old content periodically
   import os
   import time
   
   content_dir = "generated_content"
   max_age = 7 * 24 * 3600  # 7 days
   
   for filename in os.listdir(content_dir):
       filepath = os.path.join(content_dir, filename)
       if os.path.getmtime(filepath) < time.time() - max_age:
           os.remove(filepath)
   ```

---

## 📞 Support

For usage questions and support:

- **Documentation**: Check [API Documentation](api.md) for detailed API reference
- **Troubleshooting**: See [Troubleshooting Guide](troubleshooting.md) for common issues
- **Configuration**: Review [Configuration Reference](configuration.md) for setup options
- **Development**: See [Development Guide](development.md) for contributing

**Need more examples?** Check our [GitHub repository](https://github.com/project/ai-socials) for additional usage examples and community contributions!