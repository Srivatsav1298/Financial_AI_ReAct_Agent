"""
Security Middleware
Handles security headers, CSP, and other security measures
"""

import secrets
from flask import request, g, current_app
from functools import wraps
import bleach


def generate_csp_nonce():
    """Generate a secure nonce for CSP"""
    return secrets.token_hex(16)


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent XSS"""
    if not text or not isinstance(text, str):
        return ""

    # Strip dangerous HTML/JS using bleach
    cleaned = bleach.clean(text, strip=True)

    # Limit whitespace
    cleaned = ' '.join(cleaned.split())

    # Limit length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip()

    return cleaned


def security_headers(app):
    """
    Register security headers middleware
    Implements OWASP recommended headers
    """

    @app.after_request
    def add_security_headers(response):
        # Basic security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # HSTS - only in production (HTTPS)
        if not current_app.config.get('DEBUG', True) and request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy
        csp = build_csp_header()
        if csp:
            response.headers['Content-Security-Policy'] = csp

        # Remove server identification
        response.headers.pop('Server', None)

        return response

    @app.before_request
    def generate_nonce():
        """Generate CSP nonce for each request"""
        g.csp_nonce = generate_csp_nonce()


def build_csp_header() -> str:
    """Build Content Security Policy header based on config"""
    directives = []

    # Default src
    default_src = ["'self'"]
    if config := current_app.config:
        if custom := config.get('CSP_DEFAULT_SRC'):
            default_src = custom
    directives.append(f"default-src {' '.join(default_src)}")

    # Script src
    script_src = ["'self'"]
    if g.get('csp_nonce'):
        script_src.append(f"'nonce-{g.csp_nonce}'")
    if config := current_app.config:
        if custom := config.get('CSP_SCRIPT_SRC'):
            script_src.extend(custom)
    directives.append(f"script-src {' '.join(script_src)}")

    # Style src
    style_src = ["'self'", "'unsafe-inline'"]
    if config := current_app.config:
        if custom := config.get('CSP_STYLE_SRC'):
            style_src = custom
    directives.append(f"style-src {' '.join(style_src)}")

    # Font src
    font_src = ["'self'"]
    if config := current_app.config:
        if custom := config.get('CSP_FONT_SRC'):
            font_src = custom
    directives.append(f"font-src {' '.join(font_src)}")

    # Image src
    img_src = ["'self'", "data:"]
    if config := current_app.config:
        if custom := config.get('CSP_IMG_SRC'):
            img_src = custom
    directives.append(f"img-src {' '.join(img_src)}")

    # Connect src (for API calls)
    connect_src = ["'self'"]
    if config := current_app.config:
        if custom := config.get('CSP_CONNECT_SRC'):
            connect_src = custom
    directives.append(f"connect-src {' '.join(connect_src)}")

    # Frame ancestors (prevent clickjacking)
    frame_ancestors = ["'none'"]
    if config := current_app.config:
        if custom := config.get('CSP_FRAME_ANCESTORS'):
            frame_ancestors = custom
    directives.append(f"frame-ancestors {' '.join(frame_ancestors)}")

    return '; '.join(directives)


def csrf_protect(app):
    """
    Basic CSRF protection using double-submit cookie pattern
    Note: For full CSRF protection, consider Flask-WTF
    """

    @app.before_request
    def check_csrf():
        if request.method in ['POST', 'PUT', 'DELETE'] and request.path.startswith('/api/'):
            # Skip CSRF check for API tokens (use proper auth instead)
            # API endpoints should use authentication headers
            token = request.headers.get('X-CSRFToken')
            cookie = request.cookies.get('csrf_token')

            if not token or token != cookie:
                # Allow if using API token auth (future enhancement)
                # For now, log warning
                current_app.logger.warning(
                    f"CSRF check failed for {request.method} {request.path} "
                    f"from {request.remote_addr}"
                )

    @app.after_request
    def set_csrf_cookie(response):
        """Set CSRF token cookie on all responses"""
        if 'csrf_token' not in request.cookies:
            token = secrets.token_hex(32)
            response.set_cookie(
                'csrf_token',
                token,
                httponly=True,
                secure=not current_app.config.get('DEBUG', True),
                samesite='Lax',
                max_age=86400  # 24 hours
            )
        return response


def require_auth(f):
    """
    Decorator to require authentication for endpoints
    Basic implementation - integrate with proper auth system
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for Authorization header
        auth_header = request.headers.get('Authorization', '')

        if not auth_header:
            return {'error': 'Authentication required'}, 401

        # TODO: Implement proper JWT or session validation
        # For now, just check for a token format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return {'error': 'Invalid authorization format'}, 401

        token = parts[1]
        # Validate token (placeholder)
        g.user = {'token': token}

        return f(*args, **kwargs)

    return decorated
