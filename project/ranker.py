#!/usr/bin/env python3
"""
Trend Ranking System
Scores trending hashtags based on view growth and engagement metrics
Uses formula: score = Δviews_1h * log10(total+1)
"""

import sqlite3
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import math

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendRanker:
    def __init__(self, db_path: str = "trends.db"):
        """
        Initialize trend ranking system
        
        Args:
            db_path: Path to SQLite database containing trends
        """
        self.db_path = db_path
    
    def calculate_trend_scores(self) -> List[Dict]:
        """
        Calculate ranking scores for all trends
        
        Returns:
            List of trends with calculated scores
        """
        conn = sqlite3.connect(self.db_path)
        
        # Get current trends with historical data
        query = '''
            SELECT 
                t.hashtag,
                t.views as current_views,
                t.posts as current_posts,
                t.growth_rate,
                t.category,
                t.source,
                t.scraped_at
            FROM trends t
            ORDER BY t.scraped_at DESC
        '''
        
        current_trends = pd.read_sql_query(query, conn)
        
        # Get historical data for growth calculation
        history_query = '''
            SELECT 
                hashtag,
                views,
                posts,
                timestamp
            FROM trend_history
            WHERE timestamp >= datetime('now', '-2 hours')
            ORDER BY hashtag, timestamp
        '''
        
        historical_data = pd.read_sql_query(history_query, conn)
        conn.close()
        
        scored_trends = []
        
        for _, trend in current_trends.iterrows():
            hashtag = trend['hashtag']
            current_views = trend['current_views']
            current_posts = trend['current_posts']
            
            # Calculate view growth over last hour
            view_growth_1h = self._calculate_view_growth(
                hashtag, current_views, historical_data, hours=1
            )
            
            # Calculate engagement rate
            engagement_rate = self._calculate_engagement_rate(
                current_views, current_posts
            )
            
            # Calculate category bonus
            category_bonus = self._get_category_bonus(trend['category'])
            
            # Calculate final score using the specified formula
            # score = Δviews_1h * log10(total+1) + bonuses
            base_score = view_growth_1h * math.log10(current_views + 1)
            final_score = base_score + engagement_rate + category_bonus
            
            scored_trends.append({
                'hashtag': hashtag,
                'views': current_views,
                'posts': current_posts,
                'view_growth_1h': view_growth_1h,
                'engagement_rate': engagement_rate,
                'category': trend['category'],
                'category_bonus': category_bonus,
                'base_score': base_score,
                'final_score': final_score,
                'source': trend['source'],
                'scraped_at': trend['scraped_at']
            })
        
        # Sort by final score (descending)
        scored_trends.sort(key=lambda x: x['final_score'], reverse=True)
        
        logger.info(f"Calculated scores for {len(scored_trends)} trends")
        return scored_trends
    
    def _calculate_view_growth(self, hashtag: str, current_views: int, 
                              historical_data: pd.DataFrame, hours: int = 1) -> float:
        """
        Calculate view growth over specified time period
        
        Args:
            hashtag: Hashtag to calculate growth for
            current_views: Current view count
            historical_data: Historical trend data
            hours: Time period in hours
            
        Returns:
            View growth rate
        """
        # Filter historical data for this hashtag
        hashtag_history = historical_data[
            historical_data['hashtag'] == hashtag
        ].sort_values('timestamp')
        
        if len(hashtag_history) < 2:
            # No historical data, use growth_rate as fallback
            return current_views * 0.1  # Assume 10% growth
        
        # Get views from specified hours ago
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        
        older_data = hashtag_history[
            hashtag_history['timestamp'] <= cutoff_str
        ]
        
        if len(older_data) == 0:
            # No data old enough, use most recent growth
            return abs(hashtag_history.iloc[-1]['views'] - hashtag_history.iloc[0]['views'])
        
        # Calculate growth
        old_views = older_data.iloc[-1]['views']
        growth = current_views - old_views
        
        return max(0, growth)  # Ensure non-negative growth
    
    def _calculate_engagement_rate(self, views: int, posts: int) -> float:
        """
        Calculate engagement rate based on views and posts
        
        Args:
            views: Total views
            posts: Total posts
            
        Returns:
            Engagement rate score
        """
        if posts == 0:
            return 0.0
        
        # Engagement rate = views per post, normalized
        engagement = views / posts
        
        # Apply logarithmic scaling to prevent extreme values
        normalized_engagement = math.log10(engagement + 1)
        
        return normalized_engagement
    
    def _get_category_bonus(self, category: str) -> float:
        """
        Get bonus score based on content category
        
        Args:
            category: Content category
            
        Returns:
            Category bonus score
        """
        category_bonuses = {
            'gpu_tech': 2.0,      # High bonus for GPU-related content
            'trending': 1.5,      # Medium bonus for general trending
            'general': 1.0,       # Base bonus
            'crypto': 1.8,        # High bonus for crypto content
            'gaming': 1.6,        # Good bonus for gaming content
            'ai': 2.2,           # Highest bonus for AI content
        }
        
        return category_bonuses.get(category.lower(), 1.0)
    
    def get_top_ranked_trends(self, limit: int = 20) -> List[Dict]:
        """
        Get top ranked trends
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of top ranked trends
        """
        scored_trends = self.calculate_trend_scores()
        return scored_trends[:limit]
    
    def save_scores_to_db(self, scored_trends: List[Dict]):
        """
        Save calculated scores to database
        
        Args:
            scored_trends: List of trends with scores
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create scores table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trend_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hashtag TEXT NOT NULL,
                views INTEGER,
                posts INTEGER,
                view_growth_1h REAL,
                engagement_rate REAL,
                category TEXT,
                category_bonus REAL,
                base_score REAL,
                final_score REAL,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Clear old scores (keep only last 24 hours)
        cursor.execute('''
            DELETE FROM trend_scores 
            WHERE calculated_at < datetime('now', '-24 hours')
        ''')
        
        # Insert new scores
        for trend in scored_trends:
            cursor.execute('''
                INSERT INTO trend_scores 
                (hashtag, views, posts, view_growth_1h, engagement_rate, 
                 category, category_bonus, base_score, final_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trend['hashtag'],
                trend['views'],
                trend['posts'],
                trend['view_growth_1h'],
                trend['engagement_rate'],
                trend['category'],
                trend['category_bonus'],
                trend['base_score'],
                trend['final_score']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved scores for {len(scored_trends)} trends to database")
    
    def get_trending_keywords(self, limit: int = 10) -> List[str]:
        """
        Extract trending keywords from top hashtags
        
        Args:
            limit: Number of top trends to analyze
            
        Returns:
            List of trending keywords
        """
        top_trends = self.get_top_ranked_trends(limit)
        
        keywords = []
        for trend in top_trends:
            hashtag = trend['hashtag'].replace('#', '').lower()
            
            # Split compound hashtags
            if len(hashtag) > 15:  # Likely compound hashtag
                # Simple splitting by common patterns
                parts = []
                current = ""
                for char in hashtag:
                    if char.isupper() and current:
                        parts.append(current.lower())
                        current = char
                    else:
                        current += char
                if current:
                    parts.append(current.lower())
                keywords.extend(parts)
            else:
                keywords.append(hashtag)
        
        # Remove duplicates and return most common
        unique_keywords = list(set(keywords))
        return unique_keywords[:limit]
    
    def analyze_trend_performance(self) -> Dict:
        """
        Analyze overall trend performance metrics
        
        Returns:
            Dictionary with performance analytics
        """
        conn = sqlite3.connect(self.db_path)
        
        # Get recent score data
        query = '''
            SELECT 
                AVG(final_score) as avg_score,
                MAX(final_score) as max_score,
                MIN(final_score) as min_score,
                COUNT(*) as total_trends,
                AVG(view_growth_1h) as avg_growth,
                AVG(engagement_rate) as avg_engagement
            FROM trend_scores
            WHERE calculated_at >= datetime('now', '-1 hour')
        '''
        
        result = conn.execute(query).fetchone()
        conn.close()
        
        if result and result[0] is not None:
            return {
                'avg_score': result[0],
                'max_score': result[1],
                'min_score': result[2],
                'total_trends': result[3],
                'avg_growth': result[4],
                'avg_engagement': result[5],
                'analysis_time': datetime.now().isoformat()
            }
        else:
            return {
                'avg_score': 0,
                'max_score': 0,
                'min_score': 0,
                'total_trends': 0,
                'avg_growth': 0,
                'avg_engagement': 0,
                'analysis_time': datetime.now().isoformat()
            }

def main():
    """Main function for testing the ranker"""
    ranker = TrendRanker()
    
    # Calculate and display top trends
    top_trends = ranker.get_top_ranked_trends(10)
    
    print("Top 10 Ranked Trends:")
    print("-" * 80)
    print(f"{'Rank':<4} {'Hashtag':<20} {'Score':<8} {'Views':<10} {'Growth':<8} {'Category':<12}")
    print("-" * 80)
    
    for i, trend in enumerate(top_trends, 1):
        print(f"{i:<4} {trend['hashtag']:<20} {trend['final_score']:<8.2f} "
              f"{trend['views']:<10,} {trend['view_growth_1h']:<8.0f} {trend['category']:<12}")
    
    # Save scores to database
    ranker.save_scores_to_db(top_trends)
    
    # Show performance analytics
    analytics = ranker.analyze_trend_performance()
    print(f"\nPerformance Analytics:")
    print(f"Total trends analyzed: {analytics['total_trends']}")
    print(f"Average score: {analytics['avg_score']:.2f}")
    print(f"Average growth: {analytics['avg_growth']:.0f} views/hour")
    print(f"Average engagement: {analytics['avg_engagement']:.2f}")

if __name__ == "__main__":
    main()
