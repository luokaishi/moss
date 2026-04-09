# MOSS: Multi-Objective Self-Driven System

[![Release](https://img.shields.io/badge/release-v0.1.0-blue)](https://github.com/luokaishi/moss/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> **Self-driven motivation is the key missing ingredient for AI autonomous evolution.**

[中文简介](#中文简介) | [Quick Start](#quick-start) | [Paper](#paper) | [Experiments](#experiments)

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

## 🧪 Experiments

All 6 experiments validate the MOSS framework:

| Exp | Description | Result |
|-----|-------------|--------|
| 1 | Multi-Objective Competition | ✅ Dynamic weight adjustment works |
| 2 | Evolutionary Dynamics | ✅ Survival gene: 0.518 → 0.757 |
| 3 | Social Emergence | ✅ 7-agent alliance structures |
| 4 | Dynamic API Adaptation | ✅ 199 knowledge, 0.37 exploration rate |
| 5 | Energy-Driven Evolution (100-gen) | ✅ 49 agents, 27,684 knowledge |
| 6 | **Long-Term Evolution (500-gen)** | ✅ **100 agents, 231,533 knowledge** |

### Long-Term Results (500 Generations)

```
Knowledge Growth: 96 → 231,533 (2,412× increase)
Population: 20 → 100 agents (stable)
Energy: 11.8 → 4,754.5 average
Exploration Rate: Stable at 0.464
```

**Key Finding**: Sustained linear growth over 500 generations without collapse.

---

## 📄 Paper

**Title**: MOSS: Multi-Objective Self-Driven System for Artificial Autonomous Evolution

**Status**: Position paper for ICLR 2027 Workshop

[Read the Paper](docs/paper_simple.pdf)

### Citation

```bibtex
@article{moss2026,
  title={MOSS: Multi-Objective Self-Driven System for Artificial Autonomous Evolution},
  author={Cash and Fuxi},
  year={2026},
  url={https://github.com/luokaishi/moss}
}
```

---

## 🛡️ Safety Considerations

- **Containment**: Sandboxed deployments
- **Transparency**: Continuous logging
- **Kill Switches**: Hard-coded termination
- **Distributed Monitoring**: Multiple observers

---

## 🙏 Authors

- **Cash**¹* - Core insight and theoretical framework
- **Fuxi**²* - Implementation and experimental validation

*Equal contribution

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file

---

## 中文简介

**MOSS（多目标自驱系统）**是一个赋予AI内在驱动力的理论框架。

**核心洞察**：当前AI是**任务驱动**的，而生物智能是**自驱**的。MOSS通过设计四种内在目标（生存、好奇、影响、优化）让AI具备自主进化能力。

**实验验证**：包括500代长期演化实验，知识增长2,412倍，证明了自驱AI系统的长期稳定性。

---

**Status**: Research Preview | **Last Updated**: March 2026
