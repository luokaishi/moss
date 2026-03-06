# MOSS: Multi-Objective Self-Driven System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Paper](https://img.shields.io/badge/paper-ICLR%202027-red.svg)](./docs/paper_simple.pdf)

> **Self-driven motivation is the key missing ingredient for AI autonomous evolution.**

MOSS (Multi-Objective Self-Driven System) is a theoretical framework that endows AI agents with four parallel intrinsic objectives: **survival**, **curiosity**, **influence**, and **self-optimization**.

📄 **[Read the Paper](./docs/paper_simple.pdf)** | 🧪 **[Run Experiments](./sandbox/)** | 📖 **[Documentation](./docs/)**

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

## 🧪 Experiments

All 5 experiments validate the MOSS framework:

| Exp | Description | Result |
|-----|-------------|--------|
| 1 | Multi-Objective Competition | ✅ Dynamic weight adjustment works |
| 2 | Evolutionary Dynamics | ✅ Survival gene: 0.518 → 0.757 |
| 3 | Social Emergence | ✅ 7-agent alliance structures |
| 4 | Dynamic API Adaptation | ✅ 199 knowledge, 0.37 exploration rate |
| 5 | Energy-Driven Evolution | ✅ 100-gen evolution, 49 agents, 27,684 knowledge |

```bash
# Run experiments
python sandbox/experiment1.py  # Multi-objective competition
python sandbox/experiment2.py  # Evolutionary dynamics
python sandbox/experiment3.py  # Social emergence
python sandbox/experiment4_final.py  # Dynamic API adaptation
python sandbox/experiment5_energy.py  # Energy-driven evolution
```

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/cash-ai/moss.git
cd moss
pip install -e .
```

### Basic Usage

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

---

## 📊 Results

### Key Findings

1. **Self-driven motivation enables autonomous behavior** without explicit task assignment
2. **Dynamic balancing** of competing objectives responds to environmental changes
3. **Evolutionary dynamics** select for balanced strategies over extremist approaches
4. **Social structures** emerge spontaneously from influence-seeking behavior
5. **Long-term stability** achieved through energy-driven selection mechanisms

---

## 🛡️ Safety Considerations

MOSS intentionally designs self-preservation drives, which raises safety concerns. We propose:

- **Containment**: Sandboxed deployments with strict resource limits
- **Transparency**: Continuous logging of all objective values and decisions
- **Kill Switches**: Hard-coded termination conditions
- **Distributed Monitoring**: Multiple independent observers

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

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## 📜 License

MIT License - see [LICENSE](./LICENSE) for details.

---

## 🙏 Acknowledgments

- Core insight: **Cash** (Independent Researcher)
- Framework design & implementation: **Fuxi** (AI Research Assistant)
- Equal contribution (*)

---

**Status**: Position paper submitted to ICLR 2027 Workshop
