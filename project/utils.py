#!/usr/bin/env python3
"""
Utility functions for TikTok automation bot
Includes environment validation, logging setup, and cleanup functions
"""

import os
import sys
import logging
import glob
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional
import yaml


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    """
    Setup rotating file logging with proper configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create rotating file handler (10MB x 5 files)
    log_file = os.path.join(log_dir, "bottiktok.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def validate_environment() -> Dict[str, bool]:
    """
    Validate environment variables and configuration
    
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'tiktok_credentials': False,
        'config_file': False,
        'directories': False,
        'dependencies': False
    }
    
    logger = logging.getLogger(__name__)
    
    # Check TikTok API credentials
    required_env_vars = [
        'TIKTOK_CLIENT_KEY',
        'TIKTOK_CLIENT_SECRET', 
        'TIKTOK_ACCESS_TOKEN'
    ]
    
    missing_vars = []
    placeholder_vars = []
    
    for var in required_env_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif value in ['CHANGEME', 'your_key_here', 'your_secret_here', 'your_token_here']:
            placeholder_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please copy .env.example to .env and configure your credentials")
        return validation_results
    
    if placeholder_vars:
        logger.error(f"Environment variables still have placeholder values: {', '.join(placeholder_vars)}")
        logger.error("Please update your .env file with actual API credentials")
        return validation_results
    
    validation_results['tiktok_credentials'] = True
    logger.info("✅ TikTok API credentials validated")
    
    # Check config file
    if os.path.exists('config.yaml'):
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
                
            # Validate required config sections
            required_sections = ['brand', 'posting', 'video', 'disclaimers']
            for section in required_sections:
                if section not in config:
                    logger.error(f"Missing required config section: {section}")
                    return validation_results
            
            validation_results['config_file'] = True
            logger.info("✅ Configuration file validated")
            
        except Exception as e:
            logger.error(f"Invalid config.yaml file: {e}")
            return validation_results
    else:
        logger.error("config.yaml file not found")
        return validation_results
    
    # Check required directories
    required_dirs = ['assets/bg', 'assets/overlays', 'output', 'logs', 'temp', 'luts']
    missing_dirs = []
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                missing_dirs.append(dir_path)
    
    if not missing_dirs:
        validation_results['directories'] = True
        logger.info("✅ Required directories validated")
    
    # Check critical dependencies
    try:
        import requests
        import yaml
        import sqlite3
        import moviepy
        import PIL
        import numpy
        
        validation_results['dependencies'] = True
        logger.info("✅ Critical dependencies validated")
        
    except ImportError as e:
        logger.error(f"Missing critical dependency: {e}")
        logger.error("Please run: pip install -r requirements.txt")
        return validation_results
    
    return validation_results


