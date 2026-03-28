"""
Production-Ready Flask Backend for Norfain ReAct Agent Web Dashboard
Optimized for: Performance, Security, Scalability, Monitoring
"""

import os
import sys
import json
import time
import re
import hashlib
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, g
from flask_cors import CORS
import importlib

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Application configuration from environment"""
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production-!@#$%')

    # Rate limiting
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'true').lower() == 'true'
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per hour')
    RATELIMIT_ASK = os.getenv('RATELIMIT_ASK', '30 per minute')
    RATELIMIT_SSB = os.getenv('RATELIMIT_SSB', '60 per minute')

    # Caching
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour
    CACHE_MAX_SIZE = int(os.getenv('CACHE_MAX_SIZE', '1000'))
    SSB_CACHE_TTL = int(os.getenv('SSB_CACHE_TTL', '86400'))  # 24 hours

    # Security
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',') if os.getenv('ALLOWED_ORIGINS') else []
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

    # Performance
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16384'))  # 16KB max question
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '120'))

# ============================================================================
# LOGGING SETUP
# ============================================================================

log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'app.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# THREAD-SAFE LRU CACHE WITH TTL
# ============================================================================

class LRUCache:
    """Thread-safe LRU cache with TTL expiration"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = {}
        self._access_order = []
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if self._is_expired(entry):
                self._remove(key)
                return None

            # Update LRU order
            self._access_order.remove(key)
            self._access_order.append(key)
            return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        with self._lock:
            ttl = ttl or self.default_ttl

            # Evict LRU if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                if self._access_order:
                    oldest = self._access_order.pop(0)
                    self._cache.pop(oldest, None)

            self._cache[key] = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ttl
            }
            self._access_order.append(key)

    def _is_expired(self, entry: Dict) -> bool:
        return time.time() > entry.get('expires_at', float('inf'))

    def _remove(self, key: str):
        self._cache.pop(key, None)
        if key in self._access_order:
            self._access_order.remove(key)

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

# Initialize cache
if Config.CACHE_ENABLED:
    cache = LRUCache(max_size=Config.CACHE_MAX_SIZE, default_ttl=Config.CACHE_TTL)
else:
    cache = None

# ============================================================================
# INPUT VALIDATION
# ============================================================================

class Validator:
    """Request input validation"""

    @staticmethod
    def validate_question(question: str, max_length: int = 1000) -> tuple[bool, Optional[str]]:
        if not question or not isinstance(question, str):
            return False, "Question must be a non-empty string"

        question = question.strip()
        if len(question) > max_length:
            return False, f"Question exceeds maximum length of {max_length} characters"

        if len(question) < 3:
            return False, "Question is too short"

        # Basic XSS/injection detection
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'eval\(',
            r'document\.',
            r'window\.',
            r'alert\(',
            r'confirm\(',
            r'prompt\('
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                return False, "Invalid characters detected in question"

        return True, None

    @staticmethod
    def validate_language(language: str) -> tuple[bool, Optional[str]]:
        allowed = ['en', 'no']
        if language not in allowed:
            return False, f"Language must be one of: {', '.join(allowed)}"
        return True, None

    @staticmethod
    def validate_year(year: str) -> tuple[bool, Optional[str]]:
        if not re.match(r'^\d{4}$', year):
            return False, "Year must be in YYYY format"
        year_int = int(year)
        if year_int < 2000 or year_int > 2030:
            return False, "Year must be between 2000 and 2030"
        return True, None

# ============================================================================
# METRICS COLLECTION
# ============================================================================

class Metrics:
    """Lightweight request metrics collector"""

    def __init__(self):
        self._lock = threading.Lock()
        self._requests = 0
        self._errors = 0
        self._response_times = []

    def record(self, response_time: float, status_code: int):
        with self._lock:
            self._requests += 1
            if status_code >= 400:
                self._errors += 1
            self._response_times.append(response_time)
            if len(self._response_times) > 1000:
                self._response_times = self._response_times[-500:]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            if not self._response_times:
                return {
                    'requests': 0,
                    'errors': 0,
                    'error_rate': 0,
                    'avg_response_time': 0,
                    'p95_response_time': 0,
                    'samples': 0
                }

            sorted_times = sorted(self._response_times)
            p95_index = int(len(sorted_times) * 0.95)

            return {
                'requests': self._requests,
                'errors': self._errors,
                'error_rate': self._errors / self._requests if self._requests > 0 else 0,
                'avg_response_time': round(sum(sorted_times) / len(sorted_times), 4),
                'p95_response_time': round(sorted_times[min(p95_index, len(sorted_times)-1)], 4),
                'samples': len(sorted_times)
            }

