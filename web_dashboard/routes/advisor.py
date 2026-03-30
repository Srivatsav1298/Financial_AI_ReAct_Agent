"""
Advisor API Routes
Handles AI question answering
"""

import time
from flask import Blueprint, request, jsonify, g, current_app
from pydantic import BaseModel, Field, validator
from typing import Optional

from services.agent_service import AgentService

# Create blueprint
advisor_bp = Blueprint('advisor', __name__, url_prefix='/api')


# Request validation
class QuestionRequest(BaseModel):
    """Validated question request"""
    question: str = Field(..., min_length=3, max_length=1000)
    language: str = Field('en', pattern='^(en|no)$')
    persona: str = Field('analyst')
    agent_type: Optional[str] = Field(None, pattern='^(baseline|react)$')

    @validator('question')
    def sanitize_question(cls, v):
        """Basic sanitization"""
        # Strip HTML/script tags
        import re
        v = re.sub(r'<[^>]+>', '', v)
        # Limit whitespace
        v = ' '.join(v.split())
        return v.strip()


# Route handlers
@advisor_bp.route('/ask', methods=['POST'])
def ask_question():
    """
    Ask a question to both AI agents
    Rate Limit: 30/minute
    Cache: 1 hour per unique question
    """
    start_time = time.time()

    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        try:
            data = request.get_json()
        except Exception:
            return jsonify({'error': 'Invalid JSON payload'}), 400

        # Validate with Pydantic
        try:
            req = QuestionRequest(**data)
        except Exception as e:
            return jsonify({
                'error': 'Validation failed',
                'message': str(e)
            }), 400

        # Get agent service (injected in create_app)
        agent_service = current_app.extensions.get('agent_service')
        if not agent_service:
            return jsonify({'error': 'Service unavailable'}), 503

        # Process question
        result = agent_service.answer_sync(
            question=req.question,
            language=req.language,
            persona=req.persona,
            agent_type=req.agent_type
        )

        total_time = time.time() - start_time

        # Add metadata
        response = dict(result)
        response['question'] = req.question
        response['language'] = req.language
        response['server_time_ms'] = int(total_time * 1000)

        # Log success
        current_app.logger.info(
            f"✅ Ask completed: {req.question[:50]}... "
            f"(B:{result['baseline'].get('time', 0):.2f}s "
            f"R:{result['react'].get('time', 0):.2f}s)"
        )

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Ask error: {e}", exc_info=True)
        return jsonify({
            'error': 'Processing failed',
            'message': str(e) if current_app.config['DEBUG'] else 'Internal error'
        }), 500


@advisor_bp.route('/agent/info', methods=['GET'])
def get_agent_info():
    """Get information about available agents"""
    agent_service = current_app.extensions.get('agent_service')
    if not agent_service:
        return jsonify({'error': 'Service unavailable'}), 503

    return jsonify(agent_service.get_agent_info()), 200
