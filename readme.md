# Norfain ReAct Agent: Agentic Financial Reasoning with Norwegian Open Data

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.0-green.svg)](https://github.com/langchain-ai/langchain)

**A comparative study of baseline vs ReAct reasoning for explainable financial AI using Norwegian household data.**

> 📄 **Conference Paper**: *Agentic Financial Reasoning with Norwegian Open Data: A ReAct-Based Approach for Explainable Budget Analysis*  
> 🎓 **Institution**: NMBU, Norway  
> 👤 **Author**: Srivatsav Saravanan  
> 📧 **Contact**: srivatsav.saravanan@nmbu.no

---

### Overview

This project implements and evaluates two AI agent architectures for Norwegian household financial guidance:

1. **Baseline Agent** – Simple prompting with a single tool call  
2. **ReAct Agent** – Explicit reasoning using Thought → Action → Observation loops  

Both agents integrate with **Statistics Norway (SSB)** open data (Household Budget Survey, Table 10235) for accurate, evidence-based financial insights.

### Research Motivation

Financial AI tools must be **transparent** and **trustworthy**. This project demonstrates that **explicit reasoning (ReAct)** boosts explainability without reducing accuracy: addressing the “black box” issue in financial AI assistants.

---

### Key Features

- Dual agent architecture (Baseline vs ReAct)  
- Integration with official SSB household spending data  
- Full ReAct reasoning trace for transparency  
- Local LLM support via Ollama (Llama 3.2)  
- 20-question evaluation (4 complexity categories)  
- Reproducible experiments  
- GDPR-compliant (no personal data)

---

### Components

- **SSB API Wrapper** – caching, JSON-stat2 parsing  
- **Tools** – `get_average_spending`, `compare_categories`, etc.  
- **Baseline Agent** – single-step prompting  
- **ReAct Agent** – iterative reasoning

---

### Results Summary

### Performance Overview

| Metric | Baseline | ReAct | Difference |
|--------|----------|-------|------------|
| Avg Response Time | 6.90s | 11.78s | +70.7% |
| Tool Usage Rate | 85% | 100% | +15% |
| Iterations | N/A | 1.9 | +1.9 |
| Reasoning Visibility | 0 | 0.8 | +0.8 |
| Error Rate | 0% | 0% | — |

### Key Insights

- **ReAct = higher transparency & perfect grounding**  
- **Baseline = faster but sometimes skips tools**  
- **ReAct adapts to question complexity**  
- **Both agents achieve 0% error rate**

---

### Project Structure
```
norfain-react-agent/
├── src/
│   ├── agents/          # AI agents (baseline & ReAct)
│   ├── tools/           # LangChain tools for SSB
│   ├── utils/           # SSB API wrapper
│   └── evaluation/      # Evaluation framework
├── data/                # Cached SSB data
├── experiments/         # Experiment scripts
└── results/             # Evaluation results
```


### Research Findings

- ReAct significantly improves explainability.
- Slower responses are acceptable in financial.
- Complete data grounding using SSB ensures trustworthiness
- Adaptive reasoning improves performance on complex queries

### Future Work
- Larger evaluation dataset
- User study in Norway
- Real-time SSB integration

### Acknowledgments
- Statistics Norway (SSB)
- Ollama
- LangChain