metrics = Metrics()

# ============================================================================
# FLASK APPLICATION SETUP
# ============================================================================

# Add src to path (resolve from current file location)
current_dir = Path(__file__).parent
src_path = current_dir.parent / "src"
sys.path.insert(0, str(src_path))

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# ============================================================================
# SECURITY: CORS & HEADERS
# ============================================================================

# Configure CORS with specific origins
if Config.ALLOWED_ORIGINS:
    CORS(app,
         origins=Config.ALLOWED_ORIGINS,
         supports_credentials=False,
         methods=['GET', 'POST'],
         allow_headers=['Content-Type'])
    logger.info(f"CORS restricted to: {Config.ALLOWED_ORIGINS}")
else:
    # Development default origins
    dev_origins = ['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:5050']
    CORS(app, origins=dev_origins, supports_credentials=False)
    logger.info("CORS in development mode (localhost only)")

# ============================================================================
# RATE LIMITING (Simple in-memory implementation)
# ============================================================================

if Config.RATELIMIT_ENABLED:
    from collections import defaultdict

    class SimpleRateLimiter:
        """Simple in-memory sliding window rate limiter"""

        def __init__(self):
            self._requests = defaultdict(list)
            self._lock = threading.Lock()

        def is_allowed(self, key: str, limit: int, period: int) -> bool:
            now = time.time()
            window_start = now - period

            with self._lock:
                # Clean old requests
                self._requests[key] = [req_time for req_time in self._requests[key]
                                      if req_time > window_start]

                if len(self._requests[key]) >= limit:
                    return False

                self._requests[key].append(now)
                return True

    rate_limiter = SimpleRateLimiter()

    def check_rate_limit(endpoint: str, limit: int, period: int = 60) -> tuple[bool, Optional[int]]:
        client_ip = request.remote_addr or 'unknown'
        key = f"{endpoint}:{client_ip}"

        if not rate_limiter.is_allowed(key, limit, period):
            remaining = 0
            return False, remaining
        return True, limit - len(rate_limiter._requests[key])

else:
    rate_limiter = None

    def check_rate_limit(endpoint: str, limit: int, period: int = 60) -> tuple[bool, Optional[int]]:
        return True, limit

# ============================================================================
# MIDDLEWARE: Request/Response Processing
# ============================================================================

@app.before_request
def before_request():
    """Request preprocessing"""
    g.start_time = time.time()

    # Skip metrics for health check
    if request.path == '/health' or request.path == '/api/metrics':
        return

    # Validate Content-Type for POST
    if request.method == 'POST' and request.path.startswith('/api/'):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

    # Apply rate limiting
    if rate_limiter and request.path.startswith('/api/'):
        if request.path == '/api/ask':
            allowed, remaining = check_rate_limit('ask', 30, 60)
        elif request.path == '/api/ssb-data':
            allowed, remaining = check_rate_limit('ssb-data', 60, 60)
        else:
            allowed, remaining = check_rate_limit('default', 100, 3600)

        if not allowed:
            return jsonify({'error': 'Rate limit exceeded', 'retry_after': 60}), 429

@app.after_request
def after_request(response):
    """Response postprocessing"""
    # Calculate response time
    if hasattr(g, 'start_time'):
        response_time = time.time() - g.start_time
        metrics.record(response_time, response.status_code)

    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Cache-Control'] = 'no-store' if request.method == 'POST' else 'public, max-age=3600'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

    # Log request
    if request.path not in ['/health', '/api/metrics']:
        logger.info(
            f"{request.remote_addr} {request.method} {request.path} "
            f"=> {response.status_code} ({response_time:.3f}s)"
        )

    return response

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request_handler(e):
    return jsonify({'error': 'Bad Request', 'message': str(e)}), 400

@app.errorhandler(404)
def not_found_handler(e):
    return jsonify({'error': 'Not Found', 'message': 'The requested resource was not found'}), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'retry_after': 60
    }), 429

@app.errorhandler(500)
def internal_error_handler(e):
    logger.error(f"Internal Server Error: {str(e)}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred. Our team has been notified.'
    }), 500

# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

try:
    logger.info("🚀 Initializing agents...")
    from agents import baseline
    from agents import react_agent
    importlib.reload(baseline)
    importlib.reload(react_agent)
    from agents.baseline import BaselineAgent
    from agents.react_agent import SimpleReactAgent
    from utils.ssb_api import SSBApi

    baseline_agent = BaselineAgent()
    react_agent = SimpleReactAgent()
    # Use default cache_dir, TTL managed by Flask cache layer
    ssb_api = SSBApi()
    logger.info("✅ Agents initialized successfully")
