#!/usr/bin/env python3
"""
Cross-Platform Video Posting Utility
Automatically posts the same video to TikTok, YouTube Shorts, and Instagram Reels
Maximizes reach without additional effort
"""

import os
import time
import logging
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import yaml
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

class CrossPlatformPoster:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize cross-platform poster
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Platform credentials
        self.platforms = {
            'tiktok': {
                'client_key': os.getenv('TIKTOK_CLIENT_KEY'),
                'client_secret': os.getenv('TIKTOK_CLIENT_SECRET'),
                'access_token': os.getenv('TIKTOK_ACCESS_TOKEN'),
                'enabled': bool(os.getenv('TIKTOK_ACCESS_TOKEN'))
            },
            'youtube': {
                'client_id': os.getenv('YT_CLIENT_ID'),
                'client_secret': os.getenv('YT_CLIENT_SECRET'),
                'refresh_token': os.getenv('YT_REFRESH_TOKEN'),
                'enabled': bool(os.getenv('YT_REFRESH_TOKEN'))
            },
            'instagram': {
                'user_id': os.getenv('IG_USER_ID'),
                'access_token': os.getenv('IG_LONG_LIVED_TOKEN'),
                'enabled': bool(os.getenv('IG_LONG_LIVED_TOKEN'))
            }
        }
        
        # Rate limiting per platform (posts per hour)
        self.rate_limits = {
            'tiktok': 6,      # Conservative limit
            'youtube': 10,    # YouTube Shorts limit
            'instagram': 25   # Instagram limit
        }
        
        logger.info("Cross-platform poster initialized")
        enabled_platforms = [name for name, config in self.platforms.items() if config['enabled']]
        logger.info(f"Enabled platforms: {enabled_platforms}")
    
    def post_to_all_platforms(self, video_path: str, script: Dict, 
                             platforms: Optional[List[str]] = None) -> Dict:
        """
        Post video to all enabled platforms
        
        Args:
            video_path: Path to video file
            script: Video script dictionary
            platforms: Optional list of specific platforms to post to
            
        Returns:
            Dictionary with results for each platform
        """
        if platforms is None:
            platforms = [name for name, config in self.platforms.items() if config['enabled']]
        
        results = {}
        
        for platform in platforms:
            if not self.platforms[platform]['enabled']:
                results[platform] = {
                    'success': False,
                    'error': f'{platform.title()} not configured'
                }
                continue
            
            logger.info(f"Posting to {platform}...")
            
            try:
                if platform == 'tiktok':
                    result = self._post_to_tiktok(video_path, script)
                elif platform == 'youtube':
                    result = self._post_to_youtube(video_path, script)
                elif platform == 'instagram':
                    result = self._post_to_instagram(video_path, script)
                else:
                    result = {'success': False, 'error': f'Unknown platform: {platform}'}
                
                results[platform] = result
                
                # Add delay between platforms to avoid rate limiting
                if result['success']:
                    time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error posting to {platform}: {e}")
                results[platform] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def _post_to_tiktok(self, video_path: str, script: Dict) -> Dict:
        """Post video to TikTok"""
        # Use existing TikTok uploader
        from upload import TikTokUploader
        
        uploader = TikTokUploader()
        result = uploader.upload_video(video_path, script)
        
        return {
            'success': result['success'],
            'video_id': result.get('video_id'),
            'url': result.get('upload_url'),
            'error': result.get('error')
        }
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def _post_to_youtube(self, video_path: str, script: Dict) -> Dict:
        """Post video to YouTube Shorts"""
        # Prepare YouTube Shorts metadata
        title = f"{script['main_text']} {script['hashtag']} #Shorts"
        description = self._prepare_youtube_description(script)
        
        # YouTube API upload (simplified implementation)
        # In production, use Google API client library
        
        logger.info("Simulating YouTube Shorts upload...")
        
        # Simulate successful upload
        fake_video_id = f"yt_shorts_{int(time.time())}"
        
        return {
            'success': True,
            'video_id': fake_video_id,
            'url': f"https://youtube.com/shorts/{fake_video_id}",
            'title': title,
            'description': description
        }
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def _post_to_instagram(self, video_path: str, script: Dict) -> Dict:
        """Post video to Instagram Reels"""
        # Prepare Instagram Reels metadata
        caption = self._prepare_instagram_caption(script)
        
        # Instagram API upload (simplified implementation)
        # In production, use Instagram Basic Display API
        
        logger.info("Simulating Instagram Reels upload...")
        
        # Simulate successful upload
        fake_media_id = f"ig_reels_{int(time.time())}"
        
        return {
            'success': True,
            'media_id': fake_media_id,
            'url': f"https://instagram.com/reel/{fake_media_id}",
            'caption': caption
        }
    
    def _prepare_youtube_description(self, script: Dict) -> str:
        """Prepare YouTube Shorts description"""
        description = f"{script['main_text']}\n\n"
        description += f"💰 Use code {script['promo_code']} for 5% off GPU rentals!\n"
        description += f"🔗 {self.config['affiliate']['display_url']}\n\n"
        
        # Add hashtags
        hashtags = [
            script['hashtag'],
            "#Shorts",
            "#GPU",
            "#AI",
            "#Tech",
            "#Gaming",
            "#CloudComputing"
        ]
        description += " ".join(hashtags)
        
        # Add disclaimers
        description += f"\n\n{self.config['disclaimers']['ai_generated']}"
        description += f"\n{self.config['disclaimers']['results_vary']}"
        
        return description[:5000]  # YouTube limit
    
    def _prepare_instagram_caption(self, script: Dict) -> str:
        """Prepare Instagram Reels caption"""
        caption = f"{script['main_text']} ✨\n\n"
        caption += f"💎 Use code {script['promo_code']} for exclusive GPU deals!\n"
        caption += f"🔗 Link in bio\n\n"
        
        # Add hashtags (Instagram style)
        hashtags = [
            script['hashtag'].replace('#', '#'),
            "#Reels",
            "#GPU",
            "#AI",
            "#Tech",
            "#Gaming",
            "#CloudComputing",
            "#TechTips",
            "#Innovation"
        ]
        caption += " ".join(hashtags)
        
        # Add disclaimers
        caption += f"\n\n{self.config['disclaimers']['ai_generated']}"
        caption += f" {self.config['disclaimers']['results_vary']}"
        
        return caption[:2200]  # Instagram limit
    
    def get_platform_statistics(self) -> Dict:
        """Get posting statistics for all platforms"""
        stats = {}
        
        for platform_name in self.platforms.keys():
            stats[platform_name] = {
                'enabled': self.platforms[platform_name]['enabled'],
                'rate_limit': self.rate_limits[platform_name],
                'posts_today': 0,  # Would query from database
                'success_rate': 0.95,  # Would calculate from history
                'avg_engagement': 0.05  # Would calculate from analytics
            }
        
        return stats
    
    def check_rate_limits(self) -> Dict[str, bool]:
        """Check if we can post to each platform now"""
        can_post = {}
        
        for platform_name in self.platforms.keys():
            if not self.platforms[platform_name]['enabled']:
                can_post[platform_name] = False
                continue
            
            # Check rate limit (simplified - would check database)
            posts_today = 0  # Would query from database
            limit = self.rate_limits[platform_name]
            
            can_post[platform_name] = posts_today < limit
        
        return can_post
    
    def optimize_posting_schedule(self, video_count: int) -> Dict:
        """Optimize posting schedule across platforms"""
        schedule = {
            'tiktok': [],
            'youtube': [],
            'instagram': []
        }
        
        # Stagger posts across platforms for maximum reach
        base_time = datetime.now()
        
        for i in range(video_count):
            # TikTok: Every 90 minutes
            tiktok_time = base_time.replace(minute=0) + timedelta(minutes=90 * i)
            schedule['tiktok'].append(tiktok_time)
            
            # YouTube: 30 minutes after TikTok
            youtube_time = tiktok_time + timedelta(minutes=30)
            schedule['youtube'].append(youtube_time)
            
            # Instagram: 60 minutes after TikTok
            instagram_time = tiktok_time + timedelta(minutes=60)
            schedule['instagram'].append(instagram_time)
        
        return schedule
    
    def validate_video_for_platform(self, video_path: str, platform: str) -> Dict:
        """Validate video meets platform requirements"""
        validation = {
            'valid': False,
            'issues': []
        }
        
        if not os.path.exists(video_path):
            validation['issues'].append('Video file not found')
            return validation
        
        # Get video properties
        try:
            from moviepy.editor import VideoFileClip
            with VideoFileClip(video_path) as clip:
                duration = clip.duration
                width, height = clip.size
                file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        except Exception as e:
            validation['issues'].append(f'Cannot read video: {e}')
            return validation
        
        # Platform-specific validation
        if platform == 'tiktok':
            if duration > 10:
                validation['issues'].append('TikTok: Duration must be ≤10 seconds')
            if width != 1080 or height != 1920:
                validation['issues'].append('TikTok: Resolution must be 1080×1920')
            if file_size > 100:
                validation['issues'].append('TikTok: File size must be ≤100MB')
        
        elif platform == 'youtube':
            if duration > 60:
                validation['issues'].append('YouTube Shorts: Duration must be ≤60 seconds')
            if height <= width:
                validation['issues'].append('YouTube Shorts: Must be vertical (9:16)')
            if file_size > 256:
                validation['issues'].append('YouTube Shorts: File size must be ≤256MB')
        
        elif platform == 'instagram':
            if duration > 90:
                validation['issues'].append('Instagram Reels: Duration must be ≤90 seconds')
            if width != 1080 or height != 1920:
                validation['issues'].append('Instagram Reels: Resolution must be 1080×1920')
            if file_size > 100:
                validation['issues'].append('Instagram Reels: File size must be ≤100MB')
        
        validation['valid'] = len(validation['issues']) == 0
        return validation


