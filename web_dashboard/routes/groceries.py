"""
Groceries Routes
Price comparison and grocery tracking
"""

from flask import Blueprint, jsonify, current_app

groceries_bp = Blueprint('groceries', __name__)


@groceries_bp.route('/groceries', methods=['GET'])
def groceries_page():
    """Render grocery page (handled by templates, but keeping for symmetry)"""
    # This is actually handled by template render in main app
    # This blueprint is for API endpoints only
    return jsonify({'message': 'Groceries API'}), 200


@groceries_bp.route('/api/prisjakt/products', methods=['GET'])
def get_prisjakt_products():
    """Get product price comparisons from Prisjakt"""
    # Placeholder - integrate with actual Prisjakt API
    return jsonify({
        'products': [],
        'message': 'Prisjakt integration coming soon'
    }), 200
