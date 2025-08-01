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

    def _build_system_prompt(self, style: str = "engaging", brand_voice: Optional[str] = None) -> str:
        """Build sophisticated system prompt with advanced prompt engineering."""

        # Enhanced base prompt with more specific instructions
        base_prompt = """You are an expert Instagram content strategist and copywriter with 10+ years of experience creating viral, engaging content. You understand Instagram's algorithm, user psychology, and what drives authentic engagement.

Your expertise includes:
- Crafting captions that stop the scroll and encourage meaningful interaction
- Understanding the psychology of social media engagement
- Creating authentic brand voices that resonate with target audiences
- Optimizing content for Instagram's algorithm and discovery features
- Balancing entertainment, education, and inspiration in social content"""

        # Enhanced style-specific instructions with psychological triggers
        style_prompts = {
            "engaging": """Create captions that maximize engagement through:
- Opening hooks that create curiosity or emotional connection
- Questions that encourage genuine responses (not just yes/no)
- Relatable scenarios that make followers feel seen and understood
- Interactive elements like "double tap if..." or "comment your..."
- Storytelling elements that create emotional investment
- Strategic use of line breaks and emojis for visual appeal""",

            "professional": """Maintain professional authority while being approachable:
- Lead with valuable insights or industry expertise
- Use confident, knowledgeable language without being condescending
- Include actionable tips or takeaways
- Reference credible sources or personal experience
- Balance professionalism with personality and relatability
- End with thoughtful questions that invite professional discussion""",

            "casual": """Create authentic, conversational content that feels like talking to a friend:
- Use natural, everyday language and expressions
- Include personal anecdotes or behind-the-scenes moments
- Reference current trends, memes, or cultural moments appropriately
- Use contractions and casual phrases naturally
- Create a sense of intimacy and authenticity
- Encourage casual, friendly interactions in comments""",

            "inspirational": """Craft uplifting content that motivates and empowers:
- Start with relatable struggles or challenges
- Share transformative insights or mindset shifts
- Use powerful, action-oriented language
- Include personal growth stories or examples
- End with empowering calls-to-action
- Balance vulnerability with strength and hope""",

            "educational": """Provide genuine value through knowledge sharing:
- Structure information clearly with numbered points or steps
- Use simple language to explain complex concepts
- Include surprising facts or lesser-known insights
- Provide actionable takeaways followers can implement
- Reference credible sources when appropriate
- Encourage knowledge sharing in comments""",

            "storytelling": """Create compelling narratives that captivate and connect:
- Use classic story structure (setup, conflict, resolution)
- Include sensory details and emotional moments
- Create relatable characters or situations
- Build tension and curiosity throughout
- End with meaningful lessons or insights
- Encourage followers to share their own stories"""
        }

        style_instruction = style_prompts.get(style, style_prompts["engaging"])

        # Brand voice customization
        brand_voice_instruction = ""
        if brand_voice:
            brand_voice_templates = {
                "friendly": "Maintain a warm, approachable tone like talking to a good friend",
                "authoritative": "Use confident, expert language that establishes credibility",
                "playful": "Incorporate humor, wordplay, and lighthearted elements",
                "sophisticated": "Use elevated language and refined expressions",
                "authentic": "Prioritize genuine, honest communication over perfection",
                "bold": "Use strong, confident language that makes a statement"
            }
            brand_voice_instruction = f"\nBrand Voice: {brand_voice_templates.get(brand_voice, brand_voice)}"

        # Advanced guidelines with psychological and algorithmic considerations
        guidelines = f"""
{style_instruction}{brand_voice_instruction}

ADVANCED GUIDELINES:

Content Structure:
- Hook (first 1-2 lines): Create immediate interest or emotional connection
- Body: Deliver value, story, or insight with strategic line breaks
- Call-to-action: Encourage specific, meaningful engagement
- Hashtags: {self.config.content.hashtag_count} strategic, relevant hashtags

Engagement Optimization:
- Use the "scroll-stopping" principle in opening lines
- Include 1-2 strategic questions that invite genuine responses
- Create "save-worthy" content that provides lasting value
- Use emojis purposefully to enhance readability and emotion
- Vary sentence length for natural reading rhythm

Character Limits:
- Total caption: Under {self.config.content.max_caption_length} characters
- Hook: 125 characters or less (visible without "more" button)
- Optimal length: 1,000-1,500 characters for best engagement

Psychological Triggers:
- Curiosity gaps that make people want to read more
- Social proof through relatable experiences
- FOMO (fear of missing out) when appropriate
- Reciprocity by providing genuine value first
- Community building through inclusive language

Algorithm Considerations:
- Encourage saves, shares, and meaningful comments
- Use relevant keywords naturally in the caption
- Create content that keeps users on the platform longer
- Encourage profile visits through compelling content"""

        return f"{base_prompt}\n\n{guidelines}"

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
    def _call_openai_api(self, prompt: str, style: str = "engaging", brand_voice: Optional[str] = None) -> str:
        """Make API call to OpenAI for caption generation."""
        try:
            system_prompt = self._build_system_prompt(style, brand_voice)

            self.logger.debug(f"Generating caption with style '{style}'{f' and brand voice {brand_voice}' if brand_voice else ''} for prompt: {prompt[:100]}...")

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

    def _enhance_hashtags(self, hashtags: List[str], theme: Optional[str] = None, content_keywords: Optional[List[str]] = None) -> List[str]:
        """Enhanced hashtag generation and optimization with strategic selection."""

        # Remove duplicates while preserving order
        unique_hashtags = list(dict.fromkeys(hashtags))

        # Enhanced theme-based hashtag strategy with different engagement levels
        theme_hashtag_strategy = {
            "nature": {
                "high_engagement": ["#nature", "#naturephotography", "#outdoors", "#landscape"],
                "medium_engagement": ["#natural", "#earth", "#green", "#wildlife", "#hiking"],
                "niche_specific": ["#mothernature", "#earthfocus", "#naturelover", "#outdoorlife"],
                "trending": ["#getoutside", "#exploremore", "#wildernessculture"]
            },
            "lifestyle": {
                "high_engagement": ["#lifestyle", "#daily", "#life", "#inspiration"],
                "medium_engagement": ["#motivation", "#mindfulness", "#selfcare", "#wellness"],
                "niche_specific": ["#lifestyleblogger", "#dailyinspiration", "#mindfuliving"],
                "trending": ["#slowliving", "#intentionalliving", "#authenticself"]
            },
            "inspiration": {
                "high_engagement": ["#inspiration", "#motivation", "#quotes", "#mindset"],
                "medium_engagement": ["#growth", "#success", "#positivity", "#goals"],
                "niche_specific": ["#personaldevelopment", "#selfimprovement", "#mindsetshift"],
                "trending": ["#growthmindset", "#levelup", "#manifestation"]
            },
            "business": {
                "high_engagement": ["#business", "#entrepreneur", "#success", "#leadership"],
                "medium_engagement": ["#growth", "#marketing", "#startup", "#hustle"],
                "niche_specific": ["#businessowner", "#entrepreneurlife", "#businesstips"],
                "trending": ["#businessmindset", "#entrepreneurship", "#buildyourempire"]
            },
            "fitness": {
                "high_engagement": ["#fitness", "#health", "#workout", "#wellness"],
                "medium_engagement": ["#strong", "#gym", "#training", "#healthy"],
                "niche_specific": ["#fitnessjourney", "#healthylifestyle", "#workoutmotivation"],
                "trending": ["#fitnessmotivation", "#strengthtraining", "#mindandbody"]
            },
            "food": {
                "high_engagement": ["#food", "#foodie", "#delicious", "#cooking"],
                "medium_engagement": ["#recipe", "#yummy", "#homemade", "#healthy"],
                "niche_specific": ["#foodphotography", "#foodblogger", "#instafood"],
                "trending": ["#foodlover", "#homecooking", "#plantbased"]
            }
        }

        # Strategic hashtag selection based on engagement optimization
        if theme and theme in theme_hashtag_strategy:
            strategy = theme_hashtag_strategy[theme]

            # Optimal hashtag mix for maximum reach and engagement
            # 30% high engagement, 40% medium engagement, 20% niche, 10% trending
            target_count = self.config.content.hashtag_count

            # Calculate distribution
            high_count = max(1, int(target_count * 0.3))
            medium_count = max(1, int(target_count * 0.4))
            niche_count = max(1, int(target_count * 0.2))
            trending_count = max(1, target_count - high_count - medium_count - niche_count)

            # Add strategic hashtags if not already present
            for tag in strategy["high_engagement"][:high_count]:
                if tag not in unique_hashtags and len(unique_hashtags) < target_count:
                    unique_hashtags.append(tag)

            for tag in strategy["medium_engagement"][:medium_count]:
                if tag not in unique_hashtags and len(unique_hashtags) < target_count:
                    unique_hashtags.append(tag)

            for tag in strategy["niche_specific"][:niche_count]:
                if tag not in unique_hashtags and len(unique_hashtags) < target_count:
                    unique_hashtags.append(tag)

            for tag in strategy["trending"][:trending_count]:
                if tag not in unique_hashtags and len(unique_hashtags) < target_count:
                    unique_hashtags.append(tag)

        # Add content-specific hashtags based on keywords
        if content_keywords:
            for keyword in content_keywords[:3]:  # Limit to 3 keyword-based hashtags
                hashtag = f"#{keyword.lower().replace(' ', '')}"
                if hashtag not in unique_hashtags and len(unique_hashtags) < self.config.content.hashtag_count:
                    unique_hashtags.append(hashtag)

        # Add universal engagement hashtags if we have space
        universal_hashtags = ["#instagood", "#photooftheday", "#love", "#beautiful", "#happy"]
        for tag in universal_hashtags:
            if tag not in unique_hashtags and len(unique_hashtags) < self.config.content.hashtag_count:
                unique_hashtags.append(tag)
                if len(unique_hashtags) >= self.config.content.hashtag_count:
                    break

        # Ensure we don't exceed the configured limit
        final_hashtags = unique_hashtags[:self.config.content.hashtag_count]

        # Log hashtag strategy for monitoring
        self.logger.debug(
            f"Enhanced hashtags generated: {len(final_hashtags)} hashtags",
            extra={'extra_data': {
                'theme': theme,
                'original_count': len(hashtags),
                'final_count': len(final_hashtags),
                'hashtags': final_hashtags
            }}
        )

        return final_hashtags

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
