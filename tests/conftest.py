"""
Pytest Configuration and Fixtures
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "web_dashboard"))


@pytest.fixture
def mock_ssb_api():
    """Mock SSB API for testing"""
    with patch('utils.ssb_api.SSBApi') as mock:
        instance = Mock()
        instance.get_household_budget_data.return_value = {
            'value': [1000, 2000, 3000],
            'dimension': {
                'VareTjenesteGruppe': {
                    'category': {
                        'label': {'01': 'Food', '04': 'Housing'},
                        'index': {'01': 0, '04': 1}
                    }
                },
                'Tid': {
                    'category': {
                        'label': {'2022': '2022'},
                        'index': {'2022': 0}
                    }
                }
            }
        }
        instance.parse_household_data.return_value = [
            {'category': 'Food', 'value': 1000, 'unit': 'NOK'},
            {'category': 'Housing', 'value': 2000, 'unit': 'NOK'}
        ]
        instance.get_cpi_adjustments.return_value = {'01': 1.15, '04': 1.12, 'TOTAL': 1.13}
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_baseline_agent():
    """Mock Baseline Agent for testing"""
    with patch('agents.baseline.BaselineAgent') as mock:
        instance = Mock()
        instance.answer_question.return_value = {
            'answer': 'Test baseline response',
            'model': 'baseline (llama3.2)',
            'time': 1.5,
            'tool_used': False
        }
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_react_agent():
    """Mock ReAct Agent for testing"""
    with patch('agents.react_agent.SimpleReactAgent') as mock:
        instance = Mock()
        instance.answer_question.return_value = {
            'answer': 'Test react response with reasoning',
            'model': 'react (llama3.2)',
            'time': 3.0,
            'reasoning_steps': [
                {'thought': 'I need to analyze this...', 'action': 'get_data', 'observation': 'Data retrieved'}
            ],
            'iterations': 1
        }
        mock.return_value = instance
        yield instance


@pytest.fixture
def app_fixture(mock_baseline_agent, mock_react_agent, mock_ssb_api):
    """Create Flask app for testing"""
    from app import create_app

    app = create_app()
    app.config['TESTING'] = True
    app.config['CACHE_ENABLED'] = False
    app.config['RATELIMIT_ENABLED'] = False
    app.config['DEBUG'] = False

    # Ensure cache is a simple null cache for testing
    from flask_caching import Cache
    test_cache = Cache()
    test_cache.init_app(app, {'CACHE_TYPE': 'null'})
    app.extensions['cache'] = test_cache

    with app.app_context():
        yield app


@pytest.fixture
def client(app_fixture):
    """Flask test client"""
    return app_fixture.test_client()


@pytest.fixture
def runner(app_fixture):
    """Flask test CLI runner"""
    return app_fixture.test_cli_runner()
