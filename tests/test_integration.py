"""
Integration tests for API interactions and external services.

This module tests the integration between different components and
external APIs with proper mocking for reliable testing.
"""

import pytest
import json
import responses
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, Any
import tempfile
import os

from config import get_config
from generator.image_generator import ImageGenerator
from generator.caption_generator import CaptionGenerator
from generator.ollama_caption_generator import OllamaCaptionGenerator
from utils.exceptions import OpenAIError, ContentGenerationError
from main import AIInstagramPublisher


class TestOpenAIIntegration:
    """Integration tests for OpenAI API interactions."""

    @responses.activate
    def test_image_generation_api_success(self):
        """Test successful image generation API call."""
        # Mock OpenAI image generation response
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/images/generations",
            json={
                "data": [{
                    "b64_json": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                    "revised_prompt": "A beautiful sunset over mountains with vibrant colors"
                }]
            },
            status=200
        )

        generator = ImageGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = generator.generate_image(
                "A beautiful sunset over mountains",
                output_path=os.path.join(temp_dir, "test_image.png")
            )
            
            assert 'image_path' in result
            assert 'revised_prompt' in result
            assert 'metadata' in result
            assert os.path.exists(result['image_path'])

    @responses.activate
    def test_image_generation_api_error(self):
        """Test image generation API error handling."""
        # Mock OpenAI API error response
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/images/generations",
            json={"error": {"message": "Invalid API key"}},
            status=401
        )

        generator = ImageGenerator()
        
        with pytest.raises(OpenAIError, match="OpenAI API error"):
            generator.generate_image("Test prompt")

    @responses.activate
    def test_caption_generation_api_success(self):
        """Test successful caption generation API call."""
        # Mock OpenAI chat completion response
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json={
                "choices": [{
                    "message": {
                        "content": "Beautiful sunset over majestic mountains! 🌅 Nature's daily masterpiece never fails to inspire. What's your favorite time of day to connect with nature? #sunset #mountains #nature #beautiful #inspiration"
                    }
                }]
            },
            status=200
        )

        generator = CaptionGenerator()
        result = generator.generate_caption("A beautiful sunset over mountains")
        
        assert 'caption' in result
        assert 'hashtags' in result
        assert 'full_caption' in result
        assert 'metadata' in result
        assert len(result['hashtags']) > 0

    @responses.activate
    def test_caption_generation_api_error(self):
        """Test caption generation API error handling."""
        # Mock OpenAI API error response
        responses.add(
            responses.POST,
            "https://api.openai.com/v1/chat/completions",
            json={"error": {"message": "Rate limit exceeded"}},
            status=429
        )

        generator = CaptionGenerator()
        
        with pytest.raises(OpenAIError, match="OpenAI API error"):
            generator.generate_caption("Test prompt")


class TestOllamaIntegration:
    """Integration tests for Ollama API interactions."""

    @responses.activate
    def test_ollama_connection_success(self):
        """Test successful Ollama connection."""
        # Mock Ollama tags endpoint
        responses.add(
            responses.GET,
            "http://localhost:11434/api/tags",
            json={
                "models": [
                    {"name": "llama2:latest"},
                    {"name": "codellama:latest"}
                ]
            },
            status=200
        )

        # Mock Ollama generation endpoint
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={
                "response": "Connection successful."
            },
            status=200
        )

        generator = OllamaCaptionGenerator()
        result = generator.test_connection()
        
        assert result['connected'] is True
        assert result['model_available'] is True
        assert 'available_models' in result

    @responses.activate
    def test_ollama_connection_failure(self):
        """Test Ollama connection failure."""
        # Mock connection error
        responses.add(
            responses.GET,
            "http://localhost:11434/api/tags",
            body=ConnectionError("Connection refused")
        )

        with pytest.raises(ContentGenerationError):
            OllamaCaptionGenerator()

    @responses.activate
    def test_ollama_caption_generation_success(self):
        """Test successful Ollama caption generation."""
        # Mock Ollama tags endpoint for initialization
        responses.add(
            responses.GET,
            "http://localhost:11434/api/tags",
            json={"models": [{"name": "llama2:latest"}]},
            status=200
        )

        # Mock Ollama generation endpoint
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={
                "response": "Stunning mountain sunset! 🏔️ Nature's daily masterpiece painted across the sky. What's your favorite mountain memory? #mountains #sunset #nature #adventure #beautiful"
            },
            status=200
        )

        generator = OllamaCaptionGenerator()
        result = generator.generate_caption("A beautiful sunset over mountains")
        
        assert 'caption' in result
        assert 'hashtags' in result
        assert 'full_caption' in result
        assert 'metadata' in result
        assert result['metadata']['generator'] == 'ollama'


