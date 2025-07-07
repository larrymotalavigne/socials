"""
Unit tests for content moderation system.

This module tests the content safety checks, inappropriate content filtering,
quality scoring, and brand safety validation.
"""

import pytest
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from utils.content_moderation import (
    ContentModerator,
    ModerationResult,
    get_content_moderator,
    moderate_content,
    moderate_hashtags
)


class TestModerationResult:
    """Test cases for ModerationResult dataclass."""

    def test_moderation_result_creation(self):
        """Test creating a ModerationResult instance."""
        result = ModerationResult(
            is_safe=True,
            confidence_score=0.95,
            issues=[],
            warnings=["Minor warning"],
            categories=["safe"],
            details={"test": "data"}
        )
        
        assert result.is_safe is True
        assert result.confidence_score == 0.95
        assert result.issues == []
        assert result.warnings == ["Minor warning"]
        assert result.categories == ["safe"]
        assert result.details == {"test": "data"}


class TestContentModerator:
    """Test cases for ContentModerator class."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.moderator = ContentModerator()

    def test_moderator_initialization(self):
        """Test ContentModerator initialization."""
        assert self.moderator.inappropriate_keywords is not None
        assert self.moderator.brand_unsafe_keywords is not None
        assert self.moderator.quality_indicators is not None
        assert self.moderator.engagement_red_flags is not None

    def test_check_inappropriate_content_safe(self):
        """Test inappropriate content check with safe content."""
        safe_text = "this is a beautiful sunset photo"
        score = self.moderator._check_inappropriate_content(safe_text)
        assert score == 0.0

    def test_check_inappropriate_content_unsafe(self):
        """Test inappropriate content check with unsafe content."""
        unsafe_text = "this is spam content with fake promises"
        score = self.moderator._check_inappropriate_content(unsafe_text)
        assert score > 0.0

    def test_check_brand_safety_safe(self):
        """Test brand safety check with safe content."""
        safe_text = "authentic and genuine content that is helpful"
        score = self.moderator._check_brand_safety(safe_text)
        assert score > 0.7

    def test_check_brand_safety_unsafe(self):
        """Test brand safety check with unsafe content."""
        unsafe_text = "controversy and scandal in the news"
        score = self.moderator._check_brand_safety(unsafe_text)
        assert score < 0.5

    def test_assess_content_quality_high(self):
        """Test content quality assessment with high quality content."""
        quality_text = "authentic and valuable content that is helpful and informative"
        score = self.moderator._assess_content_quality(quality_text)
        assert score > 0.7

    def test_assess_content_quality_low(self):
        """Test content quality assessment with low quality content."""
        low_quality_text = "bad bad bad bad bad bad bad bad bad bad"
        score = self.moderator._assess_content_quality(low_quality_text)
        assert score < 0.5

    def test_check_engagement_manipulation_none(self):
        """Test engagement manipulation check with clean content."""
        clean_text = "beautiful sunset over the mountains"
        score = self.moderator._check_engagement_manipulation(clean_text)
        assert score == 0.0

    def test_check_engagement_manipulation_detected(self):
        """Test engagement manipulation check with manipulative content."""
        manipulative_text = "like if you agree and follow me for more"
        score = self.moderator._check_engagement_manipulation(manipulative_text)
        assert score > 0.0

    def test_check_text_structure_normal(self):
        """Test text structure check with normal text."""
        normal_text = "This is a normal text with proper structure."
        issues = self.moderator._check_text_structure(normal_text)
        assert len(issues) == 0

    def test_check_text_structure_excessive_caps(self):
        """Test text structure check with excessive capitalization."""
        caps_text = "THIS IS ALL CAPS TEXT THAT IS TOO LONG FOR NORMAL USE"
        issues = self.moderator._check_text_structure(caps_text)
        assert any("capital letters" in issue for issue in issues)

    def test_check_text_structure_excessive_punctuation(self):
        """Test text structure check with excessive punctuation."""
        punct_text = "This has too much punctuation!!!!!!!!!!!!!!!!!!"
        issues = self.moderator._check_text_structure(punct_text)
        assert any("punctuation" in issue for issue in issues)

    def test_moderate_text_safe_content(self):
        """Test text moderation with safe content."""
        safe_text = "Beautiful sunset over mountains with authentic and valuable content"
        result = self.moderator.moderate_text(safe_text, "caption")
        
        assert result.is_safe is True
        assert result.confidence_score > 0.5
        assert len(result.issues) == 0

    def test_moderate_text_unsafe_content(self):
        """Test text moderation with unsafe content."""
        unsafe_text = "spam content with fake promises and scam offers"
        result = self.moderator.moderate_text(unsafe_text, "caption")
        
        assert result.is_safe is False or len(result.warnings) > 0
        assert "inappropriate" in result.categories or len(result.warnings) > 0

    def test_moderate_text_with_context(self):
        """Test text moderation with context information."""
        text = "Test content for moderation"
        result = self.moderator.moderate_text(text, "caption")
        
        assert isinstance(result, ModerationResult)
        assert result.details is not None

    def test_moderate_text_error_handling(self):
        """Test text moderation error handling."""
        with patch.object(self.moderator, '_check_inappropriate_content', side_effect=Exception("Test error")):
            result = self.moderator.moderate_text("test", "caption")
            
            assert result.is_safe is False
            assert len(result.issues) > 0
            assert "error" in result.categories

    def test_moderate_hashtags_safe(self):
        """Test hashtag moderation with safe hashtags."""
        safe_hashtags = ["#nature", "#beautiful", "#sunset", "#photography"]
        result = self.moderator.moderate_hashtags(safe_hashtags)
        
        assert result.is_safe is True
        assert result.confidence_score > 0.5
        assert len(result.issues) == 0

    def test_moderate_hashtags_inappropriate(self):
        """Test hashtag moderation with inappropriate hashtags."""
        inappropriate_hashtags = ["#spam", "#fake", "#scam"]
        result = self.moderator.moderate_hashtags(inappropriate_hashtags)
        
        assert result.is_safe is False
        assert len(result.issues) > 0
        assert "inappropriate_hashtags" in result.categories

    def test_moderate_hashtags_excessive_count(self):
        """Test hashtag moderation with excessive hashtag count."""
        excessive_hashtags = [f"#tag{i}" for i in range(35)]
        result = self.moderator.moderate_hashtags(excessive_hashtags)
        
        assert len(result.warnings) > 0
        assert any("excessive" in warning.lower() for warning in result.warnings)

    def test_moderate_hashtags_too_generic(self):
        """Test hashtag moderation with too many generic hashtags."""
        generic_hashtags = ["#love", "#instagood", "#photooftheday", "#beautiful", "#happy"] * 3
        result = self.moderator.moderate_hashtags(generic_hashtags)
        
        assert len(result.warnings) > 0
        assert any("generic" in warning.lower() for warning in result.warnings)

    def test_moderate_hashtags_error_handling(self):
        """Test hashtag moderation error handling."""
        with patch.object(self.moderator, 'inappropriate_keywords', side_effect=Exception("Test error")):
            result = self.moderator.moderate_hashtags(["#test"])
            
            assert result.is_safe is False
            assert len(result.issues) > 0
            assert "error" in result.categories


class TestModerationUtilities:
    """Test cases for moderation utility functions."""

    def test_get_content_moderator_singleton(self):
        """Test that get_content_moderator returns the same instance."""
        moderator1 = get_content_moderator()
        moderator2 = get_content_moderator()
        
        assert moderator1 is moderator2
        assert isinstance(moderator1, ContentModerator)

    def test_moderate_content_convenience_function(self):
        """Test the moderate_content convenience function."""
        result = moderate_content("test content", "caption")
        
        assert isinstance(result, ModerationResult)
        assert result.is_safe is not None
        assert result.confidence_score is not None

    def test_moderate_hashtags_convenience_function(self):
        """Test the moderate_hashtags convenience function."""
        result = moderate_hashtags(["#test", "#hashtag"])
        
        assert isinstance(result, ModerationResult)
        assert result.is_safe is not None
        assert result.confidence_score is not None


class TestModerationIntegration:
    """Integration tests for content moderation system."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.moderator = ContentModerator()

    def test_full_content_moderation_workflow(self):
        """Test complete content moderation workflow."""
        # Test content that should pass all checks
        good_content = "Beautiful authentic sunset photography with genuine artistic value"
        result = self.moderator.moderate_text(good_content, "caption")
        
        assert result.is_safe is True
        assert result.confidence_score > 0.6
        assert len(result.issues) == 0
        assert result.details["inappropriate_score"] == 0.0
        assert result.details["brand_safety_score"] > 0.7

    def test_content_with_multiple_issues(self):
        """Test content moderation with multiple issues."""
        problematic_content = "SPAM CONTENT WITH FAKE PROMISES!!! FOLLOW ME NOW!!!"
        result = self.moderator.moderate_text(problematic_content, "caption")
        
        # Should have multiple issues/warnings
        total_issues = len(result.issues) + len(result.warnings)
        assert total_issues > 0
        assert result.confidence_score < 0.8

    def test_hashtag_moderation_with_mixed_quality(self):
        """Test hashtag moderation with mixed quality hashtags."""
        mixed_hashtags = [
            "#nature", "#beautiful",  # Good hashtags
            "#love", "#instagood",    # Generic but acceptable
            "#spam", "#fake"          # Problematic hashtags
        ]
        
        result = self.moderator.moderate_hashtags(mixed_hashtags)
        
        assert result.is_safe is False  # Due to problematic hashtags
        assert len(result.issues) > 0
        assert "inappropriate_hashtags" in result.details

    def test_moderation_performance_with_long_content(self):
        """Test moderation performance with long content."""
        long_content = "Beautiful sunset " * 100  # 1500+ characters
        
        import time
        start_time = time.time()
        result = self.moderator.moderate_text(long_content, "caption")
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 1.0  # Less than 1 second
        assert isinstance(result, ModerationResult)

    def test_moderation_with_special_characters(self):
        """Test moderation with special characters and emojis."""
        special_content = "Beautiful sunset 🌅 with special chars: @#$%^&*()"
        result = self.moderator.moderate_text(special_content, "caption")
        
        assert isinstance(result, ModerationResult)
        assert result.is_safe is not None

    def test_moderation_edge_cases(self):
        """Test moderation with edge cases."""
        edge_cases = [
            "",  # Empty string
            " ",  # Whitespace only
            "a",  # Single character
            "🌅",  # Emoji only
            "123",  # Numbers only
        ]
        
        for content in edge_cases:
            result = self.moderator.moderate_text(content, "caption")
            assert isinstance(result, ModerationResult)
            assert result.is_safe is not None