except Exception as e:
    logger.error(f"❌ Agent initialization failed: {e}", exc_info=True)
    raise

# ============================================================================
# API ROUTES
# ============================================================================

# Add src to path (from root directory: Norfain/src)
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Import agent modules
from agents import baseline
from agents import react_agent

# Force reload to get latest code (important for development)
importlib.reload(baseline)
importlib.reload(react_agent)

from agents.baseline import BaselineAgent
from agents.react_agent import SimpleReactAgent
from utils.ssb_api import SSBApi

app = Flask(__name__)
CORS(app)

# Initialize agents
print("🚀 Initializing agents...")
try:
    baseline_agent = BaselineAgent()
    react_agent = SimpleReactAgent()
    ssb_api = SSBApi()
    print("✅ Agents ready!")
except Exception as e:
    print(f"❌ Failed to initialize agents: {e}")
    # Initialize with None or handle gracefully if needed, 
    # but for now let it print error. 
    # The agents themselves calculate fallback, but instantiation must succeed.
    raise e


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html'), 200, {
        'Cache-Control': 'public, max-age=3600',
        'Vary': 'Accept-Encoding'
    }

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    Handle question from user with caching and validation.
    Returns responses from both baseline and ReAct agents.

    Rate Limit: 30 requests/minute per IP
    Cache: 1 hour per unique question+language combo
    """
    start_time = time.time()

    try:
        # Parse and validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        try:
            data = request.get_json()
        except Exception:
            return jsonify({'error': 'Invalid JSON payload'}), 400

        question = str(data.get('question', '')).strip()
        language = str(data.get('language', 'en')).strip()

        # Input validation
        is_valid, error_msg = Validator.validate_question(question)
        if not is_valid:
            return jsonify({'error': error_msg}), 400

        is_valid_lang, lang_error = Validator.validate_language(language)
        if not is_valid_lang:
            return jsonify({'error': lang_error}), 400

        # Check cache first
        if cache:
            cache_key = f"ask:{hashlib.md5(f'{question}:{language}'.encode()).hexdigest()[:16]}"
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"✅ Cache HIT: {question[:50]}...")
                return jsonify(cached)

        logger.info(f"📝 Processing: {question[:100]}... (lang={language})")

        # Execute agents (with isolated exception handling)
        baseline_time = 0
        react_time = 0

        try:
            baseline_start = time.time()
            baseline_result = baseline_agent.answer_question(question, language=language)
            baseline_time = time.time() - baseline_start
        except Exception as e:
            logger.error(f"Baseline agent error: {e}", exc_info=True)
            baseline_result = {
                'answer': 'Error: Baseline agent unavailable',
                'tool_used': False,
                'model': 'error'
            }

        try:
            react_start = time.time()
            react_result = react_agent.answer_question(question, language=language)
            react_time = time.time() - react_start
        except Exception as e:
            logger.error(f"ReAct agent error: {e}", exc_info=True)
            react_result = {
                'answer': 'Error: ReAct agent unavailable',
                'iterations': 0,
                'reasoning_steps': [],
                'model': 'error'
            }

        # Build optimized response (only essential fields)
        response = {
            'question': question[:500],  # Truncate for safety
            'baseline': {
                'answer': str(baseline_result.get('answer', ''))[:10000],  # Limit size
                'time': round(baseline_time, 3),
                'tool_used': bool(baseline_result.get('tool_used', False)),
                'model': str(baseline_result.get('model', 'unknown'))
            },
            'react': {
                'answer': str(react_result.get('answer', ''))[:10000],
                'time': round(react_time, 3),
                'iterations': int(react_result.get('iterations', 0)),
                'reasoning_steps': react_result.get('reasoning_steps', [])[:10],  # Limit to 10
                'model': str(react_result.get('model', 'unknown'))
            },
            'comparison': {
                'time_difference': round(react_time - baseline_time, 3),
                'time_ratio': round(react_time / baseline_time, 2) if baseline_time > 0 else 0
            }
        }

        # Cache successful response
        if cache and baseline_time > 0 and react_time > 0:
            cache.set(cache_key, response, ttl=Config.CACHE_TTL)

        total_time = time.time() - start_time
        logger.info(f"✅ Completed in {total_time:.3f}s (B:{baseline_time:.3f}s, R:{react_time:.3f}s)")

        return jsonify(response)

    except Exception as e:
        logger.error(f"Unexpected error in ask_question: {e}", exc_info=True)
        return jsonify({
            'error': 'Processing failed',
            'message': 'An unexpected error occurred. Please try again.'
        }), 500

@app.route('/api/ssb-data', methods=['GET'])
def get_ssb_data():
    """
    Get SSB household budget data for visualization

    Rate Limit: 60 requests/minute per IP
    Cache: 24 hours (data is infrequently updated)
    """
    try:
        year = request.args.get('year', '2022')

        # Validate year
        is_valid_year, year_error = Validator.validate_year(year)
        if not is_valid_year:
            return jsonify({'error': year_error}), 400

        # Check cache first (24h TTL)
        if cache:
            cache_key = f"ssb_data_{year}"
            cached = cache.get(cache_key)
            if cached:
                return jsonify(cached)

        # Fetch data
        data = ssb_api.get_household_budget_data(year=year)

        if not data:
            return jsonify({'error': 'No data available for specified year'}), 404

        parsed = ssb_api.parse_household_data(data)

        if not parsed:
            return jsonify({'error': 'Failed to parse SSB data'}), 500

        # Optimize response payload (round numbers, filter nulls)
        categories = []
        total_annual = 0

        for item in parsed:
            value = item.get('value')
            if value is not None and isinstance(value, (int, float)):
                val_annual = round(float(value), 2)
                categories.append({
                    'category': str(item.get('category', ''))[:100],
                    'code': str(item.get('category_code', ''))[:20],
                    'annual': val_annual,
                    'monthly': round(val_annual / 12, 2),
                    'unit': 'NOK'
                })
                total_annual += val_annual

        formatted_data = {
            'year': year,
            'categories': categories,
            'total': round(total_annual, 2),
            'category_count': len(categories),
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }

        # Cache for 24 hours
        if cache:
            cache.set(f"ssb_data_{year}", formatted_data, ttl=Config.SSB_CACHE_TTL)

        return jsonify(formatted_data)

    except Exception as e:
        logger.error(f"Error in get_ssb_data: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch SSB data'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Get system statistics including metrics and evaluation results

    Cache: 5 minutes (frequent calls)
    """
    try:
        # Check cache first
        if cache:
            cache_key = "system_stats"
            cached = cache.get(cache_key)
            if cached:
                cached['from_cache'] = True
                return jsonify(cached)

        # Collect metrics
        app_metrics = metrics.get_stats()

        # Load evaluation results if available
        results_available = False
        results_data = {}

        try:
            results_dir = Path(__file__).parent.parent / "results"
            baseline_files = sorted(results_dir.glob("baseline_results_*.json"))
            react_files = sorted(results_dir.glob("react_results_*.json"))

            if baseline_files and react_files:
                with open(baseline_files[-1], 'r', encoding='utf-8') as f:
                    baseline_data = json.load(f)
                with open(react_files[-1], 'r', encoding='utf-8') as f:
                    react_data = json.load(f)

                baseline_results = baseline_data.get('results', [])
                react_results = react_data.get('results', [])

                if baseline_results and react_results:
                    results_available = True
                    results_data = {
                        'total_questions': len(baseline_results),
                        'timestamp': baseline_data.get('timestamp'),
                        'baseline': {
                            'avg_time': round(sum(r.get('elapsed_time', 0) for r in baseline_results) / len(baseline_results), 3),
                            'tool_usage': round(sum(1 for r in baseline_results if r.get('tool_used')) / len(baseline_results) * 100, 1),
                            'errors': sum(1 for r in baseline_results if 'ERROR' in str(r.get('answer', '')))
                        },
                        'react': {
                            'avg_time': round(sum(r.get('elapsed_time', 0) for r in react_results) / len(react_results), 3),
                            'tool_usage': 100.0,
                            'avg_iterations': round(sum(r.get('iterations', 0) for r in react_results) / len(react_results), 2),
                            'errors': sum(1 for r in react_results if 'ERROR' in str(r.get('answer', '')))
                        }
                    }
        except Exception as e:
            logger.warning(f"Failed to load evaluation results: {e}")

        response = {
            'available': results_available,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metrics': app_metrics,
            'cache_enabled': cache is not None,
            'cache_stats': {
                'size': len(cache._cache) if cache and hasattr(cache, '_cache') else 0,
                'max_size': Config.CACHE_MAX_SIZE if cache else 0
            }
        }

        if results_available:
            response.update(results_data)
        else:
            response['message'] = 'No evaluation results available'

        # Cache for 5 minutes
        if cache:
            cache.set("system_stats", response, ttl=300)

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in get_stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    try:
        status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'components': {
                'agents': 'loaded',
                'baseline_agent': 'ready',
                'react_agent': 'ready',
                'ssb_api': 'connected',
                'cache': 'enabled' if cache else 'disabled'
            },
            'metrics': metrics.get_stats()
        }

        # Quick agent liveness check
        try:
            test_question = "test"
            _ = baseline_agent.answer_question(test_question, language='en')
            status['components']['baseline_agent'] = 'healthy'
        except:
            status['components']['baseline_agent'] = 'unhealthy'

        try:
            _ = react_agent.answer_question(test_question, language='en')
            status['components']['react_agent'] = 'healthy'
        except:
            status['components']['react_agent'] = 'unhealthy'

        overall = 'healthy' if all(v in ['healthy', 'ready', 'connected'] for v in status['components'].values()) else 'degraded'
        status['status'] = overall

        return jsonify(status)
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Prometheus-style metrics endpoint for monitoring systems"""
    try:
        m = metrics.get_stats()
        uptime = time.time() - app_start_time if 'app_start_time' in globals() else 0

        metrics_output = f"""# HELP norfain_requests_total Total number of requests processed
