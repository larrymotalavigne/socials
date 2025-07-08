"""
AI Socials - Main Application.

This is the main orchestrator for the AI Socials application.
It demonstrates the core infrastructure including configuration management,
logging, error handling, and content generation.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_config, config_manager
from generator import get_caption_generator, get_image_generator
from publisher.instagram_publisher import get_instagram_publisher
from utils.exceptions import (
    handle_exception,
    get_error_stats,
    ConfigurationError, PublishingError
)
from utils.logger import get_logger, setup_logging


class AISocials:
    """Main application orchestrator for AI Socials with proper lifecycle management."""

    def __init__(self):
        """Initialize the application."""
        self.logger = get_logger(__name__)
        self.config = None
        self.image_generator = None
        self.caption_generator = None
        self.instagram_publisher = None
        self._running = False
        self._shutdown_requested = False
        self._initialize()

    def start(self):
        """Start the application lifecycle."""
        self.logger.info("Starting AI Socials application")
        self._running = True

    def stop(self):
        """Stop the application gracefully."""
        self.logger.info("Stopping AI Socials application")
        self._shutdown_requested = True
        self._running = False

    def is_running(self) -> bool:
        """Check if application is running."""
        return self._running and not self._shutdown_requested

    def _initialize(self):
        """Initialize application components."""
        try:
            # Load configuration
            self.config = get_config()
            self.logger.info("Application initialized successfully")

            # Initialize generators
            self.image_generator = get_image_generator()
            self.caption_generator = get_caption_generator()

            # Initialize Instagram publisher (optional)
            try:
                if self.config.instagram.access_token and self.config.instagram.user_id:
                    self.instagram_publisher = get_instagram_publisher()
                    self.logger.info("Instagram publisher initialized successfully")
                else:
                    self.logger.info("Instagram publisher not initialized - credentials not configured")
            except Exception as e:
                self.logger.warning(f"Instagram publisher initialization failed: {str(e)}")
                self.instagram_publisher = None

            # Log configuration status
            config_status = config_manager.validate_config()
            self.logger.info("Configuration validation completed", extra={'extra_data': config_status})

        except Exception as e:
            self.logger.critical(f"Failed to initialize application: {str(e)}")
            handle_exception(e, {"component": "application_initialization"})
            raise

    def publish_content(
            self,
            image_path: str,
            caption: str,
            verify_post: bool = True
    ) -> Dict[str, Any]:
        """Publish content to Instagram.

        Args:
            image_path: Path to the image file to publish
            caption: Caption text for the post
            verify_post: Whether to verify the post was published successfully

        Returns:
            Dictionary containing publishing results

        Raises:
            PublishingError: If Instagram publisher is not available or publishing fails
        """
        try:
            if not self.instagram_publisher:
                raise PublishingError(
                    "Instagram publisher not available - check configuration",
                    platform="Instagram"
                )

            self.logger.info(
                f"Starting Instagram publishing",
                extra={'extra_data': {
                    'image_path': image_path,
                    'caption_length': len(caption),
                    'verify_post': verify_post
                }}
            )

            # Publish to Instagram
            result = self.instagram_publisher.publish_post(
                image_path=image_path,
                caption=caption,
                verify_post=verify_post
            )

            self.logger.info(
                "Content published successfully to Instagram",
                extra={'extra_data': {
                    'post_id': result['post_id'],
                    'permalink': result.get('permalink')
                }}
            )

            return result

        except Exception as e:
            self.logger.error(f"Publishing failed: {str(e)}")
            handle_exception(e, {"component": "instagram_publishing", "image_path": image_path})
            raise

    def execute_content_pipeline(
            self,
            prompt: str,
            style: str = "engaging",
            theme: Optional[str] = None,
            output_dir: Optional[str] = None,
            publish_to_instagram: bool = False,
            image_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the complete content generation pipeline with validation and quality checks.

        Args:
            prompt: Text description for content generation
            style: Caption style
            theme: Content theme for hashtag enhancement
            output_dir: Custom output directory
            publish_to_instagram: Whether to publish to Instagram
            image_options: Additional image generation options (size, quality, style)

        Returns:
            Dictionary containing pipeline results and metadata
        """
        pipeline_start_time = datetime.now()
        pipeline_results = {
            'pipeline_id': f"pipeline_{pipeline_start_time.strftime('%Y%m%d_%H%M%S')}",
            'start_time': pipeline_start_time.isoformat(),
            'status': 'running',
            'stages': {}
        }

        try:
            self.logger.info(
                f"Starting content generation pipeline",
                extra={'extra_data': {
                    'pipeline_id': pipeline_results['pipeline_id'],
                    'prompt': prompt[:100],
                    'style': style,
                    'theme': theme,
                    'publish_to_instagram': publish_to_instagram
                }}
            )

            # Stage 1: Content validation and preprocessing
            self.logger.info("Pipeline Stage 1: Content validation and preprocessing")
            validation_result = self._validate_content_request(prompt, style, theme, image_options)
            pipeline_results['stages']['validation'] = validation_result

            if not validation_result['valid']:
                pipeline_results['status'] = 'failed'
                pipeline_results['error'] = validation_result['error']
                return pipeline_results

            # Stage 2: Image generation with enhanced options
            self.logger.info("Pipeline Stage 2: Image generation")
            image_result = self._generate_image_with_options(
                prompt, output_dir, image_options or {}
            )
            pipeline_results['stages']['image_generation'] = image_result

            if 'error' in image_result:
                pipeline_results['status'] = 'failed'
                pipeline_results['error'] = f"Image generation failed: {image_result['error']}"
                return pipeline_results

            # Stage 3: Caption generation with enhanced prompts
            self.logger.info("Pipeline Stage 3: Caption generation")
            caption_result = self._generate_caption_with_enhancements(
                prompt, style, theme
            )
            pipeline_results['stages']['caption_generation'] = caption_result

            if 'error' in caption_result:
                pipeline_results['status'] = 'failed'
                pipeline_results['error'] = f"Caption generation failed: {caption_result['error']}"
                return pipeline_results

            # Stage 4: Content quality and safety checks
            self.logger.info("Pipeline Stage 4: Content quality and safety checks")
            quality_result = self._perform_content_quality_checks(
                image_result, caption_result
            )
            pipeline_results['stages']['quality_checks'] = quality_result

            if not quality_result['passed']:
                pipeline_results['status'] = 'failed'
                pipeline_results['error'] = f"Quality checks failed: {quality_result['issues']}"
                return pipeline_results

            # Stage 5: Content caching and storage
            self.logger.info("Pipeline Stage 5: Content caching and storage")
            storage_result = self._cache_generated_content(
                pipeline_results['pipeline_id'], image_result, caption_result
            )
            pipeline_results['stages']['storage'] = storage_result

            # Stage 6: Instagram publishing (if requested)
            if publish_to_instagram:
                self.logger.info("Pipeline Stage 6: Instagram publishing")
                publish_result = self._publish_with_verification(
                    image_result['image_path'], caption_result['full_caption']
                )
                pipeline_results['stages']['publishing'] = publish_result

                if 'error' in publish_result:
                    pipeline_results['status'] = 'completed_with_errors'
                    pipeline_results['warning'] = f"Publishing failed: {publish_result['error']}"
                else:
                    pipeline_results['instagram_post'] = publish_result

            # Pipeline completion
            pipeline_end_time = datetime.now()
            pipeline_results['end_time'] = pipeline_end_time.isoformat()
            pipeline_results['duration'] = (pipeline_end_time - pipeline_start_time).total_seconds()
            pipeline_results['status'] = 'completed' if pipeline_results['status'] == 'running' else pipeline_results['status']

            # Add final results
            pipeline_results['image'] = image_result
            pipeline_results['caption'] = caption_result

            self.logger.info(
                f"Content generation pipeline completed successfully",
                extra={'extra_data': {
                    'pipeline_id': pipeline_results['pipeline_id'],
                    'duration': pipeline_results['duration'],
                    'status': pipeline_results['status']
                }}
            )

            return pipeline_results

        except Exception as e:
            pipeline_results['status'] = 'failed'
            pipeline_results['error'] = str(e)
            pipeline_results['end_time'] = datetime.now().isoformat()
            self.logger.error(f"Content generation pipeline failed: {str(e)}")
            handle_exception(e, {"component": "content_pipeline", "pipeline_id": pipeline_results['pipeline_id']})
            return pipeline_results

    def generate_content(
            self,
            prompt: str,
            style: str = "engaging",
            theme: Optional[str] = None,
            output_dir: Optional[str] = None,
            publish_to_instagram: bool = False
    ) -> Dict[str, Any]:
        """Generate both image and caption content.

        Args:
            prompt: Text description for content generation
            style: Caption style
            theme: Content theme
            output_dir: Custom output directory
            publish_to_instagram: Whether to publish the generated content to Instagram

        Returns:
            Dictionary containing generated content information and publishing results
        """
        try:
            self.logger.info(
                f"Starting content generation",
                extra={'extra_data': {
                    'prompt': prompt[:100] + "..." if len(prompt) > 100 else prompt,
                    'style': style,
                    'theme': theme,
                    'output_dir': output_dir
                }}
            )

            results = {}

            # Generate image
            self.logger.info("Generating image...")
            try:
                if output_dir:
                    image_output = Path(output_dir) / "generated_image.png"
                    image_result = self.image_generator.generate_image(prompt, str(image_output))
                else:
                    image_result = self.image_generator.generate_image(prompt)

                results['image'] = image_result
                self.logger.info(f"Image generated successfully: {image_result['image_path']}")

            except Exception as e:
                self.logger.error(f"Image generation failed: {str(e)}")
                handle_exception(e, {"component": "image_generation", "prompt": prompt})
                results['image'] = {"error": str(e)}

            # Generate caption
            self.logger.info("Generating caption...")
            try:
                caption_result = self.caption_generator.generate_caption(
                    prompt,
                    style=style,
                    theme=theme
                )
                results['caption'] = caption_result
                self.logger.info("Caption generated successfully")

            except Exception as e:
                self.logger.error(f"Caption generation failed: {str(e)}")
                handle_exception(e, {"component": "caption_generation", "prompt": prompt})
                results['caption'] = {"error": str(e)}

            # Summary
            success_count = sum(1 for result in results.values() if 'error' not in result)
            self.logger.info(
                f"Content generation completed: {success_count}/2 components successful",
                extra={'extra_data': {
                    'success_count': success_count,
                    'total_components': 2,
                    'results_summary': {k: 'success' if 'error' not in v else 'failed' for k, v in results.items()}
                }}
            )

            # Publish to Instagram if requested and content generation was successful
            if publish_to_instagram and success_count == 2:
                self.logger.info("Publishing content to Instagram...")
                try:
                    image_path = results['image']['image_path']
                    caption = results['caption']['full_caption']

                    publish_result = self.publish_content(
                        image_path=image_path,
                        caption=caption,
                        verify_post=True
                    )

                    results['instagram_post'] = publish_result
                    self.logger.info("Content published to Instagram successfully")

                except Exception as e:
                    self.logger.error(f"Instagram publishing failed: {str(e)}")
                    handle_exception(e, {"component": "instagram_publishing_in_generation"})
                    results['instagram_post'] = {"error": str(e)}

            elif publish_to_instagram and success_count < 2:
                self.logger.warning("Skipping Instagram publishing due to content generation failures")
                results['instagram_post'] = {"error": "Content generation incomplete"}

            return results

        except Exception as e:
            self.logger.error(f"Content generation failed: {str(e)}")
            handle_exception(e, {"component": "content_generation", "prompt": prompt})
            raise

    def run_demo(self, prompt: Optional[str] = None):
        """Run a demonstration of the content generation capabilities."""
        try:
            # Use default prompt if none provided
            if not prompt:
                prompt = "a joyful dog playing in a sunflower field during golden hour"

            self.logger.info("Starting AI Socials demo")
            print("\n🤖📸 AI Socials - Demo")
            print("=" * 50)

            # Display configuration info
            print(f"Environment: {self.config.environment.value}")
            print(f"Debug Mode: {self.config.debug}")
            print(f"OpenAI Model (Chat): {self.config.openai.model_chat}")
            print(f"OpenAI Model (Image): {self.config.openai.model_image}")
            print(f"Output Directory: {self.config.content.output_directory}")
            print()

            # Generate content
            print(f"Prompt: {prompt}")
            print("\nGenerating content...")

            results = self.generate_content(prompt, style="engaging", theme="nature")

            # Display results
            print("\n📊 Results:")
            print("-" * 30)

            if 'image' in results and 'error' not in results['image']:
                image_info = results['image']
                print(f"✅ Image: {image_info['image_path']}")
                print(f"   Size: {image_info['metadata']['file_size']} bytes")
                print(f"   Model: {image_info['metadata']['model']}")
            else:
                print(f"❌ Image: {results.get('image', {}).get('error', 'Unknown error')}")

            if 'caption' in results and 'error' not in results['caption']:
                caption_info = results['caption']
                print(f"✅ Caption: {len(caption_info['full_caption'])} characters")
                print(f"   Hashtags: {len(caption_info['hashtags'])}")
                print(f"   Style: {caption_info['metadata']['style']}")
                print(f"\n📝 Generated Caption:")
                print(f"{caption_info['full_caption']}")
            else:
                print(f"❌ Caption: {results.get('caption', {}).get('error', 'Unknown error')}")

            # Display error statistics
            error_stats = get_error_stats()
            if error_stats:
                print(f"\n⚠️  Error Statistics:")
                for error_type, count in error_stats.items():
                    print(f"   {error_type}: {count}")

            print("\n✨ Demo completed!")

        except Exception as e:
            self.logger.error(f"Demo failed: {str(e)}")
            handle_exception(e, {"component": "demo"})
            print(f"\n❌ Demo failed: {str(e)}")
            return False

        return True

    def validate_setup(self) -> bool:
        """Validate that the application is properly set up."""
        try:
            self.logger.info("Validating application setup")

            # Check configuration
            config_status = config_manager.validate_config()
            if not config_status['valid']:
                self.logger.error(f"Configuration validation failed: {config_status.get('error')}")
                return False

            # Check required components
            if not config_status['openai_configured']:
                self.logger.error("OpenAI API key not configured")
                return False

            self.logger.info("Application setup validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Setup validation failed: {str(e)}")
            handle_exception(e, {"component": "setup_validation"})
            return False

    def _validate_content_request(self, prompt: str, style: str, theme: Optional[str], image_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate content generation request parameters."""
        try:
            validation_result = {'valid': True, 'issues': []}

            # Validate prompt
            if not prompt or len(prompt.strip()) < 10:
                validation_result['issues'].append("Prompt must be at least 10 characters long")

            if len(prompt) > 1000:
                validation_result['issues'].append("Prompt exceeds maximum length of 1000 characters")

            # Validate style
            valid_styles = ["engaging", "professional", "casual", "inspirational", "educational", "storytelling"]
            if style not in valid_styles:
                validation_result['issues'].append(f"Invalid style '{style}'. Must be one of: {', '.join(valid_styles)}")

            # Validate theme if provided
            if theme and theme not in self.config.content.content_themes:
                validation_result['issues'].append(f"Invalid theme '{theme}'. Available themes: {', '.join(self.config.content.content_themes)}")

            # Validate image options if provided
            if image_options:
                valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
                if 'size' in image_options and image_options['size'] not in valid_sizes:
                    validation_result['issues'].append(f"Invalid image size. Must be one of: {', '.join(valid_sizes)}")

                valid_qualities = ["standard", "hd"]
                if 'quality' in image_options and image_options['quality'] not in valid_qualities:
                    validation_result['issues'].append(f"Invalid image quality. Must be one of: {', '.join(valid_qualities)}")

            validation_result['valid'] = len(validation_result['issues']) == 0
            if not validation_result['valid']:
                validation_result['error'] = "; ".join(validation_result['issues'])

            return validation_result

        except Exception as e:
            return {'valid': False, 'error': f"Validation error: {str(e)}"}

    def _generate_image_with_options(self, prompt: str, output_dir: Optional[str], image_options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate image with enhanced options and capabilities."""
        try:
            # Enhance prompt for better image generation
            enhanced_prompt = self._enhance_image_prompt(prompt, image_options.get('style'))

            # Prepare generation parameters
            generation_params = {
                'prompt': enhanced_prompt,
                'output_path': output_dir
            }

            # Add image options if provided
            if 'size' in image_options:
                generation_params['size'] = image_options['size']
            if 'quality' in image_options:
                generation_params['quality'] = image_options['quality']

            # Generate image
            result = self.image_generator.generate_image(**generation_params)

            # Add metadata
            result['enhanced_prompt'] = enhanced_prompt
            result['original_prompt'] = prompt
            result['generation_options'] = image_options

            return result

        except Exception as e:
            return {'error': str(e)}

    def _enhance_image_prompt(self, prompt: str, style: Optional[str] = None) -> str:
        """Enhance image prompt with style and quality modifiers."""
        enhanced_prompt = prompt

        # Add style modifiers
        style_modifiers = {
            'professional': ', professional photography, high quality, clean composition',
            'artistic': ', artistic style, creative composition, vibrant colors',
            'minimal': ', minimalist style, clean lines, simple composition',
            'vintage': ', vintage style, retro aesthetic, film photography',
            'modern': ', modern style, contemporary design, sleek appearance'
        }

        if style and style in style_modifiers:
            enhanced_prompt += style_modifiers[style]

        # Add general quality modifiers
        enhanced_prompt += ', high resolution, detailed, Instagram-worthy'

        return enhanced_prompt

    def _generate_caption_with_enhancements(self, prompt: str, style: str, theme: Optional[str]) -> Dict[str, Any]:
        """Generate caption with enhanced prompts and optimization."""
        try:
            # Enhance prompt for better caption generation
            enhanced_prompt = self._enhance_caption_prompt(prompt, style, theme)

            # Generate caption
            result = self.caption_generator.generate_caption(
                prompt=enhanced_prompt,
                style=style,
                theme=theme,
                include_hashtags=True
            )

            # Add metadata
            result['enhanced_prompt'] = enhanced_prompt
            result['original_prompt'] = prompt

            return result

        except Exception as e:
            return {'error': str(e)}

    def _enhance_caption_prompt(self, prompt: str, style: str, theme: Optional[str]) -> str:
        """Enhance caption prompt with context and style guidance."""
        enhanced_prompt = f"Create an Instagram caption for: {prompt}"

        # Add style-specific guidance
        style_guidance = {
            'engaging': 'Make it engaging and interactive, encourage audience participation',
            'professional': 'Keep it professional and informative, suitable for business audience',
            'casual': 'Use casual, friendly tone that feels conversational',
            'inspirational': 'Make it motivational and uplifting, inspire the audience',
            'educational': 'Focus on teaching or sharing valuable information',
            'storytelling': 'Tell a compelling story that connects with the audience'
        }

        if style in style_guidance:
            enhanced_prompt += f". {style_guidance[style]}"

        # Add theme context
        if theme:
            enhanced_prompt += f". This content is related to {theme}."

        # Add Instagram best practices
        enhanced_prompt += " Include relevant hashtags and make it optimized for Instagram engagement."

        return enhanced_prompt

    def _perform_content_quality_checks(self, image_result: Dict[str, Any], caption_result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive content quality and safety checks with AI-powered moderation."""
        from utils.content_moderation import get_content_moderator

        quality_result = {'passed': True, 'issues': [], 'warnings': [], 'moderation_details': {}}

        try:
            moderator = get_content_moderator()

            # Check image quality
            if 'image_path' not in image_result:
                quality_result['issues'].append("Image generation did not produce a valid file path")
            else:
                image_path = Path(image_result['image_path'])
                if not image_path.exists():
                    quality_result['issues'].append("Generated image file does not exist")
                elif image_path.stat().st_size < 1000:  # Less than 1KB
                    quality_result['issues'].append("Generated image file is too small, likely corrupted")

            # Check caption quality and safety
            if 'caption' not in caption_result:
                quality_result['issues'].append("Caption generation did not produce valid content")
            else:
                caption = caption_result['caption']

                # Basic length checks
                if len(caption) < 10:
                    quality_result['issues'].append("Generated caption is too short")
                elif len(caption) > 2200:  # Instagram limit
                    quality_result['issues'].append("Generated caption exceeds Instagram character limit")

                # AI-powered content moderation
                caption_moderation = moderator.moderate_text(caption, context="caption")
                quality_result['moderation_details']['caption'] = {
                    'is_safe': caption_moderation.is_safe,
                    'confidence_score': caption_moderation.confidence_score,
                    'categories': caption_moderation.categories
                }

                if not caption_moderation.is_safe:
                    quality_result['issues'].extend([f"Caption safety issue: {issue}" for issue in caption_moderation.issues])

                if caption_moderation.warnings:
                    quality_result['warnings'].extend([f"Caption warning: {warning}" for warning in caption_moderation.warnings])

                # Log moderation details for monitoring
                self.logger.info(
                    f"Caption moderation completed",
                    extra={'extra_data': {
                        'is_safe': caption_moderation.is_safe,
                        'confidence_score': caption_moderation.confidence_score,
                        'issues_count': len(caption_moderation.issues),
                        'warnings_count': len(caption_moderation.warnings),
                        'categories': caption_moderation.categories
                    }}
                )

            # Check hashtags quality and safety
            if 'hashtags' in caption_result:
                hashtags = caption_result['hashtags']

                # Basic hashtag checks
                if len(hashtags) > 30:  # Instagram best practice
                    quality_result['warnings'].append("Too many hashtags, consider reducing for better engagement")

                # AI-powered hashtag moderation
                if hashtags:
                    hashtag_moderation = moderator.moderate_hashtags(hashtags)
                    quality_result['moderation_details']['hashtags'] = {
                        'is_safe': hashtag_moderation.is_safe,
                        'confidence_score': hashtag_moderation.confidence_score,
                        'categories': hashtag_moderation.categories
                    }

                    if not hashtag_moderation.is_safe:
                        quality_result['issues'].extend([f"Hashtag safety issue: {issue}" for issue in hashtag_moderation.issues])

                    if hashtag_moderation.warnings:
                        quality_result['warnings'].extend([f"Hashtag warning: {warning}" for warning in hashtag_moderation.warnings])

                    # Log hashtag moderation details
                    self.logger.info(
                        f"Hashtag moderation completed",
                        extra={'extra_data': {
                            'hashtag_count': len(hashtags),
                            'is_safe': hashtag_moderation.is_safe,
                            'confidence_score': hashtag_moderation.confidence_score,
                            'inappropriate_hashtags': hashtag_moderation.details.get('inappropriate_hashtags', [])
                        }}
                    )

            # Overall content quality assessment
            overall_confidence = 1.0
            if 'caption' in quality_result['moderation_details']:
                overall_confidence *= quality_result['moderation_details']['caption']['confidence_score']
            if 'hashtags' in quality_result['moderation_details']:
                overall_confidence *= quality_result['moderation_details']['hashtags']['confidence_score']

            quality_result['overall_confidence'] = overall_confidence
            quality_result['passed'] = len(quality_result['issues']) == 0

            # Add quality score for monitoring
            if quality_result['passed']:
                if overall_confidence > 0.8:
                    quality_result['quality_grade'] = 'excellent'
                elif overall_confidence > 0.6:
                    quality_result['quality_grade'] = 'good'
                elif overall_confidence > 0.4:
                    quality_result['quality_grade'] = 'acceptable'
                else:
                    quality_result['quality_grade'] = 'poor'
            else:
                quality_result['quality_grade'] = 'failed'

            return quality_result

        except Exception as e:
            self.logger.error(f"Content quality check failed: {str(e)}")
            return {'passed': False, 'issues': [f"Quality check error: {str(e)}"], 'warnings': []}

    def _cache_generated_content(self, pipeline_id: str, image_result: Dict[str, Any], caption_result: Dict[str, Any]) -> Dict[str, Any]:
        """Cache generated content for future reference."""
        try:
            cache_dir = Path(self.config.content.output_directory) / "cache"
            cache_dir.mkdir(exist_ok=True)

            cache_file = cache_dir / f"{pipeline_id}_metadata.json"

            cache_data = {
                'pipeline_id': pipeline_id,
                'timestamp': datetime.now().isoformat(),
                'image_metadata': {
                    'path': image_result.get('image_path'),
                    'prompt': image_result.get('original_prompt'),
                    'enhanced_prompt': image_result.get('enhanced_prompt')
                },
                'caption_metadata': {
                    'caption': caption_result.get('caption'),
                    'hashtags': caption_result.get('hashtags'),
                    'prompt': caption_result.get('original_prompt')
                }
            }

            import json
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            return {'cached': True, 'cache_file': str(cache_file)}

        except Exception as e:
            return {'cached': False, 'error': str(e)}

    def _publish_with_verification(self, image_path: str, caption: str) -> Dict[str, Any]:
        """Publish content with verification."""
        try:
            if not self.instagram_publisher:
                return {'error': 'Instagram publisher not available'}

            result = self.publish_content(image_path, caption, verify_post=True)
            return result

        except Exception as e:
            return {'error': str(e)}


def main():
    """Main entry point for the application."""
    # Initialize logging system first
    setup_logging()

    parser = argparse.ArgumentParser(description="Socials")
    parser.add_argument(
        "--prompt",
        type=str,
        help="Custom prompt for content generation"
    )
    parser.add_argument(
        "--style",
        type=str,
        default="engaging",
        choices=["engaging", "professional", "casual", "inspirational", "educational", "storytelling"],
        help="Caption style"
    )
    parser.add_argument(
        "--theme",
        type=str,
        help="Content theme for hashtag enhancement"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate setup without generating content"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory for generated content"
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish generated content to Instagram"
    )
    parser.add_argument(
        "--test-instagram",
        action="store_true",
        help="Test Instagram API connection"
    )
    parser.add_argument(
        "--test-openai",
        action="store_true",
        help="Test OpenAI API connection"
    )
    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Test both OpenAI and Instagram API connections"
    )
    parser.add_argument(
        "--image-size",
        type=str,
        choices=["1024x1024", "1792x1024", "1024x1792"],
        help="Image size for generation (default: from config)"
    )
    parser.add_argument(
        "--image-quality",
        type=str,
        choices=["standard", "hd"],
        help="Image quality for generation (default: from config)"
    )
    parser.add_argument(
        "--caption-generator",
        type=str,
        choices=["openai", "ollama"],
        help="Caption generator to use (overrides config setting)"
    )
    parser.add_argument(
        "--test-caption-generators",
        action="store_true",
        help="Test all available caption generators"
    )

    args = parser.parse_args()

    try:
        # Override caption generator if specified
        if args.caption_generator:
            import os
            os.environ['CAPTION_GENERATOR'] = args.caption_generator
            # Clear any cached configuration to ensure the override takes effect
            from config import config_manager
            config_manager._config = None
            print(f"🔧 Using {args.caption_generator} caption generator (command line override)")

        # Initialize application
        app = AISocials()

        # Start application lifecycle
        app.start()

        # Validate setup
        if not app.validate_setup():
            print("❌ Application setup validation failed. Please check your configuration.")
            app.stop()
            sys.exit(1)

        if args.validate_only:
            print("✅ Application setup validation passed!")
            return

        # Test caption generators if requested
        if args.test_caption_generators:
            print("\n🧪 Testing Caption Generators...")
            from generator import test_caption_generators, get_available_caption_generators

            available = get_available_caption_generators()
            print(f"Available generators: {', '.join(available.keys())}")

            results = test_caption_generators()

            for generator_name, result in results.items():
                print(f"\n📡 {generator_name.upper()} Generator:")
                if result.get('connected'):
                    print(f"  ✅ Connected: {result.get('model', 'N/A')}")
                    if 'available_models' in result:
                        print(f"  📋 Available models: {', '.join(result['available_models'][:3])}{'...' if len(result['available_models']) > 3 else ''}")
                    if result.get('model_available') is False:
                        print(f"  ⚠️  Warning: {result.get('error')}")
                else:
                    print(f"  ❌ Failed: {result.get('error')}")

            # Show current configuration
            config = app.config
            print(f"\n🔧 Current Configuration:")
            print(f"  Caption Generator: {config.caption_generator}")
            if config.caption_generator == 'openai':
                print(f"  OpenAI Model: {config.openai.model_chat}")
            elif config.caption_generator == 'ollama':
                print(f"  Ollama Model: {config.ollama.model}")
                print(f"  Ollama URL: {config.ollama.base_url}")

            return

        # Test Instagram connection if requested
        if args.test_instagram:
            print("\n🔗 Testing Instagram API connection...")
            if app.instagram_publisher:
                connection_result = app.instagram_publisher.test_connection()
                if connection_result['connected']:
                    print(f"✅ Instagram connection successful!")
                    print(f"   User ID: {connection_result.get('user_id')}")
                    print(f"   Username: {connection_result.get('username')}")
                    print(f"   Account Type: {connection_result.get('account_type')}")
                else:
                    print(f"❌ Instagram connection failed: {connection_result.get('error')}")
            else:
                print("❌ Instagram publisher not available - check configuration")
            return

        # Test OpenAI connection if requested
        if args.test_openai:
            print("\n🔗 Testing OpenAI API connection...")

            # Test image generation API
            print("Testing image generation API...")
            if app.image_generator:
                image_result = app.image_generator.test_connection()
                if image_result['connected']:
                    print(f"✅ OpenAI Image API connection successful!")
                    print(f"   Model: {image_result.get('model')}")
                else:
                    print(f"❌ OpenAI Image API connection failed: {image_result.get('error')}")
            else:
                print("❌ Image generator not available")

            # Test chat completion API
            print("Testing chat completion API...")
            if app.caption_generator:
                caption_result = app.caption_generator.test_connection()
                if caption_result['connected']:
                    print(f"✅ OpenAI Chat API connection successful!")
                    print(f"   Model: {caption_result.get('model')}")
                else:
                    print(f"❌ OpenAI Chat API connection failed: {caption_result.get('error')}")
            else:
                print("❌ Caption generator not available")
            return

        # Test all connections if requested
        if args.test_all:
            print("\n🔗 Testing all API connections...")

            # Test OpenAI connections
            print("\n📡 OpenAI API Tests:")
            openai_success = True

            # Test image generation API
            print("  Testing image generation API...")
            if app.image_generator:
                image_result = app.image_generator.test_connection()
                if image_result['connected']:
                    print(f"  ✅ Image API: Connected (Model: {image_result.get('model')})")
                else:
                    print(f"  ❌ Image API: Failed - {image_result.get('error')}")
                    openai_success = False
            else:
                print("  ❌ Image API: Generator not available")
                openai_success = False

            # Test chat completion API
            print("  Testing chat completion API...")
            if app.caption_generator:
                caption_result = app.caption_generator.test_connection()
                if caption_result['connected']:
                    print(f"  ✅ Chat API: Connected (Model: {caption_result.get('model')})")
                else:
                    print(f"  ❌ Chat API: Failed - {caption_result.get('error')}")
                    openai_success = False
            else:
                print("  ❌ Chat API: Generator not available")
                openai_success = False

            # Test Instagram connection
            print("\n📱 Instagram API Test:")
            instagram_success = True

            if app.instagram_publisher:
                connection_result = app.instagram_publisher.test_connection()
                if connection_result['connected']:
                    print(f"  ✅ Instagram: Connected")
                    print(f"     User ID: {connection_result.get('user_id')}")
                    print(f"     Username: {connection_result.get('username')}")
                    print(f"     Account Type: {connection_result.get('account_type')}")
                else:
                    print(f"  ❌ Instagram: Failed - {connection_result.get('error')}")
                    instagram_success = False
            else:
                print("  ❌ Instagram: Publisher not available - check configuration")
                instagram_success = False

            # Summary
            print(f"\n📊 Connection Test Summary:")
            print(f"  OpenAI APIs: {'✅ All Connected' if openai_success else '❌ Some Failed'}")
            print(f"  Instagram API: {'✅ Connected' if instagram_success else '❌ Failed'}")
            print(f"  Overall Status: {'✅ All Systems Ready' if openai_success and instagram_success else '❌ Some Issues Found'}")
            return

        # Run content generation
        if args.prompt:
            # Custom content generation using new pipeline
            print("\n🚀 Starting content generation pipeline...")

            # Prepare image options
            image_options = {}
            if args.image_size:
                image_options['size'] = args.image_size
            if args.image_quality:
                image_options['quality'] = args.image_quality

            results = app.execute_content_pipeline(
                prompt=args.prompt,
                style=args.style,
                theme=args.theme,
                output_dir=args.output_dir,
                publish_to_instagram=args.publish,
                image_options=image_options
            )

            print("\n📊 Content Generation Pipeline Results:")
            print(f"Pipeline ID: {results.get('pipeline_id')}")
            print(f"Status: {results.get('status')}")
            print(f"Duration: {results.get('duration', 0):.2f} seconds")

            if results.get('status') == 'completed':
                print("✅ Pipeline completed successfully!")

                # Show stage results
                stages = results.get('stages', {})
                for stage_name, stage_result in stages.items():
                    if stage_name == 'validation' and stage_result.get('valid'):
                        print(f"  ✅ {stage_name.title()}: Passed")
                    elif stage_name in ['image_generation', 'caption_generation'] and 'error' not in stage_result:
                        print(f"  ✅ {stage_name.replace('_', ' ').title()}: Generated successfully")
                    elif stage_name == 'quality_checks' and stage_result.get('passed'):
                        print(f"  ✅ {stage_name.replace('_', ' ').title()}: Passed")
                        if stage_result.get('warnings'):
                            for warning in stage_result['warnings']:
                                print(f"    ⚠️  Warning: {warning}")
                    elif stage_name == 'storage' and stage_result.get('cached'):
                        print(f"  ✅ {stage_name.title()}: Content cached")
                    elif stage_name == 'publishing' and 'error' not in stage_result:
                        print(f"  ✅ Instagram Publishing: Published successfully")
                        print(f"     Post ID: {stage_result.get('post_id')}")
                        if stage_result.get('permalink'):
                            print(f"     URL: {stage_result['permalink']}")

                # Show final content info
                if 'image' in results:
                    print(f"\n📸 Generated Image: {results['image'].get('image_path')}")
                if 'caption' in results:
                    print(f"📝 Generated Caption: {results['caption'].get('caption', '')[:100]}...")

            elif results.get('status') == 'completed_with_errors':
                print("⚠️  Pipeline completed with warnings!")
                print(f"Warning: {results.get('warning')}")

            elif results.get('status') == 'failed':
                print("❌ Pipeline failed!")
                print(f"Error: {results.get('error')}")

        else:
            # Run demo
            print("\n🎯 Running demo mode...")
            app.run_demo()

    except ConfigurationError as e:
        print(f"❌ Configuration Error: {str(e)}")
        print("Please check your .env file and ensure all required settings are configured.")
        if 'app' in locals():
            app.stop()
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user")
        if 'app' in locals():
            print("Shutting down gracefully...")
            app.stop()
        sys.exit(0)

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        handle_exception(e, {"component": "main"})
        if 'app' in locals():
            app.stop()
        sys.exit(1)

    finally:
        # Ensure graceful shutdown
        if 'app' in locals() and app.is_running():
            app.stop()


if __name__ == "__main__":
    main()
