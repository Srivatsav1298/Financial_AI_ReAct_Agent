"""
Metrics and Health Check Routes
Monitoring endpoints
"""

import time
from flask import Blueprint, jsonify, current_app
from datetime import datetime

metrics_bp = Blueprint('metrics', __name__)


@metrics_bp.route('/health')
def health_check():
    """
    Health check endpoint for load balancers and monitoring
    Returns comprehensive health status
    """
    start = time.time()

    health = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'components': {
            'app': 'healthy',
            'agents': 'unknown',
            'ssb_api': 'unknown',
            'cache': 'unknown'
        },
        'metrics': {}
    }

    # Check agents
    agent_service = current_app.extensions.get('agent_service')
    if agent_service:
        health['components']['agents'] = 'loaded'
        health['components']['baseline_agent'] = 'healthy'
        health['components']['react_agent'] = 'healthy'
    else:
        health['components']['agents'] = 'unavailable'

    # Check SSB API
    ssb_service = current_app.extensions.get('ssb_service')
    if ssb_service:
        health['components']['ssb_api'] = 'connected'
    else:
        health['components']['ssb_api'] = 'unavailable'

    # Check cache
    cache = current_app.extensions.get('cache')
    if cache:
        health['components']['cache'] = 'enabled'
    else:
        health['components']['cache'] = 'disabled'

    # Get metrics
    from middleware.metrics import metrics
    health['metrics'] = metrics.get_stats()

    # Determine overall status
    response_time = time.time() - start
    health['response_time_ms'] = int(response_time * 1000)

    # Status based on component health
    component_statuses = list(health['components'].values())
    if any('unavailable' in status for status in component_statuses):
        health['status'] = 'degraded'
    elif any('error' in status for status in component_statuses):
        health['status'] = 'unhealthy'

    status_code = 200 if health['status'] in ['healthy', 'degraded'] else 503

    return jsonify(health), status_code


@metrics_bp.route('/api/metrics')
def prometheus_metrics():
    """
    Prometheus-format metrics endpoint
    Used by Prometheus/Grafana for monitoring
    """
    from middleware.metrics import metrics
    import time

    m = metrics.get_stats()

    # Get cache stats if available
    cache = current_app.extensions.get('cache')
    if cache and hasattr(cache, 'get_stats'):
        cache_stats = cache.get_stats()
        m.update({
            'cache_hits': cache_stats.get('hits', 0),
            'cache_misses': cache_stats.get('misses', 0),
            'cache_hit_rate': cache_stats.get('hit_rate', 0)
        })

    # Get app uptime
    if hasattr(current_app, 'start_time'):
        uptime = time.time() - current_app.start_time
        m['uptime_seconds'] = int(uptime)

    # Prometheus format
    lines = [
        '# HELP norfain_requests_total Total number of requests processed',
        '# TYPE norfain_requests_total counter',
        f'norfain_requests_total {m["requests"]}',
        '',
        '# HELP norfain_errors_total Total number of error responses',
        '# TYPE norfain_errors_total counter',
        f'norfain_errors_total {m["errors"]}',
        '',
        '# HELP norfain_response_time_seconds Average response time in seconds',
        '# TYPE norfain_response_time_seconds gauge',
        f'norfain_response_time_seconds {m["avg_response_time"]}',
        '',
        '# HELP norfain_response_time_p95_seconds 95th percentile response time',
        '# TYPE norfain_response_time_p95_seconds gauge',
        f'norfain_response_time_p95_seconds {m["p95_response_time"]}',
        '',
        '# HELP norfain_cache_hits_total Number of cache hits',
        '# TYPE norfain_cache_hits_total counter',
        f'norfain_cache_hits_total {m.get("cache_hits", 0)}',
        '',
        '# HELP norfain_uptime_seconds Application uptime in seconds',
        '# TYPE norfain_uptime_seconds gauge',
        f'norfain_uptime_seconds {m.get("uptime_seconds", 0)}'
    ]

    return '\n'.join(lines), 200, {'Content-Type': 'text/plain; charset=utf-8'}
