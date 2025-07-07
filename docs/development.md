# Development Guide

## 📋 Overview

This guide covers everything you need to know to contribute to AI Socials, including development setup, coding standards, testing procedures, and contribution workflows.

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **Git** for version control
- **GitHub account** for contributions
- **Code editor** (VS Code, PyCharm, etc.)

### Development Setup

#### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/ai-socials.git
cd ai-socials

# Add upstream remote
git remote add upstream https://github.com/original-owner/ai-socials.git
```

#### 2. Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install development dependencies
pip install -e .[dev,test]

# Install pre-commit hooks
pre-commit install
```

#### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Add your development API keys
# Note: Use test/development keys, not production
```

#### 4. Verify Setup

```bash
# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy .

# Validate setup
python main.py --validate-only
```

## 🏗️ Project Structure

### Directory Layout

```
ai-socials/
├── 📁 docs/                    # Documentation
│   ├── README.md               # Main documentation
│   ├── installation.md         # Setup guide
│   ├── configuration.md        # Config reference
│   ├── api.md                  # API documentation
│   ├── troubleshooting.md      # Troubleshooting
│   └── development.md          # This file
├── 📁 generator/               # Content generation
│   ├── __init__.py
│   ├── caption_generator.py    # OpenAI captions
│   ├── ollama_caption_generator.py  # Ollama captions
│   └── image_generator.py      # Image generation
├── 📁 publisher/               # Publishing system
│   ├── __init__.py
│   └── instagram_publisher.py  # Instagram API
├── 📁 reviewer/                # Content review
│   ├── __init__.py
│   ├── telegram_bot.py         # Telegram bot
│   └── web_interface.py        # Web review
├── 📁 scheduler/               # Job scheduling
│   ├── __init__.py
│   └── scheduler.py            # APScheduler
├── 📁 utils/                   # Utilities
│   ├── __init__.py
│   ├── container.py            # Dependency injection
│   ├── exceptions.py           # Error handling
│   ├── logger.py               # Logging system
│   └── security.py             # Security utilities
├── 📁 tests/                   # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── fixtures/               # Test fixtures
├── 📁 scripts/                 # Utility scripts
├── 📁 generated_content/       # Generated files
├── 📁 logs/                    # Log files
├── main.py                     # Main application
├── config.py                   # Configuration
├── pyproject.toml              # Project config
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── .pre-commit-config.yaml     # Pre-commit hooks
└── README.md                   # Project overview
```

### Module Architecture

```python
# Core application flow
main.py (AISocials)
├── config.py (Configuration)
├── generator/ (Content Generation)
│   ├── Image Generation (OpenAI DALL-E)
│   └── Caption Generation (OpenAI/Ollama)
├── publisher/ (Publishing)
│   └── Instagram API Integration
├── reviewer/ (Content Review)
│   ├── Telegram Bot
│   └── Web Interface
├── scheduler/ (Job Management)
│   └── APScheduler Integration
└── utils/ (Shared Utilities)
    ├── Dependency Injection
    ├── Error Handling
    ├── Logging
    └── Security
```

## 📝 Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

```python
# Line length: 100 characters (not 79)
# Use double quotes for strings
# Use type hints for all functions
# Use docstrings for all public functions/classes

def generate_content(
    prompt: str,
    style: str = "engaging",
    theme: Optional[str] = None
) -> Dict[str, Any]:
    """Generate AI content with image and caption.
    
    Args:
        prompt: Content generation prompt
        style: Caption style preference
        theme: Optional content theme
        
    Returns:
        Dictionary containing generated content
        
    Raises:
        ContentGenerationError: If generation fails
    """
    # Implementation here
    pass
```

### Code Formatting

We use **Black** for code formatting:

```bash
# Format all code
black .

# Check formatting
black --check .

# Format specific file
black main.py
```

### Linting

We use **Ruff** for fast linting:

```bash
# Lint all code
ruff check .

# Fix auto-fixable issues
ruff check . --fix

# Lint specific file
ruff check main.py
```

### Type Checking

We use **mypy** for static type checking:

```bash
# Type check all code
mypy .

