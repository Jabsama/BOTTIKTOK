#!/usr/bin/env python3
"""
Unit tests for bandit.py
Tests the ε-greedy multi-armed bandit functionality
"""

import pytest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module to test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bandit import TrendBandit

class TestTrendBandit:
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary config file for testing"""
        config_data = {
            'bandit': {
                'epsilon': 0.1,
                'min_selections': 3,
                'confidence_level': 0.95
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config_data, f)
            yield f.name
        
        os.unlink(f.name)
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database with test data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE trend_scores (
                hashtag TEXT PRIMARY KEY,
                final_score REAL,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE bandit_arms (
                hashtag TEXT PRIMARY KEY,
                total_selections INTEGER DEFAULT 0,
                total_reward REAL DEFAULT 0.0,
                avg_reward REAL DEFAULT 0.0,
                confidence_interval REAL DEFAULT 0.0,
                last_selected TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE bandit_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hashtag TEXT,
                decision_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expected_reward REAL,
                actual_reward REAL,
                video_views INTEGER DEFAULT 0,
                video_likes INTEGER DEFAULT 0,
                video_shares INTEGER DEFAULT 0,
                video_comments INTEGER DEFAULT 0
            )
        ''')
        
        # Insert test data
        test_trends = [
            ('#gpu', 0.85),
            ('#ai', 0.75),
            ('#tech', 0.65),
            ('#gaming', 0.55),
            ('#crypto', 0.45)
        ]
        
        for hashtag, score in test_trends:
            cursor.execute(
                'INSERT INTO trend_scores (hashtag, final_score) VALUES (?, ?)',
                (hashtag, score)
            )
        
        conn.commit()
        conn.close()
        
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def bandit(self, temp_config, temp_db):
        """Create TrendBandit instance with temporary config and database"""
        with patch('bandit.sqlite3.connect') as mock_connect:
            mock_connect.return_value = sqlite3.connect(temp_db)
            return TrendBandit(temp_config)
    
    def test_init(self, bandit):
        """Test TrendBandit initialization"""
        assert bandit.epsilon == 0.1
        assert bandit.min_selections == 3
        assert bandit.confidence_level == 0.95
    
    @patch('bandit.sqlite3.connect')
    def test_get_top_trends(self, mock_connect, bandit, temp_db):
        """Test getting top trends from database"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        trends = bandit._get_top_trends(limit=3)
        
        assert len(trends) == 3
        assert trends[0]['hashtag'] == '#gpu'  # Highest score
        assert trends[0]['score'] == 0.85
        assert trends[1]['hashtag'] == '#ai'
        assert trends[2]['hashtag'] == '#tech'
    
    @patch('bandit.sqlite3.connect')
    def test_get_arm_stats(self, mock_connect, bandit, temp_db):
        """Test getting arm statistics"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        # Add some arm data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bandit_arms (hashtag, total_selections, total_reward, avg_reward)
            VALUES (?, ?, ?, ?)
        ''', ('#gpu', 5, 2.5, 0.5))
        conn.commit()
        conn.close()
        
        stats = bandit._get_arm_stats('#gpu')
        
        assert stats['total_selections'] == 5
        assert stats['total_reward'] == 2.5
        assert stats['avg_reward'] == 0.5
    
    def test_calculate_ucb(self, bandit):
        """Test Upper Confidence Bound calculation"""
        # Test with known values
        avg_reward = 0.5
        total_selections = 10
        total_decisions = 100
        confidence_level = 0.95
        
        ucb = bandit._calculate_ucb(avg_reward, total_selections, total_decisions, confidence_level)
        
        assert isinstance(ucb, float)
        assert ucb >= avg_reward  # UCB should be at least the average reward
        
        # Test edge case: no selections
        ucb_no_selections = bandit._calculate_ucb(0, 0, 100, 0.95)
        assert ucb_no_selections == float('inf')
    
    @patch('bandit.sqlite3.connect')
    def test_select_hashtag_exploration(self, mock_connect, bandit, temp_db):
        """Test hashtag selection in exploration mode"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        # Mock random to force exploration
        with patch('random.random', return_value=0.05):  # Less than epsilon (0.1)
            hashtag = bandit.select_hashtag()
            
            # Should select a hashtag (exploration)
            assert hashtag.startswith('#')
            assert hashtag in ['#gpu', '#ai', '#tech', '#gaming', '#crypto']
    
    @patch('bandit.sqlite3.connect')
    def test_select_hashtag_exploitation(self, mock_connect, bandit, temp_db):
        """Test hashtag selection in exploitation mode"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        # Add some arm statistics to enable exploitation
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Add arms with different performance
        arms_data = [
            ('#gpu', 10, 8.0, 0.8),
            ('#ai', 8, 4.0, 0.5),
            ('#tech', 5, 1.5, 0.3)
        ]
        
        for hashtag, selections, total_reward, avg_reward in arms_data:
            cursor.execute('''
                INSERT INTO bandit_arms (hashtag, total_selections, total_reward, avg_reward)
                VALUES (?, ?, ?, ?)
            ''', (hashtag, selections, total_reward, avg_reward))
        
        conn.commit()
        conn.close()
        
        # Mock random to force exploitation
        with patch('random.random', return_value=0.5):  # Greater than epsilon (0.1)
            hashtag = bandit.select_hashtag()
            
            # Should select the best performing hashtag
            assert hashtag == '#gpu'  # Highest average reward
    
    @patch('bandit.sqlite3.connect')
    def test_update_reward(self, mock_connect, bandit, temp_db):
        """Test reward updating"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        hashtag = '#gpu'
        reward = 0.75
        
        # Update reward
        bandit.update_reward(hashtag, reward, views=1000, likes=50, shares=10, comments=5)
        
        # Check that decision was logged
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bandit_decisions WHERE hashtag = ?', (hashtag,))
        decision = cursor.fetchone()
        conn.close()
        
        assert decision is not None
        assert decision[1] == hashtag  # hashtag column
        assert decision[3] == reward   # actual_reward column
    
    def test_epsilon_greedy_behavior(self, bandit):
        """Test that epsilon-greedy behavior is working correctly"""
        # Test multiple selections to verify exploration/exploitation ratio
        exploration_count = 0
        exploitation_count = 0
        
        for _ in range(1000):
            if bandit._should_explore():
                exploration_count += 1
            else:
                exploitation_count += 1
        
        # Should be approximately 10% exploration, 90% exploitation
        exploration_ratio = exploration_count / 1000
        assert 0.05 < exploration_ratio < 0.15  # Allow some variance
    
    @patch('bandit.sqlite3.connect')
    def test_get_bandit_statistics(self, mock_connect, bandit, temp_db):
        """Test getting bandit statistics"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        # Add some test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Add decisions
        decisions_data = [
            ('#gpu', 0.8, 1000, 50, 10, 5),
            ('#ai', 0.6, 800, 40, 8, 3),
            ('#tech', 0.4, 600, 30, 6, 2)
        ]
        
        for hashtag, reward, views, likes, shares, comments in decisions_data:
            cursor.execute('''
                INSERT INTO bandit_decisions 
                (hashtag, actual_reward, video_views, video_likes, video_shares, video_comments)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (hashtag, reward, views, likes, shares, comments))
        
        conn.commit()
        conn.close()
        
        stats = bandit.get_bandit_statistics()
        
        assert 'total_decisions' in stats
        assert 'avg_reward' in stats
        assert 'best_hashtag' in stats
        assert stats['total_decisions'] == 3
        assert stats['best_hashtag'] == '#gpu'
    
    def test_confidence_interval_calculation(self, bandit):
        """Test confidence interval calculation"""
        # Test with sample data
        rewards = [0.5, 0.6, 0.7, 0.8, 0.9]
        avg_reward = np.mean(rewards)
        n_selections = len(rewards)
        
        ci = bandit._calculate_confidence_interval(avg_reward, n_selections, 0.95)
        
        assert isinstance(ci, float)
        assert ci >= 0
        
        # Test edge case: single selection
        ci_single = bandit._calculate_confidence_interval(0.5, 1, 0.95)
        assert ci_single > 0

if __name__ == '__main__':
    pytest.main([__file__])
