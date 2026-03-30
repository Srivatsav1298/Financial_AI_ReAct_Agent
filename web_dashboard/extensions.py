"""
Flask Extensions Initialization
Centralized extension management for better modularity
"""

from flask_caching import Cache
from flask_cors import CORS
from flask_compress import Compress


# Extensions (initialized in create_app)
cache = Cache()
cors = CORS()
compress = Compress()


def init_extensions(app):
    """Initialize all extensions with the app"""
    # Initialize compression (gzip/brotli)
    compress.init_app(app)
    app.logger.info("✅ Compression enabled (gzip/brotli)")

    # Initialize Cache
    if app.config.get('CACHE_ENABLED', True):
        cache_config = {
            'CACHE_TYPE': app.config.get('CACHE_TYPE', 'simple'),
            'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 3600),
            'CACHE_KEY_PREFIX': app.config.get('CACHE_KEY_PREFIX', 'norfain:'),
        }

        if app.config.get('CACHE_TYPE') == 'redis':
            cache_config['CACHE_REDIS_URL'] = app.config.get('CACHE_REDIS_URL')

        cache.init_app(app, config=cache_config)
        app.logger.info(f"✅ Cache initialized: {app.config.get('CACHE_TYPE')}")
    else:
        cache.init_app(app, {'CACHE_TYPE': 'null'})
        app.logger.info("⚠️ Cache disabled")

    # Initialize CORS
    if app.config.get('CORS_ORIGINS'):
        cors.init_app(
            app,
            origins=app.config['CORS_ORIGINS'],
            supports_credentials=False,
            allow_headers=['Content-Type'],
            methods=['GET', 'POST', 'PUT', 'DELETE']
        )
        app.logger.info(f"✅ CORS restricted to: {app.config['CORS_ORIGINS']}")
    else:
        # Development fallback
        dev_origins = ['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:5050']
        cors.init_app(app, origins=dev_origins, supports_credentials=False)
        app.logger.info("⚠️ CORS in development mode (localhost only)")
