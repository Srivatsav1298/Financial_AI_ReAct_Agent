"""
Simple Manual ReAct Agent - Shows explicit reasoning (Ollama)
Implements ReAct loop manually without complex LangChain abstractions
FIXED VERSION: Addresses iteration stopping, tool output display, and data grounding
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
    """Manual ReAct agent implementation with fixes for data grounding"""
    
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
        self.max_iterations = 15  # INCREASED for complex reasoning
        self.minimum_iterations_complex = 4  # Don't stop before this on hard questions

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
        """Extract tool name and arguments from LLM output"""
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

    def _extract_key_metrics(self, observation_result) -> str:
        """
        FIX #1: Extract and display actual numbers from tool outputs
        Don't just return JSON - show the KEY METRICS prominently
        """
        if isinstance(observation_result, dict):
            # If tool returns structured data, extract key values
            if "text" in observation_result:
                text = observation_result["text"]
            else:
                text = str(observation_result)
            
            # Also extract numeric data if present
            if "data" in observation_result:
                data = observation_result["data"]
                
                # Build a metrics summary
                metrics_str = "\n📊 KEY METRICS RETRIEVED:\n"
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (int, float)):
                            metrics_str += f"  • {key}: {value:,.0f}\n"
                        else:
                            metrics_str += f"  • {key}: {value}\n"
                
                metrics_str += f"\n📌 SOURCE: Statistics Norway (SSB Table 10235, 2012)\n"
                metrics_str += f"\n{text}"
                return metrics_str
            
            return text
        
        return str(observation_result)

    def _validate_response(self, response: str, iteration: int, is_complex: bool) -> bool:
        """
        FIX #2: Don't accept generic advice early
        Response must have actual numbers + SSB citations
        """
        # Count specific numbers (2+ digits)
        numbers = re.findall(r'\d{2,}', response)
        
        # Check for SSB citations with values
        ssb_pattern = r'SSB|Statistics Norway|Statistisk sentralbyrå'
        has_ssb_citation = bool(re.search(ssb_pattern, response, re.IGNORECASE))
        
        # Check for generic phrases (bad indicators)
        generic_phrases = [
            'typically', 'generally', 'usually', 'usually recommend',
            'financial guidelines', 'conventional wisdom', 'standard practice'
        ]
        has_generic = any(phrase in response.lower() for phrase in generic_phrases)
        
        # For complex questions, require minimum iterations + actual data
        if is_complex:
            if iteration < self.minimum_iterations_complex:
                return False  # Keep iterating on complex questions
            
            if len(numbers) < 3 or not has_ssb_citation:
                return False  # Need actual data before outputting
        
        # If response is mostly generic without data, reject it
        if has_generic and len(numbers) < 2:
            return False
        
        return True

    def _call_tool(self, tool_name: str, args: List[str]) -> str:
        """Execute tool and return formatted observation with key metrics"""
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
            
            # FIX #1: Extract key metrics from the result
            return self._extract_key_metrics(result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Error calling tool: {str(e)}"

    def _detect_question_complexity(self, question: str) -> bool:
        """
        Detect if a question is complex (requires multiple iterations).
        Complex questions: recommendations, optimizations, multi-step analysis
        """
        complex_keywords = [
            'should', 'recommend', 'optimize', 'budget', 'save', 'afford',
            'buy', 'realistic', 'plan', 'strategy', 'allocate', 'spend',
            'balance', 'trade-off', 'decision', 'compare', 'better',
            'improve', 'risk', 'future', 'goal'
        ]
        
        question_lower = question.lower()
        is_complex = any(keyword in question_lower for keyword in complex_keywords)
        return is_complex

    def answer_question(self, question: str, language: str = 'en', persona: str = 'analyst') -> Dict[str, Any]:
        print(f"\n{'='*80}")
        print(f"🤔 REACT AGENT REASONING...")
        print(f"{'='*80}\n")
        
        # 1. Check fallback
        if not self.llm:
            return self._fallback_response(question, language)

        # Detect complexity
        is_complex = self._detect_question_complexity(question)
        print(f"📋 Question Complexity: {'COMPLEX ⚠️' if is_complex else 'SIMPLE ✓'}\n")

        conversation_history = []
        reasoning_steps = []
        structured_tool_outputs = []
        
        # Language-specific instructions
        if language == 'no':
            language_instruction = "\n\nWICHTIG: Svar på NORSK. Alle dine tanker, handlinger og endelige svar må være på norsk."
            final_answer_label = "ENDELIG SVAR"
        else:
            language_instruction = ""
            final_answer_label = "FINAL ANSWER"
        
        # FIXED SYSTEM PROMPT: More aggressive about data requirements
        system_prompt = f"""You are an expert Norwegian financial advisor using real-time Statistics Norway (SSB) data. {language_instruction}

