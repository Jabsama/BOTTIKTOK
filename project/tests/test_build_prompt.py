#!/usr/bin/env python3
"""
Unit tests for build_prompt.py
Tests the prompt generation and script creation functionality
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
import sqlite3

# Import the module to test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_prompt import PromptBuilder

class TestPromptBuilder:
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary config file for testing"""
        config_data = {
            'brand': {
                'hex_primary': '#00BFA6',
                'hex_secondary': '#FFD54F',
                'promo_code': 'SHA-256-76360B81D39F'
            },
            'themes': ['CHEAP GPU', 'FAST RENDER', 'AI POWER'],
            'disclaimers': {
                'ai_generated': 'AI generated',
                'results_vary': '⚠ Results may vary'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config_data, f)
            yield f.name
        
        os.unlink(f.name)
    
    @pytest.fixture
    def prompt_builder(self, temp_config):
        """Create PromptBuilder instance with temporary config"""
        return PromptBuilder(temp_config)
    
    def test_init(self, prompt_builder):
        """Test PromptBuilder initialization"""
        assert prompt_builder.primary_color == '#00BFA6'
        assert prompt_builder.secondary_color == '#FFD54F'
        assert prompt_builder.promo_code == 'SHA-256-76360B81D39F'
        assert len(prompt_builder.themes) == 3
    
    def test_generate_script_basic(self, prompt_builder):
        """Test basic script generation"""
        script = prompt_builder.generate_script('#gpu', 'power')
        
        # Check required fields
        assert 'hashtag' in script
        assert 'main_text' in script
        assert 'style' in script
        assert 'call_to_action' in script
        assert 'emoji_sequence' in script
        assert 'timing' in script
        assert 'generated_at' in script
        
        # Check values
        assert script['hashtag'] == '#gpu'
        assert script['style'] == 'power'
        assert len(script['main_text'].split()) <= 4  # ≤4 words requirement
        assert 'SHA-256-76360B81D39F' in script['call_to_action']
    
    def test_generate_script_different_styles(self, prompt_builder):
        """Test script generation with different styles"""
        styles = ['power', 'tech', 'savings']
        
        for style in styles:
            script = prompt_builder.generate_script('#test', style)
            assert script['style'] == style
            assert 'main_text' in script
            assert len(script['main_text']) > 0
    
    def test_generate_main_text_word_limit(self, prompt_builder):
        """Test that main text respects 4-word limit"""
        for _ in range(10):  # Test multiple generations
            text = prompt_builder._generate_main_text('#gpu', 'power')
            word_count = len(text.split())
            assert word_count <= 4, f"Text '{text}' has {word_count} words, exceeds 4-word limit"
    
    def test_generate_emoji_sequence(self, prompt_builder):
        """Test emoji sequence generation"""
        emojis = prompt_builder._generate_emoji_sequence('power')
        
        assert isinstance(emojis, list)
        assert len(emojis) >= 3
        assert len(emojis) <= 6
        
        # Check that all items are single characters (emojis)
        for emoji in emojis:
            assert len(emoji) <= 2  # Some emojis are 2 characters
    
    def test_calculate_timing(self, prompt_builder):
        """Test timing calculation"""
        timing = prompt_builder._calculate_timing('CHEAP GPU')
        
        assert 'total_duration' in timing
        assert 'intro_duration' in timing
        assert 'main_text_duration' in timing
        assert 'cta_duration' in timing
        assert 'outro_duration' in timing
        
        # Check duration bounds
        assert 8 <= timing['total_duration'] <= 10
        
        # Check that parts sum to total
        parts_sum = (timing['intro_duration'] + timing['main_text_duration'] + 
                    timing['cta_duration'] + timing['outro_duration'])
        assert abs(parts_sum - timing['total_duration']) < 0.1
    
    @patch('sqlite3.connect')
    def test_save_script_to_db(self, mock_connect, prompt_builder):
        """Test saving script to database"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        script = {
            'hashtag': '#test',
            'main_text': 'TEST TEXT',
            'style': 'power',
            'call_to_action': 'Use code',
            'emoji_sequence': ['⚡', '🔥'],
            'timing': {'total_duration': 9.0},
            'generated_at': '2024-01-01T12:00:00'
        }
        
        prompt_builder.save_script_to_db(script)
        
        # Verify database operations
        mock_connect.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
    
    def test_script_consistency(self, prompt_builder):
        """Test that generated scripts are consistent and valid"""
        hashtag = '#gpu'
        style = 'power'
        
        # Generate multiple scripts
        scripts = []
        for _ in range(5):
            script = prompt_builder.generate_script(hashtag, style)
            scripts.append(script)
        
        # Check consistency
        for script in scripts:
            assert script['hashtag'] == hashtag
            assert script['style'] == style
            assert 'SHA-256-76360B81D39F' in script['call_to_action']
            
            # Check timing is reasonable
            assert 8 <= script['timing']['total_duration'] <= 10
            
            # Check emoji sequence
            assert len(script['emoji_sequence']) >= 3
    
    def test_promo_code_integration(self, prompt_builder):
        """Test that promo code is properly integrated"""
        script = prompt_builder.generate_script('#test', 'power')
        
        # Check promo code appears in call to action
        assert 'SHA-256-76360B81D39F' in script['call_to_action']
        
        # Check it's formatted correctly
        cta = script['call_to_action']
        assert 'code' in cta.lower() or 'use' in cta.lower()

if __name__ == '__main__':
    pytest.main([__file__])
