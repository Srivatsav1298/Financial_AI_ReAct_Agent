# Financial AI ReAct Agent: Explainable Financial Reasoning with Norwegian Open Data

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.0-green.svg)](https://github.com/langchain-ai/langchain)
[![Conference Paper](https://img.shields.io/badge/Paper-AGI_Rank'or_2030-brightgreen)](https://github.com/Srivatsav1298/Financial_AI_ReAct_Agent)

## Overview

This repository presents a comparative study of AI agent architectures for Norwegian household financial guidance, evaluating **baseline** vs **ReAct** reasoning approaches. The project integrates with Statistics Norway (SSB) open data to provide transparent, evidence-based financial insights.

> 📄 **Conference Paper**: *Agentic Financial Reasoning with Norwegian Open Data: A ReAct-Based Approach for Explainable Budget Analysis*
> 🎓 **Institution**: NMBU, Norway
> 👤 **Author**: Srivatsav Saravanan
> 📧 **Contact**: srivatsav.saravanan@nmbu.no

---

## The Problem

Financial AI tools often operate as "black boxes," making it difficult for users to understand how recommendations are generated. This lack of transparency undermines trust—a critical factor in financial decision-making.

## Our Solution

We implement and evaluate two agent architectures:

| Architecture | Approach | Reasoning |
|---------------|----------|-----------|
| **Baseline Agent** | Single-step prompting | Minimal explanation |
| **ReAct Agent** | Thought → Action → Observation loops | Full reasoning trace |

**Key Finding**: ReAct significantly improves explainability without sacrificing accuracy, making financial AI more trustworthy and transparent.

---

## Key Features

- ✅ Dual agent implementation (Baseline vs ReAct)
- ✅ Integration with Statistics Norway (SSB) Household Budget Survey (Table 10235)
- ✅ Complete reasoning trace visualization for transparency
- ✅ Local LLM support via Ollama (Llama 3.2)
- ✅ Comprehensive evaluation suite (20 questions across 4 complexity categories)
- ✅ Fully reproducible experiments
- ✅ GDPR-compliant (no personal data)
- ✅ Real-time grocery price comparison across Norwegian retailers
- ✅ Basket-level optimization for cheapest store combinations
- ✅ Price normalization (per kg/unit) for fair comparisons
- ✅ Automated daily data updates with historical tracking
- ✅ Live currency conversion
- ✅ Smart recommendations based on price gaps

---

## Quick Start

### Prerequisites

- Python 3.13+
- [Ollama](https://ollama.ai/) with Llama 3.2 model
- [GitHub CLI](https://cli.github.com/) (optional, for repository operations)

### Installation

```bash
# Clone the repository
git clone https://github.com/Srivatsav1298/Financial_AI_ReAct_Agent
cd Financial_AI_ReAct_Agent

# Install dependencies
pip install -r requirements.txt
```

### Running the Agents

```bash
# Run baseline agent
python src/agents/baseline_agent.py

# Run ReAct agent (with reasoning trace)
python src/agents/react_agent.py

# Run evaluation suite
python experiments/evaluate_agents.py
```

---

## Project Structure

```
Financial_AI_ReAct_Agent/
├── src/
│   ├── agents/              # AI agent implementations
│   │   ├── baseline_agent.py
│   │   └── react_agent.py
│   ├── tools/               # LangChain tools for SSB API
│   │   └── ssb_tools.py
│   ├── utils/               # SSB API wrapper & caching
│   │   └── ssb_client.py
│   └── evaluation/          # Evaluation framework
│       └── evaluator.py
├── data/                    # Cached SSB data
├── experiments/             # Experiment scripts
├── results/                 # Evaluation outputs & traces
├── tests/                   # Unit & integration tests
├── docs/                    # Documentation
├── notebooks/               # Analysis notebooks
└── readme.md                # This file
```

---

## Experimental Results

### Performance Comparison (20 Questions)

| Metric | Baseline | ReAct | Δ |
|--------|----------|-------|---|
| **Avg Response Time** | 6.90s | 11.78s | +70.7% |
| **Tool Usage Rate** | 85% | 100% | +15% |
| **Avg Iterations** | N/A | 1.9 | — |
| **Reasoning Visibility** | 0 | 0.8 | — |
| **Error Rate** | 0% | 0% | — |

### Key Insights

- ✅ **ReAct provides full grounding**: 100% tool usage vs 85% for Baseline
- ✅ **Transparency**: ReAct generates explicit reasoning traces (avg 0.8 visibility score)
- ⚠️ **Speed trade-off**: ReAct is ~70% slower but still performant (<12s)
- ✅ **Adaptability**: ReAct adjusts reasoning depth based on question complexity
- ✅ **Accuracy**: Both achieve 0% error rate on test set

---

## Robustness Evaluation (50 Tasks)

An expanded evaluation covering complex scenarios including adversarial inputs, macroeconomic shocks, and multi-agent conflicts.

### Performance Highlights

| Task Type | ReAct Advantage | Baseline Limitation |
|-----------|-----------------|---------------------|
| **Diagnostic** | +60% (NT30) | Failed "Chronic Undersaving" |
| **Persona** | +20% (NT48) | Poor adherence to complex instructions |
| **Judgment** | +20% (NT2) | Nuanced lifestyle assessments |
| **Shock Response** | +10% (NT22) | Unexpected event handling |

**Conclusion**: ReAct excels in tasks requiring multi-step reasoning, persona adherence, and complex judgment, while Baseline remains efficient for simple information retrieval.

---

## Technology Stack

- **LLM Backend**: Ollama (Llama 3.2)
- **Framework**: LangChain
- **Data Source**: Statistics Norway (SSB) JSON-stat2 API
- **Language**: Python 3.13+
- **Caching**: Local JSON cache with TTL
- **Testing**: pytest

---

## Why ReAct for Financial AI?

1. **Transparency**: Users see the reasoning process, not just answers
2. **Trust**: Each recommendation is grounded in verified SSB data
3. **Explainability**: Full audit trail for regulatory compliance
4. **Adaptability**: Handles simple queries and complex multi-step analysis
5. **Robustness**: Better performance on edge cases and adversarial inputs

---

## Contributing

We welcome contributions! Please feel free to:

- 🐛 Report issues
- 🔧 Submit pull requests
- 📝 Suggest improvements to the evaluation framework
- 🧪 Add new test cases

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

---

## Future Work

- [x] Complete 50-task robustness evaluation
- [ ] User study in Norway (planning phase)
- [ ] Real-time SSB API integration (prototype)
- [ ] Multi-language support (Norwegian Bokmål/Nynorsk)
- [ ] Web interface for non-technical users
- [ ] Integration with personal banking data (with user consent)

---

## Acknowledgments

- **Statistics Norway (SSB)** for open data access
- **Ollama** for local LLM infrastructure
- **LangChain** for agent framework
- **NMBU** for research support

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Citation

If you use this work in your research, please cite:

```bibtex
@inproceedings{saravanan2025react,
  title={Agentic Financial Reasoning with Norwegian Open Data: A ReAct-Based Approach for Explainable Budget Analysis},
  author={Saravanan, Srivatsav},
  booktitle={AGI Rank'or 2030 Conference},
  year={2025},
  institution={NMBU, Norway}
}
```

---

## Contact

**Srivatsav Saravanan**
📧 srivatsav.saravanan@nmbu.no
🔗 [LinkedIn](https://linkedin.com/in/srivatsav) | [GitHub](https://github.com/Srivatsav1298)
