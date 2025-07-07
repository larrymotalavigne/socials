"""
AI Instagram Publisher - Main Application.

This is the main orchestrator for the AI Instagram Publisher application.
It demonstrates the core infrastructure including configuration management,
logging, error handling, and content generation.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_config, config_manager
from generator.caption_generator import get_caption_generator
from generator.image_generator import get_image_generator
from publisher.instagram_publisher import get_instagram_publisher
from utils.exceptions import (
    handle_exception,
    get_error_stats,
    ConfigurationError
)
from utils.logger import get_logger, setup_logging


class AIInstagramPublisher:
    """Main application orchestrator for AI Instagram Publisher."""

    def __init__(self):
        """Initialize the application."""
        self.logger = get_logger(__name__)
        self.config = None
        self.image_generator = None
        self.caption_generator = None
        self.instagram_publisher = None
        self._initialize()

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

            self.logger.info("Starting AI Instagram Publisher demo")
            print("\n🤖📸 AI Instagram Publisher - Demo")
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


def main():
    """Main entry point for the application."""
    # Initialize logging system first
    setup_logging()

    parser = argparse.ArgumentParser(description="AI Instagram Publisher")
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

    args = parser.parse_args()

    try:
        # Initialize application
        app = AIInstagramPublisher()

        # Validate setup
        if not app.validate_setup():
            print("❌ Application setup validation failed. Please check your configuration.")
            sys.exit(1)

        if args.validate_only:
            print("✅ Application setup validation passed!")
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
            # Custom content generation
            results = app.generate_content(
                prompt=args.prompt,
                style=args.style,
                theme=args.theme,
                output_dir=args.output_dir,
                publish_to_instagram=args.publish
            )

            print("\n📊 Content Generation Results:")
            for component, result in results.items():
                if component == 'instagram_post':
                    # Special handling for Instagram publishing results
                    if 'error' in result:
                        print(f"❌ Instagram Publishing: {result['error']}")
                    else:
                        print(f"✅ Instagram Publishing: Published successfully")
                        print(f"   Post ID: {result.get('post_id')}")
                        if result.get('permalink'):
                            print(f"   URL: {result['permalink']}")
                elif 'error' in result:
                    print(f"❌ {component.title()}: {result['error']}")
                else:
                    print(f"✅ {component.title()}: Generated successfully")
        else:
            # Run demo
            app.run_demo()

    except ConfigurationError as e:
        print(f"❌ Configuration Error: {str(e)}")
        print("Please check your .env file and ensure all required settings are configured.")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user")
        sys.exit(0)

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        handle_exception(e, {"component": "main"})
        sys.exit(1)


if __name__ == "__main__":
    main()
