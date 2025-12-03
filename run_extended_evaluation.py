"""
Run evaluation on extended 30-question test set
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import time

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from agents.baseline import BaselineAgent
from agents.react_agent import SimpleReactAgent


def load_extended_questions():
    """Load extended 30-question test set"""
    questions_path = Path(__file__).parent.parent / "data/evaluation/extended_questions.json"
    
    if not questions_path.exists():
        print(f"❌ Extended questions file not found: {questions_path}")
        print("   Please create the file first!")
        sys.exit(1)
    
    with open(questions_path, 'r') as f:
        data = json.load(f)
    return data['questions']


def run_baseline_extended(questions):
    """Run baseline on extended questions"""
    print("\n" + "="*80)
    print("🤖 BASELINE AGENT - EXTENDED EVALUATION (30 Questions)")
    print("="*80 + "\n")
    
    agent = BaselineAgent()
    results = []
    
    total_time = 0.0
    
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/30] Category: {q['category']} | Complexity: {q.get('complexity', 'N/A')}")
        print(f"Question: {q['question']}")
        
        try:
            start_time = time.time()
            result = agent.answer_question(q['question'])
            elapsed = time.time() - start_time
            total_time += elapsed
            
            results.append({
                "question_id": q["id"],
                "question": q["question"],
                "category": q["category"],
                "complexity": q.get("complexity", "unknown"),
                "answer": result["answer"],
                "tool_used": result.get("tool_used", False),
                "elapsed_time": elapsed,
                "model": result["model"]
            })
            
            print(f"✅ Answer: {result['answer'][:100]}...")
            print(f"⏱️  Time: {elapsed:.2f}s | Tool Used: {result.get('tool_used', False)}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "question_id": q["id"],
                "question": q["question"],
                "category": q["category"],
                "complexity": q.get("complexity", "unknown"),
                "answer": f"ERROR: {str(e)}",
                "tool_used": False,
                "elapsed_time": 0,
                "model": "baseline"
            })
    
    print("\n📊 Baseline Summary:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time: {total_time/len(questions):.2f}s per question")
    print(f"   Tool usage: {sum(1 for r in results if r['tool_used'])}/{len(questions)}")
    
    return results


def run_react_extended(questions):
    """Run ReAct on extended questions"""
    print("\n" + "="*80)
    print("🧠 REACT AGENT - EXTENDED EVALUATION (30 Questions)")
    print("="*80 + "\n")
    
    agent = SimpleReactAgent()
    results = []
    
    total_time = 0.0
    total_iterations = 0
    
    for i, q in enumerate(questions, 1):
        print("\n" + "="*80)
        print(f"[{i}/30] Category: {q['category']} | Complexity: {q.get('complexity', 'N/A')}")
        print(f"Question: {q['question']}")
        print("="*80)
        
        try:
            start_time = time.time()
            result = agent.answer_question(q['question'])
            elapsed = time.time() - start_time
            
            total_time += elapsed
            total_iterations += result.get("iterations", 0)
            
            results.append({
                "question_id": q["id"],
                "question": q["question"],
                "category": q["category"],
                "complexity": q.get("complexity", "unknown"),
                "answer": result["answer"],
                "reasoning_steps": result.get("reasoning_steps", []),
                "iterations": result.get("iterations", 0),
                "elapsed_time": elapsed,
                "model": result["model"]
            })
            
            print(f"\n✅ Answer: {result['answer'][:100]}...")
            print(f"⏱️  Time: {elapsed:.2f}s | Iterations: {result.get('iterations', 0)}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "question_id": q["id"],
                "question": q["question"],
                "category": q["category"],
                "complexity": q.get("complexity", "unknown"),
                "answer": f"ERROR: {str(e)}",
                "reasoning_steps": [],
                "iterations": 0,
                "elapsed_time": 0,
                "model": "react"
            })
    
    print("\n📊 ReAct Summary:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time: {total_time/len(questions):.2f}s per question")
    print(f"   Average iterations: {total_iterations/len(questions):.1f}")
    
    return results


def save_extended_results(baseline_results, react_results):
    """Save extended evaluation results"""
    
    results_dir = Path(__file__).parent.parent / "results" / "extended"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    baseline_file = results_dir / f"baseline_extended_{timestamp}.json"
    with open(baseline_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "agent": "baseline",
            "num_questions": len(baseline_results),
            "results": baseline_results
        }, f, indent=2)
    
    print(f"\n✅ Saved: {baseline_file}")
    
    react_file = results_dir / f"react_extended_{timestamp}.json"
    with open(react_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "agent": "react",
            "num_questions": len(react_results),
            "results": react_results
        }, f, indent=2)
    
    print(f"✅ Saved: {react_file}")
    
    return baseline_file, react_file


def compare_results(baseline_results, react_results):
    """Quick comparison of results"""
    
    print("\n" + "="*80)
    print("📊 COMPARISON SUMMARY (30 Questions)")
    print("="*80)
    
    n = len(baseline_results)

    baseline_tools = sum(1 for r in baseline_results if r["tool_used"])
    react_tools = sum(1 for r in react_results if r.get("iterations", 0) > 0)
    
    baseline_avg = sum(r["elapsed_time"] for r in baseline_results) / n
    react_avg = sum(r["elapsed_time"] for r in react_results) / n
    
    avg_iterations = sum(r.get("iterations", 0) for r in react_results) / n
    
    baseline_errors = sum(1 for r in baseline_results if "ERROR" in r["answer"])
    react_errors = sum(1 for r in react_results if "ERROR" in r["answer"])
    
    print(f"\n{'Metric':<30} {'Baseline':<15} {'ReAct':<15}")
    print("-"*60)
    print(f"{'Questions Evaluated':<30} {n:<15} {n:<15}")
    print(f"{'Tool Usage':<30} {f'{baseline_tools}/{n}':<15} {f'{react_tools}/{n}':<15}")
    print(f"{'Avg Response Time (s)':<30} {baseline_avg:<15.2f} {react_avg:<15.2f}")
    print(f"{'Avg Iterations':<30} {'1.0':<15} {avg_iterations:<15.1f}")
    print(f"{'Errors':<30} {baseline_errors:<15} {react_errors:<15}")
    print(f"{'Error Rate (%)':<30} {baseline_errors/n*100:<15.1f} {react_errors/n*100:<15.1f}")
    
    print("\n" + "="*80)


def main():
    """Run extended evaluation"""
    
    print("\n" + "🎯"*40)
    print("EXTENDED EVALUATION - 30 QUESTIONS")
    print("🎯"*40 + "\n")
    
    questions = load_extended_questions()
    print(f"📝 Loaded {len(questions)} test questions")
    
    categories = {}
    for q in questions:
        categories[q["category"]] = categories.get(q["category"], 0) + 1
    
    print("\nQuestion distribution:")
    for cat, count in sorted(categories.items()):
        print(f"   - {cat}: {count} questions")
    
    print("\n⚠️  This will take approximately 10–15 minutes...")
    print("You can interrupt with Ctrl+C\n")
    
    input("Press Enter to start baseline evaluation...")
    baseline_results = run_baseline_extended(questions)
    
    input("\n\nPress Enter to start ReAct evaluation...")
    react_results = run_react_extended(questions)
    
    baseline_file, react_file = save_extended_results(baseline_results, react_results)
    
    compare_results(baseline_results, react_results)
    
    print("\n✅ Extended evaluation complete!")
    print("\nNext step: Run advanced analysis on extended results")
    print("   Command: python advanced_analysis.py")


if __name__ == "__main__":
    main()
