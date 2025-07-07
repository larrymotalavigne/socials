# Installation Guide

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 2GB free space

### Required Accounts & API Keys
- **OpenAI Account**: For image and caption generation
  - Sign up at [OpenAI](https://platform.openai.com/)
  - Generate API key from the dashboard
- **Instagram Business Account**: For publishing (optional)
  - Convert personal account to business account
  - Set up Facebook Developer App for Instagram Graph API
- **Ollama** (optional): For local LLM support
  - Install from [Ollama website](https://ollama.ai/)

## 🚀 Quick Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd socials
```

### 2. Create Virtual Environment
```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using conda
conda create -n socials python=3.11
conda activate socials
```

### 3. Install Dependencies
```bash
# Basic installation
pip install -e .

# Development installation (includes testing and code quality tools)
pip install -e .[dev,test]

# Production installation with monitoring
pip install -e .[monitoring]
```

### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

### 5. Verify Installation
```bash
# Test basic functionality
python main.py --validate-only

# Test API connections
python main.py --test-all
```

## 🔧 Detailed Installation

### Environment Setup

#### Option 1: Using pip and venv
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the package
pip install -e .[dev,test]
```

#### Option 2: Using conda
```bash
# Create conda environment
conda create -n socials python=3.11
conda activate socials

# Install pip dependencies
pip install -e .[dev,test]
```

#### Option 3: Using Poetry (if available)
```bash
# Install dependencies with Poetry
poetry install --with dev,test
poetry shell
```

### Dependency Groups

The project uses optional dependency groups for different use cases:

```toml
# Core dependencies (always installed)
dependencies = [
    "openai>=1.0.0",
    "python-dotenv>=1.0.0",
    "requests>=2.25.0",
    # ... other core deps
]

# Development dependencies
[project.optional-dependencies]
dev = [
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    # ... other dev tools
]

# Testing dependencies
test = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    # ... other test tools
]

# Monitoring dependencies
monitoring = [
    "prometheus-client>=0.16.0",
    "psutil>=5.9.0",
    "structlog>=23.0.0",
]
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required - OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_CHAT=gpt-4
OPENAI_MODEL_IMAGE=dall-e-3
OPENAI_TEMPERATURE=0.8
OPENAI_MAX_TOKENS=150
OPENAI_IMAGE_SIZE=1024x1024
OPENAI_IMAGE_QUALITY=standard

# Optional - Ollama Configuration (for local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=30
OLLAMA_TEMPERATURE=0.8
OLLAMA_MAX_TOKENS=150

# Optional - Instagram Configuration
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
INSTAGRAM_USER_ID=your_instagram_user_id

# Optional - Telegram Configuration (for content review)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Application Configuration
ENVIRONMENT=development  # development, staging, production
DEBUG=true
CAPTION_GENERATOR=openai  # openai or ollama
CONTENT_OUTPUT_DIR=generated_content
CONTENT_HASHTAG_COUNT=10
CONTENT_MAX_CAPTION_LENGTH=2200

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log
LOG_MAX_FILE_SIZE=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Security Configuration
RETRY_ATTEMPTS=3
RETRY_DELAY=1.0
REQUEST_TIMEOUT=30

# Scheduling Configuration (optional)
SCHEDULING_ENABLED=false
SCHEDULING_INTERVAL_HOURS=24
SCHEDULING_MAX_POSTS_PER_DAY=3
SCHEDULING_TIMEZONE=UTC
```

### API Key Setup

#### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

#### Instagram API Setup
1. Create a Facebook Developer Account
2. Create a new Facebook App
3. Add Instagram Graph API product
4. Generate access tokens
5. Convert your Instagram account to Business account
6. Link your Instagram account to the Facebook App

#### Ollama Setup (Optional)
1. Install Ollama from [ollama.ai](https://ollama.ai/)
2. Pull a model: `ollama pull llama2`
3. Start Ollama service: `ollama serve`
4. Verify it's running on `http://localhost:11434`

## 🧪 Development Setup

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Code Quality Tools
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .

# Security scanning
bandit -r .

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html
```

### IDE Configuration

#### VS Code
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

#### PyCharm
1. Set Python interpreter to your virtual environment
2. Enable Black as code formatter
3. Configure Ruff as linter
4. Set pytest as test runner

## 🐳 Docker Installation (Optional)

### Using Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  socials:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - INSTAGRAM_ACCESS_TOKEN=${INSTAGRAM_ACCESS_TOKEN}
    volumes:
      - ./generated_content:/app/generated_content
      - ./logs:/app/logs
    ports:
      - "8000:8000"
```

```bash
# Build and run
docker-compose up --build
```

### Using Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .[monitoring]

CMD ["python", "main.py"]
```

## 🔍 Verification

### Test Installation
```bash
# Basic validation
python main.py --validate-only

# Test API connections
python main.py --test-openai
python main.py --test-instagram
python main.py --test-caption-generators

# Run demo
python main.py --prompt "test installation"
```

### Common Installation Issues

#### Issue: OpenAI API Key Invalid
```bash
# Verify your API key
python -c "
import openai
client = openai.OpenAI(api_key='your_key_here')
print('API key is valid')
"
```

#### Issue: Module Import Errors
```bash
# Reinstall in development mode
pip uninstall socials
pip install -e .
```

#### Issue: Permission Errors
```bash
# Fix permissions on Unix systems
chmod +x main.py
```

#### Issue: Ollama Connection Failed
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
ollama serve
```

## 📚 Next Steps

After successful installation:

1. **Read the [Configuration Guide](configuration.md)** for detailed configuration options
2. **Follow the [Usage Guide](usage.md)** to start generating content
3. **Review the [Security Guide](security.md)** for production deployment
4. **Check the [Development Guide](development.md)** if you plan to contribute

## 🆘 Getting Help

If you encounter issues during installation:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review the error logs in `logs/app.log`
3. Verify all environment variables are set correctly
4. Ensure all API keys are valid and have proper permissions
5. Check that all required services (OpenAI, Instagram, Ollama) are accessible

For additional support, please refer to the project's issue tracker or documentation.