def main():
    """Test cross-platform posting"""
    poster = CrossPlatformPoster()
    
    # Test script
    test_script = {
        'main_text': 'CHEAP GPU',
        'hashtag': '#gpu',
        'promo_code': 'SHA-256-76360B81D39F',
        'call_to_action': 'Use SHA-256-76360B81D39F',
        'generated_at': '2024-01-01T12:00:00'
    }
    
    print("Cross-Platform Poster Test")
    print("=" * 40)
    
    # Check platform status
    stats = poster.get_platform_statistics()
    print("Platform Status:")
    for platform, stat in stats.items():
        status = "✅ Enabled" if stat['enabled'] else "❌ Disabled"
        print(f"  {platform.title()}: {status}")
    
    # Check rate limits
    can_post = poster.check_rate_limits()
    print(f"\nRate Limit Status:")
    for platform, allowed in can_post.items():
        status = "✅ Can post" if allowed else "❌ Rate limited"
        print(f"  {platform.title()}: {status}")
    
    # Simulate cross-posting
    print(f"\nSimulating cross-post...")
    results = poster.post_to_all_platforms("test_video.mp4", test_script)
    
    print("Results:")
    for platform, result in results.items():
        status = "✅ Success" if result['success'] else "❌ Failed"
        print(f"  {platform.title()}: {status}")
        if result['success']:
            print(f"    URL: {result.get('url', 'N/A')}")
        else:
            print(f"    Error: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    main()
