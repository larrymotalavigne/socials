"""
Instagram Publisher for AI Socials.

This module provides Instagram publishing capabilities using the Instagram Graph API
with proper error handling, logging, and configuration management.
"""

import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import mimetypes

from config import get_config
from utils.logger import get_logger, log_api_call, log_execution_time
from utils.exceptions import (
    InstagramError,
    PublishingError,
    ValidationError,
    AuthenticationError,
    RateLimitError,
    retry_on_exception,
    RetryConfig
)


class InstagramPublisher:
    """Instagram publisher using Graph API."""

    def __init__(self):
        """Initialize the Instagram publisher with configuration."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.base_url = "https://graph.instagram.com/v23.0"
        self._validate_config()

    def _validate_config(self):
        """Validate Instagram configuration."""
        if not self.config.instagram.access_token:
            raise AuthenticationError(
                "Instagram access token is required for publishing",
                service="Instagram"
            )

        if not self.config.instagram.user_id:
            raise AuthenticationError(
                "Instagram user ID is required for publishing",
                service="Instagram"
            )

    def _validate_image_file(self, image_path: str) -> Path:
        """Validate image file for Instagram posting."""
        try:
            path = Path(image_path)

            if not path.exists():
                raise ValidationError(
                    f"Image file does not exist: {image_path}",
                    field="image_path"
                )

            if not path.is_file():
                raise ValidationError(
                    f"Path is not a file: {image_path}",
                    field="image_path"
                )

            # Check file size (Instagram limit: 8MB for images)
            file_size = path.stat().st_size
            max_size = 8 * 1024 * 1024  # 8MB
            if file_size > max_size:
                raise ValidationError(
                    f"Image file too large: {file_size} bytes (max: {max_size})",
                    field="image_path",
                    details={"file_size": file_size, "max_size": max_size}
                )

            # Check file type
            mime_type, _ = mimetypes.guess_type(str(path))
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
            if mime_type not in allowed_types:
                raise ValidationError(
                    f"Unsupported image format: {mime_type}. Allowed: {allowed_types}",
                    field="image_path",
                    details={"mime_type": mime_type, "allowed_types": allowed_types}
                )

            return path

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"Error validating image file: {str(e)}",
                field="image_path",
                original_exception=e
            )

    def _validate_caption(self, caption: str) -> str:
        """Validate caption for Instagram posting."""
        if not caption:
            raise ValidationError("Caption cannot be empty", field="caption")

        # Instagram caption limit
        max_length = 2200
        if len(caption) > max_length:
            raise ValidationError(
                f"Caption too long: {len(caption)} characters (max: {max_length})",
                field="caption",
                details={"length": len(caption), "max_length": max_length}
            )

        return caption.strip()

    @retry_on_exception(
        exceptions=(InstagramError, requests.RequestException),
        retry_config=RetryConfig(max_attempts=3, base_delay=2.0)
    )
    @log_api_call("Instagram", "upload_media")
    @log_execution_time
    def _upload_media(self, image_path: Path) -> str:
        """Upload media to Instagram and return media ID."""
        try:
            url = f"{self.base_url}/{self.config.instagram.user_id}/media"

            # Prepare the image file
            with open(image_path, 'rb') as image_file:
                files = {
                    'image': (image_path.name, image_file, 'image/jpeg')
                }

                data = {
                    'access_token': self.config.instagram.access_token
                }

                self.logger.debug(f"Uploading media to Instagram: {image_path.name}")

                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    timeout=self.config.request_timeout
                )

            # Handle response
            if response.status_code == 200:
                result = response.json()
                media_id = result.get('id')

                if not media_id:
                    raise InstagramError("No media ID returned from Instagram")

                self.logger.info(f"Media uploaded successfully: {media_id}")
                return media_id

            elif response.status_code == 429:
                # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(
                    "Instagram API rate limit exceeded",
                    service="Instagram",
                    retry_after=retry_after
                )

            elif response.status_code == 401:
                raise AuthenticationError(
                    "Instagram authentication failed - invalid access token",
                    service="Instagram"
                )

            else:
                error_data = response.json() if response.content else {}
                raise InstagramError(
                    f"Failed to upload media: {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data
                )

        except Exception as e:
            if isinstance(e, (InstagramError, AuthenticationError, RateLimitError)):
                raise
            raise InstagramError(
                f"Error uploading media to Instagram: {str(e)}",
                original_exception=e
            )

    @retry_on_exception(
        exceptions=(InstagramError, requests.RequestException),
        retry_config=RetryConfig(max_attempts=3, base_delay=1.0)
    )
    @log_api_call("Instagram", "publish_media")
    @log_execution_time
    def _publish_media(self, media_id: str, caption: str) -> str:
        """Publish uploaded media with caption."""
        try:
            url = f"{self.base_url}/{self.config.instagram.user_id}/media_publish"

            data = {
                'creation_id': media_id,
                'caption': caption,
                'access_token': self.config.instagram.access_token
            }

            self.logger.debug(f"Publishing media to Instagram: {media_id}")

            response = requests.post(
                url,
                data=data,
                timeout=self.config.request_timeout
            )

            # Handle response
            if response.status_code == 200:
                result = response.json()
                post_id = result.get('id')

                if not post_id:
                    raise InstagramError("No post ID returned from Instagram")

                self.logger.info(f"Media published successfully: {post_id}")
                return post_id

            elif response.status_code == 429:
                # Rate limit exceeded
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(
                    "Instagram API rate limit exceeded",
                    service="Instagram",
                    retry_after=retry_after
                )

            elif response.status_code == 401:
                raise AuthenticationError(
                    "Instagram authentication failed - invalid access token",
                    service="Instagram"
                )

            else:
                error_data = response.json() if response.content else {}
                raise InstagramError(
                    f"Failed to publish media: {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data
                )

        except Exception as e:
            if isinstance(e, (InstagramError, AuthenticationError, RateLimitError)):
                raise
            raise InstagramError(
                f"Error publishing media to Instagram: {str(e)}",
                original_exception=e
            )

    @log_api_call("Instagram", "get_post_status")
    def _get_post_status(self, post_id: str) -> Dict[str, Any]:
        """Get status of a published post."""
        try:
            url = f"{self.base_url}/{post_id}"

            params = {
                'fields': 'id,media_type,media_url,permalink,timestamp,caption',
                'access_token': self.config.instagram.access_token
            }

            response = requests.get(
                url,
                params=params,
                timeout=self.config.request_timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json() if response.content else {}
                raise InstagramError(
                    f"Failed to get post status: {response.status_code}",
                    status_code=response.status_code,
                    response_data=error_data
                )

        except Exception as e:
            if isinstance(e, InstagramError):
                raise
            raise InstagramError(
                f"Error getting post status: {str(e)}",
                original_exception=e
            )

    @log_execution_time
    def publish_post(
        self,
        image_path: str,
        caption: str,
        verify_post: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Publish a post to Instagram.

        Args:
            image_path: Path to the image file to post
            caption: Caption text for the post
            verify_post: Whether to verify the post was published successfully
            **kwargs: Additional parameters for future extensibility

        Returns:
            Dictionary containing:
                - post_id: Instagram post ID
                - media_id: Instagram media ID
                - permalink: URL to the published post (if available)
                - metadata: Additional metadata about the publication

        Raises:
            ValidationError: If image or caption is invalid
            AuthenticationError: If Instagram authentication fails
            PublishingError: If publishing fails
            InstagramError: If Instagram API call fails
        """
        try:
            # Validate inputs
            validated_image_path = self._validate_image_file(image_path)
            validated_caption = self._validate_caption(caption)

            self.logger.info(
                f"Starting Instagram post publication",
                extra={'extra_data': {
                    'image_path': str(validated_image_path),
                    'caption_length': len(validated_caption),
                    'image_size': validated_image_path.stat().st_size
                }}
            )

            # Step 1: Upload media
            self.logger.info("Uploading media to Instagram...")
            media_id = self._upload_media(validated_image_path)

            # Step 2: Publish media with caption
            self.logger.info("Publishing media to Instagram...")
            post_id = self._publish_media(media_id, validated_caption)

            # Step 3: Verify post (optional)
            post_data = None
            if verify_post:
                self.logger.info("Verifying published post...")
                try:
                    # Wait a moment for the post to be processed
                    time.sleep(2)
                    post_data = self._get_post_status(post_id)
                except Exception as e:
                    self.logger.warning(f"Failed to verify post: {str(e)}")

            # Prepare result
            result = {
                "post_id": post_id,
                "media_id": media_id,
                "permalink": post_data.get('permalink') if post_data else None,
                "metadata": {
                    "image_path": str(validated_image_path),
                    "caption": validated_caption,
                    "caption_length": len(validated_caption),
                    "image_size": validated_image_path.stat().st_size,
                    "published_at": datetime.now().isoformat(),
                    "verified": bool(post_data),
                    "post_data": post_data
                }
            }

            self.logger.info(
                "Instagram post published successfully",
                extra={'extra_data': {
                    'post_id': post_id,
                    'media_id': media_id,
                    'permalink': result['permalink']
                }}
            )

            return result

        except (ValidationError, AuthenticationError, InstagramError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error in Instagram publishing: {str(e)}")
            raise PublishingError(
                f"Unexpected error during Instagram publishing: {str(e)}",
                platform="Instagram",
                original_exception=e,
                details={"image_path": image_path, "caption": caption}
            )

    def test_connection(self) -> Dict[str, Any]:
        """Test Instagram API connection and authentication.

        Returns:
            Dictionary with connection test results
        """
        try:
            self.logger.info("Testing Instagram API connection...")

            url = f"{self.base_url}/{self.config.instagram.user_id}"
            params = {
                'fields': 'id,username,account_type',
                'access_token': self.config.instagram.access_token
            }

            response = requests.get(
                url,
                params=params,
                timeout=self.config.request_timeout
            )

            if response.status_code == 200:
                user_data = response.json()
                result = {
                    "connected": True,
                    "user_id": user_data.get('id'),
                    "username": user_data.get('username'),
                    "account_type": user_data.get('account_type'),
                    "message": "Instagram API connection successful"
                }

                self.logger.info("Instagram API connection test successful")
                return result

            else:
                error_data = response.json() if response.content else {}
                result = {
                    "connected": False,
                    "error": f"HTTP {response.status_code}",
                    "error_data": error_data,
                    "message": "Instagram API connection failed"
                }

                self.logger.error(f"Instagram API connection test failed: {response.status_code}")
                return result

        except Exception as e:
            result = {
                "connected": False,
                "error": str(e),
                "message": "Instagram API connection test failed with exception"
            }

            self.logger.error(f"Instagram API connection test failed: {str(e)}")
            return result


# Global instance for backward compatibility and convenience
_instagram_publisher = None


def get_instagram_publisher() -> InstagramPublisher:
    """Get or create the global Instagram publisher instance."""
    global _instagram_publisher
    if _instagram_publisher is None:
        _instagram_publisher = InstagramPublisher()
    return _instagram_publisher


def publish_to_instagram(image_path: str, caption: str) -> str:
    """Publish a post to Instagram (backward compatibility function).

    Args:
        image_path: Path to the image file to post
        caption: Caption text for the post

    Returns:
        Instagram post ID

    Raises:
        PublishingError: If publishing fails
    """
    publisher = get_instagram_publisher()
    result = publisher.publish_post(image_path, caption)
    return result["post_id"]
