# Norfain ReAct Agent

Agentic AI system for Norwegian financial data using ReAct reasoning and SSB open data.

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your API key to `.env`:
```
ANTHROPIC_API_KEY=your_key_here
```

## Project Structure
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

## Quick Test
```bash
# Test SSB API
python src/utils/ssb_api.py

# Test tools
python src/tools/ssb_tools.py

# Test baseline agent
python src/agents/baseline.py
```

## Status

- [x] Day 1: SSB API integration ✅
- [x] Day 1: LangChain tools ✅
- [x] Day 1: Baseline agent ✅
- [ ] Day 2: ReAct agent
- [ ] Day 3: Evaluation framework
- [ ] Day 4-5: Testing & results
```

---

## **🎯 TOMORROW'S PLAN (Day 2)**

We'll build the **ReAct Agent** - the star of your paper!

### Tomorrow you'll create:
1. **ReAct reasoning loop** (Thought → Action → Observation)
2. **Multi-step tool orchestration**
3. **Reasoning trace capture**
4. **Comparison with baseline**

### Expected output:
```
User: "How much do families spend on housing compared to food?"

BASELINE: "Families spend about 15,000 on housing and 6,500 on food"
(No reasoning shown, vague source)

REACT AGENT:
THOUGHT: I need to find housing and food spending data
ACTION: get_average_spending_by_category("housing")
OBSERVATION: Housing = 15,234 NOK/month (SSB Table 10235)
THOUGHT: Now I need food spending
ACTION: get_average_spending_by_category("food")  
OBSERVATION: Food = 6,543 NOK/month (SSB Table 10235)
THOUGHT: Now I can compare them
ACTION: Calculate ratio: 15234 / 6543 = 2.33
ANSWER: "Norwegian families spend 2.3x more on housing (15,234 NOK/month)
than on food (6,543 NOK/month) according to SSB Household Budget 
Survey 2023 (Table 10235)"