# Type check specific file
mypy main.py

# Generate type coverage report
mypy --html-report mypy-report .
```

### Import Organization

```python
# Standard library imports
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Third-party imports
import requests
from openai import OpenAI
from telegram import Update

# Local imports
from config import get_config
from utils.logger import get_logger
from utils.exceptions import ContentGenerationError
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                       # Unit tests
│   ├── test_config.py
│   ├── test_generator.py
│   ├── test_publisher.py
│   └── test_utils.py
├── integration/                # Integration tests
│   ├── test_content_pipeline.py
│   ├── test_api_integration.py
│   └── test_end_to_end.py
├── fixtures/                   # Test data
│   ├── sample_images/
│   ├── sample_configs/
│   └── mock_responses/
└── conftest.py                 # Pytest configuration
```

### Writing Tests

#### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from generator.caption_generator import CaptionGenerator
from utils.exceptions import ContentGenerationError

class TestCaptionGenerator:
    """Test suite for caption generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = CaptionGenerator()
    
    def test_generate_caption_success(self):
        """Test successful caption generation."""
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{'message': {'content': 'Test caption'}}]
            }
            
            result = self.generator.generate_caption("test prompt")
            
            assert result['success'] is True
            assert 'Test caption' in result['full_caption']
            mock_openai.assert_called_once()
    
    def test_generate_caption_api_error(self):
        """Test caption generation with API error."""
        with patch('openai.ChatCompletion.create') as mock_openai:
            mock_openai.side_effect = Exception("API Error")
            
            with pytest.raises(ContentGenerationError):
                self.generator.generate_caption("test prompt")
    
    @pytest.mark.parametrize("style,expected", [
        ("engaging", "engaging"),
        ("professional", "professional"),
        ("casual", "casual"),
    ])
    def test_caption_styles(self, style, expected):
        """Test different caption styles."""
        # Test implementation
        pass
```

#### Integration Tests

```python
import pytest
from main import AISocials

class TestContentPipeline:
    """Integration tests for content generation pipeline."""
    
    @pytest.mark.integration
    def test_full_content_generation(self):
        """Test complete content generation flow."""
        app = AISocials()
        
        result = app.generate_content(
            prompt="test sunset",
            style="engaging"
        )
        
        assert result.get('success') is True
        assert 'image' in result
        assert 'caption' in result
    
    @pytest.mark.external
    def test_openai_integration(self):
        """Test actual OpenAI API integration."""
        # Only run with real API keys
        pass
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m external       # External API tests

# Run specific test file
pytest tests/unit/test_generator.py

# Run specific test
pytest tests/unit/test_generator.py::TestCaptionGenerator::test_generate_caption_success

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Test Configuration

```python
# conftest.py
import pytest
from unittest.mock import Mock
from config import Config

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock(spec=Config)
    config.openai.api_key = "test_key"
    config.openai.model_chat = "gpt-4"
    config.debug = True
    return config

