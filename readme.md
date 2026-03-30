# Financial AI ReAct Agent 🤖📊

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?logo=flask)](https://flask.palletsprojects.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.0-green.svg)](https://github.com/langchain-ai/langchain)
[![Ollama](https://img.shields.io/badge/Ollama-Llama_3.2-000000?logo=ollama)](https://ollama.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **An AI-powered financial analysis platform** that provides transparent, explainable insights on Norwegian household economics using official Statistics Norway (SSB) data. Features a production-ready web dashboard and dual-agent architecture comparing baseline vs ReAct reasoning.

---

## 📸 Dashboard Preview

| Financial Advisor | Grocery Price Tracker | Savings Goals | Data Explorer |
|------------------|----------------------|---------------|---------------|
| ![Advisor](https://via.placeholder.com/400x250/1e3a8a/ffffff?text=AI+Financial+Advisor) | ![Groceries](https://via.placeholder.com/400x250/059669/ffffff?text=Grocery+Prices) | ![Savings](https://via.placeholder.com/400x250/7c3aed/ffffff?text=Inflation+Tracker) | ![Data](https://via.placeholder.com/400x250/dc2626/ffffff?text=SSB+Data) |

---

## 🎯 What Does It Do?

Norfain (Financial AI ReAct Agent) is a **production-ready AI financial advisory system** that:

1. **Answers complex financial questions** about Norwegian household economics using verified SSB data
2. **Compares two AI approaches**: Fast baseline responses vs transparent ReAct reasoning
3. **Provides a full web dashboard** for interactive exploration of financial data
4. **Tracks grocery prices** across Norwegian retailers in real-time
5. **Helps users plan savings** with inflation-adjusted goals
6. **Generates complete reasoning traces** for auditability and trust

### Perfect For:
- 📊 **Researchers** studying AI explainability in finance
- 🏠 **Norwegian households** seeking data-driven financial guidance
- 🎓 **Students** learning about agent architectures and financial AI
- 💼 **Financial advisors** wanting to understand AI tools

---

## ✨ Key Features

### 🧠 Dual AI Agent System

| Feature | Baseline Agent | ReAct Agent |
|---------|---------------|-------------|
| **Speed** | ⚡ Fast (~7s) | 🐢 Slower (~12s) |
| **Transparency** | ❌ Minimal | ✅ Full reasoning trace |
| **Tool Usage** | 85% | 100% |
| **Best For** | Simple queries | Complex analysis |
| **Explainability** | Low | High |

### 📈 Financial Analysis Capabilities

- 💰 **Household Budget Analysis** - Compare your spending against Norwegian averages
- 🛒 **Grocery Price Intelligence** - Track prices across 5+ retailers (Kiwi, Rema 1000, Meny, etc.)
- 📉 **Inflation-Aware Planning** - Automatically adjust savings goals based on CPI
- 🎯 **Smart Recommendations** - Identify cheapest store combinations and price gaps
- 📊 **Interactive Visualizations** - Charts, graphs, and maps in the web dashboard

### 🌐 Production Web Dashboard

Built with **Flask + production-grade features**:

- 🔒 **Security**: Rate limiting, CORS, session management
- ⚡ **Performance**: Thread-safe LRU caching, TTL expiration
- 📊 **Monitoring**: Comprehensive logging with file rotation
- 🎨 **UI**: Responsive Bootstrap-based templates
- 🔌 **API**: RESTful endpoints for all agent operations
- 🛠 **Configurable**: Environment-based configuration

### 🔐 Data & Privacy

- ✅ **GDPR Compliant** - No personal data collected
- ✅ **Official Data Sources** - Statistics Norway (SSB) JSON-stat2 API
- ✅ **Local Processing** - All analysis runs on your infrastructure
- ✅ **Transparent** - Every recommendation includes data source citations

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Dashboard (Flask)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Advisor │  │Groceries │  │Savings   │  │Thesis    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
└───────┼──────────────┼──────────────┼──────────────┼─────┘
        │              │              │              │
        └──────────────┼──────────────┼──────────────┘
                       │              │
            ┌──────────▼─────────────────────────┐
            │      Flask REST API Layer          │
            │  • Rate Limiting  • Caching        │
            │  • Authentication • Logging        │
            └──────────┬─────────────────────────┘
                       │
            ┌──────────▼─────────────────────────┐
            │      Agent Orchestration           │
            │  • Baseline Agent (fast)           │
            │  • ReAct Agent (explainable)       │
            └──────────┬─────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
   │ SSB API │  │  Cache   │  │ Ollama  │
   │Wrapper  │  │  Layer   │  │  LLM    │
   └─────────┘  └─────────┘  └─────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend Framework** | Flask 3.0+ with production extensions |
| **AI Framework** | LangChain (ReAct pattern implementation) |
| **LLM Backend** | Ollama (Llama 3.2) - runs locally |
| **Data Source** | Statistics Norway (SSB) JSON-stat2 API |
| **Frontend** | Jinja2 templates + Bootstrap 5 + Chart.js |
| **Caching** | Custom thread-safe LRU cache with TTL |
| **Security** | Flask-Limiter, CORS, session management |
| **Logging** | Python logging with file rotation |
| **Configuration** | Environment variables (12-factor app) |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+** - [Download](https://www.python.org/downloads/)
- **Ollama** - [Install](https://ollama.ai/) and pull Llama 3.2: `ollama pull llama3.2:latest`
- **Git** - [Download](https://git-scm.com/)

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/Srivatsav1298/Financial_AI_ReAct_Agent
cd Financial_AI_ReAct_Agent

# Create virtual environment
python -m venv venv

# Activate it:
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings (or use defaults for local dev)
```

**Key environment variables:**

```env
# Flask config
FLASK_APP=web_dashboard/app.py
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-here

# Agent config
AGENT_MODEL=llama3.2:latest  # Ollama model
DEFAULT_AGENT=react           # "baseline" or "react"

# SSB API
SSB_API_ENABLED=true
SSB_CACHE_TTL=86400           # 24 hours

# Rate limiting
RATELIMIT_ENABLED=true
RATELIMIT_DEFAULT=100 per hour
```

### 3. Run the Application

```bash
# Start the Flask development server
cd web_dashboard
python app.py
```

Or using Flask CLI:

```bash
export FLASK_APP=web_dashboard/app.py
flask run
```

Visit: **http://localhost:5050**

### 4. Try It Out

1. **Open the Advisor** - Go to `/ask` and ask questions like:
   - "How much should a family of 4 spend on groceries in Oslo?"
   - "What's the average housing cost in Bergen?"
   - "How has inflation affected food prices in 2024?"

2. **Explore Groceries** - View `/groceries` for price comparisons

3. **Plan Savings** - Use `/savings` to set inflation-adjusted goals

---

## 📁 Project Structure

```
Financial_AI_ReAct_Agent/
├── web_dashboard/           # Production Flask application
│   ├── app.py              # Main application (production-ready)
│   ├── templates/          # HTML templates (Bootstrap 5)
│   │   ├── index.html      # Home dashboard
│   │   ├── groceries.html  # Grocery price tracker
│   │   ├── savings-tracker.html  # Inflation-adjusted goals
│   │   ├── thesis.html     # Research documentation
│   │   └── ...
│   ├── static/             # CSS, JS, images
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── data/               # Cached data (gitignored)
│   └── logs/               # Application logs (gitignored)
│
├── src/                    # AI agent implementations
│   ├── agents/             # Baseline & ReAct agents
│   │   ├── baseline_agent.py
│   │   ├── react_agent.py
│   │   └── ...
│   ├── tools/              # LangChain tools for SSB data
│   │   ├── ssb_tools.py
│   │   └── ...
│   ├── utils/              # SSB API wrapper, caching, helpers
│   │   ├── ssb_client.py
│   │   └── ...
│   └── evaluation/         # Evaluation framework
│       ├── evaluator.py
│       └── ...
│
├── data/                   # Sample datasets and cached SSB responses
├── experiments/            # Experiment scripts and analysis
│   ├── run_extended_evaluation.py
│   └── advanced_analysis.py
├── paper/                  # LaTeX paper and figures
│   ├── main.tex
│   └── figures/
│
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── README.md              # This file
└── LICENSE                # MIT License
```

---

## 🎮 How It Works

### The ReAct Reasoning Loop

The ReAct agent follows an explicit **Thought → Action → Observation** cycle:

```
Question: "How should a family of 4 budget for groceries in Oslo?"

┌─────────────────────────────────────────────────────────┐
│ Thought: I need to find average grocery spending for   │
│          Norwegian households, then adjust for Oslo    │
│          and family size.                              │
├─────────────────────────────────────────────────────────┤
│ Action: get_average_spending(category="Food")         │
├─────────────────────────────────────────────────────────┤
│ Observation: SSB data shows NOK 8,500/month avg        │
├─────────────────────────────────────────────────────────┤
│ Thought: Need to adjust for Oslo (20% higher) and      │
│          family of 4 (2.5x multiplier)                 │
├─────────────────────────────────────────────────────────┤
│ Action: get_oslo_adjustment_factor()                  │
├─────────────────────────────────────────────────────────┤
│ Observation: Oslo premium = 1.2x                       │
├─────────────────────────────────────────────────────────┤
│ Final Answer: Recommended budget = 8,500 × 2.5 × 1.2  │
│               = NOK 25,500/month                       │
└─────────────────────────────────────────────────────────┘
```

**Baseline Agent** skips the reasoning and calls tools directly, which is faster but less transparent.

---

## 📊 Evaluation Results

### 20-Question Benchmark

| Metric | Baseline | ReAct | Difference |
|--------|----------|-------|------------|
| **Avg Response Time** | 6.90s | 11.78s | +70.7% |
| **Tool Usage Rate** | 85% | 100% | +15% |
| **Reasoning Visibility** | 0% | 80% | +80% |
| **Error Rate** | 0% | 0% | — |

### 50-Task Robustness Evaluation

| Task Type | ReAct Advantage | Key Improvement |
|-----------|-----------------|-----------------|
| **Diagnostic** | +60% | Correctly identifies "Chronic Undersaving" |
| **Persona Adherence** | +20% | Follows complex scenario instructions |
| **Judgment Calls** | +20% | Nuanced lifestyle assessments |
| **Shock Response** | +10% | Handles unexpected events better |

**Conclusion**: ReAct significantly outperforms on complex, multi-step reasoning tasks while maintaining perfect accuracy.

---

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run evaluation suite
python experiments/run_extended_evaluation.py

# Performance profiling
python test_advanced.py
```

### Adding a New Tool

1. Create tool in `src/tools/`
2. Implement LangChain `Tool` interface
3. Register in agent's tool list
4. Add tests in `src/tools/__tests__/`

### Running Experiments

```bash
# Standard evaluation (20 questions)
python experiments/evaluate_agents.py

# Extended evaluation (50 tasks)
python experiments/run_extended_evaluation.py

# Advanced analysis
python experiments/advanced_analysis.py
```

---

## 🚀 Deployment

### Local Production

```bash
# Set production configuration
export FLASK_DEBUG=false
export SECRET_KEY=your-secure-secret-key
export SESSION_COOKIE_SECURE=true

# Run with production server
gunicorn --bind 0.0.0.0:5050 web_dashboard.app:app
```

### Docker

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start Ollama and pull model
RUN curl -sSL https://ollama.ai/install.sh | sh && \
    ollama pull llama3.2:latest

EXPOSE 5050

CMD ["python", "web_dashboard/app.py"]
```

### Cloud Deployment (Vercel/Render)

See `DEPLOYMENT.md` for detailed cloud deployment guides.

---

## 📈 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Dashboard home |
| `GET` | `/ask` | AI advisor interface |
| `POST` | `/api/ask` | Submit question to agent |
| `GET` | `/api/agent/:id` | Get agent details |
| `GET` | `/groceries` | Grocery price tracker |
| `GET` | `/savings` | Inflation-adjusted goals |
| `GET` | `/api/ssb/:dataset` | Query SSB data directly |

### Example API Call

```bash
curl -X POST http://localhost:5050/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the average electricity cost in Norway?",
    "agent_type": "react",
    "location": "Oslo"
  }'
```

Response:

```json
{
  "answer": "Average electricity cost in Norway is NOK 1.85/kWh...",
  "reasoning": [
    "Thought: Need current electricity prices from SSB...",
    "Action: get_ssb_data(table='Elektrisitet')",
    "Observation: Found average price NOK 1.85/kWh"
  ],
  "sources": ["SSB Table 01222: Electricity Prices"],
  "execution_time": "8.42s"
}
```

---

## 🎓 Research Background

This project is part of a **master's thesis** at the **Norwegian University of Life Sciences (NMBU)** exploring:

- **Explainable AI** in financial contexts using ReAct prompting
- **Comparative evaluation** of baseline vs structured reasoning agents
- **Norwegian household economics** using open government data
- **Transparency vs speed tradeoffs** in AI financial advisors

**Paper**: *"Agentic Financial Reasoning with Norwegian Open Data: A ReAct-Based Approach for Explainable Budget Analysis"*

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Areas needing help:**
- 🐛 Bug fixes
- 📈 Additional SSB data integrations
- 🎨 Frontend improvements
- 🧪 More evaluation scenarios
- 📝 Documentation improvements

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Statistics Norway (SSB)** - Providing open economic data
- **Ollama** - Local LLM infrastructure
- **LangChain** - Agent framework and tools
- **Flask Team** - Production-grade web framework
- **NMBU** - Academic supervision and resources

---

## 📧 Contact

**Author**: Srivatsav Saravanan
📧 srivatsav.saravanan@nmbu.no
🔗 [GitHub](https://github.com/Srivatsav1298)

For questions about the research or code, please open an issue.

---

## 🔗 Resources

- **Web Dashboard**: http://localhost:5050 (when running locally)
- **SSB Data Portal**: https://www.ssb.no/en/
- **Ollama Models**: https://ollama.ai/library
- **LangChain Docs**: https://python.langchain.com/

---

**Built with ❤️ at NMBU, Norway 🇳🇴 | Making Financial AI Transparent and Trustworthy**

[⬆ Back to top](#financial-ai-react-agent-)