@pytest.fixture
def sample_safe_content():
    """Fixture providing sample safe content for testing."""
    return "Beautiful sunset over mountains with authentic photography"


@pytest.fixture
def sample_unsafe_content():
    """Fixture providing sample unsafe content for testing."""
    return "Spam content with fake promises and scam offers"


@pytest.fixture
def sample_safe_hashtags():
    """Fixture providing sample safe hashtags for testing."""
    return ["#nature", "#photography", "#sunset", "#beautiful", "#landscape"]


@pytest.fixture
def sample_unsafe_hashtags():
    """Fixture providing sample unsafe hashtags for testing."""
    return ["#spam", "#fake", "#scam", "#bot", "#follow4follow"]


class TestModerationFixtures:
    """Test cases using fixtures for consistent test data."""

    def test_safe_content_moderation(self, sample_safe_content):
        """Test moderation with safe content fixture."""
        moderator = ContentModerator()
        result = moderator.moderate_text(sample_safe_content, "caption")
        
        assert result.is_safe is True
        assert result.confidence_score > 0.5

    def test_unsafe_content_moderation(self, sample_unsafe_content):
        """Test moderation with unsafe content fixture."""
        moderator = ContentModerator()
        result = moderator.moderate_text(sample_unsafe_content, "caption")
        
        assert result.is_safe is False or len(result.warnings) > 0

    def test_safe_hashtag_moderation(self, sample_safe_hashtags):
        """Test hashtag moderation with safe hashtags fixture."""
        moderator = ContentModerator()
        result = moderator.moderate_hashtags(sample_safe_hashtags)
        
        assert result.is_safe is True
        assert len(result.issues) == 0

    def test_unsafe_hashtag_moderation(self, sample_unsafe_hashtags):
        """Test hashtag moderation with unsafe hashtags fixture."""
        moderator = ContentModerator()
        result = moderator.moderate_hashtags(sample_unsafe_hashtags)
        
        assert result.is_safe is False
        assert len(result.issues) > 0


