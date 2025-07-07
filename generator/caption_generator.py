"""
AI Caption Generator for Instagram Publisher.

This module provides caption generation capabilities using OpenAI's GPT models
with proper error handling, logging, and configuration management.
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from openai import OpenAI

from config import get_config
from utils.exceptions import (
    OpenAIError,
    ContentGenerationError,
    ValidationError,
    retry_on_exception,
    RetryConfig
)
from utils.logger import get_logger, log_api_call, log_execution_time


class CaptionGenerator:
    """AI-powered caption generator using OpenAI GPT models."""

    def __init__(self):
        """Initialize the caption generator with configuration."""
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
            self.logger.info("OpenAI client initialized successfully for caption generation")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise OpenAIError(
                "Failed to initialize OpenAI client for caption generation",
                original_exception=e
            )

    def _validate_prompt(self, prompt: str) -> None:
        """Validate caption generation prompt."""
        if not prompt or not prompt.strip():
            raise ValidationError("Caption prompt cannot be empty", field="prompt")

        if len(prompt) > 2000:  # Reasonable limit for prompt
            raise ValidationError(
                "Caption prompt too long (max 2000 characters)",
                field="prompt",
                details={"length": len(prompt), "max_length": 2000}
            )

    def _build_system_prompt(self, style: str = "engaging") -> str:
        """Build system prompt based on style and configuration."""
        base_prompt = """You are an expert social media copywriter specializing in Instagram content. 
