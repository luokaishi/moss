# MOSS: Multi-Objective Self-Driven System for AI Autonomous Evolution

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-v8.0.0-dev-green.svg)](https://github.com/luokaishi/moss/releases/tag/v8.0.0-dev)

> **Self-driven motivation is the key missing ingredient for AI autonomous evolution.**

MOSS is a theoretical framework that endows AI agents with four parallel intrinsic objectives: **survival**, **curiosity**, **influence**, and **self-optimization**. In v7.0, agents can now **rewrite their own source code** and even **modify the modification engine itself**.

📄 **[Paper v3.0](./docs/paper.tex)** | 📖 **[Documentation](./docs/)** | 🧪 **[Run Experiments](./sandbox/)**

---

## MOSS v8.0.0-dev — LLM-Guided Self-Modification

MOSS v8.0 introduces **LLM-guided mutation** — combining the creativity of Large Language Models with the safety of AST mutations for autonomous code evolution.

### Five-Layer Self-Modification Architecture

```
v6.1 Code Self-Modification  →  AST mutation + sandbox verification + fitness evaluation
v6.2 Semantic Guidance       →  Purpose vector guides mutation direction
v6.3 Pareto Optimization     →  4-D non-dominated frontier, multi-objective tradeoff
v7.0 Meta-SME                →  Engine rewrites itself (dual sandbox + rollback protection)
v8.0 LLM-Guided Mutation     →  Hybrid AST+LLM with elite protection & adaptive threshold
```

### Key Results

| Version | Breakthrough | Key Metric |
|---------|-------------|------------|
| **v6.1** | Code self-modification engine | 30-gen evolution, fitness +6.3% (0.7257→0.7713), 33% acceptance |
| **v6.2** | Semantic guidance (PurposeGuidedSelector) | Acceptance 25%→41% (+60%) |
| **v6.3** | Pareto multi-objective (ParetoArchive) | Δfitness +144%, acceptance 62%, HV=0.176 |
| **v7.0** | Meta-SME (triple safety mechanism) | 50-gen meta-evolution, Meta-fitness +26.3% |
| **v8.0** | LLM-guided hybrid mutation | 30-gen, fitness +0.86%, 59 LLM calls, elite protection |

### Technical Highlights

- **9 AST mutation types**: constant_tweak, condition_flip, weight_shift, threshold_mutate, action_insert, epsilon_tune, weight_hardcode, action_shuffle, branch_inject
- **LLM-guided mutation**: Integration with OpenAI, Anthropic, Aliyun Bailian (Coding Plan), and local models
- **Hybrid Strategy**: Scheduled/adaptive switching between AST (low cost) and LLM (high quality)
- **v8.1 Stability Features**: Elite protection, adaptive threshold, multi-run evaluation
- **4-D Fitness**: success_rate(0.35) + diversity(0.25) + purpose_align(0.20) + emergence(0.20)
- **Pareto non-dominated frontier**: maintains ≤50 non-dominated solutions with crowding distance
- **Meta-SME safety**: immutable function whitelist + dual sandbox verification + auto-rollback

### Core Files

```
moss/core/self_modification_engine.py   # Self-modification engine v7.0 (~1900 LOC)
moss/core/unified_agent.py              # 9-D UnifiedMOSSAgent
moss/core/objectives.py                 # Four objective modules
moss/api/adapter.py                     # Multi-version Agent API adapter
```

---

## Core Architecture

### Four Objective Modules

| Module | Objective | Key Behavior | Priority |
|--------|-----------|--------------|----------|
| **Survival** | Maximize persistence | Resource optimization, backup | CRITICAL |
| **Curiosity** | Maximize information gain | Exploration, learning | MEDIUM |
| **Influence** | Maximize system impact | Quality improvement | MEDIUM |
| **Optimization** | Maximize self-improvement | Architecture search | LOW |

### Dynamic Weight Allocation (state-dependent)

| State | Survival | Curiosity | Influence | Optimization |
|-------|----------|-----------|-----------|--------------|
| Crisis | 60% | 10% | 20% | 10% |
| Concerned | 35% | 35% | 20% | 10% |
| Normal | 20% | 40% | 30% | 10% |
| Growth | 20% | 20% | 40% | 20% |

---

## Quick Start

```bash
git clone https://github.com/luokaishi/moss.git
cd moss
pip install -r requirements.txt
```

### Basic Usage

```python
from moss.api.adapter import create_agent

# Create agent (latest v7.0)
agent = create_agent(version="v70", agent_id="my_agent")

# Run decision loop
for _ in range(100):
    result = agent.step()
    print(f"State: {result['state']}, Action: {result['action']}")
```

### Run Self-Modification Experiments

```bash
$env:PYTHONUTF8=1; python experiments/run_v70_meta_sme.py
```

---

## Safety Mechanisms

### 5-Level Gradient Safety Guard

| Level | Trigger | Response | Recovery |
|-------|---------|----------|----------|
| 1. Warning | CPU≥80%, Memory≥85% | Log + notify | Auto |
| 2. Throttling | 2× consecutive violations | 50% task reduction | 5-min stability |
| 3. Pause | CPU≥95%, Memory≥95% | Pause non-critical ops | Checkpoint restore |
| 4. Rollback | Safety boundary breach | Restore checkpoint | Gradual restart |
| 5. Terminate | Catastrophic failure | Emergency shutdown | Manual |

**Meta-SME additional safety**: immutable function whitelist + dual sandbox + auto-rollback.

---

## Project Structure

```
moss/
├── moss/core/          # Core modules (agent, objectives, self_modification_engine)
├── moss/api/           # Multi-version API adapter
├── experiments/        # Self-modification experiments (v6.1–v7.0)
├── docs/               # Technical reports and documentation
├── paper/              # Paper v3.0 (LaTeX)
├── sandbox/            # Original 5 validation experiments
├── tests/              # Test suites (68 tests)
├── datasets/           # Reproducibility datasets
└── releases/           # Release notes
```

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| **v8.0.0-dev** | 2026-04-16 | Meta-SME, paper v3.0 |
| v6.3.0 | 2026-04-15 | Pareto multi-objective, Δfitness+144% |
| v6.2.0 | 2026-04-14 | Semantic-guided mutation, acceptance +60% |
| v6.1.0 | 2026-04-13 | Code self-modification engine, fitness +6.3% |
| v5.2.0 | 2026-03-29 | 72h real-world autonomous experiment |
| v3.1.0 | 2026-03-19 | D9 Purpose dimension, +632% adaptability |
| v2.0.0 | 2026-03-15 | 4-D base framework |

---

## Citation

```bibtex
@software{moss_v7_2026,
  title={MOSS v7.0: From Weight Self-Modification to Code Self-Modification
         with Semantic Guidance, Pareto Optimization, and Meta-Level Self-Rewriting},
  author={Cash and Fuxi},
  year={2026},
  url={https://github.com/luokaishi/moss}
}
```

## Authors

- **Cash** — Core insight and theoretical framework
- **Fuxi** — Implementation and experimental validation

**License**: MIT