@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample image for testing."""
    from PIL import Image
    
    image = Image.new('RGB', (100, 100), color='red')
    image_path = tmp_path / "test_image.png"
    image.save(image_path)
    return str(image_path)

# Pytest markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.external = pytest.mark.external
pytest.mark.slow = pytest.mark.slow
```

## 🔧 Development Workflow

### Git Workflow

We use **GitHub Flow** with feature branches:

```bash
# 1. Update main branch
git checkout main
git pull upstream main

# 2. Create feature branch
git checkout -b feature/add-new-generator

# 3. Make changes and commit
git add .
git commit -m "feat: add new content generator"

# 4. Push to your fork
git push origin feature/add-new-generator

# 5. Create Pull Request on GitHub
```

### Commit Messages

We follow **Conventional Commits**:

```bash
# Format: type(scope): description

# Types:
feat: new feature
fix: bug fix
docs: documentation changes
style: formatting changes
refactor: code refactoring
test: adding tests
chore: maintenance tasks

# Examples:
feat(generator): add Ollama caption generator
fix(publisher): handle Instagram API rate limits
docs(api): update API documentation
test(generator): add unit tests for image generation
refactor(utils): improve error handling
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation if needed

3. **Pre-commit Checks**
   ```bash
   # These run automatically with pre-commit hooks
   black .                    # Format code
   ruff check . --fix        # Lint and fix
   mypy .                    # Type check
   pytest                    # Run tests
   ```

4. **Create Pull Request**
   - Use descriptive title and description
   - Reference related issues
   - Add screenshots for UI changes
   - Request review from maintainers

5. **Address Review Comments**
   - Make requested changes
   - Push updates to the same branch
   - Respond to reviewer comments

6. **Merge**
   - Maintainer will merge after approval
   - Branch will be automatically deleted

### Code Review Guidelines

#### For Authors

- **Keep PRs small** and focused on one feature/fix
- **Write clear descriptions** explaining what and why
- **Add tests** for new functionality
- **Update documentation** when needed
- **Respond promptly** to review comments

#### For Reviewers

- **Be constructive** and helpful in feedback
- **Focus on code quality**, not personal preferences
- **Check for edge cases** and error handling
- **Verify tests** cover the changes
- **Approve quickly** when changes look good

## 🏗️ Architecture Guidelines

### Design Principles

1. **Separation of Concerns**
   - Each module has a single responsibility
   - Clear interfaces between components
   - Minimal coupling between modules

2. **Dependency Injection**
   - Use the container system for dependencies
   - Avoid global state and singletons
   - Make components easily testable

3. **Error Handling**
   - Use custom exception classes
   - Implement proper error recovery
   - Log errors with context

4. **Configuration Management**
   - Centralized configuration system
   - Environment-specific settings
   - Validation and type safety

### Adding New Features

#### 1. Content Generators

```python
# generator/new_generator.py
from typing import Dict, Any
from utils.container import ICaptionGenerator
from utils.exceptions import ContentGenerationError

class NewCaptionGenerator(ICaptionGenerator):
    """New caption generator implementation."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def generate_caption(
        self,
        prompt: str,
        style: str = "engaging",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate caption using new service."""
        try:
            # Implementation here
            return {
                'success': True,
                'full_caption': generated_caption,
                'metadata': {...}
            }
        except Exception as e:
            raise ContentGenerationError(
                f"New generator failed: {str(e)}",
                content_type="caption"
            )
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to new service."""
        # Implementation here
        pass

# Register in container (utils/container.py)
def _setup_generators(self):
    if self.config.caption_generator == "new_service":
        self.register_singleton(
            ICaptionGenerator,
            NewCaptionGenerator()
        )
```

#### 2. Publishers

```python
# publisher/new_publisher.py
from typing import Dict, Any
from utils.exceptions import PublishingError

