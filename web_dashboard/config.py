"""
Configuration Management
Supports multiple environments: Development, Production, Testing
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system env only


@dataclass
class BaseConfig:
    """Base configuration shared across all environments"""
    DEBUG = False
    TESTING = False

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # CORS
    CORS_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else []

    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per hour')
    RATELIMIT_ASK = os.getenv('RATELIMIT_ASK', '30 per minute')
    RATELIMIT_SSB = os.getenv('RATELIMIT_SSB', '60 per minute')

    # Caching
    CACHE_ENABLED = True
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')  # 'simple', 'redis'
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '3600'))  # 1 hour
    CACHE_KEY_PREFIX = 'norfain:'
    CACHE_REDIS_URL = os.getenv('REDIS_URL')
    CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', '1000'))

    # SSB API specific
    SSB_CACHE_TTL = int(os.getenv('SSB_CACHE_TTL', '86400'))  # 24 hours

    # Performance
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16384'))  # 16KB
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '120'))

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

    # Admin
    ADMIN_TOKEN = os.getenv('ADMIN_TOKEN')

    # LLM
    AGENT_MODEL = os.getenv('AGENT_MODEL', 'llama3.2:latest')
    DEFAULT_AGENT = os.getenv('DEFAULT_AGENT', 'react')

    # SSB API
    SSB_API_BASE_URL = os.getenv('SSB_API_BASE_URL', 'https://data.ssb.no/api/v0')


@dataclass
class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:5050']
    CACHE_TYPE = 'simple'
    LOG_LEVEL = 'DEBUG'


@dataclass
class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Enforce security in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # Use Redis in production for shared cache
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Redis for rate limiting storage too
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Stronger CSP
    CSP_DEFAULT_SRC = ["'self'"]
    CSP_SCRIPT_SRC = ["'self'", "cdn.tailwindcss.com"]
    CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "fonts.googleapis.com"]
    CSP_FONT_SRC = ["'self'", "fonts.gstatic.com"]
    CSP_IMG_SRC = ["'self'", "data:"]
    CSP_CONNECT_SRC = ["'self'"]
    CSP_FRAME_ANCESTORS = ["'none'"]


@dataclass
class TestingConfig(BaseConfig):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    CACHE_ENABLED = False
    RATELIMIT_ENABLED = False


def get_config() -> BaseConfig:
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development').lower()

    config_map = {
        'development': DevelopmentConfig,
        'prod': ProductionConfig,
        'production': ProductionConfig,
        'test': TestingConfig,
        'testing': TestingConfig
    }

    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()
