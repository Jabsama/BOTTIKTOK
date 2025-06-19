"""
🔍 Trend Analysis - Production Ready
Analyse de tendances avec vraie API TikTok et token bucket rate limiting
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp
import redis.asyncio as redis
from tenacity import retry, wait_exponential, stop_after_attempt
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import Config

logger = logging.getLogger(__name__)

Base = declarative_base()

class TrendRecord(Base):
    """Modèle de données pour les tendances"""
    __tablename__ = 'trends'
    
    id = sa.Column(sa.Integer, primary_key=True)
    hashtag = sa.Column(sa.String(100), unique=True, nullable=False)
    trend_score = sa.Column(sa.Float, nullable=False)
    viral_potential = sa.Column(sa.Float, nullable=False)
    volume = sa.Column(sa.Integer, nullable=False)
    growth_rate = sa.Column(sa.Float, nullable=False)
    category = sa.Column(sa.String(50), nullable=False)
    region = sa.Column(sa.String(10), default='US')
    fetched_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    api_source = sa.Column(sa.String(50), default='creative_center')
    compliance_verified = sa.Column(sa.Boolean, default=True)

@dataclass
class TrendData:
    """Structure de données pour une tendance"""
    hashtag: str
    trend_score: float
    viral_potential: float
    volume: int
    growth_rate: float
    category: str
    region: str = 'US'
    api_source: str = 'creative_center'
    compliance_verified: bool = True

class TokenBucket:
    """Token bucket pour rate limiting TikTok API (600 req/min)"""
    
    def __init__(self, redis_client: redis.Redis, capacity: int = 600, refill_rate: int = 10):
        self.redis = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.bucket_key = "tiktok_api_bucket"
        self.last_refill_key = "tiktok_api_last_refill"
    
    async def consume(self, tokens: int = 1) -> bool:
        """Consomme des tokens, retourne True si disponible"""
        now = time.time()
        
        # Récupérer l'état actuel
        pipe = self.redis.pipeline()
        pipe.get(self.bucket_key)
        pipe.get(self.last_refill_key)
        bucket_tokens, last_refill = await pipe.execute()
        
        # Initialiser si première utilisation
        if bucket_tokens is None:
            bucket_tokens = self.capacity
            last_refill = now
        else:
            bucket_tokens = int(bucket_tokens)
            last_refill = float(last_refill)
        
        # Calculer les nouveaux tokens
        time_passed = now - last_refill
        new_tokens = min(self.capacity, bucket_tokens + (time_passed * self.refill_rate))
        
        # Vérifier si on peut consommer
        if new_tokens >= tokens:
            new_tokens -= tokens
            
            # Sauvegarder le nouvel état
            pipe = self.redis.pipeline()
            pipe.set(self.bucket_key, int(new_tokens))
            pipe.set(self.last_refill_key, now)
            await pipe.execute()
            
            return True
        
        return False
    
    async def wait_for_tokens(self, tokens: int = 1) -> float:
        """Attend que les tokens soient disponibles, retourne le temps d'attente"""
        while not await self.consume(tokens):
            wait_time = tokens / self.refill_rate
            logger.info(f"⏳ Rate limit reached, waiting {wait_time:.1f}s for {tokens} tokens")
            await asyncio.sleep(wait_time)
        return 0

