#!/usr/bin/env python3
"""
Unit tests for viral_remix.py
Tests the viral video selection and remix functionality
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock, mock_open
import sqlite3

# Import the module to test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from viral_remix import ViralRemixer

class TestViralRemixer:
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary config file for testing"""
        config_data = {
            'remix': {
                'mode_preference': 'mixed',
                'max_remix_per_day': 2,
                'min_transform_percentage': 30,
                'max_original_duration': 3,
                'fetch_interval_hours': 2,
                'top_videos_count': 100
            },
            'brand': {
                'promo_code': 'SHA-256-76360B81D39F'
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
        
        # Create viral_videos table
        cursor.execute('''
            CREATE TABLE viral_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT UNIQUE,
                username TEXT,
                description TEXT,
                views INTEGER,
                likes INTEGER,
                shares INTEGER,
                comments INTEGER,
                growth_score REAL,
                stitch_allowed BOOLEAN,
                music_original BOOLEAN,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reasoning TEXT
            )
        ''')
        
        # Insert test data
        test_videos = [
            ('vid1', 'user1', 'GPU mining setup', 1000000, 50000, 5000, 2000, 0.85, True, True, 'High growth tech content'),
            ('vid2', 'user2', 'Gaming rig showcase', 800000, 40000, 4000, 1500, 0.75, False, False, 'Popular gaming content'),
            ('vid3', 'user3', 'AI training demo', 600000, 30000, 3000, 1000, 0.65, True, True, 'Educational AI content'),
            ('vid4', 'user4', 'Crypto news update', 400000, 20000, 2000, 800, 0.55, False, True, 'News content'),
            ('vid5', 'user5', 'Tech review', 200000, 10000, 1000, 500, 0.45, True, False, 'Review content')
        ]
        
        for video_data in test_videos:
            cursor.execute('''
                INSERT INTO viral_videos 
                (video_id, username, description, views, likes, shares, comments, 
                 growth_score, stitch_allowed, music_original, reasoning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', video_data)
        
        conn.commit()
        conn.close()
        
        yield db_path
        os.unlink(db_path)
    
    @pytest.fixture
    def remixer(self, temp_config, temp_db):
        """Create ViralRemixer instance with temporary config and database"""
        with patch('viral_remix.sqlite3.connect') as mock_connect:
            mock_connect.return_value = sqlite3.connect(temp_db)
            return ViralRemixer(temp_config)
    
    def test_init(self, remixer):
        """Test ViralRemixer initialization"""
        assert remixer.mode_preference == 'mixed'
        assert remixer.max_remix_per_day == 2
        assert remixer.min_transform_percentage == 30
        assert remixer.max_original_duration == 3
    
    @patch('viral_remix.sqlite3.connect')
    def test_reason_select_basic(self, mock_connect, remixer, temp_db):
        """Test basic video selection with reasoning"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        selected_videos = remixer.reason_select(limit=3)
        
        assert len(selected_videos) == 3
        assert all('reasoning' in video for video in selected_videos)
        assert all('score' in video for video in selected_videos)
        
        # Check that videos are sorted by score (highest first)
        scores = [video['score'] for video in selected_videos]
        assert scores == sorted(scores, reverse=True)
    
    @patch('viral_remix.sqlite3.connect')
    def test_reason_select_stitch_preference(self, mock_connect, remixer, temp_db):
        """Test that stitch-allowed videos get preference"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        selected_videos = remixer.reason_select(limit=5)
        
        # Check that stitch-allowed videos are prioritized
        stitch_allowed_count = sum(1 for video in selected_videos if video.get('stitch_allowed'))
        assert stitch_allowed_count >= 2  # Should have some stitch-allowed videos
    
    @patch('viral_remix.sqlite3.connect')
    def test_reason_select_music_safety(self, mock_connect, remixer, temp_db):
        """Test that original music gets preference for safety"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        selected_videos = remixer.reason_select(limit=5)
        
        # Check reasoning mentions music safety
        music_safe_count = sum(1 for video in selected_videos 
                              if 'music' in video.get('reasoning', '').lower())
        assert music_safe_count >= 1
    
    def test_calculate_viral_score(self, remixer):
        """Test viral score calculation"""
        # Test high-performing video
        high_score = remixer._calculate_viral_score(
            views=1000000,
            likes=50000,
            shares=5000,
            comments=2000,
            stitch_allowed=True,
            music_original=True
        )
        
        # Test low-performing video
        low_score = remixer._calculate_viral_score(
            views=10000,
            likes=500,
            shares=50,
            comments=20,
            stitch_allowed=False,
            music_original=False
        )
        
        assert high_score > low_score
        assert 0 <= high_score <= 1
        assert 0 <= low_score <= 1
    
    def test_calculate_viral_score_multipliers(self, remixer):
        """Test that multipliers work correctly"""
        base_score = remixer._calculate_viral_score(
            views=100000, likes=5000, shares=500, comments=200,
            stitch_allowed=False, music_original=False
        )
        
        stitch_score = remixer._calculate_viral_score(
            views=100000, likes=5000, shares=500, comments=200,
            stitch_allowed=True, music_original=False
        )
        
        music_score = remixer._calculate_viral_score(
            views=100000, likes=5000, shares=500, comments=200,
            stitch_allowed=False, music_original=True
        )
        
        both_score = remixer._calculate_viral_score(
            views=100000, likes=5000, shares=500, comments=200,
            stitch_allowed=True, music_original=True
        )
        
        # Scores should increase with multipliers
        assert stitch_score > base_score
        assert music_score > base_score
        assert both_score > stitch_score
        assert both_score > music_score
    
    def test_generate_reasoning(self, remixer):
        """Test reasoning generation"""
        video_data = {
            'views': 1000000,
            'likes': 50000,
            'shares': 5000,
            'comments': 2000,
            'stitch_allowed': True,
            'music_original': True,
            'description': 'Amazing GPU setup for gaming'
        }
        
        reasoning = remixer._generate_reasoning(video_data, 0.85)
        
        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert 'stitch' in reasoning.lower()  # Should mention stitch capability
        assert 'music' in reasoning.lower()   # Should mention music safety
    
    def test_generate_reasoning_different_scenarios(self, remixer):
        """Test reasoning for different video scenarios"""
        # High-growth video
        high_growth = {
            'views': 2000000, 'likes': 100000, 'shares': 10000, 'comments': 5000,
            'stitch_allowed': True, 'music_original': True,
            'description': 'Viral tech content'
        }
        
        # Medium video with restrictions
        medium_restricted = {
            'views': 500000, 'likes': 25000, 'shares': 2500, 'comments': 1000,
            'stitch_allowed': False, 'music_original': False,
            'description': 'Tech review with copyrighted music'
        }
        
        high_reasoning = remixer._generate_reasoning(high_growth, 0.9)
        medium_reasoning = remixer._generate_reasoning(medium_restricted, 0.6)
        
        # High growth should mention viral potential
        assert any(word in high_reasoning.lower() for word in ['viral', 'high', 'growth', 'trending'])
        
        # Restricted should mention limitations
        assert any(word in medium_reasoning.lower() for word in ['download', 'transform', 'careful'])
    
    @patch('viral_remix.sqlite3.connect')
    def test_can_remix_today(self, mock_connect, remixer, temp_db):
        """Test daily remix limit checking"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        # Initially should be able to remix
        can_remix, reason = remixer.can_remix_today()
        assert can_remix
        assert 'ready' in reason.lower()
    
    @patch('viral_remix.sqlite3.connect')
    def test_get_remix_statistics(self, mock_connect, remixer, temp_db):
        """Test remix statistics retrieval"""
        mock_connect.return_value = sqlite3.connect(temp_db)
        
        stats = remixer.get_remix_statistics()
        
        assert 'total_videos' in stats
        assert 'stitch_allowed' in stats
        assert 'music_safe' in stats
        assert 'avg_score' in stats
        assert isinstance(stats['total_videos'], int)
    
    def test_score_edge_cases(self, remixer):
        """Test score calculation edge cases"""
        # Zero values
        zero_score = remixer._calculate_viral_score(0, 0, 0, 0, False, False)
        assert zero_score == 0
        
        # Very high values
        high_score = remixer._calculate_viral_score(
            views=100000000,  # 100M views
            likes=5000000,    # 5M likes
            shares=1000000,   # 1M shares
            comments=500000,  # 500K comments
            stitch_allowed=True,
            music_original=True
        )
        assert 0 <= high_score <= 1
    
    def test_reasoning_content_analysis(self, remixer):
        """Test that reasoning analyzes content appropriately"""
        tech_video = {
            'views': 500000, 'likes': 25000, 'shares': 2500, 'comments': 1000,
            'stitch_allowed': True, 'music_original': True,
            'description': 'GPU mining rig setup tutorial'
        }
        
        gaming_video = {
            'views': 500000, 'likes': 25000, 'shares': 2500, 'comments': 1000,
            'stitch_allowed': True, 'music_original': True,
            'description': 'Epic gaming moments compilation'
        }
        
        tech_reasoning = remixer._generate_reasoning(tech_video, 0.7)
        gaming_reasoning = remixer._generate_reasoning(gaming_video, 0.7)
        
        # Should mention relevant content themes
        assert any(word in tech_reasoning.lower() for word in ['tech', 'gpu', 'mining', 'tutorial'])
        assert any(word in gaming_reasoning.lower() for word in ['gaming', 'epic', 'moments'])
    
    @patch('viral_remix.yt_dlp.YoutubeDL')
    def test_download_video_mock(self, mock_ytdl, remixer):
        """Test video download functionality (mocked)"""
        # Mock successful download
        mock_instance = MagicMock()
        mock_ytdl.return_value.__enter__.return_value = mock_instance
        mock_instance.download.return_value = None
        
        # Mock file creation
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=1024*1024):  # 1MB
                result = remixer._download_video('https://tiktok.com/@user/video/123', 'test_output.mp4')
                
                assert result['success'] == True
                assert 'test_output.mp4' in result['file_path']
    
    def test_integration_reason_select_with_scoring(self, remixer, temp_db):
        """Integration test: reason_select with proper scoring"""
        with patch('viral_remix.sqlite3.connect') as mock_connect:
            mock_connect.return_value = sqlite3.connect(temp_db)
            
            # Get top 3 videos
            selected = remixer.reason_select(limit=3)
            
            # Verify selection quality
            assert len(selected) == 3
            
            # Check that all have required fields
            for video in selected:
                assert 'video_id' in video
                assert 'score' in video
                assert 'reasoning' in video
                assert 'stitch_allowed' in video
                assert 'music_original' in video
            
            # Verify reasoning quality
            for video in selected:
                reasoning = video['reasoning']
                assert len(reasoning) > 20  # Substantial reasoning
                assert any(word in reasoning.lower() for word in 
                          ['stitch', 'music', 'viral', 'growth', 'engagement'])

if __name__ == '__main__':
    pytest.main([__file__])
