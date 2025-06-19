#!/usr/bin/env python3
"""
Test Script for TikTok Video Creation
Quick test to verify the video creation pipeline works
Usage: python test_video.py --once
"""

import sys
import os
import logging
from datetime import datetime

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_prompt import PromptBuilder
from build_video import TikTokVideoBuilder

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_video_creation():
    """Test the complete video creation pipeline"""
    
    print("🎬 TikTok Video Creation Test")
    print("=" * 50)
    
    try:
        # Step 1: Create prompt builder
        print("📝 Initializing prompt builder...")
        prompt_builder = PromptBuilder()
        
        # Step 2: Generate test script
        print("🎯 Generating test script...")
        test_hashtag = "#gpu"
        script = prompt_builder.generate_script(test_hashtag, style="power")
        
        print(f"✅ Script generated:")
        print(f"   Hashtag: {script['hashtag']}")
        print(f"   Main Text: {script['main_text']}")
        print(f"   Style: {script['style']}")
        print(f"   CTA: {script['call_to_action']}")
        print(f"   Emojis: {' '.join(script['emoji_sequence'])}")
        print(f"   Duration: {script['timing']['total_duration']:.1f}s")
        
        # Step 3: Create video builder
        print("\n🎥 Initializing video builder...")
        video_builder = TikTokVideoBuilder()
        
        # Step 4: Create test video
        print("🚀 Creating test video...")
        output_path = f"test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        try:
            video_path = video_builder.create_video(script, output_path)
            print(f"✅ Video created successfully: {video_path}")
            
            # Check if file exists and get size
            if os.path.exists(video_path):
                file_size = os.path.getsize(video_path)
                print(f"   File size: {file_size / (1024*1024):.2f} MB")
            else:
                print("❌ Video file not found after creation")
                return False
                
        except Exception as e:
            print(f"❌ Video creation failed: {e}")
            return False
        
        # Step 5: Save script to database
        print("\n💾 Saving script to database...")
        prompt_builder.save_script_to_db(script)
        print("✅ Script saved to database")
        
        print(f"\n🎉 Test completed successfully!")
        print(f"📁 Output video: {video_path}")
        print(f"🎬 You can now play the video to verify it looks correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.exception("Test failed")
        return False

def test_individual_components():
    """Test individual components separately"""
    
    print("\n🔧 Testing Individual Components")
    print("=" * 40)
    
    # Test 1: Prompt Builder
    print("1️⃣ Testing Prompt Builder...")
    try:
        builder = PromptBuilder()
        script = builder.generate_script("#ai", "tech")
        print(f"   ✅ Generated: {script['main_text']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 2: Video Builder Initialization
    print("2️⃣ Testing Video Builder...")
    try:
        video_builder = TikTokVideoBuilder()
        print(f"   ✅ Initialized with {video_builder.width}x{video_builder.height} @ {video_builder.fps}fps")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 3: Asset Directories
    print("3️⃣ Testing Asset Directories...")
    try:
        bg_dir = video_builder.bg_dir
        overlay_dir = video_builder.overlay_dir
        
        print(f"   Background dir: {bg_dir}")
        print(f"   Overlay dir: {overlay_dir}")
        
        # Create directories if they don't exist
        os.makedirs(bg_dir, exist_ok=True)
        os.makedirs(overlay_dir, exist_ok=True)
        os.makedirs("output", exist_ok=True)
        
        print("   ✅ Asset directories ready")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 4: LUT File
    print("4️⃣ Testing LUT File...")
    lut_path = "luts/teal_orange.cube"
    if os.path.exists(lut_path):
        print(f"   ✅ LUT file found: {lut_path}")
    else:
        print(f"   ⚠️  LUT file not found: {lut_path}")
        print("   Color grading will be skipped")
    
    print("✅ All component tests passed!")
    return True

def main():
    """Main test function"""
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        print("Running single test video creation...")
    
    # Test individual components first
    if not test_individual_components():
        print("❌ Component tests failed")
        return 1
    
    # Test complete video creation
    if not test_video_creation():
        print("❌ Video creation test failed")
        return 1
    
    print("\n🎉 All tests passed successfully!")
    print("\nNext steps:")
    print("1. Add background images to assets/bg/")
    print("2. Add overlay elements to assets/overlays/")
    print("3. Configure TikTok API credentials in .env")
    print("4. Run the full pipeline with ./scheduler.sh")
    
    return 0

if __name__ == "__main__":
    exit(main())