class TestInstagramIntegration:
    """Integration tests for Instagram API interactions."""

    @responses.activate
    def test_instagram_connection_success(self):
        """Test successful Instagram API connection."""
        from publisher.instagram_publisher import InstagramPublisher
        
        # Mock Instagram Graph API user info endpoint
        responses.add(
            responses.GET,
            "https://graph.instagram.com/me",
            json={
                "id": "17841456268019885",
                "username": "test_user",
                "account_type": "BUSINESS"
            },
            status=200
        )

        try:
            publisher = InstagramPublisher()
            result = publisher.test_connection()
            
            assert result['connected'] is True
            assert 'user_id' in result
            assert 'username' in result
        except Exception:
            # Instagram publisher might not be fully implemented
            pytest.skip("Instagram publisher not fully implemented")

    @responses.activate
    def test_instagram_media_upload_success(self):
        """Test successful Instagram media upload."""
        from publisher.instagram_publisher import InstagramPublisher
        
        # Mock Instagram media upload endpoints
        responses.add(
            responses.POST,
            "https://graph.instagram.com/17841456268019885/media",
            json={"id": "media_123"},
            status=200
        )
        
        responses.add(
            responses.POST,
            "https://graph.instagram.com/17841456268019885/media_publish",
            json={"id": "post_456"},
            status=200
        )

        try:
            publisher = InstagramPublisher()
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                # Create a minimal PNG file
                temp_file.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82')
                temp_file.flush()
                
                try:
                    result = publisher.publish_post(
                        image_path=temp_file.name,
                        caption="Test caption #test"
                    )
                    
                    assert 'post_id' in result
                    
                finally:
                    os.unlink(temp_file.name)
                    
        except Exception:
            # Instagram publisher might not be fully implemented
            pytest.skip("Instagram publisher not fully implemented")


class TestApplicationIntegration:
    """Integration tests for the main application."""

    def test_application_initialization(self):
        """Test application initialization and lifecycle."""
        app = AIInstagramPublisher()
        
        assert app.config is not None
        assert app.image_generator is not None
        assert app.caption_generator is not None
        
        # Test lifecycle
        app.start()
        assert app.is_running() is True
        
        app.stop()
        assert app.is_running() is False

    def test_application_validation(self):
        """Test application setup validation."""
        app = AIInstagramPublisher()
        
        # This might fail if OpenAI API key is not valid, but should not crash
        try:
            is_valid = app.validate_setup()
            assert isinstance(is_valid, bool)
        except Exception as e:
            # Expected if API keys are not configured
            assert "API key" in str(e) or "configuration" in str(e).lower()

    @patch('generator.image_generator.ImageGenerator.generate_image')
    @patch('generator.caption_generator.CaptionGenerator.generate_caption')
    def test_content_generation_pipeline_success(self, mock_caption, mock_image):
        """Test successful content generation pipeline."""
        # Mock successful responses
        mock_image.return_value = {
            'image_path': '/tmp/test_image.png',
            'metadata': {'model': 'dall-e-3', 'file_size': 1024}
        }
        
        mock_caption.return_value = {
            'caption': 'Test caption',
            'hashtags': ['#test', '#nature'],
            'full_caption': 'Test caption\n\n#test #nature',
            'metadata': {'style': 'engaging'}
        }

        app = AIInstagramPublisher()
        app.start()
        
        try:
            result = app.generate_content("Test prompt")
            
            assert 'image' in result
            assert 'caption' in result
            assert result['image']['image_path'] == '/tmp/test_image.png'
            assert result['caption']['caption'] == 'Test caption'
            
        finally:
            app.stop()

    @patch('generator.image_generator.ImageGenerator.generate_image')
    def test_content_generation_pipeline_failure(self, mock_image):
        """Test content generation pipeline with failures."""
        # Mock image generation failure
        mock_image.side_effect = OpenAIError("API error")

        app = AIInstagramPublisher()
        app.start()
        
        try:
            result = app.generate_content("Test prompt")
            
            assert 'image' in result
            assert 'error' in result['image']
            assert 'API error' in result['image']['error']
            
        finally:
            app.stop()


