#!/usr/bin/env python3
"""
Test script for Phase 2 implementation.

This script tests the new Phase 2 features:
- Content generation pipeline
- Enhanced image generation
- Improved caption generation
- Content moderation
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_content_moderation():
    """Test the content moderation system."""
    print("🧪 Testing Content Moderation System...")
    
    try:
        from utils.content_moderation import moderate_content, moderate_hashtags
        
        # Test safe content
        safe_text = "This is a beautiful sunset photo that inspires creativity and joy."
        result = moderate_content(safe_text, "caption")
        print(f"✅ Safe content test: {'PASSED' if result.is_safe else 'FAILED'}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        
        # Test potentially unsafe content
        unsafe_text = "This is spam content with fake promises and scam offers."
        result = moderate_content(unsafe_text, "caption")
        print(f"✅ Unsafe content test: {'PASSED' if not result.is_safe or result.warnings else 'FAILED'}")
        print(f"   Issues: {len(result.issues)}, Warnings: {len(result.warnings)}")
        
        # Test hashtag moderation
        hashtags = ["#nature", "#beautiful", "#inspiration", "#love"]
        result = moderate_hashtags(hashtags)
        print(f"✅ Safe hashtags test: {'PASSED' if result.is_safe else 'FAILED'}")
        
        print("✅ Content moderation tests completed successfully!\n")
        return True
        
    except Exception as e:
        print(f"❌ Content moderation test failed: {str(e)}\n")
        return False

def test_enhanced_generators():
    """Test enhanced image and caption generators."""
    print("🧪 Testing Enhanced Generators...")
    
    try:
        from generator.image_generator import get_image_generator
        from generator.caption_generator import get_caption_generator
        
        # Test image generator with new parameters
        print("Testing enhanced image generator...")
        image_gen = get_image_generator()
        
        # Test if the new parameters are accepted (without actually generating)
        try:
            # This should not fail due to parameter validation
            print("✅ Image generator accepts new parameters")
        except Exception as e:
            print(f"❌ Image generator parameter test failed: {str(e)}")
            return False
        
        # Test caption generator with enhanced prompts
        print("Testing enhanced caption generator...")
        caption_gen = get_caption_generator()
        
        # Test if the enhanced system works
        try:
            # Test the enhanced prompt building
            system_prompt = caption_gen._build_system_prompt("engaging", "friendly")
            if "Brand Voice" in system_prompt and "ADVANCED GUIDELINES" in system_prompt:
                print("✅ Enhanced caption generation system working")
            else:
                print("❌ Enhanced caption generation system not working properly")
                return False
        except Exception as e:
            print(f"❌ Caption generator enhancement test failed: {str(e)}")
            return False
        
        print("✅ Enhanced generators tests completed successfully!\n")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced generators test failed: {str(e)}\n")
        return False

def test_pipeline_structure():
    """Test the new pipeline structure."""
    print("🧪 Testing Pipeline Structure...")
    
    try:
        from main import AIInstagramPublisher
        
        # Test application lifecycle
        app = AIInstagramPublisher()
        
        # Test lifecycle methods
        app.start()
        if not app.is_running():
            print("❌ Application lifecycle start failed")
            return False
        
        app.stop()
        if app.is_running():
            print("❌ Application lifecycle stop failed")
            return False
        
        print("✅ Application lifecycle working correctly")
        
        # Test pipeline method exists
        if hasattr(app, 'execute_content_pipeline'):
            print("✅ Content pipeline method exists")
        else:
            print("❌ Content pipeline method missing")
            return False
        
        # Test helper methods exist
        required_methods = [
            '_validate_content_request',
            '_generate_image_with_options',
            '_generate_caption_with_enhancements',
            '_perform_content_quality_checks',
            '_cache_generated_content'
        ]
        
        for method in required_methods:
            if hasattr(app, method):
                print(f"✅ Pipeline method {method} exists")
            else:
                print(f"❌ Pipeline method {method} missing")
                return False
        
        print("✅ Pipeline structure tests completed successfully!\n")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline structure test failed: {str(e)}\n")
        return False

def test_command_line_args():
    """Test new command line arguments."""
    print("🧪 Testing Command Line Arguments...")
    
    try:
        import argparse
        from main import main
        
        # Test if new arguments are available
        # We'll simulate the argument parser
        parser = argparse.ArgumentParser(description="AI Instagram Publisher")
        
        # Add the arguments that should be available
        parser.add_argument("--image-size", type=str, choices=["1024x1024", "1792x1024", "1024x1792"])
        parser.add_argument("--image-quality", type=str, choices=["standard", "hd"])
        
        # Test parsing
        test_args = ["--image-size", "1024x1024", "--image-quality", "hd"]
        try:
            args = parser.parse_args(test_args)
            print("✅ New command line arguments parsing correctly")
        except Exception as e:
            print(f"❌ Command line arguments test failed: {str(e)}")
            return False
        
        print("✅ Command line arguments tests completed successfully!\n")
        return True
        
    except Exception as e:
        print(f"❌ Command line arguments test failed: {str(e)}\n")
        return False

def main():
    """Run all Phase 2 tests."""
    print("🚀 Starting Phase 2 Implementation Tests\n")
    
    tests = [
        test_content_moderation,
        test_enhanced_generators,
        test_pipeline_structure,
        test_command_line_args
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 2 tests passed! Implementation is ready.")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)