"""
Baseline Financial Assistant - Simple prompting without explicit reasoning (Local Ollama version)
"""

import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any
import sys
from pathlib import Path

# Load environment variables (optional)
load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from tools.ssb_tools import get_average_spending_by_category


class BaselineAgent:
    """
    Simple baseline agent that uses direct prompting.
    Runs locally with Ollama (no API key needed).
    """

    def __init__(self, model_name: str = "llama3.2"):
        """Initialize local Llama model via Ollama"""
        self.llm = ChatOllama(
            model=model_name,
            temperature=0
        )

        # Prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful Norwegian financial assistant.
You have access to Statistics Norway (SSB) household budget data.

When answering questions about Norwegian household spending:
1. Identify the spending category being asked about
2. Provide average spending amount from SSB data (if available)
3. Give a clear, factual, and concise answer
4. If data is missing, say so clearly.

Always cite Statistics Norway (SSB) as your source when giving numbers."""),
            ("user", "{question}")
        ])

        # Combine prompt + model + parser
        self.chain = self.prompt | self.llm | StrOutputParser()

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a financial question using local LLM"""
        categories = [
            "housing", "food", "transport", "entertainment",
            "clothing", "health", "communication", "restaurants"
        ]

        question_lower = question.lower()
        found_category = next((cat for cat in categories if cat in question_lower), None)

        # Try to fetch data from SSB tool
        tool_result = ""
        if found_category:
            tool_result = get_average_spending_by_category.invoke({"category": found_category})

        # Enrich question with retrieved data
        enhanced_question = question
        if tool_result:
            enhanced_question = f"""Question: {question}

Relevant data from Statistics Norway: {tool_result}

Please answer the question using this data and cite SSB as the source."""

        # Run model
        answer = self.chain.invoke({"question": enhanced_question})

        return {
            "question": question,
            "answer": answer,
            "tool_used": bool(found_category),
            "tool_result": tool_result or None,
            "reasoning_steps": [],
            "model": "baseline (Ollama Llama3.2)"
        }


def test_baseline():
    """Quick test for the baseline agent"""
    print("🧪 Testing Baseline Agent (Local Ollama)\n")

    agent = BaselineAgent()

    questions = [
        "How much do Norwegian families spend on housing?",
        "What's the average food budget in Norway?",
        "Do Norwegians spend more on housing or food?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"📝 Question {i}: {question}")
        result = agent.answer_question(question)
        print(f"💡 Answer: {result['answer']}")
        print(f"🔧 Used tool: {result['tool_used']}")
        if result['tool_result']:
            print(f"📊 Tool result: {result['tool_result'][:120]}...")
        print("\n" + "="*80 + "\n")

    print("✅ Baseline tests complete!")


if __name__ == "__main__":
    test_baseline()
