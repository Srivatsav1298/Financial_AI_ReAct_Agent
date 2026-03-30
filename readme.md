# Norfain | Agentic Financial Reasoning & Retail Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.0-green.svg)](https://github.com/langchain-ai/langchain)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.0-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

**Norfain** is an end-to-end financial intelligence platform that bridges the gap between raw economic data and actionable consumer insights. Developed as part of a research initiative at **NMBU, Norway**, it combines advanced **ReAct (Reasoning & Acting)** AI architectures with live Norwegian retail data.

---

## 🚀 Key Modules & Features

### 🛒 **Matbørsen | Retail Intelligence**
A market basket analysis engine designed to fight food inflation in Norway.
- **Receipt Extraction:** Automated ingestion of unstructured grocery receipts via **Tesseract OCR**.
- **Entity Resolution:** Fuzzy matching algorithms map messy receipt strings to standardized SKUs across **5+ major supermarket chains** (Kiwi, Rema 1000, Meny, etc.).
- **Live Price Tracker:** Real-time comparison engine for thousands of grocery products.

### 🧠 **Agentic Financial Advisor**
A comparative study of AI reasoning methods for financial guidance.
- **ReAct Agent:** An iterative "Thought → Action → Observation" loop that ensures explainability and grounding.
- **Baseline Agent:** High-speed direct response module for simple data retrieval.
- **SSB Integration:** All insights are strictly verified against **Statistics Norway (SSB)** Consumer Price Index (CPI) and household spending datasets.

### 💰 **Wealth & Savings Tracker**
- **Inflation-Adjusted Goals:** Automatically adjusts your savings targets based on live Norwegian inflation indices.
- **Prisjakt Integration:** Curated price tracking for electronics and consumer goods.
- **Seasonal Year-Wheel (Årshjul):** Strategic financial planning based on Norwegian fiscal cycles (Halv Skatt, Feriepenger, Skattemelding).

---

## 🛠️ Tech Stack

- **Frontend:** HTML5, **Tailwind CSS**, Vanilla JavaScript (ES6+), Chart.js (Data Visualization).
- **Backend:** **Python (Flask)**, REST API Architecture.
- **AI/ML:** **LangChain**, ReAct Reasoning Framework, Local LLMs (via Ollama).
- **Data:** **SSB API** (JSON-stat2), yfinance, pyTesseract (OCR), FuzzyWuzzy.

---

## 🔬 Scientific Evaluation

The platform includes a rigorous evaluation framework comparing Baseline vs. ReAct reasoning across **50 complex financial tasks**.

| Metric | Baseline | ReAct | Difference |
|--------|----------|-------|------------|
| Avg Response Time | 6.90s | 11.78s | +70.7% |
| Tool Usage Rate | 85% | 100% | +15% |
| Reasoning Visibility | 0 | 100% | +100% |

**Key Finding:** While ReAct introduces a latency overhead, it provides **100% transparent reasoning traces**, which is critical for building user trust in "Black Box" financial applications.

---

## 📂 Project Structure

```bash
norfain/
├── src/
│   ├── agents/          # AI agents (baseline & ReAct)
│   ├── tools/           # LangChain tools for SSB & Retail
│   └── utils/           # SSB API wrapper & matching logic
├── experiments/
│   └── web_dashboard/   # Norfain Web Dashboard (Full Product)
├── results/             # Evaluation & Benchmark reports
└── paper/               # Research paper & documentation
```

---

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Srivatsav1298/Financial_AI_ReAct_Agentt.git
   cd Financial_AI_ReAct_Agentt
   ```

2. **Setup virtual environment:**
   ```bash
   python -m venv nvenv
   source nvenv/bin/python/activate  # On MacOS/Linux
   pip install -r requirements.txt
   ```

3. **Run the Advanced Web Dashboard:**
   ```bash
   cd experiments/web_dashboard
   python app.py
   ```
   Visit `http://localhost:5050` to interact with the platform.

---

## 📄 Authorship & Acknowledgments

- **Author:** Srivatsav Saravanan ([srivatsav.saravanan@nmbu.no](mailto:srivatsav.saravanan@nmbu.no))
- **Institution:** Norwegian University of Life Sciences (NMBU)
- **Data Source:** Statistics Norway (SSB)
- **Tools:** Special thanks to the teams behind LangChain, Ollama, and Tailwind CSS.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.
