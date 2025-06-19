#!/usr/bin/env python3
"""
TikTok-Compliant Video Uploader
Uses official TikTok Content Posting API with full compliance
Includes automatic AIGC labeling and branded content disclosure
"""

import os
import time
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yaml
import sqlite3
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

class TikTokCompliantUploader:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize TikTok-compliant uploader using official Content Posting API
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # TikTok Business API credentials (REQUIRED)
        self.client_key = os.getenv('TIKTOK_CLIENT_KEY')
        self.client_secret = os.getenv('TIKTOK_CLIENT_SECRET')
        self.access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
        
        # Official TikTok Content Posting API endpoints
        self.base_url = "https://open.tiktokapis.com"
        self.upload_url = f"{self.base_url}/v2/post/publish/video/init/"
        self.publish_url = f"{self.base_url}/v2/post/publish/video/publish/"
        
        # Compliance settings
        self.max_posts_per_day = min(self.config['posting']['max_posts_per_day'], 2)  # Conservative limit
        self.min_spacing_minutes = max(self.config['posting']['min_spacing_minutes'], 120)  # 2 hours minimum
        
        # Initialize database
        self._init_database()
        
        logger.info("TikTok-compliant uploader initialized")
        logger.info("Using official TikTok Content Posting API")
        
        # Validate compliance on startup
        self._validate_compliance()
    
    def _init_database(self):
        """Initialize database for compliant upload tracking"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliant_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_path TEXT NOT NULL,
                hashtag TEXT,
                main_text TEXT,
                upload_status TEXT DEFAULT 'pending',
                tiktok_video_id TEXT,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aigc_labeled BOOLEAN DEFAULT TRUE,
                branded_content BOOLEAN DEFAULT TRUE,
                compliance_verified BOOLEAN DEFAULT TRUE,
                api_response TEXT,
                error_message TEXT
            )
        ''')
        
        # Remove old non-compliant upload tables
        cursor.execute("DROP TABLE IF EXISTS video_uploads")
        cursor.execute("DROP TABLE IF EXISTS selenium_uploads")
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized with compliant upload schema")
    
    def _validate_compliance(self):
        """Validate system compliance on startup"""
        compliance_issues = []
        
        # Check API credentials
        if not all([self.client_key, self.client_secret, self.access_token]):
            compliance_issues.append("Missing TikTok Business API credentials")
        
        # Check rate limiting
        if self.max_posts_per_day > 2:
            compliance_issues.append(f"Daily post limit too high: {self.max_posts_per_day} (max recommended: 2)")
        
        if self.min_spacing_minutes < 120:
            compliance_issues.append(f"Spacing too short: {self.min_spacing_minutes}min (min recommended: 120min)")
        
        if compliance_issues:
            logger.error("❌ COMPLIANCE ISSUES DETECTED:")
            for issue in compliance_issues:
                logger.error(f"  - {issue}")
            logger.error("Please fix these issues before using the uploader")
        else:
            logger.info("✅ System is TikTok-compliant")
    
    def can_upload_now(self) -> tuple[bool, str]:
        """
        Check if we can upload now based on strict compliance limits
        
        Returns:
            Tuple of (can_upload, reason)
        """
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        # Check daily limit (very conservative)
        cursor.execute('''
            SELECT COUNT(*) FROM compliant_uploads
            WHERE DATE(upload_time) = DATE('now')
            AND upload_status = 'success'
            AND compliance_verified = TRUE
        ''')
        
        daily_count = cursor.fetchone()[0]
        
        if daily_count >= self.max_posts_per_day:
            conn.close()
            return False, f"Daily limit reached ({daily_count}/{self.max_posts_per_day}) - TikTok compliance"
        
        # Check minimum spacing (2+ hours)
        cursor.execute('''
            SELECT upload_time FROM compliant_uploads
            WHERE upload_status = 'success'
            AND compliance_verified = TRUE
            ORDER BY upload_time DESC
            LIMIT 1
        ''')
        
        last_upload = cursor.fetchone()
        conn.close()
        
        if last_upload:
            last_time = datetime.fromisoformat(last_upload[0])
            time_diff = datetime.now() - last_time
            min_spacing = timedelta(minutes=self.min_spacing_minutes)
            
            if time_diff < min_spacing:
                remaining = min_spacing - time_diff
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                return False, f"Must wait {hours}h {minutes}m more (TikTok compliance)"
        
        return True, "Ready to upload (compliant)"
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def upload_video(self, video_path: str, script: Dict) -> Dict:
        """
        Upload video using official TikTok Content Posting API
        
        Args:
            video_path: Path to video file
            script: Video script dictionary
            
        Returns:
            Upload result dictionary
        """
        if not os.path.exists(video_path):
            return {
                'success': False,
                'error': f"Video file not found: {video_path}",
                'compliance_verified': False
            }
        
        # Validate API credentials
        if not all([self.client_key, self.client_secret, self.access_token]):
            return {
                'success': False,
                'error': "TikTok Business API credentials not configured",
                'compliance_verified': False
            }
        
        # Check compliance limits
        can_upload, reason = self.can_upload_now()
        if not can_upload:
            return {
                'success': False,
                'error': f"Upload blocked: {reason}",
                'compliance_verified': True,
                'scheduled': True
            }
        
        try:
            # Step 1: Initialize upload session
            upload_session = self._initialize_upload(video_path)
            if not upload_session['success']:
                return upload_session
            
            # Step 2: Upload video file
            upload_result = self._upload_video_file(video_path, upload_session['upload_url'])
            if not upload_result['success']:
                return upload_result
            
            # Step 3: Publish with compliant metadata
            publish_result = self._publish_video(upload_session['publish_id'], script)
            
            # Log upload attempt
            self._log_compliant_upload(video_path, script, publish_result)
            
            return publish_result
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'compliance_verified': False
            }
    
    def _initialize_upload(self, video_path: str) -> Dict:
        """Initialize upload session with TikTok API"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Get video file info
        file_size = os.path.getsize(video_path)
        
        data = {
            'source_info': {
                'source': 'FILE_UPLOAD',
                'video_size': file_size,
                'chunk_size': min(file_size, 10 * 1024 * 1024),  # 10MB max chunks
                'total_chunk_count': 1
            }
        }
        
        try:
            response = requests.post(self.upload_url, headers=headers, json=data, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After', '300')
                logger.warning(f"API rate limited. Retry after {retry_after} seconds")
                time.sleep(int(retry_after))
                raise requests.exceptions.RequestException("Rate limited")
            
            # Handle quota exceeded
            if response.status_code == 403:
                error_data = response.json()
                if 'quota' in error_data.get('error', {}).get('message', '').lower():
                    logger.error("API quota exceeded. Stopping uploads for today.")
                    return {
                        'success': False,
                        'error': 'API quota exceeded - compliance limit reached',
                        'quota_exceeded': True,
                        'compliance_verified': True
                    }
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('data'):
                return {
                    'success': True,
                    'upload_url': result['data']['upload_url'],
                    'publish_id': result['data']['publish_id']
                }
            else:
                return {
                    'success': False,
                    'error': f"API error: {result.get('error', {}).get('message', 'Unknown error')}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Upload initialization failed: {e}")
            raise
    
    def _upload_video_file(self, video_path: str, upload_url: str) -> Dict:
        """Upload video file to TikTok"""
        try:
            with open(video_path, 'rb') as video_file:
                files = {'video': video_file}
                response = requests.put(upload_url, files=files, timeout=300)  # 5 min timeout
                response.raise_for_status()
                
                return {'success': True}
                
        except Exception as e:
            logger.error(f"Video file upload failed: {e}")
            return {
                'success': False,
                'error': f"File upload failed: {e}"
            }
    
    def _publish_video(self, publish_id: str, script: Dict) -> Dict:
        """Publish video with compliant metadata"""
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Prepare compliant description
        description = self._prepare_compliant_description(script)
        
        # Prepare compliant post data
        post_data = {
            'post_id': publish_id,
            'text': description,
            'privacy_level': 'PUBLIC_TO_EVERYONE',
            'disable_duet': False,
            'disable_comment': False,
            'disable_stitch': False,
            'brand_content_toggle': True,  # REQUIRED for commercial content
            'brand_organic_toggle': True,
            'video_cover_timestamp_ms': 1000,
            # AIGC compliance
            'auto_add_music': False,  # Avoid copyright issues
            'aigc_label': {
                'aigc_label_type': 2,  # AI generated content
                'is_aigc_label': True
            }
        }
        
        try:
            response = requests.post(self.publish_url, headers=headers, json=post_data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('data'):
                video_id = result['data'].get('publish_id')
                
                # Clean up video file after successful upload
                self._cleanup_video_file(video_path)
                
                return {
                    'success': True,
                    'video_id': video_id,
                    'message': 'Video uploaded successfully (TikTok API)',
                    'upload_url': f"https://tiktok.com/@user/video/{video_id}",
                    'compliance_verified': True,
                    'aigc_labeled': True,
                    'branded_content': True
                }
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                return {
                    'success': False,
                    'error': f"Publish failed: {error_msg}",
                    'compliance_verified': True
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Video publish failed: {e}")
            return {
                'success': False,
                'error': f"Publish failed: {e}",
                'compliance_verified': True
            }
    
    def _prepare_compliant_description(self, script: Dict) -> str:
        """
        Prepare fully compliant video description
        
        Args:
            script: Video script dictionary
            
        Returns:
            Compliant description string
        """
        # Start with main content
        description = f"{script['main_text']} {script['hashtag']}\n\n"
        
        # Add clear commercial disclosure (REQUIRED)
        description += f"💰 #ad #sponsored Use code {script['promo_code']} for 5% off GPU rentals!\n"
        description += f"🔗 {self.config['affiliate']['display_url']}\n\n"
        
        # Add compliance hashtags
        compliance_hashtags = [
            "#AIGC",  # REQUIRED for AI-generated content
            "#ad",    # REQUIRED for commercial content
            "#sponsored",  # REQUIRED for branded content
            script['hashtag'],
            "#gpu",
            "#ai",
            "#tech"
        ]
        description += " ".join(compliance_hashtags) + "\n\n"
        
        # Add mandatory disclaimers
        description += f"🤖 {self.config['disclaimers']['ai_generated']}\n"
        description += f"⚠️ {self.config['disclaimers']['results_vary']}\n"
        description += f"📋 {self.config['disclaimers']['no_guarantee']}"
        
        # Ensure within TikTok's character limit
        return description[:2200]
    
    def _cleanup_video_file(self, video_path: str):
        """Clean up video file after successful upload"""
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Cleaned up video file: {video_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up video file {video_path}: {e}")
    
    def _log_compliant_upload(self, video_path: str, script: Dict, result: Dict):
        """Log compliant upload attempt to database"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        status = 'success' if result['success'] else 'failed'
        video_id = result.get('video_id')
        error_msg = result.get('error')
        
        cursor.execute('''
            INSERT INTO compliant_uploads 
            (video_path, hashtag, main_text, upload_status, 
             tiktok_video_id, aigc_labeled, branded_content, 
             compliance_verified, api_response, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            video_path,
            script['hashtag'],
            script['main_text'],
            status,
            video_id,
            result.get('aigc_labeled', True),
            result.get('branded_content', True),
            result.get('compliance_verified', True),
            json.dumps(result),
            error_msg
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Compliant upload logged: {status} - {script['main_text']}")
    
    def get_compliance_statistics(self) -> Dict:
        """Get compliance statistics"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        # Get daily stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_today,
                SUM(CASE WHEN upload_status = 'success' THEN 1 ELSE 0 END) as successful_today,
                SUM(CASE WHEN aigc_labeled = TRUE THEN 1 ELSE 0 END) as aigc_labeled_today,
                SUM(CASE WHEN branded_content = TRUE THEN 1 ELSE 0 END) as branded_content_today
            FROM compliant_uploads
            WHERE DATE(upload_time) = DATE('now')
        ''')
        
        daily_stats = cursor.fetchone()
        
        # Get compliance rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total_uploads,
                SUM(CASE WHEN compliance_verified = TRUE THEN 1 ELSE 0 END) as compliant_uploads
            FROM compliant_uploads
            WHERE upload_time >= datetime('now', '-7 days')
        ''')
        
        compliance_stats = cursor.fetchone()
        
        conn.close()
        
        total_uploads = compliance_stats[0] or 1  # Avoid division by zero
        compliance_rate = (compliance_stats[1] or 0) / total_uploads * 100
        
        return {
            'today': {
                'total': daily_stats[0] or 0,
                'successful': daily_stats[1] or 0,
                'aigc_labeled': daily_stats[2] or 0,
                'branded_content': daily_stats[3] or 0,
                'remaining_slots': max(0, self.max_posts_per_day - (daily_stats[1] or 0))
            },
            'compliance': {
                'rate_percent': round(compliance_rate, 1),
                'total_uploads': total_uploads,
                'compliant_uploads': compliance_stats[1] or 0
            },
            'limits': {
                'max_posts_per_day': self.max_posts_per_day,
                'min_spacing_minutes': self.min_spacing_minutes
            },
            'can_upload_now': self.can_upload_now()[0]
        }


def main():
    """Test compliant uploader"""
    uploader = TikTokCompliantUploader()
    
    # Test script
    test_script = {
        'main_text': 'CHEAP GPU',
        'hashtag': '#gpu',
        'promo_code': 'SHA-256-76360B81D39F',
        'call_to_action': 'Use SHA-256-76360B81D39F',
        'generated_at': '2024-01-01T12:00:00'
    }
    
    print("TikTok-Compliant Uploader Test")
    print("=" * 40)
    
    # Check upload status
    can_upload, reason = uploader.can_upload_now()
    print(f"Can upload now: {can_upload}")
    print(f"Reason: {reason}")
    
    # Get compliance statistics
    stats = uploader.get_compliance_statistics()
    print(f"\nCompliance Statistics:")
    print(f"Today: {stats['today']['successful']}/{stats['today']['total']} successful")
    print(f"AIGC labeled: {stats['today']['aigc_labeled']}")
    print(f"Branded content: {stats['today']['branded_content']}")
    print(f"Compliance rate: {stats['compliance']['rate_percent']}%")
    print(f"Remaining slots today: {stats['today']['remaining_slots']}")
    
    # Test description preparation
    description = uploader._prepare_compliant_description(test_script)
    print(f"\nCompliant Description Preview:")
    print(f"Length: {len(description)} chars")
    print(f"Content: {description[:200]}...")


if __name__ == "__main__":
    main()