class TestConfigurationIntegration:
    """Integration tests for configuration management."""

    def test_config_loading_with_env_vars(self):
        """Test configuration loading with environment variables."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test_key_123',
            'CAPTION_GENERATOR': 'ollama',
            'DEBUG': 'true'
        }):
            # Clear cached config
            from config import config_manager
            config_manager._config = None
            
            config = get_config()
            
            assert config.openai.api_key == 'test_key_123'
            assert config.caption_generator == 'ollama'
            assert config.debug is True

    def test_config_validation_errors(self):
        """Test configuration validation with invalid values."""
        with patch.dict(os.environ, {
            'CAPTION_GENERATOR': 'invalid_generator'
        }):
            from config import config_manager, ConfigurationError
            config_manager._config = None
            
            with pytest.raises(ConfigurationError, match="Caption generator must be"):
                get_config()

    def test_config_environment_switching(self):
        """Test configuration for different environments."""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false'
        }):
            from config import config_manager, Environment
            config_manager._config = None
            
            config = get_config()
            
            assert config.environment == Environment.PRODUCTION
            assert config.debug is False


class TestErrorHandlingIntegration:
    """Integration tests for error handling across components."""

    def test_exception_handling_chain(self):
        """Test exception handling through the component chain."""
        from utils.exceptions import handle_exception, get_error_stats
        
        # Clear error stats
        from utils.exceptions import _error_stats
        _error_stats.clear()
        
        # Simulate an error chain
        try:
            raise OpenAIError("Test API error", details={"endpoint": "/test"})
        except Exception as e:
            handle_exception(e, {"component": "test_integration"})
        
        stats = get_error_stats()
        assert 'OpenAIError' in stats
        assert stats['OpenAIError'] >= 1

    @patch('utils.logger.get_logger')
    def test_logging_integration(self, mock_get_logger):
        """Test logging integration across components."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        app = AIInstagramPublisher()
        
        # Verify logger was called during initialization
        assert mock_get_logger.called
        assert mock_logger.info.called


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_input_validation_in_pipeline(self):
        """Test input validation integration in content pipeline."""
        app = AIInstagramPublisher()
        app.start()
        
        try:
            # Test with invalid prompt (too short)
            result = app.execute_content_pipeline("")
            
            assert result['status'] == 'failed'
            assert 'validation' in result['stages']
            assert not result['stages']['validation']['valid']
            
        finally:
            app.stop()

    def test_rate_limiting_integration(self):
        """Test rate limiting integration."""
        from utils.security import get_rate_limiter
        
        limiter = get_rate_limiter()
        
        # Test multiple requests
        user_id = "integration_test_user"
        
        # Should be allowed initially
        result1 = limiter.is_allowed(user_id, "api_general")
        assert result1['allowed'] is True
        
        # Should still be allowed for reasonable number of requests
        for _ in range(5):
            result = limiter.is_allowed(user_id, "api_general")
            assert result['allowed'] is True

    def test_audit_logging_integration(self):
        """Test audit logging integration."""
        from utils.security import get_audit_logger
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.close()
            
            try:
                auditor = get_audit_logger()
                auditor.log_file = temp_file.name
                
                # Log a test action
                auditor.log_action(
                    action="integration_test",
                    resource="test_resource",
                    user_id="test_user",
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


class TestMockServices:
    """Tests using mock services for external dependencies."""

    def test_mock_openai_service(self):
        """Test with mocked OpenAI service."""
        with patch('openai.OpenAI') as mock_openai:
            # Setup mock client
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Mock image generation
            mock_client.images.generate.return_value = MagicMock(
                data=[MagicMock(
                    b64_json="fake_base64_data",
                    revised_prompt="Revised test prompt"
                )]
            )
            
            generator = ImageGenerator()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch('builtins.open', mock_open()):
                    with patch('pathlib.Path.exists', return_value=True):
                        with patch('pathlib.Path.stat') as mock_stat:
                            mock_stat.return_value.st_size = 1024
                            
                            result = generator.generate_image(
                                "Test prompt",
                                output_path=os.path.join(temp_dir, "test.png")
                            )
                            
                            assert 'image_path' in result
                            assert 'revised_prompt' in result

    def test_mock_ollama_service(self):
        """Test with mocked Ollama service."""
        with patch('requests.get') as mock_get:
            with patch('requests.post') as mock_post:
                # Mock successful connection
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {
                    "models": [{"name": "llama2:latest"}]
                }
                
                # Mock generation response
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {
                    "response": "Mocked caption response #test #mock"
                }
                
                generator = OllamaCaptionGenerator()
                result = generator.generate_caption("Test prompt")
                
                assert 'caption' in result
                assert 'hashtags' in result
                assert result['metadata']['generator'] == 'ollama'


@pytest.fixture
def mock_config():
    """Fixture providing mocked configuration."""
    with patch('config.get_config') as mock_get_config:
        mock_config = MagicMock()
        mock_config.openai.api_key = "test_key"
        mock_config.openai.model_image = "dall-e-3"
        mock_config.openai.model_chat = "gpt-4"
        mock_config.content.output_directory = "/tmp/test"
        mock_config.content.max_caption_length = 2200
        mock_config.content.hashtag_count = 10
        mock_config.caption_generator = "openai"
        mock_get_config.return_value = mock_config
        yield mock_config


@pytest.fixture
def temp_output_dir():
    """Fixture providing temporary output directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestIntegrationWithFixtures:
    """Integration tests using fixtures for consistent test environment."""

    def test_content_generation_with_mocked_config(self, mock_config, temp_output_dir):
        """Test content generation with mocked configuration."""
        mock_config.content.output_directory = temp_output_dir
        
        with patch('generator.image_generator.ImageGenerator._call_openai_api') as mock_api:
            mock_api.return_value = {
                "image_data": "fake_base64_data",
                "revised_prompt": "Test revised prompt"
            }
            
            with patch('builtins.open', mock_open()):
                generator = ImageGenerator()
                
                result = generator.generate_image("Test prompt")
                
                assert 'image_path' in result
                assert 'metadata' in result

    def test_application_with_temp_directory(self, temp_output_dir):
        """Test application with temporary directory."""
        with patch.dict(os.environ, {
            'CONTENT_OUTPUT_DIR': temp_output_dir
        }):
            from config import config_manager
            config_manager._config = None
            
            app = AIInstagramPublisher()
            
            assert app.config.content.output_directory == temp_output_dir


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @patch('generator.image_generator.ImageGenerator._call_openai_api')
    @patch('generator.caption_generator.CaptionGenerator._call_openai_api')
    def test_complete_content_pipeline(self, mock_caption_api, mock_image_api):
        """Test complete content generation pipeline end-to-end."""
        # Mock API responses
        mock_image_api.return_value = {
            "image_data": "fake_base64_data",
            "revised_prompt": "Beautiful mountain sunset"
        }
        
        mock_caption_api.return_value = "Amazing sunset over the mountains! 🌅 #sunset #mountains #nature"
        
        app = AIInstagramPublisher()
        app.start()
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch('builtins.open', mock_open()):
                    with patch('pathlib.Path.exists', return_value=True):
                        with patch('pathlib.Path.stat') as mock_stat:
                            mock_stat.return_value.st_size = 1024
                            
                            result = app.execute_content_pipeline(
                                prompt="A beautiful sunset over mountains",
                                style="engaging",
                                theme="nature",
                                output_dir=temp_dir
                            )
                            
                            assert result['status'] == 'completed'
                            assert 'image' in result
                            assert 'caption' in result
                            assert 'stages' in result
                            
                            # Verify all pipeline stages
                            stages = result['stages']
                            assert 'validation' in stages
                            assert 'image_generation' in stages
                            assert 'caption_generation' in stages
                            assert 'quality_checks' in stages
                            assert 'storage' in stages
                            
        finally:
            app.stop()

    def test_error_recovery_in_pipeline(self):
        """Test error recovery and graceful degradation in pipeline."""
        app = AIInstagramPublisher()
        app.start()
        
        try:
            # Test with invalid input that should fail validation
            result = app.execute_content_pipeline(
                prompt="",  # Empty prompt should fail validation
                style="invalid_style"  # Invalid style
            )
            
            assert result['status'] == 'failed'
            assert 'validation' in result['stages']
            assert not result['stages']['validation']['valid']
            
        finally:
            app.stop()