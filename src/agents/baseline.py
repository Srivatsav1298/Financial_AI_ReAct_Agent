"""
Baseline Financial Assistant - Simple prompting without explicit reasoning (Local Ollama version)
"""

import os
from dotenv import load_dotenv
import sys
from pathlib import Path
from typing import Dict, Any

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
        self.model_name = model_name
        self.llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Try to initialize LLM, setup fallback if it fails"""
        try:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(
                model=self.model_name,
                temperature=0
            )
            # Test connection lightly? No, lazy load is better usually, 
            # but we want to know if we should fallback.
            # We'll handle runtime errors during invoke instead.
        except ImportError:
            print("⚠️ langchain_ollama not found. Running in Fallback Mode.")
            self.llm = None
        except Exception as e:
            print(f"⚠️ Error initializing Ollama: {e}. Running in Fallback Mode.")
            self.llm = None

    def answer_question(self, question: str, language: str = 'en') -> Dict[str, Any]:
        """Answer a financial question using local LLM"""
        
        # 1. Check if LLM is available
        if not self.llm:
            return self._fallback_response(question, language)

        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser

            # Language-specific system prompt
            if language == 'no':
                system_prompt = """Du er en hjelpsom norsk finansiell assistent.
Du har tilgang til Statistics Norway (SSB) husholdningsbudsjettdata.

Når du svarer på spørsmål om norsk husholdningsforbruk:
1. Identifiser forbrukskategorien som spørres om
2. Oppgi gjennomsnittlig forbruk fra SSB-data (hvis tilgjengelig)
3. Gi et klart, faktabasert og konsist svar
4. Hvis data mangler, si det tydelig.

Referer alltid til Statistics Norway (SSB) som kilde når du gir tall."""
            else:
                system_prompt = """You are a helpful Norwegian financial assistant.
You have access to Statistics Norway (SSB) household budget data.

When answering questions about Norwegian household spending:
1. Identify the spending category being asked about
2. Provide average spending amount from SSB data (if available)
3. Give a clear, factual, and concise answer
4. If data is missing, say so clearly.

Always cite Statistics Norway (SSB) as your source when giving numbers."""
            
            # Create language-specific prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            
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
                if language == 'no':
                    enhanced_question = f"""Spørsmål: {question}

Relevant data fra Statistics Norway: {tool_result}

Vennligst svar på spørsmålet ved å bruke disse dataene og referer til SSB som kilde."""
                else:
                    enhanced_question = f"""Question: {question}

Relevant data from Statistics Norway: {tool_result}

Please answer the question using this data and cite SSB as the source."""

            # Run model
            try:
                answer = chain.invoke({"question": enhanced_question})
            except Exception as e:
                # Catch specific connection errors to Ollama
                print(f"❌ Ollama connection failed: {e}")
                return self._fallback_response(question, language, error=str(e))

            return {
                "question": question,
                "answer": answer,
                "tool_used": bool(found_category),
                "tool_result": tool_result or None,
                "reasoning_steps": [],
                "model": f"baseline ({self.model_name})"
            }
            
        except Exception as e:
            print(f"❌ Critical error in Baseline Agent: {e}")
            return self._fallback_response(question, language, error=str(e))

    def _fallback_response(self, question: str, language: str, error: str = None) -> Dict[str, Any]:
        """Provide a canned response when LLM/Ollama is down"""
        
        print("⚠️ USING FALLBACK RESPONSE")
        
        categories = [
            "housing", "food", "transport", "entertainment",
            "clothing", "health", "communication", "restaurants"
        ]
        question_lower = question.lower()
        found_category = next((cat for cat in categories if cat in question_lower), None)
        
        tool_result = ""
        if found_category:
            try:
                tool_result = get_average_spending_by_category.invoke({"category": found_category})
            except:
                tool_result = "Data lookup failed."

        # Canned responses
        if language == 'no':
            msg = "Beklager, men den lokale AI-modellen (Ollama) kjører ikke eller svarer ikke."
            if tool_result and "NOK" in str(tool_result):
                 msg += f"\n\nMen jeg fant disse dataene fra SSB: {tool_result}"
            else:
                 msg += "\n\nVennligst sjekk at Ollama kjører lokalt."
        else:
            msg = "Sorry, the local AI model (Ollama) is not running or not responding."
            if tool_result and "NOK" in str(tool_result):
                 msg += f"\n\nHowever, I found this data from SSB: {tool_result}"
            else:
                 msg += "\n\nPlease ensure Ollama is running locally."

        if error:
            msg += f"\n\n(Technical Error: {error})"

        return {
            "question": question,
            "answer": msg,
            "tool_used": bool(found_category),
            "tool_result": tool_result,
            "model": "Fallback (No LLM)"
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
        if result.get('tool_result'):
            print(f"📊 Tool result: {str(result['tool_result'])[:120]}...")
        print("\n" + "="*80 + "\n")

    print("✅ Baseline tests complete!")


if __name__ == "__main__":
    test_baseline()
