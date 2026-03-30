"""
Admin API Routes
Administrative functions (cache management, diagnostics)
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    Clear application cache
    Requires ADMIN_TOKEN header in production
    """
    # Check authentication
    if not current_app.config.get('DEBUG', True):
        token = request.headers.get('X-Admin-Token')
        expected = current_app.config.get('ADMIN_TOKEN')
        if not expected or token != expected:
            current_app.logger.warning(
                f"Unauthorized cache clear attempt from {request.remote_addr}"
            )
            return jsonify({'error': 'Unauthorized'}), 403

    # Clear cache
    cache = current_app.extensions.get('cache')
    if cache:
        try:
            cache.clear()
            current_app.logger.info("Cache cleared by admin")
            return jsonify({
                'message': 'Cache cleared successfully',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        except Exception as e:
            current_app.logger.error(f"Cache clear failed: {e}")
            return jsonify({'error': 'Cache clear failed'}), 500
    else:
        return jsonify({'message': 'Cache is disabled'}), 200


@admin_bp.route('/metrics/detailed', methods=['GET'])
def detailed_metrics():
    """Get detailed system metrics (admin only)"""
    # In production, require admin auth

    cache = current_app.extensions.get('cache')
    cache_stats = {}
    if cache:
        try:
            # Get stats if available
            if hasattr(cache, 'get_stats'):
                cache_stats = cache.get_stats()
        except:
            pass

    return jsonify({
        'cache': cache_stats,
        'config': {
            'debug': current_app.config.get('DEBUG'),
            'cache_enabled': current_app.config.get('CACHE_ENABLED'),
            'cache_type': current_app.config.get('CACHE_TYPE'),
            'rate_limiting': current_app.config.get('RATELIMIT_ENABLED')
        }
    }), 200
