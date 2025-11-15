"""
Simple Manual ReAct Agent - Shows explicit reasoning (Ollama)
Implements ReAct loop manually without complex LangChain abstractions
"""

import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
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


class SimpleReactAgent:
    """Manual ReAct agent implementation"""
    
    def __init__(self, model_name: str = "llama3.2"):
        self.llm = ChatOllama(model=model_name, temperature=0)
        self.tools = {
            "get_spending": get_average_spending_by_category,
            "compare_spending": compare_spending_categories,
            "get_total_spending": get_total_household_spending
        }
        self.max_iterations = 5

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
            "get_total_household_spending": "get_total_spending"
        }
        mapped_tool = tool_mapping.get(tool_name)
        if not mapped_tool or mapped_tool not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"
        tool = self.tools[mapped_tool]
        try:
            if mapped_tool == "get_spending":
                result = tool.invoke({"category": args[0], "year": "2012"})
            elif mapped_tool == "compare_spending":
                result = tool.invoke({
                    "category1": args[0],
                    "category2": args[1] if len(args) > 1 else "food",
                    "year": "2012"
                })
            else:
                result = tool.invoke({"year": "2012"})
            return result
        except Exception as e:
            return f"Error calling tool: {str(e)}"

    def answer_question(self, question: str) -> Dict[str, Any]:
        print(f"\n{'='*80}")
        print(f"🤔 REACT AGENT REASONING...")
        print(f"{'='*80}\n")

        conversation_history = []
        reasoning_steps = []
        system_prompt = """You are a helpful Norwegian financial assistant using Statistics Norway data.

Answer questions using this EXACT format:

THOUGHT: [explain what you need to know]
ACTION: tool_name("argument")
[wait for observation]

Available tools:
- get_spending("category") - get spending for a category like "housing", "food", etc.
- compare_spending("category1", "category2") - compare two categories
- get_total_spending() - get total household spending

After getting observations, provide:
FINAL ANSWER: [your complete answer with sources]

Be concise. Use tools to get data before answering."""

        current_question = f"Question: {question}"

        for iteration in range(self.max_iterations):
            print(f"--- Iteration {iteration + 1} ---\n")
            if iteration == 0:
                prompt_text = f"{system_prompt}\n\n{current_question}\n\nLet's think step by step:"
            else:
                prompt_text = f"{system_prompt}\n\n{current_question}\n\n"
                prompt_text += "\n".join(conversation_history)
                prompt_text += "\n\nContinue reasoning:"
            response = self.llm.invoke(prompt_text)
            llm_output = response.content if hasattr(response, 'content') else str(response)
            print(f"🧠 LLM Output:\n{llm_output}\n")
            conversation_history.append(llm_output)

            if "FINAL ANSWER" in llm_output.upper():
                final_match = re.search(r'FINAL ANSWER:?\s*(.+)', llm_output, re.IGNORECASE | re.DOTALL)
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
