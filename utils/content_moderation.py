"""
Content moderation and safety checks for AI-generated content.

This module provides basic content moderation capabilities including:
- Inappropriate content detection
- Safety keyword filtering
- Content quality scoring
- Brand safety checks
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from utils.logger import get_logger


@dataclass
class ModerationResult:
    """Result of content moderation check."""
    is_safe: bool
    confidence_score: float
    issues: List[str]
    warnings: List[str]
    categories: List[str]
    details: Dict[str, Any]


class ContentModerator:
    """Basic content moderation system for AI-generated content."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Inappropriate content keywords (basic implementation)
        self.inappropriate_keywords = {
            'spam': ['spam', 'scam', 'fake', 'bot', 'follow4follow', 'f4f', 'l4l'],
            'offensive': ['hate', 'racist', 'sexist', 'discrimination', 'harassment'],
            'adult': ['adult', 'nsfw', 'explicit', 'sexual'],
            'violence': ['violence', 'kill', 'death', 'murder', 'weapon'],
            'illegal': ['illegal', 'drugs', 'piracy', 'fraud', 'stolen'],
            'misleading': ['miracle', 'guaranteed', 'instant', 'secret', 'hack']
        }
        
        # Brand safety keywords to avoid
        self.brand_unsafe_keywords = [
            'controversy', 'scandal', 'lawsuit', 'bankruptcy', 'crisis',
            'disaster', 'tragedy', 'accident', 'emergency'
        ]
        
        # Quality indicators (positive)
        self.quality_indicators = [
            'authentic', 'genuine', 'honest', 'transparent', 'valuable',
            'helpful', 'informative', 'inspiring', 'creative', 'original'
        ]
        
        # Engagement red flags
        self.engagement_red_flags = [
            'like if', 'comment if', 'follow me', 'check my bio',
            'link in bio', 'dm me', 'click link', 'swipe up'
        ]

    def moderate_text(self, text: str, context: Optional[str] = None) -> ModerationResult:
        """
        Perform comprehensive text moderation.
        
        Args:
            text: Text content to moderate
            context: Additional context (e.g., 'caption', 'hashtag')
            
        Returns:
            ModerationResult with safety assessment
        """
        try:
            text_lower = text.lower()
            issues = []
            warnings = []
            categories = []
            details = {}
            
            # Check for inappropriate content
            inappropriate_score = self._check_inappropriate_content(text_lower)
            if inappropriate_score > 0.7:
                issues.append("Contains potentially inappropriate content")
                categories.append("inappropriate")
            elif inappropriate_score > 0.3:
                warnings.append("May contain questionable content")
            
            details['inappropriate_score'] = inappropriate_score
            
            # Check brand safety
            brand_safety_score = self._check_brand_safety(text_lower)
            if brand_safety_score < 0.5:
                warnings.append("Content may not be brand-safe")
                categories.append("brand_risk")
            
            details['brand_safety_score'] = brand_safety_score
            
            # Check content quality
            quality_score = self._assess_content_quality(text_lower)
            if quality_score < 0.3:
                warnings.append("Content quality may be low")
            
            details['quality_score'] = quality_score
            
            # Check for engagement manipulation
            engagement_manipulation = self._check_engagement_manipulation(text_lower)
            if engagement_manipulation > 0.5:
                warnings.append("Contains potential engagement manipulation tactics")
                categories.append("engagement_manipulation")
            
            details['engagement_manipulation_score'] = engagement_manipulation
            
            # Check text length and structure
            structure_issues = self._check_text_structure(text)
            if structure_issues:
                warnings.extend(structure_issues)
            
            # Calculate overall safety
            is_safe = len(issues) == 0
            confidence_score = min(brand_safety_score, 1.0 - inappropriate_score, quality_score)
            
            self.logger.debug(
                f"Content moderation completed",
                extra={'extra_data': {
                    'is_safe': is_safe,
                    'confidence_score': confidence_score,
                    'issues_count': len(issues),
                    'warnings_count': len(warnings),
                    'context': context
                }}
            )
            
            return ModerationResult(
                is_safe=is_safe,
                confidence_score=confidence_score,
                issues=issues,
                warnings=warnings,
                categories=categories,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Content moderation failed: {str(e)}")
            return ModerationResult(
                is_safe=False,
                confidence_score=0.0,
                issues=[f"Moderation error: {str(e)}"],
                warnings=[],
                categories=["error"],
                details={}
            )

    def _check_inappropriate_content(self, text: str) -> float:
        """Check for inappropriate content keywords."""
        total_keywords = 0
        found_keywords = 0
        
        for category, keywords in self.inappropriate_keywords.items():
            total_keywords += len(keywords)
            for keyword in keywords:
                if keyword in text:
                    found_keywords += 1
        
        return found_keywords / max(total_keywords, 1) if total_keywords > 0 else 0.0

    def _check_brand_safety(self, text: str) -> float:
        """Assess brand safety of content."""
        unsafe_count = sum(1 for keyword in self.brand_unsafe_keywords if keyword in text)
        safe_indicators = sum(1 for indicator in self.quality_indicators if indicator in text)
        
        # Calculate brand safety score (0-1, higher is safer)
        if unsafe_count > 0:
            safety_score = max(0.0, 0.5 - (unsafe_count * 0.2))
        else:
            safety_score = min(1.0, 0.7 + (safe_indicators * 0.1))
        
        return safety_score

    def _assess_content_quality(self, text: str) -> float:
        """Assess overall content quality."""
        quality_score = 0.5  # Base score
        
        # Positive indicators
        quality_indicators_found = sum(1 for indicator in self.quality_indicators if indicator in text)
        quality_score += quality_indicators_found * 0.1
        
        # Check for proper sentence structure
        sentences = text.split('.')
        if len(sentences) > 1:
            quality_score += 0.1
        
        # Check for varied vocabulary (simple heuristic)
        words = text.split()
        unique_words = set(words)
        if len(words) > 0:
            vocabulary_diversity = len(unique_words) / len(words)
            quality_score += vocabulary_diversity * 0.2
        
        # Penalize excessive repetition
        if len(words) > 10:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            max_repetition = max(word_counts.values()) if word_counts else 1
            if max_repetition > len(words) * 0.3:  # More than 30% repetition
                quality_score -= 0.2
        
        return min(1.0, max(0.0, quality_score))

    def _check_engagement_manipulation(self, text: str) -> float:
        """Check for engagement manipulation tactics."""
        manipulation_count = sum(1 for phrase in self.engagement_red_flags if phrase in text)
        return min(1.0, manipulation_count * 0.3)

    def _check_text_structure(self, text: str) -> List[str]:
        """Check text structure and formatting issues."""
        issues = []
        
        # Check for excessive capitalization
        if text.isupper() and len(text) > 20:
            issues.append("Excessive use of capital letters")
        
        # Check for excessive punctuation
        punctuation_count = sum(1 for char in text if char in '!?.')
        if punctuation_count > len(text) * 0.1:
            issues.append("Excessive punctuation usage")
        
        # Check for excessive emojis (basic check)
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+')
        emoji_count = len(emoji_pattern.findall(text))
        if emoji_count > len(text.split()) * 0.5:  # More emojis than half the words
            issues.append("Excessive emoji usage")
        
        return issues

    def moderate_hashtags(self, hashtags: List[str]) -> ModerationResult:
        """Moderate hashtag list for safety and quality."""
        try:
            issues = []
            warnings = []
            categories = []
            details = {}
            
            # Check each hashtag
            inappropriate_hashtags = []
            for hashtag in hashtags:
                hashtag_clean = hashtag.replace('#', '').lower()
                
                # Check against inappropriate keywords
                for category, keywords in self.inappropriate_keywords.items():
                    if any(keyword in hashtag_clean for keyword in keywords):
                        inappropriate_hashtags.append(hashtag)
                        break
            
            if inappropriate_hashtags:
                issues.append(f"Inappropriate hashtags detected: {', '.join(inappropriate_hashtags)}")
                categories.append("inappropriate_hashtags")
            
            # Check for spam-like patterns
            if len(hashtags) > 30:
                warnings.append("Excessive number of hashtags may appear spammy")
            
            # Check for hashtag quality
            generic_hashtags = ['#love', '#instagood', '#photooftheday', '#beautiful', '#happy']
            generic_count = sum(1 for tag in hashtags if tag.lower() in [g.lower() for g in generic_hashtags])
            
            if generic_count > len(hashtags) * 0.7:
                warnings.append("Too many generic hashtags, consider more specific ones")
            
            details['inappropriate_hashtags'] = inappropriate_hashtags
            details['generic_ratio'] = generic_count / len(hashtags) if hashtags else 0
            
            is_safe = len(issues) == 0
            confidence_score = 1.0 - (len(inappropriate_hashtags) / len(hashtags)) if hashtags else 1.0
            
            return ModerationResult(
                is_safe=is_safe,
                confidence_score=confidence_score,
                issues=issues,
                warnings=warnings,
                categories=categories,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Hashtag moderation failed: {str(e)}")
            return ModerationResult(
                is_safe=False,
                confidence_score=0.0,
                issues=[f"Hashtag moderation error: {str(e)}"],
                warnings=[],
                categories=["error"],
                details={}
            )


# Global instance
_content_moderator = None


def get_content_moderator() -> ContentModerator:
    """Get the global content moderator instance."""
    global _content_moderator
    if _content_moderator is None:
        _content_moderator = ContentModerator()
    return _content_moderator


def moderate_content(text: str, context: Optional[str] = None) -> ModerationResult:
    """Convenience function for content moderation."""
    return get_content_moderator().moderate_text(text, context)


def moderate_hashtags(hashtags: List[str]) -> ModerationResult:
    """Convenience function for hashtag moderation."""
    return get_content_moderator().moderate_hashtags(hashtags)