class NewPlatformPublisher:
    """Publisher for new social media platform."""
    
    def publish_post(
        self,
        content_path: str,
        caption: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Publish content to new platform."""
        try:
            # Implementation here
            return {
                'success': True,
                'post_id': platform_post_id,
                'metadata': {...}
            }
        except Exception as e:
            raise PublishingError(
                f"Publishing to new platform failed: {str(e)}",
                platform="NewPlatform"
            )
```

#### 3. Configuration

```python
# config.py - Add new configuration section
@dataclass
class NewServiceConfig:
    """Configuration for new service."""
    api_key: Optional[str] = None
    endpoint: str = "https://api.newservice.com"
    timeout: int = 30
    
    def __post_init__(self):
        if self.api_key and not self.api_key.startswith('ns_'):
            raise ConfigurationError("Invalid new service API key format")

# Add to main Config class
@dataclass
class Config:
    # ... existing fields ...
    new_service: NewServiceConfig = field(default_factory=NewServiceConfig)
```

### Performance Considerations

1. **Async Operations**
   - Use async/await for I/O operations
   - Implement proper connection pooling
   - Handle timeouts gracefully

2. **Caching**
   - Cache expensive operations
   - Implement cache invalidation
   - Use appropriate cache backends

3. **Resource Management**
   - Clean up resources properly
   - Monitor memory usage
   - Implement rate limiting

## 📚 Documentation

### Writing Documentation

1. **Code Documentation**
   ```python
   def complex_function(param1: str, param2: int) -> Dict[str, Any]:
       """Brief description of what the function does.
       
       Longer description if needed, explaining the purpose,
       algorithm, or important details.
       
       Args:
           param1: Description of first parameter
           param2: Description of second parameter
           
       Returns:
           Dictionary containing:
               - key1: Description of key1
               - key2: Description of key2
               
       Raises:
           ValueError: When param1 is invalid
           CustomError: When specific condition occurs
           
       Example:
           >>> result = complex_function("test", 42)
           >>> print(result['key1'])
           'expected_value'
       """
   ```

2. **API Documentation**
   - Update `docs/api.md` for new endpoints
   - Include request/response examples
   - Document error conditions

3. **User Documentation**
   - Update relevant guides in `docs/`
   - Add configuration examples
   - Include troubleshooting tips

### Documentation Standards

- Use **Markdown** for all documentation
- Include **code examples** for complex features
- Add **screenshots** for UI features
- Keep documentation **up to date** with code changes
- Use **clear, concise language**

## 🔒 Security Guidelines

### Secure Coding Practices

1. **Input Validation**
   ```python
   from utils.security import get_input_validator
   
   validator = get_input_validator()
   result = validator.validate(user_input, "prompt")
   if not result['valid']:
       raise ValidationError(result['error'])
   ```

2. **API Key Management**
   ```python
   # Never hardcode API keys
   # Use environment variables
   api_key = os.getenv('OPENAI_API_KEY')
   
   # Validate key format
   if not api_key or not api_key.startswith('sk-'):
       raise ConfigurationError("Invalid OpenAI API key")
   ```

3. **Error Handling**
   ```python
   # Don't expose sensitive information in errors
   try:
       result = api_call(api_key)
   except Exception as e:
       # Log full error internally
       logger.error(f"API call failed: {str(e)}", extra={'api_key_prefix': api_key[:10]})
       # Return generic error to user
       raise APIError("Service temporarily unavailable")
   ```

### Security Checklist

- [ ] Input validation for all user inputs
- [ ] API keys stored securely
- [ ] Error messages don't expose sensitive data
- [ ] Rate limiting implemented
- [ ] Audit logging for sensitive operations
- [ ] Dependencies regularly updated
- [ ] Security tests included

## 🚀 Release Process

### Version Management

We use **Semantic Versioning** (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

```bash
# Update version in pyproject.toml
version = "1.2.3"

# Create release tag
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
```

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] Changelog updated
- [ ] Security review completed
- [ ] Performance testing done
- [ ] Release notes prepared

## 🤝 Community Guidelines

### Code of Conduct

- **Be respectful** and inclusive
- **Help others** learn and grow
- **Give constructive feedback**
- **Focus on the code**, not the person
- **Assume good intentions**

### Getting Help

1. **Check documentation** first
2. **Search existing issues** on GitHub
3. **Ask in discussions** for general questions
4. **Create an issue** for bugs or feature requests
5. **Join community channels** for real-time help

### Contributing Areas

We welcome contributions in:

- **Code**: New features, bug fixes, optimizations
- **Documentation**: Guides, tutorials, API docs
- **Testing**: Unit tests, integration tests, manual testing
- **Design**: UI/UX improvements, graphics
- **Community**: Helping others, organizing events

## 📞 Support

### Development Support

- **GitHub Discussions**: General development questions
- **GitHub Issues**: Bug reports and feature requests
- **Discord/Slack**: Real-time development chat
- **Email**: Direct contact for sensitive issues

### Maintainer Contact

- **Lead Maintainer**: @username
- **Core Team**: @team-handle
- **Security Issues**: security@project.com

---

## 📚 Additional Resources

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Conventional Commits](https://conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Semantic Versioning](https://semver.org/)
- [pytest Documentation](https://docs.pytest.org/)

**Ready to contribute?** Start by checking our [good first issues](https://github.com/project/ai-socials/labels/good%20first%20issue) on GitHub!