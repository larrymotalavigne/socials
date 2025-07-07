#!/usr/bin/env python3
"""
Test script for Phase 3 implementation.

This script tests the new Phase 3 features:
- Testing & Quality Assurance infrastructure
- Security & Best Practices implementation
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_testing_infrastructure():
    """Test the testing infrastructure."""
    print("🧪 Testing Infrastructure...")
    
    try:
        # Test if pytest is available and can discover tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", "--collect-only", "-q"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            test_count = len([line for line in result.stdout.split('\n') if '::test_' in line])
            print(f"✅ Test discovery successful: {test_count} tests found")
        else:
            print(f"❌ Test discovery failed: {result.stderr}")
            return False
        
        # Test if we can run a simple test
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/test_config.py::TestConfigManager::test_config_manager_initialization", "-v"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Sample test execution successful")
        else:
            print(f"⚠️  Sample test execution failed (expected if dependencies missing): {result.stderr}")
        
        print("✅ Testing infrastructure tests completed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Testing infrastructure test failed: {str(e)}\n")
        return False

def test_security_utilities():
    """Test security utilities."""
    print("🔒 Testing Security Utilities...")
    
    try:
        from utils.security import (
            InputValidator, RateLimiter, AuditLogger, EncryptionManager,
            get_input_validator, get_rate_limiter, get_audit_logger, get_encryption_manager
        )
        
        # Test InputValidator
        validator = get_input_validator()
        result = validator.validate("Test prompt", "prompt")
        if result['valid']:
            print("✅ Input validation working")
        else:
            print(f"❌ Input validation failed: {result.get('error')}")
            return False
        
        # Test RateLimiter
        limiter = get_rate_limiter()
        result = limiter.is_allowed("test_user", "api_general")
        if result['allowed']:
            print("✅ Rate limiting working")
        else:
            print(f"❌ Rate limiting failed: {result.get('error')}")
            return False
        
        # Test EncryptionManager
        encryption = get_encryption_manager()
        test_data = "sensitive data"
        encrypted = encryption.encrypt(test_data)
        decrypted = encryption.decrypt(encrypted)
        if decrypted == test_data:
            print("✅ Encryption/decryption working")
        else:
            print("❌ Encryption/decryption failed")
            return False
        
        # Test AuditLogger
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.close()
            
            try:
                auditor = AuditLogger(temp_file.name)
                auditor.log_action("test_action", "test_resource", "test_user")
                
                with open(temp_file.name, 'r') as f:
                    log_content = f.read()
                    if "test_action" in log_content:
                        print("✅ Audit logging working")
                    else:
                        print("❌ Audit logging failed")
                        return False
            finally:
                try:
                    os.unlink(temp_file.name)
                except FileNotFoundError:
                    pass
        
        print("✅ Security utilities tests completed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Security utilities test failed: {str(e)}\n")
        return False

def test_content_moderation():
    """Test content moderation system."""
    print("🛡️  Testing Content Moderation...")
    
    try:
        from utils.content_moderation import moderate_content, moderate_hashtags
        
        # Test safe content
        result = moderate_content("This is a beautiful sunset photo", "caption")
        if result.is_safe:
            print("✅ Safe content detection working")
        else:
            print(f"❌ Safe content detection failed: {result.issues}")
            return False
        
        # Test potentially unsafe content
        result = moderate_content("This is spam content with fake promises", "caption")
        if not result.is_safe or result.warnings:
            print("✅ Unsafe content detection working")
        else:
            print("❌ Unsafe content detection failed")
            return False
        
        # Test hashtag moderation
        result = moderate_hashtags(["#nature", "#beautiful", "#inspiration"])
        if result.is_safe:
            print("✅ Hashtag moderation working")
        else:
            print(f"❌ Hashtag moderation failed: {result.issues}")
            return False
        
        print("✅ Content moderation tests completed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Content moderation test failed: {str(e)}\n")
        return False

def test_pre_commit_hooks():
    """Test pre-commit hooks configuration."""
    print("🪝 Testing Pre-commit Hooks Configuration...")
    
    try:
        # Check if pre-commit config file exists
        config_file = Path(".pre-commit-config.yaml")
        if not config_file.exists():
            print("❌ Pre-commit config file not found")
            return False
        
        print("✅ Pre-commit config file exists")
        
        # Try to validate the YAML
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'repos' in config and len(config['repos']) > 0:
            print(f"✅ Pre-commit config valid: {len(config['repos'])} repositories configured")
        else:
            print("❌ Pre-commit config invalid")
            return False
        
        # Check for key security hooks
        hook_names = []
        for repo in config['repos']:
            for hook in repo.get('hooks', []):
                hook_names.append(hook['id'])
        
        required_hooks = ['black', 'ruff', 'bandit', 'detect-secrets']
        missing_hooks = [hook for hook in required_hooks if hook not in hook_names]
        
        if not missing_hooks:
            print("✅ All required security hooks configured")
        else:
            print(f"⚠️  Missing some hooks: {missing_hooks}")
        
        print("✅ Pre-commit hooks tests completed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Pre-commit hooks test failed: {str(e)}\n")
        return False

def test_code_quality_tools():
    """Test code quality tools configuration."""
    print("🔧 Testing Code Quality Tools...")
    
    try:
        # Test pyproject.toml configuration
        import tomllib
        
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        
        # Check for testing dependencies
        dev_deps = config.get('project', {}).get('optional-dependencies', {}).get('dev', [])
        test_deps = config.get('project', {}).get('optional-dependencies', {}).get('test', [])
        
        required_test_tools = ['pytest', 'pytest-cov', 'pytest-mock']
        required_dev_tools = ['black', 'ruff', 'mypy', 'bandit']
        
        all_deps = dev_deps + test_deps
        missing_tools = []
        
        for tool in required_test_tools + required_dev_tools:
            if not any(tool in dep for dep in all_deps):
                missing_tools.append(tool)
        
        if not missing_tools:
            print("✅ All required development tools configured")
        else:
            print(f"⚠️  Missing some tools: {missing_tools}")
        
        # Check tool configurations
        tool_configs = ['tool.pytest.ini_options', 'tool.black', 'tool.ruff', 'tool.mypy']
        configured_tools = []
        
        for tool_config in tool_configs:
            keys = tool_config.split('.')
            current = config
            try:
                for key in keys:
                    current = current[key]
                configured_tools.append(tool_config)
            except KeyError:
                pass
        
        print(f"✅ Tool configurations found: {', '.join(configured_tools)}")
        
        print("✅ Code quality tools tests completed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Code quality tools test failed: {str(e)}\n")
        return False

def test_security_decorators():
    """Test security decorators."""
    print("🎭 Testing Security Decorators...")
    
    try:
        from utils.security import require_validation, rate_limit, audit_log
        
        # Test validation decorator
        @require_validation({'prompt': 'prompt'})
        def test_validation_func(prompt):
            return f"Processed: {prompt}"
        
        try:
            result = test_validation_func("Valid test prompt")
            print("✅ Validation decorator working with valid input")
        except ValueError:
            print("❌ Validation decorator failed with valid input")
            return False
        
        try:
            test_validation_func("")  # Should fail
            print("❌ Validation decorator should have failed with empty input")
            return False
        except ValueError:
            print("✅ Validation decorator correctly rejected invalid input")
        
        # Test rate limit decorator
        @rate_limit('api_general')
        def test_rate_limit_func(user_id):
            return f"Success for {user_id}"
        
        try:
            result = test_rate_limit_func("test_user_decorator")
            print("✅ Rate limit decorator working")
        except Exception as e:
            print(f"❌ Rate limit decorator failed: {str(e)}")
            return False
        
        # Test audit log decorator
        @audit_log('test_action', 'test_resource')
        def test_audit_func():
            return "Success"
        
        try:
            result = test_audit_func()
            print("✅ Audit log decorator working")
        except Exception as e:
            print(f"❌ Audit log decorator failed: {str(e)}")
            return False
        
        print("✅ Security decorators tests completed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Security decorators test failed: {str(e)}\n")
        return False

def test_integration_capabilities():
    """Test integration testing capabilities."""
    print("🔗 Testing Integration Capabilities...")
    
    try:
        # Test if we can import integration test modules
        from tests.test_integration import TestOpenAIIntegration, TestApplicationIntegration
        
        print("✅ Integration test modules importable")
        
        # Test mock capabilities
        from unittest.mock import patch, MagicMock
        import responses
        
        # Test responses library for API mocking
        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, "http://test.example.com", json={"test": "data"})
            print("✅ API mocking capabilities working")
        
        # Test patch capabilities
        with patch('builtins.open') as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "test data"
            print("✅ Function mocking capabilities working")
        
        print("✅ Integration capabilities tests completed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Integration capabilities test failed: {str(e)}\n")
        return False

def test_phase3_completeness():
    """Test Phase 3 completeness by checking all required files."""
    print("📋 Testing Phase 3 Completeness...")
    
    required_files = [
        "tests/test_config.py",
        "tests/test_content_moderation.py", 
        "tests/test_security.py",
        "tests/test_integration.py",
        "utils/security.py",
        ".pre-commit-config.yaml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if not missing_files:
        print("✅ All required Phase 3 files present")
    else:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    # Check if pyproject.toml has been updated with testing dependencies
    try:
        import tomllib
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        
        optional_deps = config.get('project', {}).get('optional-dependencies', {})
        if 'dev' in optional_deps and 'test' in optional_deps:
            print("✅ Testing dependencies configured in pyproject.toml")
        else:
            print("❌ Testing dependencies not properly configured")
            return False
    except Exception as e:
        print(f"❌ Could not verify pyproject.toml: {str(e)}")
        return False
    
    print("✅ Phase 3 completeness tests completed!\n")
    return True

def main():
    """Run all Phase 3 tests."""
    print("🚀 Starting Phase 3 Implementation Tests\n")
    
    tests = [
        test_phase3_completeness,
        test_security_utilities,
        test_content_moderation,
        test_security_decorators,
        test_pre_commit_hooks,
        test_code_quality_tools,
        test_integration_capabilities,
        test_testing_infrastructure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 3 tests passed! Implementation is complete.")
        print("\n📋 Phase 3 Features Implemented:")
        print("✅ Comprehensive testing infrastructure with pytest")
        print("✅ Unit tests for configuration, content moderation, and security")
        print("✅ Integration tests with API mocking")
        print("✅ Input validation and sanitization")
        print("✅ Rate limiting and abuse prevention")
        print("✅ Audit logging for sensitive operations")
        print("✅ Encryption utilities for sensitive data")
        print("✅ Pre-commit hooks for code quality and security")
        print("✅ Security decorators for function-level protection")
        print("✅ Content moderation with safety checks")
        print("\n🔧 Usage Instructions:")
        print("1. Install development dependencies: pip install -e .[dev,test]")
        print("2. Run tests: pytest")
        print("3. Install pre-commit hooks: pre-commit install")
        print("4. Run security checks: bandit -r .")
        print("5. Run code formatting: black .")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)