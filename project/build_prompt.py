#!/usr/bin/env python3
"""
AI Prompt Builder for TikTok Videos
Generates short, punchy video scripts (≤4 words) using local AI
Optimized for faceless content with strong visual impact
"""

import random
import logging
from typing import List, Dict, Optional
import yaml
import sqlite3
from datetime import datetime
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptBuilder:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize prompt builder
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.themes = self.config.get('themes', [])
        self.brand_code = self.config['brand']['promo_code']
        
        # Pre-defined templates for different video styles
        self.templates = {
            'power': [
                "UNLEASH {theme}",
                "BOOST {theme}",
                "SUPERCHARGE {theme}",
                "MAXIMIZE {theme}",
                "DOMINATE {theme}"
            ],
            'speed': [
                "INSTANT {theme}",
                "LIGHTNING {theme}",
                "RAPID {theme}",
                "BLAZING {theme}",
                "TURBO {theme}"
            ],
            'savings': [
                "CHEAP {theme}",
                "SAVE {theme}",
                "BUDGET {theme}",
                "AFFORDABLE {theme}",
                "DISCOUNT {theme}"
            ],
            'tech': [
                "NEXT-GEN {theme}",
                "PRO {theme}",
                "ELITE {theme}",
                "PREMIUM {theme}",
                "ADVANCED {theme}"
            ],
            'action': [
                "GET {theme}",
                "GRAB {theme}",
                "CLAIM {theme}",
                "SECURE {theme}",
                "ACCESS {theme}"
            ]
        }
        
        # Power words for emphasis
        self.power_words = [
            "NOW", "FREE", "FAST", "EASY", "INSTANT", "PROVEN", 
            "SECRET", "ULTIMATE", "EXCLUSIVE", "LIMITED", "VIRAL",
            "INSANE", "CRAZY", "EPIC", "MASSIVE", "HUGE"
        ]
        
        # GPU/Tech specific terms
        self.gpu_terms = {
            'gpu': ['GPU', 'GRAPHICS', 'RENDER', 'COMPUTE'],
            'ai': ['AI', 'NEURAL', 'MACHINE', 'DEEP'],
            'crypto': ['CRYPTO', 'MINING', 'HASH', 'BLOCKCHAIN'],
            'gaming': ['GAMING', 'FPS', 'RTX', 'PERFORMANCE'],
            'cloud': ['CLOUD', 'SERVER', 'REMOTE', 'VIRTUAL'],
            'speed': ['FAST', 'INSTANT', 'RAPID', 'TURBO'],
            'power': ['POWER', 'BEAST', 'MONSTER', 'TITAN']
        }
    
    def generate_script(self, hashtag: str, style: str = "auto") -> Dict:
        """
        Generate a short video script based on trending hashtag
        
        Args:
            hashtag: Selected trending hashtag
            style: Video style ('power', 'speed', 'savings', 'tech', 'action', 'auto')
            
        Returns:
            Dictionary with script components
        """
        # Clean hashtag
        clean_tag = hashtag.replace('#', '').lower()
        
        # Auto-detect style if not specified
        if style == "auto":
            style = self._detect_style(clean_tag)
        
        # Generate main text (≤4 words)
        main_text = self._generate_main_text(clean_tag, style)
        
        # Generate supporting elements
        script = {
            'main_text': main_text,
            'hashtag': hashtag,
            'style': style,
            'promo_code': self.brand_code,
            'call_to_action': self._generate_cta(),
            'visual_cues': self._generate_visual_cues(style),
            'timing': self._generate_timing(),
            'emoji_sequence': self._generate_emoji_sequence(clean_tag),
            'generated_at': datetime.now().isoformat()
        }
        
        logger.info(f"Generated script: '{main_text}' (style: {style})")
        return script
    
    def _detect_style(self, hashtag: str) -> str:
        """
        Auto-detect video style based on hashtag content
        
        Args:
            hashtag: Clean hashtag string
            
        Returns:
            Detected style
        """
        hashtag_lower = hashtag.lower()
        
        # Style detection rules
        if any(word in hashtag_lower for word in ['cheap', 'free', 'save', 'budget', 'discount']):
            return 'savings'
        elif any(word in hashtag_lower for word in ['fast', 'speed', 'instant', 'quick', 'rapid']):
            return 'speed'
        elif any(word in hashtag_lower for word in ['pro', 'elite', 'premium', 'advanced', 'next']):
            return 'tech'
        elif any(word in hashtag_lower for word in ['get', 'grab', 'claim', 'access', 'unlock']):
            return 'action'
        else:
            return 'power'  # Default to power style
    
    def _generate_main_text(self, hashtag: str, style: str) -> str:
        """
        Generate main text for video (≤4 words)
        
        Args:
            hashtag: Clean hashtag
            style: Video style
            
        Returns:
            Main text string
        """
        # Get templates for style
        templates = self.templates.get(style, self.templates['power'])
        
        # Find relevant theme
        theme = self._extract_theme(hashtag)
        
        # Select random template and fill
        template = random.choice(templates)
        main_text = template.format(theme=theme.upper())
        
        # Ensure ≤4 words
        words = main_text.split()
        if len(words) > 4:
            main_text = ' '.join(words[:4])
        
        return main_text
    
    def _extract_theme(self, hashtag: str) -> str:
        """
        Extract relevant theme from hashtag
        
        Args:
            hashtag: Clean hashtag
            
        Returns:
            Extracted theme
        """
        hashtag_lower = hashtag.lower()
        
        # Check for GPU/tech terms
        for category, terms in self.gpu_terms.items():
            for term in terms:
                if term.lower() in hashtag_lower:
                    return term
        
        # Check configured themes
        for theme in self.themes:
            theme_clean = theme.replace('#', '').lower()
            if theme_clean in hashtag_lower:
                return theme_clean.upper()
        
        # Fallback to hashtag itself (truncated)
        return hashtag[:8].upper()
    
    def _generate_cta(self) -> str:
        """Generate call-to-action text"""
        ctas = [
            f"Use {self.brand_code}",
            f"Code: {self.brand_code}",
            f"Try {self.brand_code}",
            f"Get {self.brand_code}",
            f"Claim {self.brand_code}"
        ]
        return random.choice(ctas)
    
    def _generate_visual_cues(self, style: str) -> List[str]:
        """
        Generate visual cues for video editing
        
        Args:
            style: Video style
            
        Returns:
            List of visual cue instructions
        """
        base_cues = [
            "fade_in_text",
            "zoom_on_keyword",
            "flash_promo_code",
            "particle_effects"
        ]
        
        style_cues = {
            'power': ["screen_shake", "lightning_flash", "energy_burst"],
            'speed': ["motion_blur", "speed_lines", "quick_cuts"],
            'savings': ["coin_drop", "price_slash", "money_rain"],
            'tech': ["digital_glitch", "matrix_effect", "hologram"],
            'action': ["button_pulse", "arrow_point", "hand_gesture"]
        }
        
        return base_cues + style_cues.get(style, [])
    
    def _generate_timing(self) -> Dict:
        """Generate timing information for video segments"""
        total_duration = random.uniform(8, 10)  # 8-10 seconds
        
        return {
            'total_duration': total_duration,
            'intro_duration': 1.0,
            'main_text_duration': total_duration - 3.0,
            'cta_duration': 1.5,
            'outro_duration': 0.5,
            'text_animation_speed': 0.3
        }
    
    def _generate_emoji_sequence(self, hashtag: str) -> List[str]:
        """
        Generate emoji sequence for particle effects
        
        Args:
            hashtag: Clean hashtag
            
        Returns:
            List of relevant emojis
        """
        # Base emojis for GPU/tech content
        base_emojis = ["⚡", "💎", "🔥", "✨", "💫"]
        
        # Category-specific emojis
        category_emojis = {
            'gpu': ["🖥️", "💻", "🎮", "⚡"],
            'ai': ["🤖", "🧠", "⚡", "💡"],
            'crypto': ["💰", "🪙", "💎", "📈"],
            'gaming': ["🎮", "🕹️", "🏆", "🔥"],
            'cloud': ["☁️", "🌐", "📡", "⚡"],
            'mining': ["⛏️", "💎", "🪙", "💰"],
            'render': ["🎨", "🖼️", "✨", "💫"]
        }
        
        # Find relevant category
        hashtag_lower = hashtag.lower()
        selected_emojis = base_emojis.copy()
        
        for category, emojis in category_emojis.items():
            if category in hashtag_lower:
                selected_emojis.extend(emojis)
                break
        
        # Return random selection
        return random.sample(selected_emojis, min(6, len(selected_emojis)))
    
    def save_script_to_db(self, script: Dict, db_path: str = "trends.db"):
        """
        Save generated script to database
        
        Args:
            script: Generated script dictionary
            db_path: Database path
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create scripts table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hashtag TEXT NOT NULL,
                main_text TEXT NOT NULL,
                style TEXT,
                call_to_action TEXT,
                visual_cues TEXT,
                emoji_sequence TEXT,
                timing_data TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_for_video BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Insert script
        cursor.execute('''
            INSERT INTO video_scripts 
            (hashtag, main_text, style, call_to_action, visual_cues, 
             emoji_sequence, timing_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            script['hashtag'],
            script['main_text'],
            script['style'],
            script['call_to_action'],
            ','.join(script['visual_cues']),
            ','.join(script['emoji_sequence']),
            str(script['timing'])
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved script to database: {script['main_text']}")
    
    def get_recent_scripts(self, limit: int = 10) -> List[Dict]:
        """
        Get recently generated scripts
        
        Args:
            limit: Maximum number of scripts to return
            
        Returns:
            List of recent scripts
        """
        conn = sqlite3.connect("trends.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT hashtag, main_text, style, call_to_action, generated_at
            FROM video_scripts
            ORDER BY generated_at DESC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        scripts = []
        for row in results:
            scripts.append({
                'hashtag': row[0],
                'main_text': row[1],
                'style': row[2],
                'call_to_action': row[3],
                'generated_at': row[4]
            })
        
        return scripts
    
    def generate_variations(self, base_script: Dict, count: int = 3) -> List[Dict]:
        """
        Generate variations of a base script
        
        Args:
            base_script: Base script to vary
            count: Number of variations to generate
            
        Returns:
            List of script variations
        """
        variations = []
        hashtag = base_script['hashtag'].replace('#', '').lower()
        style = base_script['style']
        
        for _ in range(count):
            # Generate new variation
            variation = self.generate_script(f"#{hashtag}", style)
            
            # Ensure it's different from base
            if variation['main_text'] != base_script['main_text']:
                variations.append(variation)
        
        return variations

def main():
    """Main function for testing the prompt builder"""
    builder = PromptBuilder()
    
    # Test hashtags
    test_hashtags = ["#gpu", "#ai", "#crypto", "#gaming", "#cheapgpu", "#fastrender"]
    
    print("TikTok Script Generator Test")
    print("=" * 50)
    
    for hashtag in test_hashtags:
        script = builder.generate_script(hashtag)
        
        print(f"\nHashtag: {hashtag}")
        print(f"Main Text: {script['main_text']}")
        print(f"Style: {script['style']}")
        print(f"CTA: {script['call_to_action']}")
        print(f"Emojis: {' '.join(script['emoji_sequence'])}")
        print(f"Duration: {script['timing']['total_duration']:.1f}s")
        
        # Save to database
        builder.save_script_to_db(script)
    
    # Show recent scripts
    print(f"\nRecent Scripts:")
    print("-" * 30)
    recent = builder.get_recent_scripts(5)
    for script in recent:
        print(f"{script['hashtag']:<12} {script['main_text']:<20} ({script['style']})")

if __name__ == "__main__":
    main()