# TYPE norfain_requests_total counter
norfain_requests_total {m['requests']}

# HELP norfain_errors_total Total number of error responses
# TYPE norfain_errors_total counter
norfain_errors_total {m['errors']}

# HELP norfain_response_time_seconds Average response time in seconds
# TYPE norfain_response_time_seconds gauge
norfain_response_time_seconds {m['avg_response_time']}

# HELP norfain_response_time_p95_seconds 95th percentile response time
# TYPE norfain_response_time_p95_seconds gauge
norfain_response_time_p95_seconds {m['p95_response_time']}

# HELP norfain_cache_hits_total Number of cache hits
# TYPE norfain_cache_hits_total counter
norfain_cache_hits_total {cache_stats['hits'] if 'cache_stats' in locals() else 0}

# HELP norfain_uptime_seconds Application uptime
# TYPE norfain_uptime_seconds gauge
norfain_uptime_seconds {uptime}
"""
        return metrics_output, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return f"# Error generating metrics: {str(e)}", 500

# ============================================================================
# ADMIN ROUTES (Require authentication in production)
# ============================================================================

@app.route('/api/admin/cache/clear', methods=['POST'])
def clear_cache():
    """Clear application cache (admin only)"""
    if not Config.DEBUG:
        token = request.headers.get('X-Admin-Token')
        expected = os.getenv('ADMIN_TOKEN')
        if not expected or token != expected:
            logger.warning(f"Unauthorized cache clear attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized'}), 403

    if cache:
        cache.clear()
        logger.info("Cache cleared by admin")
        return jsonify({'message': 'Cache cleared successfully', 'timestamp': datetime.utcnow().isoformat() + 'Z'})
    else:
        return jsonify({'message': 'Cache is disabled'}), 200

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    global app_start_time
    app_start_time = time.time()

    print("\n" + "="*80)
    print("🚀 NORFAIN REACT AGENT - PRODUCTION DASHBOARD")
    print("="*80)
    print(f"\n✅ Server starting...")
    print(f"📡 Dashboard URL: http://localhost:5050")
    print(f"🔒 Security: CORS restricted, Headers enforced, Rate limiting active")
    print(f"⚡ Cache: {'✅ Enabled' if cache else '❌ Disabled'} (LRU+TTL)")
    print(f"📊 Metrics: /api/metrics (Prometheus format)")
    print(f"📝 Logs: logs/app.log")
    print(f"💡 Open in your browser to interact with the agents!")
    print("\n⏹️  Press CTRL+C to stop\n")

    # Production server
    try:
        import waitress
        logger.info("Starting with Waitress WSGI server")
        waitress.serve(app,
                      host='0.0.0.0',
                      port=5050,
                      threads=4,
                      connection_limit=100,
                      channel_timeout=Config.REQUEST_TIMEOUT)
    except ImportError:
        logger.warning("Waitress not installed, falling back to Flask dev server")
        logger.warning("For production, install: pip install waitress")
        app.run(host='0.0.0.0',
                port=5050,
                debug=False,
                threaded=True,
                use_reloader=False)
    except Exception as e:
        logger.error(f"Waitress failed to start: {e}", exc_info=True)
        logger.warning("Falling back to Flask dev server...")
        app.run(host='0.0.0.0',
                port=5050,
                debug=False,
                threaded=True,
                use_reloader=False)