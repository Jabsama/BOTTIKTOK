#!/usr/bin/env python3
"""
Multi-Armed Bandit for Trend Selection
Uses ε-greedy algorithm to balance exploration vs exploitation
Selects optimal hashtags from top-20 trends for video creation
"""

import numpy as np
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import random
from mabwiser.mab import MAB, LearningPolicy, NeighborhoodPolicy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendBandit:
    def __init__(self, db_path: str = "trends.db", epsilon: float = 0.1):
        """
        Initialize multi-armed bandit for trend selection
        
        Args:
            db_path: Path to SQLite database containing trends
            epsilon: Exploration rate for ε-greedy algorithm (0.1 = 10% exploration)
        """
        self.db_path = db_path
        self.epsilon = epsilon
        self.mab = None
        self._init_database()
        self._init_bandit()
    
    def _init_database(self):
        """Initialize database tables for bandit tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table to track bandit decisions and rewards
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bandit_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hashtag TEXT NOT NULL,
                decision_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expected_reward REAL,
                actual_reward REAL DEFAULT NULL,
                video_views INTEGER DEFAULT 0,
                video_likes INTEGER DEFAULT 0,
                video_shares INTEGER DEFAULT 0,
                video_comments INTEGER DEFAULT 0,
                reward_updated_at TIMESTAMP DEFAULT NULL
            )
        ''')
        
        # Table to track arm performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bandit_arms (
                hashtag TEXT PRIMARY KEY,
                total_selections INTEGER DEFAULT 0,
                total_reward REAL DEFAULT 0.0,
                avg_reward REAL DEFAULT 0.0,
                confidence_interval REAL DEFAULT 0.0,
                last_selected TIMESTAMP DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_bandit(self):
        """Initialize MABWiser bandit algorithm"""
        # Use ε-greedy learning policy
        self.mab = MAB(
            arms=[],  # Will be populated dynamically
            learning_policy=LearningPolicy.EpsilonGreedy(epsilon=self.epsilon),
            seed=42
        )
    
    def get_top_trends_as_arms(self, limit: int = 20) -> List[str]:
        """
        Get top-ranked trends to use as bandit arms
        
        Args:
            limit: Number of top trends to consider
            
        Returns:
            List of hashtag strings to use as arms
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get top trends from trend_scores table
        cursor.execute('''
            SELECT hashtag, final_score
            FROM trend_scores
            WHERE calculated_at >= datetime('now', '-2 hours')
            ORDER BY final_score DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            # Fallback to basic trends if no scores available
            logger.warning("No trend scores found, using fallback trends")
            return self._get_fallback_arms()
        
        arms = [row[0] for row in results]
        logger.info(f"Retrieved {len(arms)} trending hashtags as bandit arms")
        return arms
    
    def _get_fallback_arms(self) -> List[str]:
        """Get fallback arms when no trend data is available"""
        return [
            '#gpu', '#ai', '#crypto', '#gaming', '#tech',
            '#nvidia', '#render', '#mining', '#cloud', '#server',
            '#performance', '#benchmark', '#build', '#setup', '#pc'
        ]
    
    def select_hashtag(self, context: Optional[Dict] = None) -> str:
        """
        Select optimal hashtag using bandit algorithm
        
        Args:
            context: Optional context information for contextual bandits
            
        Returns:
            Selected hashtag string
        """
        # Get current arms (top trends)
        current_arms = self.get_top_trends_as_arms()
        
        if not current_arms:
            logger.error("No arms available for selection")
            return "#gpu"  # Safe fallback
        
        # Update bandit with current arms
        self.mab.arms = current_arms
        
        # Get historical data for warm start
        self._warm_start_bandit()
        
        # Select arm using bandit algorithm
        try:
            if context:
                selected_arm = self.mab.predict(context)
            else:
                selected_arm = self.mab.predict()
            
            # Log the decision
            self._log_decision(selected_arm)
            
            logger.info(f"Bandit selected hashtag: {selected_arm}")
            return selected_arm
            
        except Exception as e:
            logger.error(f"Bandit selection failed: {e}")
            # Fallback to random selection from top trends
            selected = random.choice(current_arms)
            self._log_decision(selected)
            return selected
    
    def _warm_start_bandit(self):
        """Warm start the bandit with historical performance data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get historical rewards for current arms
        arms_str = "', '".join(self.mab.arms)
        cursor.execute(f'''
            SELECT hashtag, actual_reward
            FROM bandit_decisions
            WHERE hashtag IN ('{arms_str}')
            AND actual_reward IS NOT NULL
            AND decision_time >= datetime('now', '-7 days')
            ORDER BY decision_time
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        # Feed historical data to bandit
        for hashtag, reward in results:
            try:
                self.mab.partial_fit(decisions=[hashtag], rewards=[reward])
            except Exception as e:
                logger.warning(f"Failed to warm start with {hashtag}: {e}")
    
    def _log_decision(self, hashtag: str):
        """Log bandit decision to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate expected reward based on trend score
        cursor.execute('''
            SELECT final_score
            FROM trend_scores
            WHERE hashtag = ?
            ORDER BY calculated_at DESC
            LIMIT 1
        ''', (hashtag,))
        
        result = cursor.fetchone()
        expected_reward = result[0] if result else 0.0
        
        # Log decision
        cursor.execute('''
            INSERT INTO bandit_decisions 
            (hashtag, expected_reward)
            VALUES (?, ?)
        ''', (hashtag, expected_reward))
        
        # Update arm statistics
        cursor.execute('''
            INSERT OR REPLACE INTO bandit_arms 
            (hashtag, total_selections, last_selected)
            VALUES (
                ?, 
                COALESCE((SELECT total_selections FROM bandit_arms WHERE hashtag = ?), 0) + 1,
                CURRENT_TIMESTAMP
            )
        ''', (hashtag, hashtag))
        
        conn.commit()
        conn.close()
    
    def update_reward(self, hashtag: str, video_metrics: Dict):
        """
        Update reward for a previously selected hashtag based on video performance
        
        Args:
            hashtag: The hashtag that was used
            video_metrics: Dictionary with video performance metrics
                          {views, likes, shares, comments, engagement_rate}
        """
        # Calculate reward based on video performance
        reward = self._calculate_reward(video_metrics)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update the most recent decision for this hashtag
        cursor.execute('''
            UPDATE bandit_decisions
            SET 
                actual_reward = ?,
                video_views = ?,
                video_likes = ?,
                video_shares = ?,
                video_comments = ?,
                reward_updated_at = CURRENT_TIMESTAMP
            WHERE hashtag = ?
            AND actual_reward IS NULL
            ORDER BY decision_time DESC
            LIMIT 1
        ''', (
            reward,
            video_metrics.get('views', 0),
            video_metrics.get('likes', 0),
            video_metrics.get('shares', 0),
            video_metrics.get('comments', 0),
            hashtag
        ))
        
        # Update arm statistics
        cursor.execute('''
            UPDATE bandit_arms
            SET 
                total_reward = total_reward + ?,
                avg_reward = (total_reward + ?) / total_selections
            WHERE hashtag = ?
        ''', (reward, reward, hashtag))
        
        conn.commit()
        conn.close()
        
        # Update bandit with new reward
        try:
            self.mab.partial_fit(decisions=[hashtag], rewards=[reward])
            logger.info(f"Updated reward for {hashtag}: {reward:.2f}")
        except Exception as e:
            logger.warning(f"Failed to update bandit reward: {e}")
    
    def _calculate_reward(self, metrics: Dict) -> float:
        """
        Calculate reward score based on video performance metrics
        
        Args:
            metrics: Video performance metrics
            
        Returns:
            Calculated reward score (0-100)
        """
        views = metrics.get('views', 0)
        likes = metrics.get('likes', 0)
        shares = metrics.get('shares', 0)
        comments = metrics.get('comments', 0)
        
        # Weighted reward calculation
        # Views are most important, but engagement matters too
        view_score = min(views / 1000, 50)  # Cap at 50 points for views
        engagement_score = min((likes + shares * 2 + comments * 3) / 100, 30)  # Cap at 30 points
        
        # Bonus for high engagement rate
        if views > 0:
            engagement_rate = (likes + shares + comments) / views
            engagement_bonus = min(engagement_rate * 20, 20)  # Cap at 20 points
        else:
            engagement_bonus = 0
        
        total_reward = view_score + engagement_score + engagement_bonus
        return min(total_reward, 100)  # Cap total reward at 100
    
    def get_bandit_statistics(self) -> Dict:
        """
        Get bandit performance statistics
        
        Returns:
            Dictionary with bandit performance metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get overall statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_decisions,
                AVG(actual_reward) as avg_reward,
                MAX(actual_reward) as max_reward,
                COUNT(CASE WHEN actual_reward IS NOT NULL THEN 1 END) as completed_decisions
            FROM bandit_decisions
            WHERE decision_time >= datetime('now', '-7 days')
        ''')
        
        overall_stats = cursor.fetchone()
        
        # Get top performing arms
        cursor.execute('''
            SELECT hashtag, total_selections, avg_reward
            FROM bandit_arms
            WHERE total_selections > 0
            ORDER BY avg_reward DESC
            LIMIT 10
        ''')
        
        top_arms = cursor.fetchall()
        conn.close()
        
        return {
            'total_decisions': overall_stats[0] or 0,
            'avg_reward': overall_stats[1] or 0,
            'max_reward': overall_stats[2] or 0,
            'completed_decisions': overall_stats[3] or 0,
            'completion_rate': (overall_stats[3] or 0) / max(overall_stats[0] or 1, 1),
            'top_performing_arms': [
                {'hashtag': row[0], 'selections': row[1], 'avg_reward': row[2]}
                for row in top_arms
            ],
            'epsilon': self.epsilon
        }
    
    def optimize_epsilon(self) -> float:
        """
        Dynamically optimize epsilon based on performance
        
        Returns:
            New epsilon value
        """
        stats = self.get_bandit_statistics()
        
        # If we have good performance data, reduce exploration
        if stats['completed_decisions'] > 50:
            if stats['avg_reward'] > 50:  # Good performance
                new_epsilon = max(0.05, self.epsilon * 0.9)  # Reduce exploration
            else:  # Poor performance
                new_epsilon = min(0.3, self.epsilon * 1.1)   # Increase exploration
        else:
            # Not enough data, keep current epsilon
            new_epsilon = self.epsilon
        
        if new_epsilon != self.epsilon:
            logger.info(f"Optimized epsilon: {self.epsilon:.3f} -> {new_epsilon:.3f}")
            self.epsilon = new_epsilon
            # Reinitialize bandit with new epsilon
            self._init_bandit()
        
        return new_epsilon

def main():
    """Main function for testing the bandit"""
    bandit = TrendBandit(epsilon=0.15)
    
    print("TikTok Trend Bandit Test")
    print("=" * 40)
    
    # Show current arms
    arms = bandit.get_top_trends_as_arms()
    print(f"Available arms: {len(arms)}")
    for i, arm in enumerate(arms[:10], 1):
        print(f"  {i:2d}. {arm}")
    
    # Make several selections
    print(f"\nMaking 5 bandit selections:")
    for i in range(5):
        selected = bandit.select_hashtag()
        print(f"  Selection {i+1}: {selected}")
        
        # Simulate some reward feedback
        fake_metrics = {
            'views': random.randint(100, 5000),
            'likes': random.randint(10, 500),
            'shares': random.randint(1, 50),
            'comments': random.randint(1, 100)
        }
        bandit.update_reward(selected, fake_metrics)
    
    # Show statistics
    stats = bandit.get_bandit_statistics()
    print(f"\nBandit Statistics:")
    print(f"Total decisions: {stats['total_decisions']}")
    print(f"Average reward: {stats['avg_reward']:.2f}")
    print(f"Completion rate: {stats['completion_rate']:.1%}")
    print(f"Current epsilon: {stats['epsilon']:.3f}")
    
    print(f"\nTop performing hashtags:")
    for arm in stats['top_performing_arms'][:5]:
        print(f"  {arm['hashtag']:<15} {arm['avg_reward']:>6.2f} avg reward ({arm['selections']} selections)")

if __name__ == "__main__":
    main()
