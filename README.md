# MOSS v6.1 - Multi-Objective Self-Driven System

> **Production-Ready AGI Emergence Research Framework**
>
> An autonomous AI agent that operates without external tasks, discovering and evolving its own drive functions through genetic programming and self-organization.

[![CI](https://github.com/luokaishi/moss/actions/workflows/ci.yml/badge.svg)](https://github.com/luokaishi/moss/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-6.1.0-green.svg)](https://github.com/luokaishi/moss/releases)

---

## What is MOSS?

**MOSS** (Multi-Objective Self-Driven System) is a research framework exploring whether AI systems can develop **intrinsic motivations** without task-specific reward signals.

### Key Research Question

> Can AI systems autonomously generate and maintain behavioral drives without externally defined tasks?

### Core Innovation

Unlike traditional AI systems that rely on external rewards or task definitions, MOSS:
- **Operates without external tasks** - No human-defined objectives
- **Self-generates drives** - Discovers new motivations through genetic programming
- **Self-organizes behavior** - Emergent patterns from drive competition
- **Self-validates emergence** - Built-in falsification and verification

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/luokaishi/moss.git
cd moss

# Install dependencies
pip install -e .

# Or install with full features (recommended)
pip install -e ".[full]"
```

### Run Demo

```bash
# Quick 200-cycle demo (~10 seconds)
python demo.py

# Full experiment (10,000 cycles)
python examples/run_experiment.py --cycles 10000

# With visualization
python examples/run_experiment.py --cycles 5000 --visualize
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_agi_core.py -v
```

---

## Core Features

### 1. Multi-Drive Architecture

Four initial drives with dynamic weight adaptation:

| Drive | Initial Weight | Description |
|-------|---------------|-------------|
| **Survival** | 0.30 → 0.60 | Resource maintenance, system health |
| **Curiosity** | 0.25 → 0.14 | Exploration, novelty seeking |
| **Influence** | 0.25 → 0.14 | External interactions, task completion |
| **Optimization** | 0.20 → 0.11 | Efficiency, self-improvement |

### 2. Emergent Drive Discovery

Genetic Programming-based emergence detection:
- **Automatic detection** of behavioral pattern shifts
- **GP evolution** of new eval functions
- **Triple validation**: correlation, behavioral gain, null model
- **Causal verification** through intervention experiments

### 3. Drive Competition System

Natural selection among drives:
- **Probation period**: 500-cycle evaluation window
- **Performance-based adaptation**: Reward-driven weight updates
- **Elimination mechanism**: Drives below 0.02 weight are removed
- **Weight caps**: Prevent dominance (survival ≤ 30%, emergent ≤ 35%)

### 4. Self-Modeling & Meta-Cognition

7-layer AGI emergence architecture:
- **Layer 7**: Concept System - State compression & abstraction
- **Layer 6**: Goal System - Trajectory pattern extraction
- **Layer 5**: Drive System - Intrinsic motivation (existing)
- **Layer 4**: Meta-Drive - Self-modification of drives
- **Layer 3**: Self-Model - Self-prediction (89.6% accuracy)
- **Layer 2**: Ecology - Multi-agent competition
- **Layer 1**: Policy/Action - Behavior execution

---

## Key Results

### Long-Term Stability (100K+ Cycles)

| Metric | Value |
|--------|-------|
| Total cycles | 100,000+ |
| Runtime | 173.87 seconds |
| Speed | 575 cycles/second |
| Memory usage | 77.05 MB |
| Emergence persistence | 100% |
| Emergence weight | 0.35 (35%) |

### Cross-Seed Validation (3 seeds)

| Metric | Seed 42 | Seed 123 | Seed 456 | Consistency |
|--------|---------|----------|----------|-------------|
| Emergence detected | ✓ | ✓ | ✓ | 100% |
| Emergence weight | 0.35 | 0.35 | 0.35 | 100% |
| Survival weight | 0.30 | 0.30 | 0.30 | 100% |

### Emergence Detection Rate

- **computational_mastery**: 86% detection rate across 7 experiments
- **systematic_exploration**: 57% detection rate
- **Average emergence weight**: 0.20-0.35

---

## Architecture

```
agi/
├── agent.py                 # Main agent loop
├── drive_manager.py         # Multi-drive weight management
├── drive_competition.py     # Drive competition & elimination
├── drive_weight_cap.py      # Weight limit enforcement
├── emergence_detector.py    # Behavior change detection
├── genetic_programmer_v3.py # GP-based drive evolution
├── concept/                 # Layer 7: Concept system
├── goal/                    # Layer 6: Goal system
├── meta_drive/              # Layer 4 & 3: Meta-cognition
├── ecology/                 # Layer 2: Multi-agent system
└── analysis/                # Interpretability tools
```

---

## Documentation

### Getting Started

- [Installation Guide](docs/mves/INSTALLATION.md)
- [Quick Start Tutorial](docs/mves/QUICKSTART.md)
- [Interactive Visualization Guide](docs/mves/interactive_visualization_guide.md)

### Research Documentation

- [MOSS v6.1 Release Notes](docs/mves/v6.1_RELEASE_NOTES.md)
- [Long-term Stability Report](docs/mves/v6_longterm_stability_report.md)
- [Meta-Analysis Report (57K cycles)](docs/mves/meta_analysis_57k_data.md)
- [Meta-Drive Falsification Report](docs/mves/meta_drive_falsification_report.md)

### API Documentation

- [API Reference](docs/api/)
- [Tutorial Notebooks](notebooks/)
  - [01 Quick Start](notebooks/tutorial_01_quickstart.ipynb)
  - [02 Custom Drives](notebooks/tutorial_02_custom_drives.ipynb)
  - [03 Emergence Analysis](notebooks/tutorial_03_emergence_analysis.ipynb)

---

## Research & Publications

### Scientific Validation

| Validation Type | Status | Evidence |
|----------------|--------|----------|
| Pre-registration | Complete | H1/H2/H3 hypotheses defined |
| Cross-seed validation | Complete | 3 seeds, 100% consistency |
| Meta-analysis | Complete | 36,907 cycles analyzed |
| Falsification tests | Complete | Meta-drive validated |
| Long-term stability | Complete | 100K cycles verified |
| External benchmark | Partial | TextWorld integration |

### Key Findings

1. **Survival Dominance**: Survival drive naturally becomes the dominant attractor (weight 0.60) consistent with evolutionary theory and active inference frameworks

2. **Emergence Persistence**: Emergent drives maintain stable weights (0.20-0.35) over 100K+ cycles

3. **Self-Model Accuracy**: Conditional self-model achieves 89.6% prediction accuracy (vs 12% for unconditional)

4. **Goal Emergence**: System spontaneously extracts stable goals (explore/exploit) with >99% stability

---

## Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
flake8 agi/ --max-line-length=100

# Run type checking
mypy agi/

# Run tests with coverage
pytest tests/ --cov=agi --cov-report=html
```

### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Key areas for contribution:
- Performance optimization
- Additional visualization tools
- New emergence detection algorithms
- External environment integrations
- Documentation improvements

---

## Repository Structure

```
moss/
├── agi/                    # Core AGI modules
├── tests/                  # Unit tests (81 tests)
├── examples/               # Example scripts
├── scripts/                # Analysis & visualization tools
├── notebooks/              # Jupyter tutorials
├── docs/                   # Documentation
│   ├── mves/              # Research documentation
│   ├── api/               # API documentation
│   └── paper/             # Paper materials
├── logs/                   # Experiment logs
├── config/                 # Configuration files
└── .github/workflows/      # CI/CD configurations
```

---

## Citation

If you use MOSS in your research, please cite:

```bibtex
@software{moss2026,
  title={MOSS: Multi-Objective Self-Driven System},
  author={MOSS Team},
  year={2026},
  url={https://github.com/luokaishi/moss}
}
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Inspired by research in artificial life, self-organization, and active inference
- Built with Python, NumPy, and open-source scientific computing tools
- Thanks to all contributors and the research community

---

**Maintainer**: MOSS Team  
**Repository**: https://github.com/luokaishi/moss  
**Issues**: https://github.com/luokaishi/moss/issues
