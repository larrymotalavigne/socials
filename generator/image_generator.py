"""
AI Image Generator for Instagram Publisher.

This module provides image generation capabilities using OpenAI's DALL-E API
with proper error handling, logging, and configuration management.
"""

import base64
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from openai import OpenAI

from config import get_config
from utils.logger import get_logger, log_api_call, log_execution_time
from utils.exceptions import (
    OpenAIError, 
    ContentGenerationError, 
    ValidationError,
    retry_on_exception,
    RetryConfig
)


class ImageGenerator:
    """AI-powered image generator using OpenAI DALL-E."""

    def __init__(self):
        """Initialize the image generator with configuration."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client with proper configuration."""
        try:
            self.client = OpenAI(
                api_key=self.config.openai.api_key,
                timeout=self.config.request_timeout
            )
            self.logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise OpenAIError(
                "Failed to initialize OpenAI client",
                original_exception=e
            )

    def _validate_prompt(self, prompt: str) -> None:
        """Validate image generation prompt."""
        if not prompt or not prompt.strip():
            raise ValidationError("Image prompt cannot be empty", field="prompt")

        if len(prompt) > 1000:  # OpenAI limit
            raise ValidationError(
                "Image prompt too long (max 1000 characters)", 
                field="prompt",
                details={"length": len(prompt), "max_length": 1000}
            )

    def _validate_output_path(self, output_path: str) -> Path:
        """Validate and prepare output path."""
        try:
            path = Path(output_path)

            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Ensure proper extension
            if not path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                path = path.with_suffix('.png')

            return path

        except Exception as e:
            raise ValidationError(
                f"Invalid output path: {output_path}",
                field="output_path",
                original_exception=e
            )

    def _generate_default_filename(self) -> str:
        """Generate a default filename for the image."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"generated_image_{timestamp}.png"

    @retry_on_exception(
        exceptions=(OpenAIError, ConnectionError),
        retry_config=RetryConfig(max_attempts=3, base_delay=2.0)
    )
    @log_api_call("OpenAI", "image_generation")
    @log_execution_time
    def _call_openai_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to OpenAI for image generation."""
        try:
            self.logger.debug(f"Generating image with prompt: {prompt[:100]}...")

            response = self.client.images.generate(
                model=self.config.openai.model_image,
                prompt=prompt,
                size=self.config.openai.image_size,
                quality=self.config.openai.image_quality,
                n=1,
                response_format="b64_json"
            )

            if not response.data or len(response.data) == 0:
                raise OpenAIError("No image data received from OpenAI")

            return {
                "image_data": response.data[0].b64_json,
                "revised_prompt": getattr(response.data[0], 'revised_prompt', None)
            }

        except Exception as e:
            if "content_policy_violation" in str(e).lower():
                raise ContentGenerationError(
                    "Image prompt violates content policy",
                    content_type="image",
                    details={"prompt": prompt}
                )
            elif "rate_limit" in str(e).lower():
                raise OpenAIError(
                    "OpenAI rate limit exceeded",
                    details={"prompt": prompt}
                )
            else:
                raise OpenAIError(
                    f"OpenAI API error: {str(e)}",
                    original_exception=e,
                    details={"prompt": prompt}
                )

    def _save_image(self, image_data: str, output_path: Path) -> None:
        """Save base64 image data to file."""
        try:
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image_data))

            # Verify file was created and has content
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise ContentGenerationError(
                    "Failed to save image file",
                    content_type="image",
                    details={"output_path": str(output_path)}
                )

            self.logger.info(
                f"Image saved successfully: {output_path}",
                extra={'extra_data': {
                    'file_size': output_path.stat().st_size,
                    'file_path': str(output_path)
                }}
            )

        except Exception as e:
            raise ContentGenerationError(
                f"Failed to save image: {str(e)}",
                content_type="image",
                original_exception=e,
                details={"output_path": str(output_path)}
            )

    @log_execution_time
    def generate_image(
        self, 
        prompt: str, 
        output_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate an image using AI based on the given prompt.

        Args:
            prompt: Text description of the image to generate
            output_path: Path where to save the generated image
            **kwargs: Additional parameters for future extensibility

        Returns:
            Dictionary containing:
                - image_path: Path to the saved image
                - revised_prompt: OpenAI's revised version of the prompt (if available)
                - metadata: Additional metadata about the generation

        Raises:
            ValidationError: If prompt or output path is invalid
            ContentGenerationError: If image generation fails
            OpenAIError: If OpenAI API call fails
        """
        try:
            # Validate inputs
            self._validate_prompt(prompt)

            # Prepare output path
            if output_path is None:
                output_dir = Path(self.config.content.output_directory)
                output_path = output_dir / self._generate_default_filename()

            validated_path = self._validate_output_path(output_path)

            self.logger.info(
                f"Starting image generation",
                extra={'extra_data': {
                    'prompt_length': len(prompt),
                    'output_path': str(validated_path),
                    'model': self.config.openai.model_image,
                    'size': self.config.openai.image_size
                }}
            )

            # Generate image via OpenAI API
            api_response = self._call_openai_api(prompt)

            # Save image to file
            self._save_image(api_response["image_data"], validated_path)

            # Prepare result
            result = {
                "image_path": str(validated_path),
                "revised_prompt": api_response.get("revised_prompt"),
                "metadata": {
                    "original_prompt": prompt,
                    "model": self.config.openai.model_image,
                    "size": self.config.openai.image_size,
                    "quality": self.config.openai.image_quality,
                    "generated_at": datetime.now().isoformat(),
                    "file_size": validated_path.stat().st_size
                }
            }

            self.logger.info(
                "Image generation completed successfully",
                extra={'extra_data': result["metadata"]}
            )

            return result

        except (ValidationError, ContentGenerationError, OpenAIError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error in image generation: {str(e)}")
            raise ContentGenerationError(
                f"Unexpected error during image generation: {str(e)}",
                content_type="image",
                original_exception=e,
                details={"prompt": prompt, "output_path": output_path}
            )

    def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI API connection and authentication.

        Returns:
            Dictionary with connection test results
        """
        try:
            self.logger.info("Testing OpenAI API connection...")

            # Make a simple API call to test connectivity
            # We'll use a minimal image generation request
            response = self.client.images.generate(
                model=self.config.openai.model_image,
                prompt="test",
                size="1024x1024",
                quality="standard",
                n=1,
                response_format="url"  # Use URL format to avoid downloading data
            )

            if response.data and len(response.data) > 0:
                result = {
                    "connected": True,
                    "model": self.config.openai.model_image,
                    "api_key_valid": True,
                    "message": "OpenAI API connection successful"
                }

                self.logger.info("OpenAI API connection test successful")
                return result
            else:
                result = {
                    "connected": False,
                    "error": "No response data received",
                    "message": "OpenAI API connection failed"
                }

                self.logger.error("OpenAI API connection test failed: No response data")
                return result

        except Exception as e:
            error_msg = str(e)
            result = {
                "connected": False,
                "error": error_msg,
                "message": "OpenAI API connection test failed with exception"
            }

            # Check for specific error types
            if "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                result["api_key_valid"] = False
            elif "rate_limit" in error_msg.lower():
                result["rate_limited"] = True
            elif "quota" in error_msg.lower():
                result["quota_exceeded"] = True

            self.logger.error(f"OpenAI API connection test failed: {str(e)}")
            return result


# Global instance for backward compatibility and convenience
_image_generator = None


def get_image_generator() -> ImageGenerator:
    """Get or create the global image generator instance."""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator


def generate_image(prompt: str, output_path: str = "output.png") -> str:
    """Generate an image using AI (backward compatibility function).

    Args:
        prompt: Text description of the image to generate
        output_path: Path where to save the generated image

    Returns:
        Path to the generated image file

    Raises:
        ContentGenerationError: If image generation fails
    """
    generator = get_image_generator()
    result = generator.generate_image(prompt, output_path)
    return result["image_path"]
