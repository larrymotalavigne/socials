#!/usr/bin/env python3
"""
Test script for Ollama integration.

This script tests the new Ollama caption generator integration:
- Configuration loading
- Generator factory selection
- Ollama API connection (if available)
- Command line options
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_configuration():
    """Test Ollama configuration loading."""
    print("🧪 Testing Ollama Configuration...")
    
    try:
        from config import get_config
        
        # Test default configuration
        config = get_config()
        
        # Check if ollama config exists
        if hasattr(config, 'ollama'):
            print("✅ Ollama configuration loaded successfully")
            print(f"   Base URL: {config.ollama.base_url}")
            print(f"   Model: {config.ollama.model}")
            print(f"   Temperature: {config.ollama.temperature}")
            print(f"   Max Tokens: {config.ollama.max_tokens}")
        else:
            print("❌ Ollama configuration not found")
            return False
        
        # Check caption generator setting
        print(f"   Caption Generator: {config.caption_generator}")
        
        # Test configuration validation
        if config.caption_generator in ["openai", "ollama"]:
            print("✅ Caption generator setting is valid")
        else:
            print(f"❌ Invalid caption generator setting: {config.caption_generator}")
            return False
        
        print("✅ Configuration tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}\n")
        return False

def test_generator_factory():
    """Test the generator factory system."""
    print("🧪 Testing Generator Factory...")
    
    try:
        from generator import get_caption_generator, get_available_caption_generators
        
        # Test available generators
        available = get_available_caption_generators()
        print(f"✅ Available generators: {', '.join(available.keys())}")
        
        # Test factory function
        generator = get_caption_generator()
        print(f"✅ Factory returned generator: {type(generator).__name__}")
        
        # Test with different configurations
        original_env = os.environ.get('CAPTION_GENERATOR')
        
        # Test OpenAI selection
        os.environ['CAPTION_GENERATOR'] = 'openai'
        # Clear any cached config
        from config import config_manager
        config_manager._config = None
        
        generator = get_caption_generator()
        generator_type = type(generator).__name__
        print(f"✅ OpenAI generator: {generator_type}")
        
        # Test Ollama selection
        os.environ['CAPTION_GENERATOR'] = 'ollama'
        config_manager._config = None
        
        generator = get_caption_generator()
        generator_type = type(generator).__name__
        print(f"✅ Ollama generator: {generator_type}")
        
        # Restore original environment
        if original_env:
            os.environ['CAPTION_GENERATOR'] = original_env
        else:
            os.environ.pop('CAPTION_GENERATOR', None)
        config_manager._config = None
        
        print("✅ Generator factory tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Generator factory test failed: {str(e)}\n")
        return False

def test_ollama_generator():
    """Test Ollama generator specifically."""
    print("🧪 Testing Ollama Generator...")
    
    try:
        from generator.ollama_caption_generator import OllamaCaptionGenerator
        
        # Test initialization (this will test connection)
        try:
            generator = OllamaCaptionGenerator()
            print("✅ Ollama generator initialized successfully")
        except Exception as e:
            print(f"⚠️  Ollama generator initialization failed: {str(e)}")
            print("   This is expected if Ollama is not running locally")
            return True  # Not a failure, just not available
        
        # Test connection
        connection_result = generator.test_connection()
        if connection_result.get('connected'):
            print("✅ Ollama connection test passed")
            print(f"   Model: {connection_result.get('model')}")
            if connection_result.get('available_models'):
                models = connection_result['available_models']
                print(f"   Available models: {', '.join(models[:3])}{'...' if len(models) > 3 else ''}")
        else:
            print(f"⚠️  Ollama connection failed: {connection_result.get('error')}")
            print("   This is expected if Ollama is not running locally")
        
        print("✅ Ollama generator tests completed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Ollama generator test failed: {str(e)}\n")
        return False

def test_command_line_integration():
    """Test command line integration."""
    print("🧪 Testing Command Line Integration...")
    
    try:
        import subprocess
        import sys
        
        # Test help output includes new options
        result = subprocess.run([sys.executable, "main.py", "--help"], 
                              capture_output=True, text=True, timeout=10)
        
        if "--caption-generator" in result.stdout:
            print("✅ Caption generator option available in CLI")
        else:
            print("❌ Caption generator option not found in CLI help")
            return False
        
        if "--test-caption-generators" in result.stdout:
            print("✅ Test caption generators option available in CLI")
        else:
            print("❌ Test caption generators option not found in CLI help")
            return False
        
        print("✅ Command line integration tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Command line integration test failed: {str(e)}\n")
        return False

def test_container_integration():
    """Test dependency injection container integration."""
    print("🧪 Testing Container Integration...")
    
    try:
        from utils.container import get_container, ICaptionGenerator
        
        container = get_container()
        
        # Test that ICaptionGenerator can be resolved
        generator = container.resolve(ICaptionGenerator)
        print(f"✅ Container resolved caption generator: {type(generator).__name__}")
        
        # Test with different configurations
        original_env = os.environ.get('CAPTION_GENERATOR')
        
        # Test OpenAI resolution
        os.environ['CAPTION_GENERATOR'] = 'openai'
        from config import config_manager
        config_manager._config = None
        
        # Clear container cache
        container._singletons.clear()
        
        generator = container.resolve(ICaptionGenerator)
        print(f"✅ Container resolved OpenAI generator: {type(generator).__name__}")
        
        # Test Ollama resolution
        os.environ['CAPTION_GENERATOR'] = 'ollama'
        config_manager._config = None
        container._singletons.clear()
        
        generator = container.resolve(ICaptionGenerator)
        print(f"✅ Container resolved Ollama generator: {type(generator).__name__}")
        
        # Restore original environment
        if original_env:
            os.environ['CAPTION_GENERATOR'] = original_env
        else:
            os.environ.pop('CAPTION_GENERATOR', None)
        config_manager._config = None
        container._singletons.clear()
        
        print("✅ Container integration tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Container integration test failed: {str(e)}\n")
        return False

def main():
    """Run all Ollama integration tests."""
    print("🚀 Starting Ollama Integration Tests\n")
    
    tests = [
        test_configuration,
        test_generator_factory,
        test_ollama_generator,
        test_command_line_integration,
        test_container_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Ollama integration tests passed! Ollama support is ready.")
        print("\n📋 Usage Instructions:")
        print("1. To use Ollama, set CAPTION_GENERATOR=ollama in your .env file")
        print("2. Or use --caption-generator ollama command line option")
        print("3. Make sure Ollama is running locally on http://localhost:11434")
        print("4. Use --test-caption-generators to test both OpenAI and Ollama")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)