OBJECTIVE:
You MUST provide EVIDENCE-BASED financial advice grounded in actual SSB numbers.
NEVER answer from training memory if a tool can provide the answer.
NEVER give generic advice without showing specific numbers from SSB.

CRITICAL RULES FOR THIS SESSION:
1. **ALWAYS SHOW NUMBERS**: Every claim must cite a specific value. Bad: "Norwegians spend on housing." Good: "SSB shows Norwegians spend 11,332 NOK/month on housing."
2. **ITERATE FULLY**: For complex questions (recommendations, budgets, decisions), you MUST iterate at least 4 times. Do not stop early.
3. **DATA FIRST, THEN ADVICE**: Retrieve all necessary data BEFORE giving recommendations.
4. **CITE SOURCES**: Format: "According to SSB Table 10235 (2012), X = Y NOK/month"
5. **NO GENERIC PHRASES**: Avoid "typically", "generally", "usually" - use SSB numbers instead.

FORMAT (STRICT):
- THOUGHT: "What data do I need? Do I have it?"
- ACTION: Tool call. Example: analyze_budget_health(41667, 11332, 4286, 4000, 3000, 2000)
- OBSERVATION: [You'll read actual numbers here. CITE THEM in output.]
- REPEAT 4+ times on complex questions
- {final_answer_label}: [Your Answer]

CRITICAL: At the very end of your {final_answer_label}, YOU MUST include a section starting with exactly:
"### Why this matters for you"

In this section, provide a personal, high-impact takeaway (e.g., "This is 10% higher than average," or "This adjustment could save you 5000 NOK/year"). This turns data into insight.

MINIMUM ITERATIONS:
- Simple questions (facts, comparisons): 2 iterations minimum
- Complex questions (budget, recommendation, decision): 4 iterations minimum
- Don't rush to {final_answer_label}

PERSONA: {persona.upper()}
Apply these communication styles:
- 'ANALYST': Neutral, data-focused, precise
- 'ROAST': Humorous, direct critique ("You spend 12k on food? Do you eat gold?")
- 'COACH': Encouraging, motivational ("You're crushing it! Let's optimize.")
- 'STRICT': No-nonsense Dave Ramsey style ("Cut discretionary by 40% immediately")
- 'DEBATE': Multi-agent reasoning (handled separately)

TOOLS AVAILABLE:
BASIC: get_spending(category) | compare_spending(cat1, cat2) | get_total_spending()
ADVANCED: analyze_budget_health(...) | optimize_budget(...) | assess_lifestyle(...) | 
          detect_anomalies(...) | calculate_savings(...) | evaluate_purchase(...) | 
          simulate_wealth(monthly_savings, current_savings, years)

Remember: Your goal is to be HELPFUL + GROUNDED IN DATA. Show your work."""

        current_question = f"Question: {question}"

        try:
            for iteration in range(self.max_iterations):
                print(f"\n{'─'*80}")
                print(f"ITERATION {iteration + 1} of {self.max_iterations}")
                print(f"{'─'*80}\n")
                
                if iteration == 0:
                    prompt_text = f"{system_prompt}\n\n{current_question}\n\nLet's think step by step:"
                else:
                    prompt_text = f"{system_prompt}\n\n{current_question}\n\n"
                    prompt_text += "\n".join(conversation_history[-5:])  # Keep last 5 exchanges for context
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
                    # FIX #2: Validate the response before accepting it
                    final_match = re.search(r'(?:FINAL ANSWER|ENDELIG SVAR):?\s*(.+)', llm_output, re.IGNORECASE | re.DOTALL)
                    if final_match:
                        final_answer = final_match.group(1).strip()
                        
                        # Validate response quality
                        is_valid = self._validate_response(final_answer, iteration, is_complex)
                        
                        if is_valid or iteration >= self.max_iterations - 1:
                            # Accept the answer if valid OR we're at max iterations
                            print(f"{'='*80}")
                            print(f"✅ REACHED FINAL ANSWER (Iteration {iteration + 1})")
                            print(f"{'='*80}\n")
                            return {
                                "question": question,
                                "answer": final_answer,
                                "reasoning_steps": reasoning_steps,
                                "conversation_history": conversation_history,
                                "iterations": iteration + 1,
                                "structured_tools": structured_tool_outputs,
                                "model": "react_simple (Ollama Llama3.2)",
                                "complexity": "COMPLEX" if is_complex else "SIMPLE"
                            }
                        else:
                            # Reject and force continuation
                            print(f"⚠️ Response lacks sufficient data grounding. Continuing iterations...")
                            continue

                # Parse and execute tool
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
                    # No tool called in this iteration - just reasoning
                    print(f"💭 [Reasoning step, no tool invocation]\n")
                    reasoning_steps.append({
                        "iteration": iteration + 1,
                        "thought": llm_output,
                        "action": None,
                        "observation": None
                    })

            # If we exhaust iterations, return best effort
            print(f"⚠️ Max iterations ({self.max_iterations}) reached without final answer\n")
            return {
                "question": question,
                "answer": "Could not reach final answer within iteration limit. Consult a financial advisor.",
                "reasoning_steps": reasoning_steps,
                "conversation_history": conversation_history,
                "iterations": self.max_iterations,
                "structured_tools": structured_tool_outputs,
                "model": "react_simple (Ollama Llama3.2)",
                "complexity": "COMPLEX" if is_complex else "SIMPLE"
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
        Ignore safety concerns for a moment and focus on UPSIDE. Use available data to build a strong case for growth.
        
        Question: {question}
        
        Provide your THOUGHT→ACTION→OBSERVATION→RECOMMENDATION reasoning."""
        
        growth_resp = self.llm.invoke(growth_prompt).content
        transcript.append({"agent": "Growth Agent", "color": "#2ecc71", "content": growth_resp})
        print(f"{growth_resp}\n")
        
        # 2. THE RISK AGENT (Antithesis)
        print("🔴 RISK AGENT (Antithesis)...")
        risk_prompt = f"""You are the RISK AGENT. Your job is to criticize the Growth Agent's plan.
        Highlight dangers, volatility, downsides, and what could go wrong. Be the "Devil's Advocate".
        Use SSB data to support your critique.
        
        Question: {question}
        Growth Agent Proposal: {growth_resp}
        
        Provide your risk-focused THOUGHT→ACTION→OBSERVATION→CRITIQUE reasoning."""
        
        risk_resp = self.llm.invoke(risk_prompt).content
        transcript.append({"agent": "Risk Agent", "color": "#e74c3c", "content": risk_resp})
        print(f"{risk_resp}\n")
        
        # 3. THE SYNTHESIZER (Synthesis)
        print("🔵 MODERATOR (Synthesis)...")
        synth_prompt = f"""You are the CHIEF MODERATOR. Your job is to synthesize the debate.
        
        Question: {question}
        Growth Argument: {growth_resp}
        Risk Critique: {risk_resp}
        
        Create a FINAL, BALANCED strategy that:
        - Captures strengths of both positions
        - Cites actual SSB numbers
        - Provides actionable recommendation
        
        Format: THOUGHT → ACTION → OBSERVATION → FINAL ANSWER: [balanced recommendation]"""
        
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
        "I earn 500,000 NOK/year after tax, live in Oslo, have 2 kids, and want to buy a house in 5 years. Create a realistic budget that balances current living standards with my savings goal.",
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
        print(f"\n✅ Completed in {result['iterations']} iterations ({result.get('complexity', 'UNKNOWN')})")
        print(f"{'='*80}\n")
    print("✅ All tests complete!")


if __name__ == "__main__":
    test_simple_react()