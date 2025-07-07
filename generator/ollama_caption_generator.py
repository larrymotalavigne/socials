"""
Ollama Caption Generator for Instagram Publisher.

This module provides caption generation capabilities using Ollama's local LLM API
with proper error handling, logging, and configuration management.
"""

import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List

from config import get_config
from utils.exceptions import (
    ContentGenerationError,
    ValidationError,
    retry_on_exception,
    RetryConfig
)
from utils.logger import get_logger, log_api_call, log_execution_time
from utils.container import ICaptionGenerator


class OllamaCaptionGenerator(ICaptionGenerator):
    """AI-powered caption generator using Ollama local LLM."""

    def __init__(self):
        """Initialize the Ollama caption generator with configuration."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Ollama client configuration."""
        try:
            # Test connection to Ollama
            response = requests.get(f"{self.config.ollama.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.logger.info("Ollama client initialized successfully for caption generation")
            else:
                self.logger.warning(f"Ollama server responded with status {response.status_code}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Ollama server: {str(e)}")
            raise ContentGenerationError(
                "Failed to initialize Ollama client for caption generation",
                content_type="caption",
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

    @retry_on_exception(
        exceptions=(requests.RequestException, ConnectionError),
        retry_config=RetryConfig(max_attempts=3, base_delay=1.0)
    )
    @log_api_call("Ollama", "caption_generation")
    @log_execution_time
    def _call_ollama_api(self, prompt: str, style: str = "engaging", brand_voice: Optional[str] = None) -> str:
        """Make API call to Ollama for caption generation."""
        try:
            system_prompt = self._build_system_prompt(style, brand_voice)

            self.logger.debug(f"Generating caption with Ollama using style '{style}'{f' and brand voice {brand_voice}' if brand_voice else ''} for prompt: {prompt[:100]}...")

            # Prepare the request payload for Ollama
            payload = {
                "model": self.config.ollama.model,
                "prompt": f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": self.config.ollama.temperature,
                    "num_predict": self.config.ollama.max_tokens
                }
            }

            response = requests.post(
                f"{self.config.ollama.base_url}/api/generate",
                json=payload,
                timeout=self.config.ollama.timeout
            )

            if response.status_code != 200:
                raise ContentGenerationError(
                    f"Ollama API error: HTTP {response.status_code}",
                    content_type="caption",
                    details={"status_code": response.status_code, "response": response.text}
                )

            result = response.json()
            
            if "response" not in result:
                raise ContentGenerationError(
                    "No caption generated by Ollama",
                    content_type="caption",
                    details={"result": result}
                )

            caption = result["response"].strip()

            if not caption:
                raise ContentGenerationError(
                    "Empty caption received from Ollama",
                    content_type="caption"
                )

            return caption

        except requests.RequestException as e:
            raise ContentGenerationError(
                f"Ollama API connection error: {str(e)}",
                content_type="caption",
                original_exception=e,
                details={"prompt": prompt}
            )
        except Exception as e:
            raise ContentGenerationError(
                f"Ollama API error: {str(e)}",
                content_type="caption",
                original_exception=e,
                details={"prompt": prompt}
            )

    def _extract_hashtags(self, caption: str) -> tuple[str, List[str]]:
        """Extract hashtags from caption and return clean caption and hashtag list."""
        import re
        
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
        """Generate a caption using Ollama based on the given prompt.

        Args:
            prompt: Text description or context for the caption
            style: Caption style (engaging, professional, casual, inspirational, educational, storytelling)
            theme: Content theme for hashtag enhancement
            include_hashtags: Whether to include hashtags in the output
            **kwargs: Additional parameters for future extensibility

        Returns:
            Dictionary containing:
                - caption: The main caption text (without hashtags)
                - hashtags: List of hashtags
                - full_caption: Complete caption with hashtags
                - metadata: Additional metadata about the generation

        Raises:
            ValidationError: If prompt is invalid
            ContentGenerationError: If caption generation fails
        """
        try:
            # Validate inputs
            self._validate_prompt(prompt)

            # Extract additional parameters
            brand_voice = kwargs.get('brand_voice')
            content_keywords = kwargs.get('content_keywords', [])

            self.logger.info(
                f"Starting Ollama caption generation",
                extra={'extra_data': {
                    'prompt_length': len(prompt),
                    'style': style,
                    'theme': theme,
                    'model': self.config.ollama.model,
                    'include_hashtags': include_hashtags
                }}
            )

            # Generate caption via Ollama API
            raw_caption = self._call_ollama_api(prompt, style, brand_voice)

            # Extract hashtags from generated content
            clean_caption, extracted_hashtags = self._extract_hashtags(raw_caption)

            # Enhance hashtags if requested
            final_hashtags = []
            if include_hashtags:
                final_hashtags = self._enhance_hashtags(
                    extracted_hashtags, 
                    theme, 
                    content_keywords
                )

            # Create full caption
            full_caption = clean_caption
            if final_hashtags:
                hashtag_string = " ".join(final_hashtags)
                full_caption = f"{clean_caption}\n\n{hashtag_string}"

            # Validate final caption length
            self._validate_caption_length(full_caption)

            # Prepare result
            result = {
                "caption": clean_caption,
                "hashtags": final_hashtags,
                "full_caption": full_caption,
                "metadata": {
                    "original_prompt": prompt,
                    "style": style,
                    "theme": theme,
                    "model": self.config.ollama.model,
                    "generated_at": datetime.now().isoformat(),
                    "caption_length": len(clean_caption),
                    "full_caption_length": len(full_caption),
                    "hashtag_count": len(final_hashtags),
                    "generator": "ollama"
                }
            }

            self.logger.info(
                "Ollama caption generation completed successfully",
                extra={'extra_data': result["metadata"]}
            )

            return result

        except (ValidationError, ContentGenerationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error in Ollama caption generation: {str(e)}")
            raise ContentGenerationError(
                f"Unexpected error during Ollama caption generation: {str(e)}",
                content_type="caption",
                original_exception=e,
                details={"prompt": prompt, "style": style}
            )

    def test_connection(self) -> Dict[str, Any]:
        """Test Ollama API connection and model availability.

        Returns:
            Dictionary with connection test results
        """
        try:
            self.logger.info("Testing Ollama API connection...")

            # Test basic connectivity
            response = requests.get(f"{self.config.ollama.base_url}/api/tags", timeout=10)
            
            if response.status_code != 200:
                return {
                    "connected": False,
                    "error": f"Ollama server returned status {response.status_code}",
                    "details": {"status_code": response.status_code}
                }

            # Check if our model is available
            models_data = response.json()
            available_models = [model["name"] for model in models_data.get("models", [])]
            
            model_available = any(self.config.ollama.model in model for model in available_models)
            
            if not model_available:
                return {
                    "connected": True,
                    "model_available": False,
                    "error": f"Model '{self.config.ollama.model}' not found",
                    "available_models": available_models
                }

            # Test a simple generation
            test_payload = {
                "model": self.config.ollama.model,
                "prompt": "Test prompt for connection verification. Respond with 'Connection successful.'",
                "stream": False,
                "options": {"num_predict": 10}
            }

            test_response = requests.post(
                f"{self.config.ollama.base_url}/api/generate",
                json=test_payload,
                timeout=30
            )

            if test_response.status_code == 200:
                return {
                    "connected": True,
                    "model_available": True,
                    "model": self.config.ollama.model,
                    "base_url": self.config.ollama.base_url,
                    "available_models": available_models
                }
            else:
                return {
                    "connected": True,
                    "model_available": True,
                    "generation_test": False,
                    "error": f"Generation test failed with status {test_response.status_code}"
                }

        except requests.RequestException as e:
            return {
                "connected": False,
                "error": f"Connection failed: {str(e)}",
                "details": {"exception_type": type(e).__name__}
            }
        except Exception as e:
            return {
                "connected": False,
                "error": f"Unexpected error: {str(e)}",
                "details": {"exception_type": type(e).__name__}
            }


# Global instance
_ollama_caption_generator = None


def get_ollama_caption_generator() -> OllamaCaptionGenerator:
    """Get the global Ollama caption generator instance."""
    global _ollama_caption_generator
    if _ollama_caption_generator is None:
        _ollama_caption_generator = OllamaCaptionGenerator()
    return _ollama_caption_generator