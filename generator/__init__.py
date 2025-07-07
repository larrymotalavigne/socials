"""
Generator module for AI Socials.

This module provides factory functions for creating content generators
with automatic selection based on configuration.
"""

from typing import Dict, Any
from utils.container import get_container, ICaptionGenerator, IImageGenerator


def get_caption_generator() -> ICaptionGenerator:
    """Get the configured caption generator (OpenAI or Ollama).

    Returns:
        Caption generator instance based on configuration
    """
    container = get_container()
    return container.resolve(ICaptionGenerator)


def get_image_generator() -> IImageGenerator:
    """Get the image generator.

    Returns:
        Image generator instance
    """
    container = get_container()
    return container.resolve(IImageGenerator)


def test_caption_generators() -> Dict[str, Any]:
    """Test all available caption generators.

    Returns:
        Dictionary with test results for each generator
    """
    results = {}

    try:
        # Test OpenAI generator
        from generator.caption_generator import CaptionGenerator
        openai_gen = CaptionGenerator()
        results['openai'] = openai_gen.test_connection()
    except Exception as e:
        results['openai'] = {
            'connected': False,
            'error': f'Failed to initialize: {str(e)}'
        }

    try:
        # Test Ollama generator
        from generator.ollama_caption_generator import OllamaCaptionGenerator
        ollama_gen = OllamaCaptionGenerator()
        results['ollama'] = ollama_gen.test_connection()
    except Exception as e:
        results['ollama'] = {
            'connected': False,
            'error': f'Failed to initialize: {str(e)}'
        }

    return results


def get_available_caption_generators() -> Dict[str, str]:
    """Get list of available caption generators.

    Returns:
        Dictionary mapping generator names to descriptions
    """
    return {
        'openai': 'OpenAI GPT-based caption generator',
        'ollama': 'Ollama local LLM caption generator'
    }
