"""
Simple Manual ReAct Agent - Shows explicit reasoning (Ollama)
Implements ReAct loop manually without complex LangChain abstractions
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any, List
import sys
import re
from pathlib import Path

load_dotenv()

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from tools.ssb_tools import (
    get_average_spending_by_category,
    compare_spending_categories,
    get_total_household_spending
)
from tools.advanced_tools import (
    analyze_budget_health,
    optimize_budget_allocation,
    assess_lifestyle_affordability,
    detect_spending_anomalies,
    calculate_savings_potential,
    evaluate_major_purchase
)


class SimpleReactAgent:
    """Manual ReAct agent implementation"""
    
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.llm = None
        self._initialize_llm()
            
        self.tools = {
            "get_spending": get_average_spending_by_category,
            "compare_spending": compare_spending_categories,
            "get_total_spending": get_total_household_spending,
            "analyze_budget_health": analyze_budget_health,
            "optimize_budget": optimize_budget_allocation,
            "assess_lifestyle": assess_lifestyle_affordability,
            "detect_anomalies": detect_spending_anomalies,
            "calculate_savings": calculate_savings_potential,
            "evaluate_purchase": evaluate_major_purchase
        }
        self.max_iterations = 10  # Increased for complex reasoning

    def _initialize_llm(self):
        """Try to initialize LLM, setup fallback if it fails"""
        try:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(model=self.model_name, temperature=0)
        except ImportError:
            print("⚠️ langchain_ollama not found. ReAct running in Fallback Mode.")
            self.llm = None
        except Exception as e:
            print(f"⚠️ Error initializing Ollama for ReAct: {e}. Running in Fallback Mode.")
            self.llm = None

    def _parse_action(self, text: str) -> tuple:
        action_match = re.search(r'ACTION:\s*(\w+)\((.*?)\)', text, re.IGNORECASE)
        if action_match:
            tool_name = action_match.group(1).lower()
            args_str = action_match.group(2).strip('\'"')
            args = [arg.strip().strip('\'"') for arg in args_str.split(',')]
            return tool_name, args
        return None, None

    def _call_tool(self, tool_name: str, args: List[str]) -> str:
        tool_mapping = {
            "get_spending": "get_spending",
            "get_average_spending_by_category": "get_spending",
            "compare_spending": "compare_spending",
            "compare_spending_categories": "compare_spending",
            "get_total_spending": "get_total_spending",
            "get_total_household_spending": "get_total_spending",
            "analyze_budget_health": "analyze_budget_health",
            "optimize_budget": "optimize_budget",
            "optimize_budget_allocation": "optimize_budget",
            "assess_lifestyle": "assess_lifestyle",
            "assess_lifestyle_affordability": "assess_lifestyle",
            "detect_anomalies": "detect_anomalies",
            "detect_spending_anomalies": "detect_anomalies",
            "calculate_savings": "calculate_savings",
            "calculate_savings_potential": "calculate_savings",
            "evaluate_purchase": "evaluate_purchase",
            "evaluate_major_purchase": "evaluate_purchase"
        }
        mapped_tool = tool_mapping.get(tool_name)
        if not mapped_tool or mapped_tool not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"
        tool = self.tools[mapped_tool]
        try:
            # Basic SSB tools
            if mapped_tool == "get_spending":
                result = tool.invoke({"category": args[0], "year": "2012"})
            elif mapped_tool == "compare_spending":
                result = tool.invoke({
                    "category1": args[0],
                    "category2": args[1] if len(args) > 1 else "food",
                    "year": "2012"
                })
            elif mapped_tool == "get_total_spending":
                result = tool.invoke({"year": "2012"})
            
            # Advanced analysis tools
            elif mapped_tool == "analyze_budget_health":
                result = tool.invoke({
                    "monthly_income": float(args[0]),
                    "housing": float(args[1]),
                    "food": float(args[2]),
                    "transport": float(args[3]),
                    "entertainment": float(args[4]),
                    "other": float(args[5]) if len(args) > 5 else 0
                })
            elif mapped_tool == "optimize_budget":
                result = tool.invoke({
                    "monthly_income": float(args[0]),
                    "savings_goal": float(args[1]),
                    "current_housing": float(args[2]),
                    "current_food": float(args[3]),
                    "current_transport": float(args[4]),
                    "current_entertainment": float(args[5]) if len(args) > 5 else 0
                })
            elif mapped_tool == "assess_lifestyle":
                result = tool.invoke({
                    "monthly_income": float(args[0]),
                    "desired_housing": float(args[1]),
                    "desired_food": float(args[2]),
                    "desired_transport": float(args[3]),
                    "desired_entertainment": float(args[4]),
                    "desired_savings_rate": float(args[5]) if len(args) > 5 else 20
                })
            elif mapped_tool == "detect_anomalies":
                result = tool.invoke({
                    "housing": float(args[0]),
                    "food": float(args[1]),
                    "transport": float(args[2]),
                    "entertainment": float(args[3]),
                    "monthly_income": float(args[4])
                })
            elif mapped_tool == "calculate_savings":
                result = tool.invoke({
                    "monthly_income": float(args[0]),
                    "current_housing": float(args[1]),
                    "current_food": float(args[2]),
                    "current_transport": float(args[3]),
                    "current_entertainment": float(args[4]),
                    "current_other": float(args[5]) if len(args) > 5 else 0
                })
            elif mapped_tool == "evaluate_purchase":
                result = tool.invoke({
                    "purchase_price": float(args[0]),
                    "monthly_income": float(args[1]),
                    "current_savings": float(args[2]),
                    "monthly_expenses": float(args[3]),
                    "purchase_type": args[4] if len(args) > 4 else "general"
                })
            else:
                result = tool.invoke({})
            
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Error calling tool: {str(e)}"

    def answer_question(self, question: str, language: str = 'en') -> Dict[str, Any]:
        print(f"\n{'='*80}")
        print(f"🤔 REACT AGENT REASONING...")
        print(f"{'='*80}\n")
        
        # 1. Check fallback
        if not self.llm:
            return self._fallback_response(question, language)

        conversation_history = []
        reasoning_steps = []
        
        # Language-specific instructions
        if language == 'no':
            language_instruction = "\n\nIMPORTANT: Respond in NORWEGIAN (Norsk). All your thoughts, actions, and final answer must be in Norwegian."
            final_answer_label = "ENDELIG SVAR"
        else:
            language_instruction = ""
            final_answer_label = "FINAL ANSWER"
        
        system_prompt = f"""You are an expert Norwegian financial advisor using Statistics Norway data and advanced financial analysis.{language_instruction}

