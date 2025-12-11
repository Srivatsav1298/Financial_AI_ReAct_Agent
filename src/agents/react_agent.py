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
    evaluate_major_purchase,
    simulate_future_wealth,
    generate_financial_persona_comment
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
            "evaluate_purchase": evaluate_major_purchase,
            "simulate_wealth": simulate_future_wealth,
            "generate_persona": generate_financial_persona_comment
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
            # Split by comma, respecting quotes would be better but simple split works for numbers
            raw_args = [arg.strip().strip('\'"') for arg in args_str.split(',')]
            
            # Clean args: remove "key=" if the LLM hallucinated kwargs
            clean_args = []
            for arg in raw_args:
                if '=' in arg:
                    # 'income=50000' -> '50000'
                    clean_args.append(arg.split('=')[1].strip())
                else:
                    clean_args.append(arg)
            
            return tool_name, clean_args
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
            "evaluate_major_purchase": "evaluate_purchase",
            "simulate_wealth": "simulate_wealth",
            "simulate_future_wealth": "simulate_wealth",
            "generate_persona": "generate_persona",
            "generate_financial_persona_comment": "generate_persona"
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
            elif mapped_tool == "simulate_wealth":
                result = tool.invoke({
                    "monthly_savings": float(args[0]),
                    "current_savings": float(args[1]),
                    "years": int(args[2]) if len(args) > 2 else 30
                })
            elif mapped_tool == "generate_persona":
                result = tool.invoke({
                    "persona": args[0],
                    "context_data": args[1]
                })
            else:
                result = tool.invoke({})
            
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Error calling tool: {str(e)}"

    def answer_question(self, question: str, language: str = 'en', persona: str = 'analyst') -> Dict[str, Any]:
        print(f"\n{'='*80}")
        print(f"🤔 REACT AGENT REASONING...")
        print(f"{'='*80}\n")
        
        # 1. Check fallback
        if not self.llm:
            return self._fallback_response(question, language)

        conversation_history = []
        reasoning_steps = []
        structured_tool_outputs = []
        
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
- simulate_wealth(monthly_savings, current_savings, years) - simulate future wealth with compound interest (returns chart data)
- generate_persona(persona, context) - get a persona-driven comment (roast, coach, etc)

For COMPLEX questions requiring personalized recommendations:
For COMPLEX questions requiring personalized recommendations:
1. Use MULTIPLE tools to gather comprehensive data
2. Analyze from multiple angles (health, optimization, anomalies)
3. Provide SPECIFIC, ACTIONABLE recommendations
4. Show your multi-step reasoning clearly

After thorough analysis, provide:
{final_answer_label}: [comprehensive answer with specific recommendations and sources]

Use advanced tools for non-trivial questions. Be thorough and analytical.

CURRENT PERSONA: {persona.upper()}

IMPORTANT: You MUST adopt this persona in your THOUGHTS and FINAL ANSWER.
- If 'ROAST': Be sarcastic, funny, and brutally honest. Mock bad financial habits. Use emojis like 💀💸.
- If 'COACH': Be essentially supportive, encouraging, and motivational. Use emojis like 🚀💪.
- If 'STRICT': Be extremely professional, concise, and efficiency-obsessed. No fluff. Use emojis like 📉🧐.
- If 'DEBATE': (Covered by multi-agent mode, ignore here).