Your task is to create engaging, authentic captions that drive engagement and reflect the brand's voice."""

        style_prompts = {
            "engaging": "Focus on creating captions that encourage interaction, ask questions, and spark conversations.",
            "professional": "Maintain a professional tone while being approachable and informative.",
            "casual": "Use a friendly, conversational tone that feels natural and relatable.",
            "inspirational": "Create uplifting, motivational content that inspires and empowers the audience.",
            "educational": "Focus on providing value through tips, insights, or interesting facts.",
            "storytelling": "Craft narrative-driven captions that tell a compelling story."
        }

        style_instruction = style_prompts.get(style, style_prompts["engaging"])

        guidelines = f"""
{style_instruction}

Guidelines:
- Keep captions under {self.config.content.max_caption_length} characters
- Include {self.config.content.hashtag_count} relevant hashtags at the end
- Use emojis strategically to enhance readability
- Include a call-to-action when appropriate
- Ensure content is authentic and brand-appropriate
- Avoid overly promotional language
"""

        return f"{base_prompt}\n{guidelines}"

    def _extract_hashtags(self, caption: str) -> tuple[str, List[str]]:
        """Extract hashtags from caption and return clean caption and hashtag list."""
        # Find all hashtags
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, caption)

        # Remove hashtags from caption
        clean_caption = re.sub(hashtag_pattern, '', caption).strip()

        # Clean up extra whitespace
        clean_caption = re.sub(r'\s+', ' ', clean_caption)

        return clean_caption, hashtags

    def _validate_caption_length(self, caption: str) -> None:
        """Validate caption length against Instagram limits."""
        if len(caption) > self.config.content.max_caption_length:
            raise ContentGenerationError(
                f"Generated caption exceeds Instagram limit ({len(caption)} > {self.config.content.max_caption_length})",
                content_type="caption",
                details={
                    "caption_length": len(caption),
                    "max_length": self.config.content.max_caption_length
                }
            )

    @retry_on_exception(
        exceptions=(OpenAIError, ConnectionError),
        retry_config=RetryConfig(max_attempts=3, base_delay=1.0)
    )
    @log_api_call("OpenAI", "caption_generation")
    @log_execution_time
    def _call_openai_api(self, prompt: str, style: str = "engaging") -> str:
        """Make API call to OpenAI for caption generation."""
        try:
            system_prompt = self._build_system_prompt(style)

            self.logger.debug(f"Generating caption with style '{style}' for prompt: {prompt[:100]}...")

            response = self.client.chat.completions.create(
                model=self.config.openai.model_chat,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.openai.temperature,
                max_tokens=self.config.openai.max_tokens
            )

            if not response.choices or len(response.choices) == 0:
                raise OpenAIError("No caption generated by OpenAI")

            caption = response.choices[0].message.content.strip()

            if not caption:
                raise OpenAIError("Empty caption received from OpenAI")

            return caption

        except Exception as e:
            if "content_policy_violation" in str(e).lower():
                raise ContentGenerationError(
                    "Caption prompt violates content policy",
                    content_type="caption",
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

    def _enhance_hashtags(self, hashtags: List[str], theme: Optional[str] = None) -> List[str]:
        """Enhance hashtags based on content themes and configuration."""
        # Remove duplicates while preserving order
        unique_hashtags = list(dict.fromkeys(hashtags))

        # Add theme-based hashtags if theme is provided
        if theme and theme in self.config.content.content_themes:
            theme_hashtags = {
                "nature": ["#nature", "#outdoors", "#natural", "#earth", "#green"],
                "lifestyle": ["#lifestyle", "#daily", "#life", "#inspiration", "#motivation"],
                "inspiration": ["#inspiration", "#motivation", "#quotes", "#mindset", "#growth"],
                "business": ["#business", "#entrepreneur", "#success", "#growth", "#leadership"],
                "fitness": ["#fitness", "#health", "#workout", "#wellness", "#strong"],
                "food": ["#food", "#foodie", "#delicious", "#cooking", "#recipe"]
            }

            if theme in theme_hashtags:
                # Add a few theme hashtags if not already present
                for tag in theme_hashtags[theme][:3]:
                    if tag not in unique_hashtags:
                        unique_hashtags.append(tag)

        # Limit to configured number of hashtags
        return unique_hashtags[:self.config.content.hashtag_count]

    @log_execution_time
    def generate_caption(
            self,
            prompt: str,
            style: str = "engaging",
            theme: Optional[str] = None,
            include_hashtags: bool = True,
            **kwargs
    ) -> Dict[str, Any]:
        """Generate a caption using AI based on the given prompt.

        Args:
            prompt: Text description or context for the caption
            style: Caption style (engaging, professional, casual, inspirational, educational, storytelling)
            theme: Content theme for hashtag enhancement
            include_hashtags: Whether to include hashtags in the result
            **kwargs: Additional parameters for future extensibility

        Returns:
            Dictionary containing:
                - caption: The generated caption text
                - hashtags: List of hashtags (if include_hashtags is True)
                - full_caption: Caption with hashtags appended
                - metadata: Additional metadata about the generation

        Raises:
            ValidationError: If prompt is invalid
            ContentGenerationError: If caption generation fails
            OpenAIError: If OpenAI API call fails
        """
        try:
            # Validate inputs
            self._validate_prompt(prompt)

            # Validate style
            valid_styles = ["engaging", "professional", "casual", "inspirational", "educational", "storytelling"]
            if style not in valid_styles:
                self.logger.warning(f"Invalid style '{style}', using 'engaging'")
                style = "engaging"

            self.logger.info(
                f"Starting caption generation",
                extra={'extra_data': {
                    'prompt_length': len(prompt),
                    'style': style,
                    'theme': theme,
                    'include_hashtags': include_hashtags,
                    'model': self.config.openai.model_chat
                }}
            )

            # Generate caption via OpenAI API
            raw_caption = self._call_openai_api(prompt, style)

            # Extract hashtags from generated caption
            clean_caption, extracted_hashtags = self._extract_hashtags(raw_caption)

            # Enhance hashtags if needed
            if include_hashtags:
                enhanced_hashtags = self._enhance_hashtags(extracted_hashtags, theme)
                hashtag_string = " ".join(enhanced_hashtags)
                full_caption = f"{clean_caption}\n\n{hashtag_string}" if hashtag_string else clean_caption
            else:
                enhanced_hashtags = []
                full_caption = clean_caption

            # Validate final caption length
            self._validate_caption_length(full_caption)

            # Prepare result
            result = {
                "caption": clean_caption,
                "hashtags": enhanced_hashtags if include_hashtags else [],
                "full_caption": full_caption,
                "metadata": {
                    "original_prompt": prompt,
                    "style": style,
                    "theme": theme,
                    "model": self.config.openai.model_chat,
                    "temperature": self.config.openai.temperature,
                    "generated_at": datetime.now().isoformat(),
                    "caption_length": len(full_caption),
                    "hashtag_count": len(enhanced_hashtags) if include_hashtags else 0
                }
            }

            self.logger.info(
                "Caption generation completed successfully",
                extra={'extra_data': result["metadata"]}
            )

            return result

        except (ValidationError, ContentGenerationError, OpenAIError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error in caption generation: {str(e)}")
            raise ContentGenerationError(
                f"Unexpected error during caption generation: {str(e)}",
                content_type="caption",
                original_exception=e,
                details={"prompt": prompt, "style": style}
            )

    def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI API connection and authentication for chat completions.

        Returns:
            Dictionary with connection test results
        """
        try:
            self.logger.info("Testing OpenAI API connection for chat completions...")

            # Make a simple API call to test connectivity
            # We'll use a minimal chat completion request
            response = self.client.chat.completions.create(
                model=self.config.openai.model_chat,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=5,
                temperature=0.1
            )

            if response.choices and len(response.choices) > 0:
                result = {
                    "connected": True,
                    "model": self.config.openai.model_chat,
                    "api_key_valid": True,
                    "message": "OpenAI API connection successful"
                }

                self.logger.info("OpenAI API connection test successful")
                return result
            else:
                result = {
                    "connected": False,
                    "error": "No response choices received",
                    "message": "OpenAI API connection failed"
                }

                self.logger.error("OpenAI API connection test failed: No response choices")
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
_caption_generator = None


def get_caption_generator() -> CaptionGenerator:
    """Get or create the global caption generator instance."""
    global _caption_generator
    if _caption_generator is None:
        _caption_generator = CaptionGenerator()
    return _caption_generator


def generate_caption(prompt: str) -> str:
    """Generate a caption using AI (backward compatibility function).

    Args:
        prompt: Text description or context for the caption

    Returns:
        Generated caption text with hashtags

    Raises:
        ContentGenerationError: If caption generation fails
    """
    generator = get_caption_generator()
    result = generator.generate_caption(prompt)
    return result["full_caption"]
