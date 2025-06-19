#!/usr/bin/env python3
"""
Viral TikTok Remix System
Fetches trending videos, analyzes them, and creates compliant remixes
Includes duet/stitch functionality and download+transform capabilities
"""

import os
import time
import json
import logging
import sqlite3
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import yaml
import requests
from urllib.parse import urlparse, parse_qs
import subprocess

# Video processing
import yt_dlp
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, ImageClip, ColorClip
import ffmpeg

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ViralRemixer:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize viral remix system"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Remix settings
        self.remix_config = self.config['remix']
        self.mode_preference = self.remix_config['mode_preference']
        self.max_remix_per_day = self.remix_config['max_remix_per_day']
        self.min_transform_percentage = self.remix_config['min_transform_percentage']
        self.max_original_duration = self.remix_config['max_original_duration']
        self.fetch_interval_hours = self.remix_config['fetch_interval_hours']
        self.top_videos_count = self.remix_config['top_videos_count']
        
        # Brand settings
        self.promo_code = self.config['brand']['promo_code']
        self.affiliate_url = self.config['affiliate']['main_url']
        self.display_url = self.config['affiliate']['display_url']
        
        # Video settings
        self.width = self.config['video']['width']
        self.height = self.config['video']['height']
        self.fps = self.config['video']['fps_target']
        
        # Initialize database
        self._init_database()
        
        logger.info("Viral Remixer initialized")
    
    def _init_database(self):
        """Initialize database tables for remix tracking"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        # Table for viral videos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS viral_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT UNIQUE NOT NULL,
                creator_username TEXT,
                description TEXT,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                growth_rate REAL DEFAULT 0.0,
                music_id TEXT,
                music_protected BOOLEAN DEFAULT FALSE,
                stitch_allowed BOOLEAN DEFAULT TRUE,
                duet_allowed BOOLEAN DEFAULT TRUE,
                reasoned_score REAL DEFAULT 0.0,
                selection_reason TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Table for remix attempts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS remix_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_video_id TEXT NOT NULL,
                remix_method TEXT,
                transform_percentage REAL,
                output_path TEXT,
                upload_status TEXT DEFAULT 'pending',
                tiktok_video_id TEXT,
                copyright_match BOOLEAN DEFAULT FALSE,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_at TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def fetch_top_videos(self) -> List[Dict]:
        """Fetch top 100 fastest-growing TikTok videos"""
        logger.info("Fetching top viral videos...")
        
        videos = []
        
        try:
            # Generate synthetic trending data for testing
            videos = self._generate_synthetic_trending()
            
        except Exception as e:
            logger.error(f"Failed to fetch viral videos: {e}")
            videos = self._generate_synthetic_trending()
        
        # Save to database
        self._save_viral_videos(videos)
        
        logger.info(f"Fetched {len(videos)} viral videos")
        return videos[:self.top_videos_count]
    
    def _generate_synthetic_trending(self) -> List[Dict]:
        """Generate synthetic trending video data for testing"""
        videos = []
        
        # GPU/Tech related trending topics
        trending_topics = [
            "AI breakthrough", "GPU mining", "Gaming setup", "Tech review",
            "Crypto update", "Cloud computing", "Machine learning", "3D rendering",
            "Game development", "Programming tips", "Tech news", "Hardware review"
        ]
        
        for i in range(50):
            topic = random.choice(trending_topics)
            base_views = random.randint(100000, 5000000)
            growth_rate = random.uniform(0.1, 3.0)
            
            video = {
                'video_id': f'synthetic_{i}_{int(time.time())}',
                'creator_username': f'techuser{i}',
                'description': f'{topic} #tech #gpu #ai',
                'views': base_views,
                'likes': int(base_views * random.uniform(0.05, 0.15)),
                'shares': int(base_views * random.uniform(0.01, 0.05)),
                'comments': int(base_views * random.uniform(0.02, 0.08)),
                'growth_rate': growth_rate,
                'music_id': f'music_{random.randint(1000, 9999)}',
                'music_protected': random.choice([True, False]),
                'stitch_allowed': random.choice([True, False]),
                'duet_allowed': random.choice([True, False]),
                'url': f'https://tiktok.com/@techuser{i}/video/{video["video_id"]}'
            }
            
            videos.append(video)
        
        return videos
    
    def _save_viral_videos(self, videos: List[Dict]):
        """Save viral videos to database"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        for video in videos:
            cursor.execute('''
                INSERT OR REPLACE INTO viral_videos 
                (video_id, creator_username, description, views, likes, shares, comments,
                 growth_rate, music_id, music_protected, stitch_allowed, duet_allowed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video['video_id'],
                video['creator_username'],
                video['description'],
                video['views'],
                video['likes'],
                video.get('shares', 0),
                video['comments'],
                video['growth_rate'],
                video.get('music_id', ''),
                video.get('music_protected', False),
                video.get('stitch_allowed', True),
                video.get('duet_allowed', True)
            ))
        
        conn.commit()
        conn.close()
    
    def reason_select(self, video_meta_list: List[Dict]) -> List[Dict]:
        """Select top 3 videos using reasoned scoring algorithm"""
        logger.info("Analyzing and selecting top videos...")
        
        scored_videos = []
        
        for video in video_meta_list:
            # Calculate reasoned score
            views = video['views']
            growth_rate = video['growth_rate']
            
            # Calculate view growth in last hour (estimated)
            delta_views_1h = views * growth_rate * 0.1  # Simplified estimation
            
            # Base score: (Δviews_1h / total_views) * log10(total_views+1)
            if views > 0:
                base_score = (delta_views_1h / views) * math.log10(views + 1)
            else:
                base_score = 0
            
            # Stitch/Duet multiplier
            stitch_multiplier = 1.0 if video.get('stitch_allowed', True) else 0.7
            
            # Music protection multiplier
            music_multiplier = 0.5 if video.get('music_protected', False) else 1.0
            
            # Final reasoned score
            reasoned_score = base_score * stitch_multiplier * music_multiplier
            
            # Generate selection reason
            reason_parts = []
            if video.get('stitch_allowed', True):
                reason_parts.append("stitch-friendly")
            if not video.get('music_protected', False):
                reason_parts.append("music-safe")
            if growth_rate > 1.0:
                reason_parts.append("high-growth")
            if views > 1000000:
                reason_parts.append("viral-scale")
            
            selection_reason = ", ".join(reason_parts) if reason_parts else "baseline-eligible"
            
            scored_video = video.copy()
            scored_video['reasoned_score'] = reasoned_score
            scored_video['selection_reason'] = selection_reason
            
            scored_videos.append(scored_video)
        
        # Sort by reasoned score and take top 3
        scored_videos.sort(key=lambda x: x['reasoned_score'], reverse=True)
        top_3 = scored_videos[:3]
        
        # Save selection reasons to database
        self._save_selection_reasons(top_3)
        
        logger.info(f"Selected top 3 videos with scores: {[v['reasoned_score']:.3f for v in top_3]}")
        return top_3
    
    def _save_selection_reasons(self, selected_videos: List[Dict]):
        """Save selection reasons to database"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        for video in selected_videos:
            cursor.execute('''
                UPDATE viral_videos 
                SET reasoned_score = ?, selection_reason = ?, status = 'selected'
                WHERE video_id = ?
            ''', (
                video['reasoned_score'],
                video['selection_reason'],
                video['video_id']
            ))
        
        conn.commit()
        conn.close()
    
    def transform_video(self, video_id: str) -> Optional[str]:
        """Transform a viral video into a compliant remix"""
        logger.info(f"Transforming video: {video_id}")
        
        # Get video metadata from database
        video_meta = self._get_video_metadata(video_id)
        if not video_meta:
            logger.error(f"Video metadata not found: {video_id}")
            return None
        
        try:
            # Determine transformation method
            if (self.mode_preference in ['duet_only', 'mixed'] and 
                video_meta.get('stitch_allowed', True)):
                # Use stitch/duet method
                output_path = self._create_stitch_remix(video_meta)
                method = 'stitch'
            else:
                # Use download + transform method
                output_path = self._create_download_remix(video_meta)
                method = 'download_transform'
            
            if output_path:
                # Log the remix attempt
                self._log_remix_attempt(video_id, method, output_path)
                logger.info(f"Video transformed successfully: {output_path}")
                return output_path
            else:
                logger.error(f"Failed to transform video: {video_id}")
                return None
                
        except Exception as e:
            logger.error(f"Video transformation failed: {e}")
            self._log_remix_attempt(video_id, 'failed', None, error=str(e))
            return None
    
    def _get_video_metadata(self, video_id: str) -> Optional[Dict]:
        """Get video metadata from database"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT video_id, creator_username, description, views, likes, shares, comments,
                   stitch_allowed, duet_allowed, music_protected
            FROM viral_videos
            WHERE video_id = ?
        ''', (video_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'video_id': result[0],
                'creator_username': result[1],
                'description': result[2],
                'views': result[3],
                'likes': result[4],
                'shares': result[5],
                'comments': result[6],
                'stitch_allowed': result[7],
                'duet_allowed': result[8],
                'music_protected': result[9]
            }
        return None
    
    def _create_stitch_remix(self, video_meta: Dict) -> Optional[str]:
        """Create remix using TikTok's stitch functionality"""
        output_path = f"output/stitch_remix_{video_meta['video_id']}_{int(time.time())}.mp4"
        
        try:
            # Create our own content (7-8 seconds)
            from build_video import TikTokVideoBuilder
            from build_prompt import PromptBuilder
            
            # Generate script for our response
            prompt_builder = PromptBuilder()
            script = prompt_builder.generate_script("#gpu", "tech")
            
            # Modify script for stitch context
            script['main_text'] = "CHEAP GPU"
            script['call_to_action'] = f"Code {self.promo_code}"
            
            # Create video
            video_builder = TikTokVideoBuilder()
            our_video_path = video_builder.create_video(script, output_path)
            
            return our_video_path
            
        except Exception as e:
            logger.error(f"Stitch remix creation failed: {e}")
            return None
    
    def _create_download_remix(self, video_meta: Dict) -> Optional[str]:
        """Create remix by downloading and transforming original video"""
        video_id = video_meta['video_id']
        output_path = f"output/remix_{video_id}_{int(time.time())}.mp4"
        
        try:
            # For testing, create a synthetic remix
            return self._create_synthetic_remix(video_meta, output_path)
            
        except Exception as e:
            logger.error(f"Download remix creation failed: {e}")
            return None
    
    def _create_synthetic_remix(self, video_meta: Dict, output_path: str) -> Optional[str]:
        """Create synthetic remix for testing"""
        try:
            # Create gradient background
            bg_clip = ColorClip(size=(self.width, self.height), color=(0, 50, 100), duration=8)
            
            # Add text overlay
            text_clip = TextClip(
                f"Cheap GPU Rental\n{self.display_url}",
                fontsize=60,
                color='white',
                font='Arial-Bold'
            ).set_duration(8).set_position('center')
            
            # Add promo code
            promo_clip = TextClip(
                f"Code: {self.promo_code}",
                fontsize=36,
                color='#FFD54F',
                font='Arial-Bold'
            ).set_duration(8).set_position((50, self.height - 150))
            
            # Credit original creator
            credit = TextClip(
                f"🎥 original: @{video_meta['creator_username']}",
                fontsize=18,
                color='white',
                font='Arial'
            ).set_duration(8).set_position((20, self.height - 150))
            
            # Disclaimers
            disclaimer = TextClip(
                "AI generated • ⚠ Results may vary",
                fontsize=14,
                color='white',
                font='Arial'
            ).set_duration(8).set_position((20, self.height - 50))
            
            # Combine all elements
            final_clip = CompositeVideoClip([bg_clip, text_clip, promo_clip, credit, disclaimer])
            
            # Export
            final_clip.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Clean up
            final_clip.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Synthetic remix creation failed: {e}")
            return None
    
    def _log_remix_attempt(self, video_id: str, method: str, output_path: Optional[str], error: Optional[str] = None):
        """Log remix attempt to database"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        # Calculate transform percentage (simplified)
        transform_percentage = 35.0 if method == 'download_transform' else 100.0
        
        cursor.execute('''
            INSERT INTO remix_attempts 
            (original_video_id, remix_method, transform_percentage, output_path, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (video_id, method, transform_percentage, output_path, error))
        
        conn.commit()
        conn.close()
    
    def upload_remix(self, video_path: str, original_video_meta: Dict) -> Dict:
        """Upload remix video to TikTok"""
        logger.info(f"Uploading remix: {video_path}")
        
        try:
            from upload import TikTokUploader
            
            # Create upload script
            script = {
                'main_text': 'CHEAP GPU',
                'hashtag': '#gpu',
                'promo_code': self.promo_code,
                'call_to_action': f"Code {self.promo_code}",
                'generated_at': datetime.now().isoformat()
            }
            
            # Create custom caption for remix
            caption = self._create_remix_caption(original_video_meta)
            script['custom_caption'] = caption
            
            # Upload as draft first
            uploader = TikTokUploader()
            result = uploader.upload_video(video_path, script, draft=True)
            
            if result.get('success'):
                # Check for copyright match
                if self._check_copyright_match(result.get('video_id')):
                    logger.warning("Copyright match detected, marking as denied")
                    self._update_remix_status(video_path, 'denied', 'copyright_match')
                    return {'success': False, 'reason': 'copyright_match'}
                else:
                    # Publish the draft
                    publish_result = uploader.publish_draft(result.get('video_id'))
                    if publish_result.get('success'):
                        self._update_remix_status(video_path, 'published', result.get('video_id'))
                        return {'success': True, 'video_id': result.get('video_id')}
            
            self._update_remix_status(video_path, 'failed', None, result.get('error'))
            return result
            
        except Exception as e:
            logger.error(f"Remix upload failed: {e}")
            self._update_remix_status(video_path, 'failed', None, str(e))
            return {'success': False, 'error': str(e)}
    
    def _create_remix_caption(self, original_video_meta: Dict) -> str:
        """Create caption for remix video"""
        caption = f"""🔥 Powered by {self.display_url} — cheap GPUs
Earn 5% with code {self.promo_code}
🎥 original: @{original_video_meta['creator_username']}

#gpu #ai #tech #cheapgpu #voltageGPU"""
        
        return caption
    
    def _check_copyright_match(self, video_id: str) -> bool:
        """Check if TikTok detected copyright match (simplified)"""
        # In a real implementation, this would check TikTok's response
        # For now, simulate random copyright detection
        return random.random() < 0.1  # 10% chance of copyright match
    
    def _update_remix_status(self, video_path: str, status: str, video_id: Optional[str] = None, error: Optional[str] = None):
        """Update remix status in database"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE remix_attempts 
            SET upload_status = ?, tiktok_video_id = ?, error_message = ?, uploaded_at = CURRENT_TIMESTAMP
            WHERE output_path = ?
        ''', (status, video_id, error, video_path))
        
        conn.commit()
        conn.close()
    
    def get_remix_statistics(self) -> Dict:
        """Get remix performance statistics"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        # Get daily stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_today,
                SUM(CASE WHEN upload_status = 'published' THEN 1 ELSE 0 END) as published_today,
                SUM(CASE WHEN upload_status = 'denied' THEN 1 ELSE 0 END) as denied_today
            FROM remix_attempts
            WHERE DATE(created_at) = DATE('now')
        ''')
        
        daily_stats = cursor.fetchone()
        
        # Get weekly performance
        cursor.execute('''
            SELECT 
                AVG(views) as avg_views,
                AVG(likes) as avg_likes,
                COUNT(*) as total_week
            FROM remix_attempts
            WHERE created_at >= datetime('now', '-7 days')
            AND upload_status = 'published'
        ''')
        
        weekly_stats = cursor.fetchone()
        conn.close()
        
        return {
            'today': {
                'total': daily_stats[0] or 0,
                'published': daily_stats[1] or 0,
                'denied': daily_stats[2] or 0,
                'remaining_slots': max(0, self.max_remix_per_day - (daily_stats[1] or 0))
            },
            'week': {
                'total': weekly_stats[2] or 0,
                'avg_views': weekly_stats[0] or 0,
                'avg_likes': weekly_stats[1] or 0
            }
        }

def main():
    """Main function for testing viral remixer"""
    remixer = ViralRemixer()
    
    print("🎬 Viral TikTok Remixer Test")
    print("=" * 40)
    
    # Test 1: Fetch viral videos
    print("1️⃣ Fetching viral videos...")
    videos = remixer.fetch_top_videos()
    print(f"   ✅ Fetched {len(videos)} videos")
    
    # Test 2: Select top videos
    print("2️⃣ Selecting top videos...")
    top_videos = remixer.reason_select(videos)
    print(f"   ✅ Selected {len(top_videos)} videos")
    
    for i, video in enumerate(top_videos, 1):
        print(f"   {i}. {video['video_id']} (score: {video['reasoned_score']:.3f})")
        print(f"      Reason: {video['selection_reason']}")
    
    # Test 3: Transform video (simulate)
    if top_videos:
        print("3️⃣ Testing video transformation...")
        test_video = top_videos[0]
        print(f"   Transforming: {test_video['video_id']}")
        
        # For testing, we'll simulate the transformation
        print("   ✅ Transformation simulated (would create actual remix in production)")
    
    # Test 4: Get statistics
    print("4️⃣ Getting remix statistics...")
    stats = remixer.get_remix_statistics()
    print(f"   Today: {stats['today']['published']}/{stats['today']['total']} published")
    print(f"   Remaining slots: {stats['today']['remaining_slots']}")
    
    print("\n🎉 Viral remixer test completed!")

if __name__ == "__main__":
    main()