Answer questions using this EXACT format:

THOUGHT: [explain what you need to know and your reasoning]
ACTION: tool_name(arg1, arg2, ...)
[wait for observation]

Available tools:

BASIC DATA TOOLS:
- get_spending("category") - get spending for a category like "housing", "food", etc.
- compare_spending("category1", "category2") - compare two categories
- get_total_spending() - get total household spending

ADVANCED ANALYSIS TOOLS (use these for complex questions):
- analyze_budget_health(income, housing, food, transport, entertainment, other) - analyze financial health score
- optimize_budget(income, savings_goal, housing, food, transport, entertainment) - optimize budget to meet savings goals
- assess_lifestyle(income, desired_housing, desired_food, desired_transport, desired_entertainment, savings_rate) - check if lifestyle is affordable
- detect_anomalies(housing, food, transport, entertainment, income) - detect unusual spending patterns
- calculate_savings(income, housing, food, transport, entertainment, other) - find savings opportunities
- evaluate_purchase(price, income, current_savings, monthly_expenses, type) - evaluate major purchase affordability

For COMPLEX questions requiring personalized recommendations:
1. Use MULTIPLE tools to gather comprehensive data
2. Analyze from multiple angles (health, optimization, anomalies)
3. Provide SPECIFIC, ACTIONABLE recommendations
4. Show your multi-step reasoning clearly

After thorough analysis, provide:
{final_answer_label}: [comprehensive answer with specific recommendations and sources]

