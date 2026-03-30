"""
Savings Goals Routes
User savings goals management
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import uuid

savings_bp = Blueprint('savings', __name__)


# In-memory storage for demo (replace with database in production)
_savings_goals = {}


@savings_bp.route('/api/goals', methods=['GET'])
def get_goals():
    """Get all savings goals"""
    return jsonify({
        'goals': list(_savings_goals.values())
    }), 200


@savings_bp.route('/api/goals', methods=['POST'])
def create_goal():
    """Create a new savings goal"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()

    required = ['name', 'target_amount', 'deadline']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    goal_id = str(uuid.uuid4())
    goal = {
        'id': goal_id,
        'name': data['name'],
        'target_amount': float(data['target_amount']),
        'current_amount': float(data.get('current_amount', 0)),
        'deadline': data['deadline'],  # ISO date string
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'inflation_adjusted': data.get('inflation_adjusted', True)
    }

    _savings_goals[goal_id] = goal

    return jsonify({'goal': goal}), 201


@savings_bp.route('/api/goals/<goal_id>', methods=['PUT'])
def update_goal(goal_id):
    """Update a savings goal"""
    if goal_id not in _savings_goals:
        return jsonify({'error': 'Goal not found'}), 404

    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()
    goal = _savings_goals[goal_id]

    # Update allowed fields
    for field in ['name', 'target_amount', 'current_amount', 'deadline', 'inflation_adjusted']:
        if field in data:
            if field in ['target_amount', 'current_amount']:
                goal[field] = float(data[field])
            else:
                goal[field] = data[field]

    _savings_goals[goal_id] = goal

    return jsonify({'goal': goal}), 200


@savings_bp.route('/api/goals/<goal_id>', methods=['DELETE'])
def delete_goal(goal_id):
    """Delete a savings goal"""
    if goal_id not in _savings_goals:
        return jsonify({'error': 'Goal not found'}), 404

    del _savings_goals[goal_id]
    return jsonify({'message': 'Goal deleted'}), 200


@savings_bp.route('/api/goals/<goal_id>/contribute', methods=['POST'])
def contribute_to_goal(goal_id):
    """Add a contribution to a goal"""
    if goal_id not in _savings_goals:
        return jsonify({'error': 'Goal not found'}), 404

    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.get_json()

    if 'amount' not in data:
        return jsonify({'error': 'Missing amount field'}), 400

    amount = float(data['amount'])
    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400

    goal = _savings_goals[goal_id]
    goal['current_amount'] += amount

    return jsonify({
        'goal': goal,
        'contribution': amount,
        'message': f'Added {amount} to goal'
    }), 200
