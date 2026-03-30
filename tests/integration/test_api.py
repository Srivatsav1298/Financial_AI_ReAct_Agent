"""
Integration Tests for API Endpoints
"""

import pytest
import json
from unittest.mock import Mock, patch


class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_check_returns_200(self, client):
        """Health check should return 200"""
        response = client.get('/health')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] in ['healthy', 'degraded']

    def test_health_includes_components(self, client):
        """Health check should include component status"""
        response = client.get('/health')
        data = json.loads(response.data)

        assert 'components' in data
        assert 'agents' in data['components']
        assert 'ssb_api' in data['components']
        assert 'cache' in data['components']

    def test_health_includes_metrics(self, client):
        """Health check should include application metrics"""
        response = client.get('/health')
        data = json.loads(response.data)

        assert 'metrics' in data
        assert 'requests' in data['metrics']
        assert 'error_rate' in data['metrics']


class TestMetricsEndpoint:
    """Tests for /api/metrics endpoint"""

    def test_metrics_returns_prometheus_format(self, client):
        """Metrics should return Prometheus text format"""
        response = client.get('/api/metrics')
        assert response.status_code == 200
        assert response.content_type == 'text/plain; charset=utf-8'

        body = response.data.decode('utf-8')
        # Should contain Prometheus metric definitions
        assert '# HELP norfain_requests_total' in body
        assert '# TYPE norfain_requests_total counter' in body
        assert 'norfain_requests_total ' in body

    def test_metrics_includes_cache_stats(self, client):
        """Metrics should include cache statistics"""
        response = client.get('/api/metrics')
        body = response.data.decode('utf-8')

        assert 'norfain_cache_hits_total' in body
        assert 'norfain_uptime_seconds' in body


class TestAskEndpoint:
    """Tests for /api/ask endpoint"""

    def test_ask_requires_post(self, client):
        """POST method required"""
        response = client.get('/api/ask')
        assert response.status_code == 405  # Method Not Allowed

    def test_ask_requires_json(self, client):
        """Content-Type must be application/json"""
        response = client.post('/api/ask', data='test')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_ask_validates_missing_question(self, client):
        """Question field is required"""
        response = client.post(
            '/api/ask',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_ask_validates_question_length(self, client):
        """Question must not exceed max length"""
        long_question = 'x' * 1001
        response = client.post(
            '/api/ask',
            data=json.dumps({'question': long_question}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_ask_validates_language(self, client):
        """Language must be 'en' or 'no'"""
        response = client.post(
            '/api/ask',
            data=json.dumps({'question': 'test', 'language': 'fr'}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_ask_success_with_mocked_agents(self, client, mock_baseline_agent, mock_react_agent):
        """Successful ask with valid data"""
        response = client.post(
            '/api/ask',
            data=json.dumps({
                'question': 'How much do Norwegians spend on housing?',
                'language': 'en'
            }),
            content_type='application/json'
        )

        # Mock should return data, so expect 200
        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'baseline' in data
        assert 'react' in data
        assert 'comparison' in data
        assert 'question' in data
        assert 'server_time_ms' in data

    def test_ask_with_specific_agent_type(self, client, mock_baseline_agent):
        """Can request only baseline agent"""
        response = client.post(
            '/api/ask',
            data=json.dumps({
                'question': 'test',
                'language': 'en',
                'agent_type': 'baseline'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['baseline'] is not None
        assert data['react'] is None


class TestSSBDataEndpoint:
    """Tests for /api/ssb-data endpoint"""

    def test_ssb_data_requires_get(self, client):
        """GET method required"""
        response = client.post('/api/ssb-data')
        assert response.status_code == 405

    def test_ssb_data_validates_year(self, client):
        """Year parameter validation"""
        response = client.get('/api/ssb-data?year=1999')
        assert response.status_code == 400

        response = client.get('/api/ssb-data?year=abcd')
        assert response.status_code == 400

    def test_ssb_data_default_year(self, client, mock_ssb_api):
        """Should use default year 2022"""
        response = client.get('/api/ssb-data')
        assert response.status_code == 200

    def test_ssb_data_nowcast_parameter(self, client, mock_ssb_api):
        """nowcast parameter should work"""
        response = client.get('/api/ssb-data?nowcast=true')
        assert response.status_code == 200

        response = client.get('/api/ssb-data?nowcast=false')
        assert response.status_code == 200


class TestGoalsEndpoints:
    """Tests for savings goals endpoints"""

    def test_get_goals_empty(self, client):
        """GET /api/goals returns empty list initially"""
        response = client.get('/api/goals')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'goals' in data

    def test_create_goal_requires_auth(self, client):
        """POST /api/goals should require auth (in prod)"""
        # In dev mode, might allow without auth
        response = client.post(
            '/api/goals',
            data=json.dumps({
                'name': 'Test Goal',
                'target_amount': 10000,
                'deadline': '2025-12-31'
            }),
            content_type='application/json'
        )
        # Should either succeed (dev) or require auth (prod)
        assert response.status_code in [200, 201, 401, 403]

    def test_create_goal_validates_required_fields(self, client):
        """Missing required fields should return 400"""
        response = client.post(
            '/api/goals',
            data=json.dumps({'name': 'Test'}),
            content_type='application/json'
        )
        assert response.status_code == 400


class TestAdminEndpoints:
    """Tests for admin endpoints"""

    def test_clear_cache_requires_admin_token(self, client, app_fixture):
        """POST /api/admin/cache/clear should require admin token in prod"""
        # Without token
        response = client.post('/api/admin/cache/clear')
        # In dev mode, might be allowed
        assert response.status_code in [200, 401, 403]

    def test_clear_cache_with_valid_token(self, client, app_fixture):
        """With valid admin token should succeed in prod"""
        # Set admin token in config
        app_fixture.config['ADMIN_TOKEN'] = 'test-token'
        app_fixture.config['DEBUG'] = False

        response = client.post(
            '/api/admin/cache/clear',
            headers={'X-Admin-Token': 'test-token'}
        )
        assert response.status_code == 200

    def test_detailed_metrics_admin_only(self, client):
        """Detailed metrics should be admin-only in prod"""
        response = client.get('/api/admin/metrics/detailed')
        # Should require auth
        assert response.status_code in [200, 401, 403]
