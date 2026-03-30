"""
SSB Data API Routes
Direct access to SSB statistics
"""

import time
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Optional

from services.ssb_service import SSBService

ssb_bp = Blueprint('ssb', __name__)


@ssb_bp.route('/api/ssb-data', methods=['GET'])
def get_ssb_data():
    """
    Get SSB household budget data
    Query params:
    - year: 4-digit year (default: 2022)
    - nowcast: true/false (default: true) - apply inflation adjustment
    """
    start_time = time.time()

    try:
        year = request.args.get('year', '2022')
        nowcast = request.args.get('nowcast', 'true').lower() == 'true'

        # Validate year
        if not year.isdigit() or len(year) != 4 or int(year) < 2000 or int(year) > 2030:
            return jsonify({'error': 'Invalid year parameter'}), 400

        # Get SSB service
        ssb_service: SSBService = current_app.extensions.get('ssb_service')
        if not ssb_service:
            return jsonify({'error': 'SSB service unavailable'}), 503

        # Fetch data
        data = ssb_service.get_household_budget_data(year=year, nowcast=nowcast)

        elapsed = time.time() - start_time
        current_app.logger.info(f"SSB data request: year={year}, nowcast={nowcast}, time={elapsed:.2f}s")

        return jsonify({
            'data': data,
            'metadata': {
                'year': year,
                'nowcast': nowcast,
                'source': 'SSB (Statistics Norway)',
                'count': len(data)
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"SSB data error: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to fetch SSB data',
            'message': str(e) if current_app.config['DEBUG'] else 'Service temporarily unavailable'
        }), 500


@ssb_bp.route('/api/cpi', methods=['GET'])
def get_cpi():
    """
    Get CPI inflation data
    Returns multipliers for different spending categories
    """
    try:
        ssb_service: SSBService = current_app.extensions.get('ssb_service')
        if not ssb_service:
            return jsonify({'error': 'SSB service unavailable'}), 503

        multipliers = ssb_service.get_cpi_adjustments()

        return jsonify({
            'multipliers': multipliers,
            'source': 'SSB Table 03013',
            'description': 'CPI multipliers from 2022 to present',
            'base_year': '2022'
        }), 200

    except Exception as e:
        current_app.logger.error(f"CPI error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@ssb_bp.route('/api/landing_context', methods=['GET'])
def get_landing_context():
    """
    Get all context data needed for landing page dashboard
    Includes household budget, CPI, inflation trends
    """
    try:
        ssb_service: SSBService = current_app.extensions.get('ssb_service')
        if not ssb_service:
            return jsonify({'error': 'SSB service unavailable'}), 503

        context = ssb_service.get_landing_context()

        return jsonify(context), 200

    except Exception as e:
        current_app.logger.error(f"Landing context error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
