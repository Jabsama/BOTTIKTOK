"""
🚀 Main Orchestrator - Viral AI System
Point d'entrée principal pour le système modulaire
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

from .config import Config, setup_logging
from .trends import TrendAnalyzer

logger = logging.getLogger(__name__)

class ViralAI:
    """Orchestrateur principal du système Viral AI"""
    
    def __init__(self, config: Config):
        self.config = config
        self.running = False
        self.trend_analyzer: Optional[TrendAnalyzer] = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🚀 Viral AI System initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("🔧 Initializing Viral AI components...")
        
        try:
            # Initialize trend analyzer
            self.trend_analyzer = TrendAnalyzer(self.config)
            await self.trend_analyzer.initialize_database()
            
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise
    
    async def run_cycle(self):
        """Run one complete viral content cycle"""
        logger.info("🔄 Starting viral content cycle...")
        
        try:
            # Step 1: Analyze trends
            logger.info("🔍 Analyzing viral trends...")
            trends = await self.trend_analyzer.fetch_viral_trends(limit=20)
            
            if not trends:
                logger.warning("⚠️ No trends found, skipping cycle")
                return
            
            logger.info(f"📊 Found {len(trends)} viral trends")
            
            # For now, just log the top trends
            for i, trend in enumerate(trends[:5], 1):
                logger.info(f"#{i} {trend.hashtag} (viral score: {trend.viral_potential:.3f})")
            
            # TODO: Implement content generation
            logger.info("🧠 Content generation - Coming soon!")
            
            # TODO: Implement video production
            logger.info("🎬 Video production - Coming soon!")
            
            # TODO: Implement upload
            logger.info("📱 Multi-platform upload - Coming soon!")
            
            logger.info("✅ Cycle completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error in viral cycle: {e}")
            raise
    
    async def run(self):
        """Main run loop"""
        logger.info("🚀 Starting Viral AI System...")
        
        try:
            # Initialize components
            await self.initialize()
            
            self.running = True
            cycle_count = 0
            
            logger.info("🎯 Viral AI System is now running!")
            logger.info("📊 Dashboard available at: http://localhost:8000/metrics")
            logger.info("🛑 Press Ctrl+C to stop")
            
            while self.running:
                cycle_count += 1
                start_time = datetime.now()
                
                logger.info(f"🔄 Starting cycle #{cycle_count}")
                
                try:
                    await self.run_cycle()
                    
                    # Calculate cycle time
                    cycle_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"⏱️ Cycle #{cycle_count} completed in {cycle_time:.1f}s")
                    
                except Exception as e:
                    logger.error(f"❌ Cycle #{cycle_count} failed: {e}")
                
                # Wait before next cycle (configurable)
                cycle_interval = self.config.get('system.cycle_interval_minutes', 30) * 60
                logger.info(f"😴 Waiting {cycle_interval//60} minutes before next cycle...")
                
                # Sleep with interruption check
                for _ in range(cycle_interval):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("👋 Shutdown requested by user")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up resources...")
        
        try:
            if self.trend_analyzer:
                await self.trend_analyzer.close()
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

async def main():
    """Entry point for the modular system"""
    try:
        # Load configuration
        config = Config()
        setup_logging(config)
        
        # Create and run the system
        viral_ai = ViralAI(config)
        await viral_ai.run()
        
    except Exception as e:
        print(f"❌ Failed to start Viral AI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
