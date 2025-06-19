#!/usr/bin/env python3
"""
🚀 Viral AI Bot Launcher
Simple launcher for the modular viral AI system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from viral_ai.config import get_config, setup_logging
    from viral_ai.main import ViralAI
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Make sure you've installed all dependencies:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

async def main():
    """Main launcher function"""
    print("🚀 Starting Viral AI Bot...")
    print("=" * 50)
    
    try:
        # Load configuration
        config = get_config()
        setup_logging(config)
        
        # Initialize and run the bot
        bot = ViralAI(config)
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your .env file has all required TikTok credentials")
        print("2. Verify your TikTok Business API access")
        print("3. Check the logs for detailed error information")
        sys.exit(1)

if __name__ == "__main__":
    # Check if .env exists
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("🔧 Please copy .env.example to .env and configure your credentials:")
        print("   cp .env.example .env")
        print("   # Then edit .env with your TikTok API credentials")
        sys.exit(1)
    
    # Run the bot
    asyncio.run(main())
