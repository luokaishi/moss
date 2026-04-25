# MOSS v9.6.0 🌿

**M**ulti-**O**bjective **S**elf-Driven **S**ystem

> *Evolved from autonomous agent research to intelligent code refactoring*
> 
> **v9.6.0**: Unified architecture - MVES v8.6 fully merged into `moss/core`

[![Version](https://img.shields.io/badge/version-9.6.0-blue.svg)](https://github.com/moss-devtools/moss)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> AI-powered code refactoring, analysis, and quality insights for Python

## ✨ Features

### 🚀 Performance
- Incremental analysis with multi-level caching (L1/L2/L3)
- Parallel processing utilizing all CPU cores (~127 files/sec tested on standard hardware)
- Hot cache analysis for repeated scans

### 🔧 Refactoring
- Cross-file refactoring with dependency analysis
- Intelligent code extraction and movement
- Safe refactoring with transaction rollback
- Import organization and optimization

### 💡 Intelligence
- ML-powered refactoring recommendations based on historical data
- Code pattern learning and anti-pattern detection
- Project-specific best practices

### 🤖 Autonomous Agent (v9.6)
- **Self-driven learning loop**: Observe → Decide → Act → Learn → Reflect
- **9-dimension policy**: Linear weights for Survival/Curiosity/Influence/Optimization/Coherence/Valence/Other/Norm/Purpose
- **CodeEnvironment**: Real reward signals from code quality metrics
- **ExperimentRunner**: N=30 statistical validation, A/B testing
- **UnifiedMOSSAgentV2**: Bridges v9 (9-dim) and v8.6 (drive emergence) architectures

### 🧬 Genetic Programming & Meta-Learning (v9.6)
- **GP System**: 3 generations of genetic programmers with fitness tracking
- **Meta-Learning**: MetaLearner, MetaSME with self-modification capabilities
- **Meta-Cognition**: BeliefSystem, UncertaintyTracker, ReflectionEngine
- **Advanced Agents**: SelfModifyingAgent, SevenLayerAgent

### 🌍 Environments & Integration (v9.6)
- **RealEnvironment**: State management with action space
- **Event-Driven**: 5 event types with priority-based purpose generation
- **Auto-Recovery**: 5 recovery strategies for agent crashes
- **Real-World Bridge**: File/network/system monitoring
- **TextWorld**: Full RL agent integration with memory and understanding

### 🔧 Refactoring (v9.2-9.3)
- Cross-file refactoring with dependency analysis
- Intelligent code extraction and movement
- Safe refactoring with transaction rollback
- Import organization and optimization

### 🧩 Extensibility (v9.4)
- **Plugin System**: Extensible architecture for custom analyzers
- **Task-Aware Agent**: 5 autonomous task scenarios
- **LLM Cost Controller**: Token budget management, every-N-generations strategy
- **Statistical Validator**: N=30 validation, t-test, Cohen's d effect size
- **File Watcher**: Real-time monitoring with debounce batching

### 🛠️ Developer Experience
- **VSCode Extension** with full LSP support
- **PyCharm Plugin** with inspections and quick fixes
- CLI for CI/CD integration
- Team collaboration features

## 📦 Installation

```bash
pip install moss-refactor
```

### IDE Extensions

- **VSCode:** Search "MOSS - Smart Code Refactoring" in the marketplace
- **PyCharm:** Install from JetBrains Plugin Repository

## 🚀 Quick Start

### 1. Initialize Your Project

```bash
cd your-project
moss init
```

### 2. Analyze Your Code

```bash
moss analyze . --format text
```

Output:
```
============================================================
MOSS v9.6.0 分析报告
============================================================
项目: /path/to/your-project
文件: 42
耗时: 0.32s
────────────────────────────────────────────────────────────
问题: 15 (错误: 0, 警告: 5, 信息: 10)
────────────────────────────────────────────────────────────
  ⚠ main.py:45 - 函数 'process_data' 过长 (65 行)
  ⚠ utils.py:12 - 函数 'helper' 复杂度过高 (15)
  ℹ main.py:1 - 未使用的导入: os
...
```

### 3. Get ML-Powered Recommendations

```python
from moss.core import RefactoringRecommender

recommender = RefactoringRecommender("./src")
recommendations = recommender.recommend("main.py", code_content)

for rec in recommendations:
    print(f"[{rec.action_type}] 置信度: {rec.confidence:.0%}")
    print(f"  建议: {rec.reason}")
```

### 4. Enable IDE Integration

The VSCode extension and PyCharm plugin automatically connect to MOSS LSP server.

## 📊 Performance Benchmarks

> **Note**: Benchmarks run on Intel Xeon (simulated). Actual performance varies by hardware.

| Metric | v9.5 Baseline | v9.6 Optimized | Improvement |
|--------|---------------|----------------|-------------|
| Analysis throughput | ~127 files/sec | ~127 files/sec | 1.0x (baseline) |
| Cache hit ratio | - | 85-95% | Significant for repeated scans |
| Memory usage | ~150MB | ~120MB | 20% reduction |

*Run your own benchmark: `python scripts/benchmark.py`*

## 🛠️ CLI Usage

```bash
# Analysis
moss analyze [path] [--format text|json|github|junit]
moss analyze . --format github --fail-on-error

# Refactoring
moss refactor move --symbol X --source A --target B [--dry-run]
moss refactor extract --file main.py --start-line 10 --end-line 50 --name helper
moss refactor imports --file main.py

# Autonomous Agent (v9.6)
moss agent --task system_monitor
moss agent --task code_review --path ./src
moss agent --list

# Genetic Programming (v9.6)
moss gp evolve --population 100 --generations 50 --target fitness_goal
moss gp optimize --file algorithm.py --strategy mutation

# Meta-Learning (v9.6)
moss meta learn --task task_config.json --episodes 1000
moss meta adapt --agent agent_config.json --environment env_config.json

# Reports (v9.4)
moss report cost --budget 5.0
moss report cost --history ./cost_history.json

# Statistical Validation (v9.4)
moss validate --experiment exp_data.json --control ctrl_data.json --name "MyExperiment"
moss validate -e exp.json -c ctrl.json --alpha 0.05

# File Watcher (v9.4)
moss watch ./src --pattern "*.py" --debounce 1.0
moss watch . --pattern "*.py" --pattern "*.js" --auto-refactor

# Server (for IDE integration)
moss server --mode stdio
moss server --mode tcp --port 2087

# Cache Management
moss cache status
moss cache clear
moss cache warm

# Benchmarking
moss benchmark . --iterations 5 --compare
```

## 🔧 CI/CD Integration

### GitHub Actions

```yaml
name: MOSS Analysis
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: moss-devtools/moss@v9.3
        with:
          path: ./src
          fail-on-error: false
```

### GitLab CI

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/moss-devtools/moss/main/ci/gitlab-ci.yml'
```

### pre-commit

```yaml
repos:
  - repo: https://github.com/moss-devtools/moss
    rev: v9.3.0
    hooks:
      - id: moss-analyze
```

## 📚 Documentation

- [Installation Guide](https://moss-devtools.github.io/moss/getting-started/installation/)
- [CLI Reference](https://moss-devtools.github.io/moss/guides/cli/)
- [API Documentation](https://moss-devtools.github.io/moss/api/core/)
- [Examples](https://moss-devtools.github.io/moss/examples/)
- [Migration Guide](docs/MIGRATION_GUIDE.md) - Migrating from `agi/` to `moss.core`
- [Merge Strategy](docs/MERGE_STRATEGY.md) - MVES v8.6 to main merge details

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MOSS v9.6.0                              │
├─────────────────────────────────────────────────────────────┤
│  VSCode / PyCharm / CLI / CI/CD / Web Dashboard             │
├─────────────────────────────────────────────────────────────┤
│  LSP Server (JSON-RPC 2.0)                                  │
├─────────────────────────────────────────────────────────────┤
│  Unified Architecture Layer (v9.6)                          │
│  ├─ UnifiedMOSSAgentV2 (v9/v8.6 bridge)                     │
│  ├─ AGI Compatibility Layer (agi/ → moss.core)              │
│  ├─ GP System (3 generations)                               │
│  ├─ Meta-Learning (MetaLearner, MetaSME)                    │
│  ├─ Meta-Cognition (Belief, Uncertainty, Reflection)        │
│  └─ TextWorld Integration (RL Agent + Memory)               │
├─────────────────────────────────────────────────────────────┤
│  Autonomous Agent Layer (v9.5)                              │
│  ├─ IntegratedMOSSSystem (Agent + LearningLoop)             │
│  ├─ CodeEnvironment (Real reward signals)                   │
│  ├─ UnifiedAgentPolicy (9-dim decision)                     │
│  └─ ExperimentRunner (N=30 validation)                      │
├─────────────────────────────────────────────────────────────┤
│  Extensibility Layer (v9.4)                                 │
│  ├─ Plugin System (Git/Coverage/TypeCheck)                  │
│  ├─ Task-Aware Agent (5 scenarios)                          │
│  ├─ LLM Cost Controller (Token budget)                      │
│  ├─ Statistical Validator (t-test, Cohen's d)               │
│  ├─ File Watcher (Real-time monitoring)                     │
│  ├─ Event-Driven Purpose (5 event types)                    │
│  └─ Auto-Recovery (5 strategies)                            │
├─────────────────────────────────────────────────────────────┤
│  Performance Engine (v9.3)                                  │
│  ├─ Incremental Analyzer                                    │
│  ├─ Parallel Analyzer                                       │
│  └─ Multi-Level Cache (L1/L2/L3)                           │
├─────────────────────────────────────────────────────────────┤
│  ML Features (v9.3)                                         │
│  ├─ Refactoring Recommender                                 │
│  └─ Pattern Learning Engine                                 │
├─────────────────────────────────────────────────────────────┤
│  Refactoring Engine (v9.2)                                  │
│  ├─ Cross-File Refactor                                     │
│  ├─ Move Operations                                         │
│  └─ Split Operations                                        │
├─────────────────────────────────────────────────────────────┤
│  Core Agent (9-Dimension + Drive System)                    │
│  ├─ D1-D4: Survival/Curiosity/Influence/Optimization        │
│  ├─ D5-D8: Coherence/Valence/Other/Norm                     │
│  ├─ D9: Purpose                                             │
│  └─ Drive System (9-dimension emergence)                    │
└─────────────────────────────────────────────────────────────┘
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MOSS is released under the [MIT License](LICENSE).

## 🙏 Acknowledgments

Special thanks to all contributors who made this release possible.

---

**[Documentation](https://moss-devtools.github.io/moss)** | **[GitHub](https://github.com/moss-devtools/moss)** | **[Issues](https://github.com/moss-devtools/moss/issues)**