Internalize this persona NOW. Do not break character."""

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
                            "structured_tools": structured_tool_outputs,
                            "model": "react_simple (Ollama Llama3.2)"
                        }

                tool_name, args = self._parse_action(llm_output)
                if tool_name and args:
                    print(f"🔧 Executing: {tool_name}({args})\n")
                    observation = self._call_tool(tool_name, args)
                    
                    # Handle structured output (Dict) vs String
                    if isinstance(observation, dict) and "text" in observation:
                        text_observation = observation["text"]
                        if "data" in observation:
                            structured_tool_outputs.append(observation["data"])
                    else:
                        text_observation = str(observation)
                        
                    print(f"📊 OBSERVATION:\n{text_observation}\n")
                    conversation_history.append(f"OBSERVATION: {text_observation}")
                    reasoning_steps.append({
                        "iteration": iteration + 1,
                        "thought": llm_output,
                        "action": f"{tool_name}({args})",
                        "observation": text_observation
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
                "structured_tools": structured_tool_outputs,
                "model": "react_simple (Ollama Llama3.2)"
            }
        except Exception as e:
            print(f"❌ Critical error in ReAct Agent: {e}")
            return self._fallback_response(question, language, error=str(e))

    def _fallback_response(self, question: str, language: str, error: str = None) -> Dict[str, Any]:
        """Mock ReAct response for demo purposes"""
        print("⚠️ USING FALLBACK RESPONSE")
        
        if language == 'no':
            reasoning_steps = [
                {
                    "iteration": 1,
                    "thought": "Jeg må sjekke om AI-modellen kjører.",
                    "action": "sjekk_tilkobling(Ollama)",
                    "observation": "Tilkobling mislyktes"
                },
                {
                    "iteration": 2,
                    "thought": "Siden den lokale AI-en er nede, bør jeg informere brukeren direkte.",
                    "action": "svar_fallback()",
                    "observation": "Forbereder feilmelding"
                }
            ]
            msg = "Jeg kan ikke koble til den lokale AI-modellen (Ollama), så jeg kan ikke utføre avansert resonnering akkurat nå."
            if error:
                msg += f"\n\nTeknisk feil: {error}"
            msg += "\n\nVennligst start Ollama lokalt for å se ReAct i aksjon."
        else:
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


    def reason_with_debate(self, question: str, language: str = 'en') -> Dict[str, Any]:
        """
        Research-Grade Feature: Multi-Agent Debate.
        Orchestrates a dialectic between specialized sub-agents.
        """
        print(f"\n{'='*80}")
        print(f"🗣️ MULTI-AGENT DEBATE PROTOCOL INITIATED")
        print(f"{'='*80}\n")
        
        if not self.llm:
            return self._fallback_response(question, language, error="No LLM for debate")
            
        transcript = []
        
        # 1. THE GROWTH AGENT (Thesis)
        print("🟢 GROWTH AGENT (Thesis)...")
        growth_prompt = f"""You are the GROWTH AGENT. Your goal is to maximize wealth, suggesting aggressive but viable financial strategies.
        Ignore safety concerns for a moment and focus on UPSIDE. Use the available data to build a strong case for growth.
        
        Question: {question}
        
        Provide your formatted argument."""
        
        growth_resp = self.llm.invoke(growth_prompt).content
        transcript.append({"agent": "Growth Agent", "color": "#2ecc71", "content": growth_resp})
        print(f"{growth_resp}\n")
        
        # 2. THE RISK AGENT (Antithesis)
        print("🔴 RISK AGENT (Antithesis)...")
        risk_prompt = f"""You are the RISK AGENT. Your job is to criticize the Growth Agent's plan.
        Highlight dangers, volatility, downsides, and what could go wrong. Be the "Devils Advocate".
        
        Question: {question}
        Growth Agent Proposal: {growth_resp}
        
        Provide your critique."""
        
        risk_resp = self.llm.invoke(risk_prompt).content
        transcript.append({"agent": "Risk Agent", "color": "#e74c3c", "content": risk_resp})
        print(f"{risk_resp}\n")
        
        # 3. THE SYNTHESIZER (Synthesis)
        print("🔵 MODERATOR (Synthesis)...")
        synth_prompt = f"""You are the CHIEF MODERATOR.
        Review the debate between Growth and Risk agents.
        
        Question: {question}
        Growth Argument: {growth_resp}
        Risk Critique: {risk_resp}
        
        Synthesize a FINAL, BALANCED strategy that captures the best of both worlds.
        FINAL ANSWER:"""
        
        synth_resp = self.llm.invoke(synth_prompt).content
        transcript.append({"agent": "Synthesizer", "color": "#3498db", "content": synth_resp})
        print(f"{synth_resp}\n")
        
        return {
            "question": question,
            "answer": synth_resp,
            "debate_transcript": transcript,
            "model": "Multi-Agent Debate (Llama3.2)"
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
