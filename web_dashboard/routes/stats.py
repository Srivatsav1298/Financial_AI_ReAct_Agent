"""
Additional Stats Route
Completes the route coverage from original app.py
"""

from flask import Blueprint, jsonify, current_app
from services.ssb_service import SSBService

stats_bp = Blueprint('stats', __name__, url_prefix='/api')


@stats_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get comprehensive statistics about the application
    Includes agent metrics, SSB data summaries, etc.
    """
    try:
        ssb_service: SSBService = current_app.extensions.get('ssb_service')
        if ssb_service:
            household_data = ssb_service.get_household_budget_data(nowcast=True)
            cpi_data = ssb_service.get_cpi_adjustments()
        else:
            household_data = []
            cpi_data = {}

        stats = {
            'agents': {
                'baseline': 'available',
                'react': 'available'
            },
            'ssb_data': {
                'household_categories': len(household_data) if household_data else 0,
                'cpi_categories': len(cpi_data) if cpi_data else 0,
                'source': 'Statistics Norway (SSB)'
            },
            'cache': {
                'type': current_app.config.get('CACHE_TYPE', 'none'),
                'enabled': current_app.config.get('CACHE_ENABLED', False)
            },
            'rate_limiting': {
                'enabled': current_app.config.get('RATELIMIT_ENABLED', False),
                'default': current_app.config.get('RATELIMIT_DEFAULT')
            }
        }

        return jsonify(stats), 200

    except Exception as e:
        current_app.logger.error(f"Stats error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# Note: /api/analyze-bill is not implemented in original app either (placeholder)
# If needed, it can be added to a separate bills blueprint
