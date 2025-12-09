"""
Flask Backend for Norfain ReAct Agent Web Dashboard
Provides REST API for chat interface and data visualization
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
import json
import time
import importlib

# Add src to path (from root directory: Norfain/src)
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

# Import agent modules
from agents import baseline
from agents import react_agent

# Force reload to get latest code (important for development)
importlib.reload(baseline)
importlib.reload(react_agent)

from agents.baseline import BaselineAgent
from agents.react_agent import SimpleReactAgent
from utils.ssb_api import SSBApi

app = Flask(__name__)
CORS(app)

# Initialize agents
print("🚀 Initializing agents...")
try:
    baseline_agent = BaselineAgent()
    react_agent = SimpleReactAgent()
    ssb_api = SSBApi()
    print("✅ Agents ready!")
except Exception as e:
    print(f"❌ Failed to initialize agents: {e}")
    # Initialize with None or handle gracefully if needed, 
    # but for now let it print error. 
    # The agents themselves calculate fallback, but instantiation must succeed.
    raise e


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    Handle question from user
    Returns responses from both baseline and ReAct agents
    """
    data = request.json
    question = data.get('question', '')
    language = data.get('language', 'en')  # Get language preference (en or no)
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    try:
        # Get baseline response
        print(f"\n📝 Question: {question}")
        print(f"🌍 Language: {language}")
        print("🤖 Running Baseline...")
        
        baseline_start = time.time()
        baseline_result = baseline_agent.answer_question(question, language=language)
        baseline_time = time.time() - baseline_start
        
        # Get ReAct response
        print("🧠 Running ReAct...")
        react_start = time.time()
        react_result = react_agent.answer_question(question, language=language)
        react_time = time.time() - react_start
        
        print("✅ Both agents complete!")
        
        # Format response
        response = {
            'question': question,
            'baseline': {
                'answer': baseline_result['answer'],
                'time': baseline_time,
                'tool_used': baseline_result.get('tool_used', False),
                'model': baseline_result['model']
            },
            'react': {
                'answer': react_result['answer'],
                'time': react_time,
                'iterations': react_result.get('iterations', 0),
                'reasoning_steps': react_result.get('reasoning_steps', []),
                'conversation_history': react_result.get('conversation_history', []),
                'model': react_result['model']
            },
            'comparison': {
                'time_difference': react_time - baseline_time,
                'time_ratio': react_time / baseline_time if baseline_time > 0 else 0
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        # Return a structured error response that the frontend can parse
        return jsonify({
            'error': str(e),
            'type': 'Internal Server Error'
        }), 500


@app.route('/api/ssb-data', methods=['GET'])
def get_ssb_data():
    """Get SSB household budget data for visualization"""
    try:
        year = request.args.get('year', '2012')
        
        # Get all household budget data
        data = ssb_api.get_household_budget_data(year=year)
        
        if not data:
            return jsonify({'error': 'No data available'}), 404
        
        # Parse data
        parsed = ssb_api.parse_household_data(data)
        
        # Format for frontend
        formatted_data = {
            'year': year,
            'categories': [
                {
                    'category': item['category'],
                    'code': item['category_code'],
                    'annual': item['value'],
                    'monthly': item['value'] / 12,
                    'unit': 'NOK'
                }
                for item in parsed
            ],
            'total': sum(item['value'] for item in parsed)
        }
        
        return jsonify(formatted_data)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        # Try to load latest results from root results directory
        results_dir = Path(__file__).parent.parent.parent / "results"
        
        baseline_files = sorted(results_dir.glob("baseline_results_*.json"))
        react_files = sorted(results_dir.glob("react_results_*.json"))
        
        if not baseline_files or not react_files:
            return jsonify({
                'available': False,
                'message': 'No evaluation results available. Run evaluation first.'
            })
        
        # Load latest results
        with open(baseline_files[-1], 'r') as f:
            baseline_data = json.load(f)
        
        with open(react_files[-1], 'r') as f:
            react_data = json.load(f)
        
        # Calculate statistics
        baseline_results = baseline_data['results']
        react_results = react_data['results']
        
        stats = {
            'available': True,
            'total_questions': len(baseline_results),
            'timestamp': baseline_data.get('timestamp', 'N/A'),
            'baseline': {
                'avg_time': sum(r['elapsed_time'] for r in baseline_results) / len(baseline_results),
                'tool_usage': sum(1 for r in baseline_results if r.get('tool_used', False)) / len(baseline_results) * 100,
                'errors': sum(1 for r in baseline_results if 'ERROR' in r['answer'])
            },
            'react': {
                'avg_time': sum(r['elapsed_time'] for r in react_results) / len(react_results),
                'tool_usage': 100.0,
                'avg_iterations': sum(r.get('iterations', 0) for r in react_results) / len(react_results),
                'errors': sum(1 for r in react_results if 'ERROR' in r['answer'])
            }
        }
        
        return jsonify(stats)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'available': False, 'error': str(e)})


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'agents': 'loaded',
        'ssb_api': 'connected'
    })


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 NORFAIN REACT AGENT WEB DASHBOARD")
    print("="*80)
    print("\n✅ Server starting...")
    print("📡 Dashboard URL: http://localhost:5000")
    print("💡 Open in your browser to interact with agents!")
    print("\n⏹️  Press CTRL+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5050)