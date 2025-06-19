#!/usr/bin/env python3
"""
TikTok Analytics Scraper
Web scrapes studio.tiktok.com for video performance metrics
Tracks views, CTR, average watch time, and engagement
"""

import time
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TikTokAnalyticsScraper:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize analytics scraper
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.driver = None
        self.wait = None
        
        # Scraping settings
        self.base_url = "https://studio.tiktok.com"
        self.login_url = f"{self.base_url}/login"
        self.analytics_url = f"{self.base_url}/analytics"
        
        logger.info("TikTok Analytics Scraper initialized")
    
    def _setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Disable images and CSS for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(
                ChromeDriverManager().install(),
                options=chrome_options
            )
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("Chrome WebDriver initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def _cleanup_driver(self):
        """Clean up WebDriver resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
    
    def login_to_studio(self, username: str, password: str) -> bool:
        """
        Login to TikTok Studio
        
        Args:
            username: TikTok username/email
            password: TikTok password
            
        Returns:
            True if login successful
        """
        try:
            self.driver.get(self.login_url)
            
            # Wait for login form
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Find and fill username field
            username_field = self.driver.find_element(By.NAME, "username")
            username_field.clear()
            username_field.send_keys(username)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit form
            login_button = self.driver.find_element(By.TYPE, "submit")
            login_button.click()
            
            # Wait for redirect to dashboard
            self.wait.until(EC.url_contains("studio.tiktok.com"))
            
            # Check if login was successful
            if "login" not in self.driver.current_url:
                logger.info("Successfully logged into TikTok Studio")
                return True
            else:
                logger.error("Login failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def scrape_video_analytics(self, video_id: str = None) -> List[Dict]:
        """
        Scrape analytics for videos
        
        Args:
            video_id: Specific video ID to scrape (None for all recent videos)
            
        Returns:
            List of video analytics dictionaries
        """
        if not self.driver:
            logger.error("WebDriver not initialized")
            return []
        
        try:
            # Navigate to analytics page
            self.driver.get(self.analytics_url)
            
            # Wait for analytics to load
            time.sleep(3)
            
            # Get video list
            videos = self._get_video_list()
            
            analytics_data = []
            
            for video in videos[:10]:  # Limit to recent 10 videos
                video_analytics = self._scrape_single_video_analytics(video)
                if video_analytics:
                    analytics_data.append(video_analytics)
                
                # Random delay between requests
                time.sleep(random.uniform(1, 3))
            
            logger.info(f"Scraped analytics for {len(analytics_data)} videos")
            return analytics_data
            
        except Exception as e:
            logger.error(f"Failed to scrape analytics: {e}")
            return []
    
    def _get_video_list(self) -> List[Dict]:
        """Get list of videos from analytics page"""
        videos = []
        
        try:
            # Look for video elements (this would need to be adapted to actual TikTok Studio structure)
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='video-item']")
            
            for element in video_elements:
                try:
                    # Extract video information
                    video_id = element.get_attribute("data-video-id")
                    video_url = element.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    videos.append({
                        'id': video_id,
                        'url': video_url,
                        'element': element
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to extract video info: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to get video list: {e}")
        
        return videos
    
    def _scrape_single_video_analytics(self, video: Dict) -> Optional[Dict]:
        """
        Scrape analytics for a single video
        
        Args:
            video: Video dictionary with id and url
            
        Returns:
            Video analytics dictionary
        """
        try:
            # Click on video to view details
            video['element'].click()
            
            # Wait for analytics to load
            time.sleep(2)
            
            # Extract metrics (these selectors would need to be adapted to actual TikTok Studio)
            analytics = {
                'video_id': video['id'],
                'scraped_at': datetime.now().isoformat(),
                'views': self._extract_metric('views'),
                'likes': self._extract_metric('likes'),
                'shares': self._extract_metric('shares'),
                'comments': self._extract_metric('comments'),
                'watch_time': self._extract_metric('watch_time'),
                'ctr': self._extract_metric('ctr'),
                'engagement_rate': self._extract_metric('engagement_rate')
            }
            
            # Go back to video list
            self.driver.back()
            time.sleep(1)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to scrape video {video['id']}: {e}")
            return None
    
    def _extract_metric(self, metric_name: str) -> float:
        """
        Extract specific metric from current page
        
        Args:
            metric_name: Name of metric to extract
            
        Returns:
            Metric value as float
        """
        try:
            # These selectors would need to be adapted to actual TikTok Studio structure
            selectors = {
                'views': "[data-testid='views-count']",
                'likes': "[data-testid='likes-count']",
                'shares': "[data-testid='shares-count']",
                'comments': "[data-testid='comments-count']",
                'watch_time': "[data-testid='watch-time']",
                'ctr': "[data-testid='ctr']",
                'engagement_rate': "[data-testid='engagement-rate']"
            }
            
            selector = selectors.get(metric_name)
            if not selector:
                return 0.0
            
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            text = element.text.strip()
            
            # Parse numeric value from text
            return self._parse_numeric_value(text)
            
        except NoSuchElementException:
            logger.warning(f"Metric {metric_name} not found on page")
            return 0.0
        except Exception as e:
            logger.error(f"Failed to extract {metric_name}: {e}")
            return 0.0
    
    def _parse_numeric_value(self, text: str) -> float:
        """
        Parse numeric value from text (handles K, M suffixes)
        
        Args:
            text: Text containing numeric value
            
        Returns:
            Parsed numeric value
        """
        if not text:
            return 0.0
        
        # Remove non-numeric characters except K, M, ., %
        import re
        cleaned = re.sub(r'[^\d.KM%]', '', text.upper())
        
        if not cleaned:
            return 0.0
        
        # Handle percentage
        if '%' in cleaned:
            return float(cleaned.replace('%', '')) / 100
        
        # Handle K/M suffixes
        if 'K' in cleaned:
            return float(cleaned.replace('K', '')) * 1000
        elif 'M' in cleaned:
            return float(cleaned.replace('M', '')) * 1000000
        else:
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
    
    def save_analytics_to_db(self, analytics_data: List[Dict]):
        """
        Save analytics data to database
        
        Args:
            analytics_data: List of analytics dictionaries
        """
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        # Create analytics table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                watch_time REAL DEFAULT 0,
                ctr REAL DEFAULT 0,
                engagement_rate REAL DEFAULT 0,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert analytics data
        for data in analytics_data:
            cursor.execute('''
                INSERT INTO video_analytics 
                (video_id, views, likes, shares, comments, watch_time, ctr, engagement_rate, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['video_id'],
                int(data['views']),
                int(data['likes']),
                int(data['shares']),
                int(data['comments']),
                data['watch_time'],
                data['ctr'],
                data['engagement_rate'],
                data['scraped_at']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved analytics for {len(analytics_data)} videos to database")
    
    def update_bandit_rewards(self):
        """Update bandit rewards based on latest analytics"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        # Get recent analytics with corresponding uploads
        cursor.execute('''
            SELECT 
                va.video_id,
                va.views,
                va.likes,
                va.shares,
                va.comments,
                vu.hashtag
            FROM video_analytics va
            JOIN video_uploads vu ON va.video_id = vu.tiktok_video_id
            WHERE va.scraped_at >= datetime('now', '-24 hours')
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        # Update bandit with performance data
        from bandit import TrendBandit
        bandit = TrendBandit()
        
        for video_id, views, likes, shares, comments, hashtag in results:
            metrics = {
                'views': views,
                'likes': likes,
                'shares': shares,
                'comments': comments
            }
            
            bandit.update_reward(hashtag, metrics)
        
        logger.info(f"Updated bandit rewards for {len(results)} videos")
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary from analytics data"""
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        # Get recent performance metrics
        cursor.execute('''
            SELECT 
                AVG(views) as avg_views,
                AVG(likes) as avg_likes,
                AVG(shares) as avg_shares,
                AVG(comments) as avg_comments,
                AVG(ctr) as avg_ctr,
                AVG(engagement_rate) as avg_engagement,
                COUNT(*) as total_videos
            FROM video_analytics
            WHERE scraped_at >= datetime('now', '-7 days')
        ''')
        
        result = cursor.fetchone()
        
        # Get top performing videos
        cursor.execute('''
            SELECT video_id, views, engagement_rate
            FROM video_analytics
            WHERE scraped_at >= datetime('now', '-7 days')
            ORDER BY views DESC
            LIMIT 5
        ''')
        
        top_videos = cursor.fetchall()
        conn.close()
        
        return {
            'avg_views': result[0] or 0,
            'avg_likes': result[1] or 0,
            'avg_shares': result[2] or 0,
            'avg_comments': result[3] or 0,
            'avg_ctr': result[4] or 0,
            'avg_engagement': result[5] or 0,
            'total_videos': result[6] or 0,
            'top_videos': [
                {'video_id': row[0], 'views': row[1], 'engagement': row[2]}
                for row in top_videos
            ]
        }
    
    def run_analytics_cycle(self, username: str = None, password: str = None):
        """
        Run complete analytics scraping cycle
        
        Args:
            username: TikTok username (from env if not provided)
            password: TikTok password (from env if not provided)
        """
        try:
            # Setup driver
            self._setup_driver()
            
            # Use environment variables if credentials not provided
            if not username:
                import os
                username = os.getenv('TIKTOK_USERNAME')
                password = os.getenv('TIKTOK_PASSWORD')
            
            if not username or not password:
                logger.error("TikTok credentials not provided")
                return
            
            # Login to TikTok Studio
            if not self.login_to_studio(username, password):
                logger.error("Failed to login to TikTok Studio")
                return
            
            # Scrape analytics
            analytics_data = self.scrape_video_analytics()
            
            if analytics_data:
                # Save to database
                self.save_analytics_to_db(analytics_data)
                
                # Update bandit rewards
                self.update_bandit_rewards()
                
                # Log summary
                summary = self.get_performance_summary()
                logger.info(f"Analytics Summary: {summary['total_videos']} videos, "
                          f"avg {summary['avg_views']:.0f} views, "
                          f"{summary['avg_engagement']:.1%} engagement")
            
        except Exception as e:
            logger.error(f"Analytics cycle failed: {e}")
        finally:
            # Always cleanup
            self._cleanup_driver()

def main():
    """Main function for testing analytics scraper"""
    scraper = TikTokAnalyticsScraper()
    
    print("TikTok Analytics Scraper Test")
    print("=" * 40)
    
    # Note: This would require actual TikTok credentials
    print("This is a test run - actual scraping requires TikTok Studio credentials")
    
    # Show performance summary from existing data
    summary = scraper.get_performance_summary()
    print(f"\nCurrent Performance Summary:")
    print(f"Total videos analyzed: {summary['total_videos']}")
    print(f"Average views: {summary['avg_views']:.0f}")
    print(f"Average engagement: {summary['avg_engagement']:.1%}")
    
    if summary['top_videos']:
        print(f"\nTop performing videos:")
        for video in summary['top_videos']:
            print(f"  {video['video_id']}: {video['views']:.0f} views")

if __name__ == "__main__":
    main()
