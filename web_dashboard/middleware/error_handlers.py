"""
Global Error Handlers
Provides consistent error responses across the API
"""

import traceback
from flask import jsonify, current_app, request
import json


class APIError(Exception):
    """Base API error with structured response"""

    def __init__(self, message: str, status_code: int = 400, payload: dict = None):
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self) -> dict:
        rv = dict(self.payload)
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


class ValidationError(APIError):
    """Raised when input validation fails"""

    def __init__(self, message: str, field: str = None, payload: dict = None):
        super().__init__(message, 400, payload)
        if field:
            self.payload['field'] = field


class AuthenticationError(APIError):
    """Raised when authentication fails"""

    def __init__(self, message: str = 'Authentication required'):
        super().__init__(message, 401)


class AuthorizationError(APIError):
    """Raised when user lacks permission"""

    def __init__(self, message: str = 'Insufficient permissions'):
        super().__init__(message, 403)


class RateLimitError(APIError):
    """Raised when rate limit is exceeded"""

    def __init__(self, message: str = 'Rate limit exceeded', retry_after: int = 60):
        super().__init__(message, 429, {'retry_after': retry_after})


def register_error_handlers(app):
    """Register global error handlers"""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors"""
        current_app.logger.warning(
            f"API Error {error.status_code}: {error.message} "
            f"from {request.remote_addr} for {request.path}"
        )
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def bad_request_handler(e):
        """Handle bad request errors"""
        current_app.logger.warning(f"Bad Request: {request.path} - {str(e)}")
        return jsonify({
            'error': 'Bad Request',
            'message': str(e),
            'status_code': 400
        }), 400

    @app.errorhandler(404)
    def not_found_handler(e):
        """Handle 404 errors"""
        current_app.logger.info(f"Not Found: {request.path}")
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404

    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Handle rate limit errors"""
        retry_after = getattr(e, 'retry_after', 60)
        current_app.logger.warning(
            f"Rate limit exceeded: {request.remote_addr} on {request.path}"
        )
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': retry_after,
            'status_code': 429
        }), 429

    @app.errorhandler(500)
    def internal_error_handler(e):
        """Handle internal server errors"""
        current_app.logger.error(
            f"Internal Server Error: {request.path}",
            exc_info=True
        )

        # Only show detailed error in development
        if current_app.config.get('DEBUG', False):
            error_details = {
                'exception': str(e),
                'traceback': traceback.format_exc()
            }
        else:
            error_details = {
                'message': 'An unexpected error occurred. Our team has been notified.'
            }

        response = jsonify({
            'error': 'Internal server error',
            'status_code': 500,
            **error_details
        })
        response.status_code = 500
        return response

    @app.errorhandler(Exception)
    def unhandled_exception_handler(e):
        """Catch-all for unhandled exceptions"""
        current_app.logger.error(
            f"Unhandled Exception: {request.path}",
            exc_info=True
        )

        response = jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred.' if not current_app.config.get('DEBUG') else str(e),
            'status_code': 500
        })
        response.status_code = 500
        return response
