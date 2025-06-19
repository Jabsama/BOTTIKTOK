"""
🚀 Viral AI - Production-Ready TikTok Automation System
Architecture modulaire pour robustesse et maintenabilité
"""

__version__ = "2.0.0"
__author__ = "Viral AI Team"
__description__ = "Production-ready TikTok automation with modular architecture"

from .config import Config
from .trends import TrendAnalyzer
from .content import ContentGenerator
from .video import VideoProducer
from .upload import MultiPlatformUploader
from .main import ViralAI

__all__ = [
    "Config",
    "TrendAnalyzer", 
    "ContentGenerator",
    "VideoProducer",
    "MultiPlatformUploader",
    "ViralAI"
]