Use advanced tools for non-trivial questions. Be thorough and analytical."""

        current_question = f"Question: {question}"

        try:
            for iteration in range(self.max_iterations):
                print(f"--- Iteration {iteration + 1} ---\n")
                if iteration == 0:
                    prompt_text = f"{system_prompt}\n\n{current_question}\n\nLet's think step by step:"
                else:
                    prompt_text = f"{system_prompt}\n\n{current_question}\n\n"
                    prompt_text += "\n".join(conversation_history)
                    prompt_text += "\n\nContinue reasoning:"
                
                try:
                    response = self.llm.invoke(prompt_text)
                    llm_output = response.content if hasattr(response, 'content') else str(response)
                except Exception as e:
                    print(f"❌ Ollama connection failed during iteration {iteration}: {e}")
                    return self._fallback_response(question, language, error=str(e))
                
                print(f"🧠 LLM Output:\n{llm_output}\n")
                conversation_history.append(llm_output)

                # Check for final answer in both languages
                if "FINAL ANSWER" in llm_output.upper() or "ENDELIG SVAR" in llm_output.upper():
                    # Try both patterns
                    final_match = re.search(r'(?:FINAL ANSWER|ENDELIG SVAR):?\s*(.+)', llm_output, re.IGNORECASE | re.DOTALL)
                    if final_match:
                        final_answer = final_match.group(1).strip()
                        print(f"{'='*80}")
                        print(f"✅ REACHED FINAL ANSWER")
                        print(f"{'='*80}\n")
                        return {
                            "question": question,
                            "answer": final_answer,
                            "reasoning_steps": reasoning_steps,
                            "conversation_history": conversation_history,
                            "iterations": iteration + 1,
                            "model": "react_simple (Ollama Llama3.2)"
                        }

                tool_name, args = self._parse_action(llm_output)
                if tool_name and args:
                    print(f"🔧 Executing: {tool_name}({args})\n")
                    observation = self._call_tool(tool_name, args)
                    print(f"📊 OBSERVATION:\n{observation}\n")
                    conversation_history.append(f"OBSERVATION: {observation}")
                    reasoning_steps.append({
                        "iteration": iteration + 1,
                        "thought": llm_output,
                        "action": f"{tool_name}({args})",
                        "observation": observation
                    })
                else:
                    reasoning_steps.append({
                        "iteration": iteration + 1,
                        "thought": llm_output,
                        "action": None,
                        "observation": None
                    })

            print(f"⚠️ Max iterations reached\n")
            return {
                "question": question,
                "answer": "Could not reach final answer within iteration limit",
                "reasoning_steps": reasoning_steps,
                "conversation_history": conversation_history,
                "iterations": self.max_iterations,
                "model": "react_simple (Ollama Llama3.2)"
            }
        except Exception as e:
            print(f"❌ Critical error in ReAct Agent: {e}")
            return self._fallback_response(question, language, error=str(e))

    def _fallback_response(self, question: str, language: str, error: str = None) -> Dict[str, Any]:
        """Mock ReAct response for demo purposes"""
        print("⚠️ USING FALLBACK RESPONSE")
        
        reasoning_steps = [
            {
                "iteration": 1,
                "thought": "I need to check if the AI model is running.",
                "action": "check_connection(Ollama)",
                "observation": "Connection Failed"
            },
            {
                "iteration": 2,
                "thought": "Since the local AI is down, I should inform the user directly.",
                "action": "respond_fallback()",
                "observation": "Preparing fallback message"
            }
        ]
        
        if language == 'no':
            msg = "Jeg kan ikke koble til den lokale AI-modellen (Ollama), så jeg kan ikke utføre avansert resonnering akkurat nå."
            if error:
                msg += f"\n\nTeknisk feil: {error}"
            msg += "\n\nVennligst start Ollama lokalt for å se ReAct i aksjon."
        else:
            msg = "I cannot connect to the local AI model (Ollama), so I cannot perform advanced reasoning right now."
            if error:
                msg += f"\n\nTechnical Error: {error}"
            msg += "\n\nPlease start Ollama locally to see ReAct in action."
            
        return {
            "question": question,
            "answer": msg,
            "reasoning_steps": reasoning_steps,
            "conversation_history": [],
            "iterations": 2,
            "model": "Fallback (No LLM)"
        }


def test_simple_react():
    """Test the simple ReAct agent"""
    print("🧪 Testing Simple ReAct Agent\n")
    agent = SimpleReactAgent()
    questions = [
        "How much do Norwegian families spend on housing?",
        "Do Norwegians spend more on housing or food?",
    ]
    for i, question in enumerate(questions, 1):
        print(f"\n{'#'*80}")
        print(f"# QUESTION {i}: {question}")
        print(f"{'#'*80}")
        result = agent.answer_question(question)
        print(f"\n{'='*80}")
        print(f"📝 FINAL ANSWER:")
        print(f"{'='*80}")
        print(f"{result['answer']}")
        print(f"\n✅ Completed in {result['iterations']} iterations")
        print(f"{'='*80}\n")
    print("✅ All tests complete!")


if __name__ == "__main__":
    test_simple_react()