class TestModerationConfiguration:
    """Test cases for moderation configuration and customization."""

    def test_inappropriate_keywords_configuration(self):
        """Test inappropriate keywords configuration."""
        moderator = ContentModerator()
        
        assert "spam" in moderator.inappropriate_keywords
        assert isinstance(moderator.inappropriate_keywords, dict)
        
        # Test each category has keywords
        for category, keywords in moderator.inappropriate_keywords.items():
            assert len(keywords) > 0
            assert all(isinstance(keyword, str) for keyword in keywords)

    def test_brand_safety_keywords_configuration(self):
        """Test brand safety keywords configuration."""
        moderator = ContentModerator()
        
        assert len(moderator.brand_unsafe_keywords) > 0
        assert all(isinstance(keyword, str) for keyword in moderator.brand_unsafe_keywords)

    def test_quality_indicators_configuration(self):
        """Test quality indicators configuration."""
        moderator = ContentModerator()
        
        assert len(moderator.quality_indicators) > 0
        assert all(isinstance(indicator, str) for indicator in moderator.quality_indicators)

    def test_engagement_red_flags_configuration(self):
        """Test engagement red flags configuration."""
        moderator = ContentModerator()
        
        assert len(moderator.engagement_red_flags) > 0
        assert all(isinstance(flag, str) for flag in moderator.engagement_red_flags)