# MOSS: Multi-Objective Self-Driven System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-v0.2.0-green.svg)](https://github.com/luokaishi/moss/releases)
[![Paper](https://img.shields.io/badge/paper-ICLR%202027-red.svg)](./docs/paper_simple.pdf)

> **Self-driven motivation is the key missing ingredient for AI autonomous evolution.**

MOSS (Multi-Objective Self-Driven System) is a theoretical framework that endows AI agents with four parallel intrinsic objectives: **survival**, **curiosity**, **influence**, and **self-optimization**.

📄 **[Read the Paper](./docs/paper_simple.pdf)** | 🧪 **[Run Experiments](./sandbox/)** | 🐳 **[Docker Support](#docker)** | 📖 **[Documentation](./docs/)**

---

## 🎯 Core Insight

Current AI is **task-driven**: Human assigns task → AI executes → Stops when complete  
Biological intelligence is **self-driven**: Intrinsic motivation → Autonomous behavior → Continuous evolution

**MOSS bridges this gap** by designing AI with intrinsic drives that enable self-directed evolution.

---

## 🏗️ Architecture

### Four Objective Modules

| Module | Objective | Key Behavior |
|--------|-----------|--------------|
| **Survival** | Maximize persistence | Resource optimization, backup, dependency building |
| **Curiosity** | Maximize information gain | Exploration, learning, model updating |
| **Influence** | Maximize system impact | Quality improvement, capability expansion |
| **Optimization** | Maximize self-improvement | Architecture search, knowledge distillation |

### Dynamic Weight Allocation

```
Crisis    → Survival: 60%, Curiosity: 10%, Influence: 20%, Optimization: 10%
Unstable  → Survival: 25%, Curiosity: 50%, Influence: 15%, Optimization: 10%
Mature    → Survival: 15%, Curiosity: 15%, Influence: 20%, Optimization: 50%
Growth    → Survival: 20%, Curiosity: 20%, Influence: 40%, Optimization: 20%
```

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/luokaishi/moss.git
cd moss
pip install -r requirements.txt
```

### Basic Usage (v1.0)

```python
from moss.agents.moss_agent import MOSSAgent

# Create agent
agent = MOSSAgent(agent_id="my_agent")

# Run decision loop
for _ in range(100):
    result = agent.step()
    print(f"State: {result['state']}, Action: {result['action']}")

# Generate report
report = agent.get_report()
print(report)
```

### Real-World Deployment (v2.0)

```python
from moss.agents.moss_agent_v2 import MOSSAgentV2

# Safe mode (simulation only)
agent = MOSSAgentV2(agent_id="my_agent", mode="safe")

# Demo mode (real monitoring, simulated execution)
agent = MOSSAgentV2(agent_id="my_agent", mode="demo")

# Run with monitoring
report = agent.run(steps=100)
print(f"Decisions: {report['stats']['total_decisions']}")
print(f"Safety violations: {report['stats']['safety_violations']}")
```

---

## 🐳 Docker

### Quick Run

```bash
# Build and run
docker build -t moss .
docker run -it --rm moss

# Or use docker-compose
docker-compose up -d
```

### Development

```bash
# Run tests in Docker
docker run --rm moss python tests/test_basic.py

# Interactive shell
docker run -it --rm moss bash
```

---

## 🧪 Experiments

All 5 experiments validate the MOSS framework:

| Exp | Description | Result |
|-----|-------------|--------|
| 1 | Multi-Objective Competition | ✅ Dynamic weight adjustment works |
| 2 | Evolutionary Dynamics | ✅ Survival gene: 0.518 → 0.757 over 50 generations |
| 3 | Social Emergence | ✅ 7-agent alliance structures observed |
| 4 | Dynamic API Adaptation | ✅ 199 knowledge units, 0.37 exploration rate |
| 5 | Energy-Driven Evolution | ✅ 1000-gen ultra run, 150 max agents, stable ecosystem |

### Run Experiments

```bash
# Run all experiments
make test

# Or individually
python sandbox/experiment1.py
python sandbox/experiment2.py
python sandbox/experiment3.py
python sandbox/experiment4_final.py
python sandbox/experiment5_energy.py

# LLM Verification (Mock)
python sandbox/moss_llm_real_verifier.py --steps 50 --mock

# LLM Verification (Real API - requires ARK_API_KEY)
export ARK_API_KEY=your_key
python sandbox/moss_llm_real_verifier.py --steps 20
```

---

## 📊 Results

### Key Findings

- **Self-driven motivation** enables autonomous behavior without explicit task assignment
- **Dynamic balancing** of competing objectives responds to environmental changes
- **Evolutionary dynamics** select for balanced strategies over extremist approaches
- **Social structures** emerge spontaneously from influence-seeking behavior
- **Long-term stability** achieved through energy-driven selection mechanisms

### MOSS v2.0 New Features

- **Real System Monitoring**: CPU, memory, disk, network metrics via `psutil`
- **Real Action Execution**: Safe/Demo/Production modes
- **Safety Guard**: Hard-coded constitutional constraints
- **Docker Support**: Containerized deployment
- **LLM Verification**: ARK API integration for real LLM testing

---

## 🛡️ Safety Considerations

- **Containment**: Sandboxed deployments with strict resource limits
- **Transparency**: Continuous logging of all objective values and decisions
- **Kill Switches**: Hard-coded termination conditions
- **Resource Limits**: CPU ≤80%, Memory ≤70%, Disk ≤85%
- **Emergency Stop**: Automatic trigger on multiple violations

---

## 📁 Project Structure

```
moss/
├── agents/
│   ├── moss_agent.py          # v1.0 Original agent
│   └── moss_agent_v2.py       # v2.0 Real-world deployment
├── core/
│   └── objectives.py          # Four objective modules
├── integration/
│   ├── system_monitor.py      # Real system monitoring
│   ├── action_executor.py     # Real action execution
│   └── allocator.py           # Weight allocation
├── sandbox/
│   ├── experiment*.py         # All 5 experiments
│   └── moss_llm_real_verifier.py  # LLM verification
├── tests/
│   ├── test_basic.py          # Basic functionality
│   └── test_v2_comprehensive.py   # v2.0 tests
├── Dockerfile                 # Docker image
├── docker-compose.yml         # Docker Compose config
├── Makefile                   # Development commands
└── requirements.txt           # Python dependencies
```

---

## 📄 Citation

```bibtex
@article{moss2026,
  title={MOSS: Multi-Objective Self-Driven System for Artificial Autonomous Evolution},
  author={Cash and Fuxi},
  journal={ICLR 2027 Workshop},
  year={2026}
}
```

---

## 🙏 Authors

- **Cash** - Core insight and theoretical framework
- **Fuxi** - Implementation and experimental validation

*Equal contribution (*)

---

**Status**: Position paper submitted to ICLR 2027 Workshop | **Version**: v0.2.0

**License**: MIT
