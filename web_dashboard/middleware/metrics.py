"""
Metrics Collection Middleware
Tracks request counts, response times, and error rates
"""

import time
import threading
from flask import g, request, current_app
from typing import Dict, Any


class MetricsCollector:
    """Thread-safe metrics collector"""

    def __init__(self):
        self._lock = threading.Lock()
        self._requests = 0
        self._errors = 0
        self._response_times = []
        self._cache_hits = 0
        self._cache_misses = 0

    def record_request(self, response_time: float, status_code: int):
        with self._lock:
            self._requests += 1
            if status_code >= 400:
                self._errors += 1
            self._response_times.append(response_time)
            # Keep last 10000 samples
            if len(self._response_times) > 10000:
                self._response_times = self._response_times[-5000:]

    def record_cache_hit(self):
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self):
        with self._lock:
            self._cache_misses += 1

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            if not self._response_times:
                return {
                    'requests': 0,
                    'errors': 0,
                    'error_rate': 0,
                    'avg_response_time': 0,
                    'p95_response_time': 0,
                    'p99_response_time': 0,
                    'cache_hits': self._cache_hits,
                    'cache_misses': self._cache_misses,
                    'cache_hit_rate': 0,
                    'samples': 0
                }

            sorted_times = sorted(self._response_times)
            n = len(sorted_times)
            p95_index = int(n * 0.95)
            p99_index = int(n * 0.99)

            total_cache = self._cache_hits + self._cache_misses
            cache_hit_rate = self._cache_hits / total_cache if total_cache > 0 else 0

            return {
                'requests': self._requests,
                'errors': self._errors,
                'error_rate': self._errors / self._requests if self._requests > 0 else 0,
                'avg_response_time': round(sum(sorted_times) / n, 4),
                'min_response_time': round(sorted_times[0], 4),
                'max_response_time': round(sorted_times[-1], 4),
                'p50_response_time': round(sorted_times[n // 2], 4),
                'p95_response_time': round(sorted_times[min(p95_index, n - 1)], 4),
                'p99_response_time': round(sorted_times[min(p99_index, n - 1)], 4),
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'cache_hit_rate': round(cache_hit_rate, 4),
                'samples': n
            }


# Global metrics instance
metrics = MetricsCollector()


def register_metrics_middleware(app):
    """Register metrics collection middleware"""

    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.metrics_request_start = time.time()

    @app.after_request
    def after_request(response):
        # Skip metrics for health/metrics endpoints
        if request.path in ['/health', '/api/metrics']:
            return response

        # Calculate response time
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            metrics.record_request(response_time, response.status_code)

            # Log slow requests
            if response_time > 5.0:
                current_app.logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {response_time:.2f}s (status={response.status_code})"
                )

        return response
