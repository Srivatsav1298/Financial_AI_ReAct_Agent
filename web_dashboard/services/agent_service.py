"""
Agent Service
Manages interactions with Baseline and ReAct agents
"""

import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from flask import current_app
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.baseline import BaselineAgent
from agents.react_agent import SimpleReactAgent


class AgentService:
    """Service layer for agent operations"""

    def __init__(self, baseline_agent: BaselineAgent, react_agent: SimpleReactAgent):
        self.baseline_agent = baseline_agent
        self.react_agent = react_agent
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix='agent_')
        self._loop = None

    def answer_sync(self, question: str, language: str = 'en',
                   persona: str = 'analyst', agent_type: str = None) -> Dict[str, Any]:
        """
        Synchronous answer from agents
        Runs both agents if no specific type requested
        """
        start_time = time.time()

        try:
            if agent_type == 'baseline':
                result = self.baseline_agent.answer_question(question, language)
                return {
                    'baseline': result,
                    'react': None,
                    'comparison': None,
                    'question': question,
                    'language': language
                }

            elif agent_type == 'react':
                result = self.react_agent.answer_question(question, language)
                return {
                    'baseline': None,
                    'react': result,
                    'comparison': None,
                    'question': question,
                    'language': language
                }

            else:
                # Run both agents
                baseline_result = self.baseline_agent.answer_question(question, language)
                react_result = self.react_agent.answer_question(question, language)

                total_time = time.time() - start_time

                return {
                    'baseline': baseline_result,
                    'react': react_result,
                    'comparison': {
                        'time_difference': react_result.get('execution_time', 0) - baseline_result.get('execution_time', 0),
                        'time_ratio': react_result.get('execution_time', 0) / baseline_result.get('execution_time', 1) if baseline_result.get('execution_time', 0) > 0 else 0,
                        'reasoning_available': bool(react_result.get('reasoning'))
                    },
                    'question': question,
                    'language': language,
                    'total_time': total_time
                }

        except Exception as e:
            current_app.logger.error(f"AgentService error: {e}", exc_info=True)
            raise

    async def answer_async(self, question: str, language: str = 'en',
                          persona: str = 'analyst') -> Dict[str, Any]:
        """
        Async answer from agents (runs both concurrently)
        """
        start_time = time.time()

        try:
            # Run both agents concurrently in thread pool
            baseline_future = self.executor.submit(
                self.baseline_agent.answer_question,
                question, language
            )
            react_future = self.executor.submit(
                self.react_agent.answer_question,
                question, language
            )

            # Wait for both with timeout
            baseline_result = baseline_future.result(timeout=120)
            react_result = react_future.result(timeout=120)

            total_time = time.time() - start_time

            return {
                'baseline': baseline_result,
                'react': react_result,
                'comparison': {
                    'time_difference': react_result.get('execution_time', 0) - baseline_result.get('execution_time', 0),
                    'time_ratio': react_result.get('execution_time', 0) / baseline_result.get('execution_time', 1) if baseline_result.get('execution_time', 0) > 0 else 0,
                    'reasoning_available': bool(react_result.get('reasoning'))
                },
                'question': question,
                'language': language,
                'total_time': total_time
            }

        except Exception as e:
            current_app.logger.error(f"AgentService async error: {e}", exc_info=True)
            raise

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about available agents"""
        return {
            'baseline': {
                'name': 'Baseline Agent',
                'description': 'Fast, direct prompting without explicit reasoning',
                'model': getattr(self.baseline_agent, 'model_name', 'unknown'),
                'typical_time': '6-8 seconds'
            },
            'react': {
                'name': 'ReAct Agent',
                'description': 'Explicit reasoning with Thought → Action → Observation loop',
                'model': getattr(self.react_agent, 'model_name', 'unknown'),
                'typical_time': '10-14 seconds'
            }
        }