def cleanup_old_files(max_age_days: int = 7) -> Dict[str, int]:
    """
    Clean up old files to prevent disk space issues
    
    Args:
        max_age_days: Maximum age of files to keep
        
    Returns:
        Dictionary with cleanup statistics
    """
    logger = logging.getLogger(__name__)
    cleanup_stats = {
        'videos_cleaned': 0,
        'logs_cleaned': 0,
        'temp_cleaned': 0,
        'space_freed_mb': 0
    }
    
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    # Clean up old videos in output directory
    if os.path.exists('output'):
        video_files = glob.glob('output/*.mp4') + glob.glob('output/*.mov')
        for video_file in video_files:
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(video_file))
                if file_time < cutoff_date:
                    file_size = os.path.getsize(video_file)
                    os.remove(video_file)
                    cleanup_stats['videos_cleaned'] += 1
                    cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
                    logger.info(f"Cleaned up old video: {video_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {video_file}: {e}")
    
    # Clean up old log files (beyond rotation)
    if os.path.exists('logs'):
        log_files = glob.glob('logs/*.log.*')
        for log_file in log_files:
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_time < cutoff_date:
                    file_size = os.path.getsize(log_file)
                    os.remove(log_file)
                    cleanup_stats['logs_cleaned'] += 1
                    cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
                    logger.info(f"Cleaned up old log: {log_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {log_file}: {e}")
    
    # Clean up temp directory
    if os.path.exists('temp'):
        temp_files = glob.glob('temp/*')
        for temp_file in temp_files:
            try:
                if os.path.isfile(temp_file):
                    file_time = datetime.fromtimestamp(os.path.getmtime(temp_file))
                    if file_time < cutoff_date:
                        file_size = os.path.getsize(temp_file)
                        os.remove(temp_file)
                        cleanup_stats['temp_cleaned'] += 1
                        cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
                        logger.info(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {e}")
    
    logger.info(f"Cleanup completed: {cleanup_stats}")
    return cleanup_stats


def check_disk_space(min_free_gb: float = 1.0) -> Dict[str, float]:
    """
    Check available disk space
    
    Args:
        min_free_gb: Minimum free space required in GB
        
    Returns:
        Dictionary with disk space information
    """
    import shutil
    
    total, used, free = shutil.disk_usage('.')
    
    disk_info = {
        'total_gb': total / (1024**3),
        'used_gb': used / (1024**3),
        'free_gb': free / (1024**3),
        'usage_percent': (used / total) * 100,
        'sufficient_space': free / (1024**3) >= min_free_gb
    }
    
    logger = logging.getLogger(__name__)
    
    if not disk_info['sufficient_space']:
        logger.warning(f"Low disk space: {disk_info['free_gb']:.2f}GB free (minimum: {min_free_gb}GB)")
        logger.warning("Consider running cleanup or freeing disk space")
    else:
        logger.info(f"Disk space OK: {disk_info['free_gb']:.2f}GB free")
    
    return disk_info


def validate_video_file(video_path: str) -> Dict[str, any]:
    """
    Validate video file properties
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dictionary with validation results
    """
    validation = {
        'exists': False,
        'readable': False,
        'size_mb': 0,
        'duration': 0,
        'resolution': None,
        'valid': False
    }
    
    if not os.path.exists(video_path):
        return validation
    
    validation['exists'] = True
    
    try:
        # Check file size
        file_size = os.path.getsize(video_path)
        validation['size_mb'] = file_size / (1024 * 1024)
        
        # Check if file is readable
        with open(video_path, 'rb') as f:
            f.read(1024)  # Try to read first 1KB
        validation['readable'] = True
        
        # Try to get video properties with moviepy
        try:
            from moviepy.editor import VideoFileClip
            with VideoFileClip(video_path) as clip:
                validation['duration'] = clip.duration
                validation['resolution'] = (clip.w, clip.h)
                
                # Check if it's a valid TikTok video
                if (8 <= validation['duration'] <= 12 and 
                    validation['resolution'] == (1080, 1920) and
                    validation['size_mb'] < 100):
                    validation['valid'] = True
                    
        except Exception as e:
            logging.getLogger(__name__).warning(f"Could not analyze video properties: {e}")
    
    except Exception as e:
        logging.getLogger(__name__).error(f"Error validating video file: {e}")
    
    return validation


def get_system_info() -> Dict[str, any]:
    """
    Get system information for debugging
    
    Returns:
        Dictionary with system information
    """
    import platform
    import psutil
    
    return {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': psutil.cpu_count(),
        'memory_gb': psutil.virtual_memory().total / (1024**3),
        'disk_free_gb': psutil.disk_usage('.').free / (1024**3),
        'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
    }


def main():
    """Test utility functions"""
    # Setup logging
    logger = setup_logging()
    
    logger.info("Testing utility functions...")
    
    # Validate environment
    validation = validate_environment()
    logger.info(f"Environment validation: {validation}")
    
    # Check disk space
    disk_info = check_disk_space()
    logger.info(f"Disk space: {disk_info}")
    
    # Get system info
    sys_info = get_system_info()
    logger.info(f"System info: {sys_info}")
    
    # Test cleanup (dry run)
    cleanup_stats = cleanup_old_files(max_age_days=30)  # Only very old files
    logger.info(f"Cleanup stats: {cleanup_stats}")


if __name__ == "__main__":
    main()