class TikTokAPIClient:
    """Client API TikTok avec gestion complète des tokens et rate limiting"""
    
    def __init__(self, config: Config, redis_client: redis.Redis):
        self.config = config
        self.token_bucket = TokenBucket(redis_client)
        
        # Endpoints officiels TikTok
        self.base_url = "https://business-api.tiktok.com/open_api/v1.3"
        self.creative_center_url = "https://ads.tiktok.com/creative_radar_api/v1.0"
        
        # Headers par défaut
        self.headers = {
            "Access-Token": config.tiktok.access_token,
            "Content-Type": "application/json"
        }
        
        logger.info("✅ TikTok API Client initialized")
    
    async def refresh_access_token(self) -> bool:
        """Rafraîchit le token d'accès (expire en 24h)"""
        refresh_url = f"{self.base_url}/oauth2/refresh_token/"
        
        payload = {
            "client_key": self.config.tiktok.client_key,
            "client_secret": self.config.tiktok.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.config.tiktok.refresh_token
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(refresh_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("code") == 0:
                            # Mettre à jour les tokens
                            new_access_token = data["data"]["access_token"]
                            new_refresh_token = data["data"]["refresh_token"]
                            
                            self.config.tiktok.access_token = new_access_token
                            self.config.tiktok.refresh_token = new_refresh_token
                            self.headers["Access-Token"] = new_access_token
                            
                            logger.info("✅ Access token refreshed successfully")
                            return True
                        else:
                            logger.error(f"❌ Token refresh failed: {data.get('message')}")
                            return False
                    else:
                        logger.error(f"❌ Token refresh HTTP error: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"❌ Token refresh exception: {e}")
            return False
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def fetch_trending_hashtags(self, limit: int = 50, region: str = "US") -> List[TrendData]:
        """Récupère les hashtags tendance via Creative Center API"""
        
        # Attendre les tokens disponibles
        await self.token_bucket.wait_for_tokens(1)
        
        url = f"{self.creative_center_url}/popular_trend/hashtag/list/"
        
        params = {
            "period": 7,  # 7 derniers jours
            "country_code": region,
            "limit": limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    
                    if response.status == 401:
                        # Token expiré, essayer de le rafraîchir
                        if await self.refresh_access_token():
                            # Retry avec le nouveau token
                            async with session.get(url, headers=self.headers, params=params) as retry_response:
                                if retry_response.status == 200:
                                    data = await retry_response.json()
                                else:
                                    raise aiohttp.ClientResponseError(
                                        request_info=retry_response.request_info,
                                        history=retry_response.history,
                                        status=retry_response.status
                                    )
                        else:
                            raise Exception("Failed to refresh access token")
                    
                    elif response.status == 200:
                        data = await response.json()
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status
                        )
            
            # Parser la réponse
            trends = []
            if data.get("code") == 0 and "data" in data:
                hashtag_list = data["data"].get("hashtag_list", [])
                
                for item in hashtag_list:
                    trend = TrendData(
                        hashtag=f"#{item.get('hashtag_name', '')}",
                        trend_score=item.get("trend_score", 0.5),
                        viral_potential=self._calculate_viral_potential(item),
                        volume=item.get("publish_cnt", 0),
                        growth_rate=item.get("trend_score", 0) / 100,  # Normaliser
                        category=self._categorize_hashtag(item.get('hashtag_name', '')),
                        region=region,
                        api_source='creative_center'
                    )
                    trends.append(trend)
            
            logger.info(f"✅ Fetched {len(trends)} trending hashtags from TikTok API")
            return trends
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch trending hashtags: {e}")
            raise
    
    def _calculate_viral_potential(self, hashtag_data: Dict) -> float:
        """Calcule le potentiel viral basé sur les métriques TikTok"""
        score = 0.0
        
        # Score de tendance (0-100 de TikTok)
        trend_score = hashtag_data.get("trend_score", 0) / 100
        score += trend_score * 0.4
        
        # Volume de publications
        publish_count = hashtag_data.get("publish_cnt", 0)
        if 1000 <= publish_count <= 50000:  # Sweet spot
            score += 0.3
        elif publish_count > 50000:
            score += 0.1  # Oversaturated
        elif publish_count > 100:
            score += 0.2
        
        # Croissance (basée sur trend_score)
        if trend_score > 0.8:
            score += 0.2
        elif trend_score > 0.6:
            score += 0.1
        
        # Bonus pour catégories tech
        hashtag_name = hashtag_data.get('hashtag_name', '').lower()
        tech_keywords = ['ai', 'tech', 'gpu', 'crypto', 'gaming', 'ml', 'data']
        if any(keyword in hashtag_name for keyword in tech_keywords):
            score += 0.1
        
        return min(score, 1.0)
    
    def _categorize_hashtag(self, hashtag: str) -> str:
        """Catégorise un hashtag"""
        hashtag_lower = hashtag.lower()
        
        tech_keywords = ['ai', 'tech', 'gpu', 'crypto', 'gaming', 'ml', 'data', 'code']
        viral_keywords = ['fyp', 'viral', 'trending', 'amazing', 'incredible']
        
        if any(keyword in hashtag_lower for keyword in tech_keywords):
            return 'tech'
        elif any(keyword in hashtag_lower for keyword in viral_keywords):
            return 'viral'
        else:
            return 'general'

class TrendAnalyzer:
    """Analyseur de tendances - Production Ready"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Connexion base de données
        self.engine = create_async_engine(config.database.url)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Connexion Redis pour rate limiting
        self.redis = redis.Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            password=config.redis.password,
            decode_responses=True
        )
        
        # Client API TikTok
        self.api_client = TikTokAPIClient(config, self.redis)
        
        logger.info("✅ TrendAnalyzer initialized")
    
    async def initialize_database(self):
        """Initialise la base de données"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database initialized")
    
    async def fetch_viral_trends(self, limit: int = 50, region: str = "US") -> List[TrendData]:
        """Récupère les tendances virales avec l'API officielle"""
        try:
            # Récupérer depuis l'API TikTok
            trends = await self.api_client.fetch_trending_hashtags(limit, region)
            
            # Sauvegarder en base
            await self._store_trends(trends)
            
            # Trier par potentiel viral
            trends.sort(key=lambda x: x.viral_potential, reverse=True)
            
            logger.info(f"✅ Analyzed {len(trends)} viral trends")
            return trends
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch viral trends: {e}")
            
            # Fallback sur les données en cache
            cached_trends = await self._get_cached_trends(limit)
            if cached_trends:
                logger.info(f"⚠️ Using {len(cached_trends)} cached trends as fallback")
                return cached_trends
            
            raise
    
    async def _store_trends(self, trends: List[TrendData]):
        """Sauvegarde les tendances en base"""
        async with self.async_session() as session:
            try:
                for trend_data in trends:
                    # Vérifier si existe déjà
                    existing = await session.execute(
                        sa.select(TrendRecord).where(TrendRecord.hashtag == trend_data.hashtag)
                    )
                    existing_trend = existing.scalar_one_or_none()
                    
                    if existing_trend:
                        # Mettre à jour
                        existing_trend.trend_score = trend_data.trend_score
                        existing_trend.viral_potential = trend_data.viral_potential
                        existing_trend.volume = trend_data.volume
                        existing_trend.growth_rate = trend_data.growth_rate
                        existing_trend.fetched_at = datetime.utcnow()
                    else:
                        # Créer nouveau
                        new_trend = TrendRecord(
                            hashtag=trend_data.hashtag,
                            trend_score=trend_data.trend_score,
                            viral_potential=trend_data.viral_potential,
                            volume=trend_data.volume,
                            growth_rate=trend_data.growth_rate,
                            category=trend_data.category,
                            region=trend_data.region,
                            api_source=trend_data.api_source,
                            compliance_verified=trend_data.compliance_verified
                        )
                        session.add(new_trend)
                
                await session.commit()
                logger.info(f"✅ Stored {len(trends)} trends in database")
            
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Failed to store trends: {e}")
                raise
    
    async def _get_cached_trends(self, limit: int) -> List[TrendData]:
        """Récupère les tendances en cache (fallback)"""
        async with self.async_session() as session:
            try:
                # Récupérer les tendances récentes (moins de 4 heures)
                cutoff_time = datetime.utcnow() - timedelta(hours=4)
                
                result = await session.execute(
                    sa.select(TrendRecord)
                    .where(TrendRecord.fetched_at > cutoff_time)
                    .order_by(TrendRecord.viral_potential.desc())
                    .limit(limit)
                )
                
                records = result.scalars().all()
                
                trends = []
                for record in records:
                    trend = TrendData(
                        hashtag=record.hashtag,
                        trend_score=record.trend_score,
                        viral_potential=record.viral_potential,
                        volume=record.volume,
                        growth_rate=record.growth_rate,
                        category=record.category,
                        region=record.region,
                        api_source=record.api_source,
                        compliance_verified=record.compliance_verified
                    )
                    trends.append(trend)
                
                return trends
            
            except Exception as e:
                logger.error(f"❌ Failed to get cached trends: {e}")
                return []
    
    async def get_trend_analytics(self) -> Dict:
        """Récupère les analytics des tendances"""
        async with self.async_session() as session:
            try:
                # Statistiques générales
                total_trends = await session.execute(sa.select(sa.func.count(TrendRecord.id)))
                total_count = total_trends.scalar()
                
                # Tendances par catégorie
                category_stats = await session.execute(
                    sa.select(TrendRecord.category, sa.func.count(TrendRecord.id))
                    .group_by(TrendRecord.category)
                )
                
                categories = {}
                for category, count in category_stats:
                    categories[category] = count
                
                # Top tendances virales
                top_viral = await session.execute(
                    sa.select(TrendRecord.hashtag, TrendRecord.viral_potential)
                    .order_by(TrendRecord.viral_potential.desc())
                    .limit(10)
                )
                
                top_trends = []
                for hashtag, potential in top_viral:
                    top_trends.append({
                        'hashtag': hashtag,
                        'viral_potential': round(potential, 3)
                    })
                
                return {
                    'total_trends': total_count,
                    'categories': categories,
                    'top_viral_trends': top_trends,
                    'last_updated': datetime.utcnow().isoformat()
                }
            
            except Exception as e:
                logger.error(f"❌ Failed to get trend analytics: {e}")
                return {}
    
    async def cleanup_old_trends(self, days: int = 7):
        """Nettoie les anciennes tendances"""
        async with self.async_session() as session:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                result = await session.execute(
                    sa.delete(TrendRecord).where(TrendRecord.fetched_at < cutoff_date)
                )
                
                deleted_count = result.rowcount
                await session.commit()
                
                logger.info(f"🧹 Cleaned up {deleted_count} old trends (older than {days} days)")
            
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Failed to cleanup old trends: {e}")
    
    async def close(self):
        """Ferme les connexions"""
        await self.redis.close()
        await self.engine.dispose()
        logger.info("✅ TrendAnalyzer connections closed")
