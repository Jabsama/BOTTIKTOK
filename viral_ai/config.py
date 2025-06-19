"""
🔧 Configuration Management - Production Ready
Gestion sécurisée des configurations et secrets
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

@dataclass
class TikTokConfig:
    """Configuration TikTok API"""
    client_key: str
    client_secret: str
    access_token: str
    refresh_token: str
    business_account_id: str
    
@dataclass
class DatabaseConfig:
    """Configuration base de données"""
    url: str = "sqlite:///viral_ai.db"
    pool_size: int = 10
    max_overflow: int = 20
    
@dataclass
class RedisConfig:
    """Configuration Redis pour rate limiting"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
@dataclass
class MonitoringConfig:
    """Configuration monitoring Prometheus"""
    enabled: bool = True
    port: int = 8000
    metrics_path: str = "/metrics"

class SecretManager:
    """Gestionnaire de secrets sécurisé"""
    
    def __init__(self, use_aws: bool = False):
        self.use_aws = use_aws
        if use_aws:
            try:
                self.secrets_client = boto3.client('secretsmanager')
                logger.info("✅ AWS Secrets Manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ AWS Secrets Manager failed: {e}")
                self.use_aws = False
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Récupère un secret de manière sécurisée"""
        
        # 1. Essayer AWS Secrets Manager
        if self.use_aws:
            try:
                response = self.secrets_client.get_secret_value(SecretId=secret_name)
                return response['SecretString']
            except ClientError as e:
                logger.warning(f"⚠️ AWS secret {secret_name} not found: {e}")
        
        # 2. Essayer Docker Secrets
        docker_secret_path = f"/run/secrets/{secret_name}"
        if os.path.exists(docker_secret_path):
            try:
                with open(docker_secret_path, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"⚠️ Docker secret {secret_name} read failed: {e}")
        
        # 3. Fallback sur variables d'environnement
        env_value = os.getenv(secret_name.upper())
        if env_value:
            return env_value
        
        # 4. Valeur par défaut
        if default is not None:
            logger.warning(f"⚠️ Using default value for {secret_name}")
            return default
        
        logger.error(f"❌ Secret {secret_name} not found anywhere!")
        return None

class Config:
    """Configuration principale - Production Ready"""
    
    def __init__(self, config_path: str = "config.yaml", use_aws_secrets: bool = False):
        self.config_path = Path(config_path)
        self.secret_manager = SecretManager(use_aws=use_aws_secrets)
        
        # Charger la configuration
        self._load_config()
        self._load_secrets()
        self._validate_config()
        
        logger.info("✅ Configuration loaded successfully")
    
    def _load_config(self):
        """Charge la configuration depuis YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"❌ Config file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"❌ Invalid YAML in config: {e}")
            raise
    
    def _load_secrets(self):
        """Charge les secrets de manière sécurisée"""
        # TikTok API credentials
        self.tiktok = TikTokConfig(
            client_key=self.secret_manager.get_secret("tiktok_client_key", ""),
            client_secret=self.secret_manager.get_secret("tiktok_client_secret", ""),
            access_token=self.secret_manager.get_secret("tiktok_access_token", ""),
            refresh_token=self.secret_manager.get_secret("tiktok_refresh_token", ""),
            business_account_id=self.secret_manager.get_secret("tiktok_business_account_id", "")
        )
        
        # Database
        self.database = DatabaseConfig(
            url=self.secret_manager.get_secret("database_url", "sqlite:///viral_ai.db")
        )
        
        # Redis
        self.redis = RedisConfig(
            host=self.secret_manager.get_secret("redis_host", "localhost"),
            port=int(self.secret_manager.get_secret("redis_port", "6379")),
            password=self.secret_manager.get_secret("redis_password")
        )
        
        # Monitoring
        self.monitoring = MonitoringConfig(
            enabled=self.secret_manager.get_secret("monitoring_enabled", "true").lower() == "true",
            port=int(self.secret_manager.get_secret("monitoring_port", "8000"))
        )
    
    def _validate_config(self):
        """Valide la configuration"""
        errors = []
        
        # Validation TikTok
        if not self.tiktok.client_key:
            errors.append("TikTok client_key is required")
        if not self.tiktok.client_secret:
            errors.append("TikTok client_secret is required")
        if not self.tiktok.access_token:
            errors.append("TikTok access_token is required")
        
        # Validation structure config
        required_sections = ['brand', 'video', 'posting', 'disclaimers']
        for section in required_sections:
            if section not in self.data:
                errors.append(f"Missing required config section: {section}")
        
        if errors:
            logger.error(f"❌ Configuration validation failed: {errors}")
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de configuration"""
        keys = key.split('.')
        value = self.data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_brand_config(self) -> Dict[str, Any]:
        """Configuration de marque"""
        return self.get('brand', {})
    
    def get_video_config(self) -> Dict[str, Any]:
        """Configuration vidéo"""
        return self.get('video', {})
    
    def get_posting_config(self) -> Dict[str, Any]:
        """Configuration posting"""
        return self.get('posting', {})
    
    def get_disclaimers(self) -> Dict[str, str]:
        """Disclaimers de compliance"""
        return self.get('disclaimers', {})
    
    def get_templates_config(self, language: str = 'en') -> Dict[str, Any]:
        """Templates par langue pour internationalisation"""
        templates_file = f"templates_{language}.yaml"
        
        try:
            with open(templates_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"⚠️ Templates file not found: {templates_file}, using English")
            try:
                with open("templates_en.yaml", 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except FileNotFoundError:
                logger.error("❌ No template files found!")
                return {}
    
    def is_production(self) -> bool:
        """Vérifie si on est en production"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    
    def get_log_level(self) -> str:
        """Niveau de log selon l'environnement"""
        if self.is_production():
            return 'INFO'
        return os.getenv('LOG_LEVEL', 'DEBUG')
    
    def reload(self):
        """Recharge la configuration (utile pour les tests)"""
        self._load_config()
        self._load_secrets()
        self._validate_config()
        logger.info("🔄 Configuration reloaded")

# Instance globale pour faciliter l'import
config = None

def get_config(config_path: str = "config.yaml", use_aws_secrets: bool = None) -> Config:
    """Factory pour obtenir l'instance de configuration"""
    global config
    
    if config is None:
        # Auto-détection AWS en production
        if use_aws_secrets is None:
            use_aws_secrets = os.getenv('ENVIRONMENT') == 'production'
        
        config = Config(config_path, use_aws_secrets)
    
    return config

def setup_logging(config: Config):
    """Configure le logging selon la configuration"""
    log_level = getattr(logging, config.get_log_level().upper())
    
    # Format selon l'environnement
    if config.is_production():
        # Format JSON pour production (compatible avec ELK stack)
        import json
        import datetime
        
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)
                return json.dumps(log_entry)
        
        formatter = JSONFormatter()
    else:
        # Format lisible pour développement
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Configuration du logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Handler fichier rotatif en production
    if config.is_production():
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            'logs/viral_ai.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    logger.info(f"✅ Logging configured (level: {config.get_log_level()})")
