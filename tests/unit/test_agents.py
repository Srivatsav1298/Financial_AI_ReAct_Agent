"""
Unit Tests for AI Agents
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agents.baseline import BaselineAgent
from src.agents.react_agent import SimpleReactAgent


class TestBaselineAgent:
    """Tests for Baseline Agent"""

    def test_init_without_ollama(self):
        """Test initialization when Ollama is not available"""
        with patch('langchain_ollama.ChatOllama', side_effect=ImportError):
            agent = BaselineAgent(model_name="llama3.2")
            assert agent.llm is None

    def test_answer_question_fallback(self):
        """Test answer_question with no LLM (fallback mode)"""
        agent = BaselineAgent()
        agent.llm = None

        result = agent.answer_question("test question", "en")

        assert 'answer' in result
        # Should return fallback message
        assert 'Ollama' in result['answer'] or 'local AI' in result['answer']

    def test_model_name_setting(self):
        """Test that model name is set correctly"""
        agent = BaselineAgent(model_name="custom-model")
        assert agent.model_name == "custom-model"


class TestReactAgent:
    """Tests for ReAct Agent"""

    def test_init_without_ollama(self):
        """Test initialization when Ollama is not available"""
        with patch('langchain_ollama.ChatOllama', side_effect=ImportError):
            agent = SimpleReactAgent(model_name="llama3.2")
            assert agent.llm is None

    def test_tools_initialization(self):
        """Test that tools dictionary is initialized"""
        agent = SimpleReactAgent()
        assert hasattr(agent, 'tools')
        assert isinstance(agent.tools, dict)
        expected_tools = [
            'get_spending',
            'compare_spending',
            'get_total_spending',
            'analyze_budget_health',
            'optimize_budget',
            'assess_lifestyle',
            'detect_anomalies',
            'calculate_savings',
            'evaluate_purchase',
            'simulate_wealth',
            'generate_persona'
        ]
        for tool in expected_tools:
            assert tool in agent.tools
