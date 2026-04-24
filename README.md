# MOSS v9.5.0 🌿

**M**ulti-**O**bjective **S**elf-Driven **S**ystem

> *Evolved from autonomous agent research to intelligent code refactoring*

[![Version](https://img.shields.io/badge/version-9.5.0-blue.svg)](https://github.com/moss-devtools/moss)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> AI-powered code refactoring, analysis, and quality insights for Python

## ✨ Features

### 🚀 Performance
- **58.5x speedup** with incremental analysis and multi-level caching (L1/L2/L3)
- Parallel processing utilizing all CPU cores (850+ files/sec)
- Hot cache analysis: 5000+ files/second

### 🔧 Refactoring
- Cross-file refactoring with dependency analysis
- Intelligent code extraction and movement
- Safe refactoring with transaction rollback
- Import organization and optimization

### 💡 Intelligence
- ML-powered refactoring recommendations based on historical data
- Code pattern learning and anti-pattern detection
- Project-specific best practices

### 🤖 Autonomous Agent (v9.5)
- **Self-driven learning loop**: Observe → Decide → Act → Learn → Reflect
- **9-dimension policy**: Linear weights for Survival/Curiosity/Influence/Optimization/Coherence/Valence/Other/Norm/Purpose
- **CodeEnvironment**: Real reward signals from code quality metrics
- **ExperimentRunner**: N=30 statistical validation, A/B testing

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
MOSS v9.5.0 分析报告
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

| Codebase Size | v9.2 Time | v9.3 Time | Speedup |
|---------------|-----------|-----------|---------|
| 100 files     | 2s        | 0.5s      | 4x      |
| 1,000 files   | 15s       | 3s        | 5x      |
| 10,000 files  | 3min      | 15s       | **12x** |

## 🛠️ CLI Usage

```bash
# Analysis
moss analyze [path] [--format text|json|github|junit]
moss analyze . --format github --fail-on-error

# Refactoring
moss refactor move --symbol X --source A --target B [--dry-run]
moss refactor extract --file main.py --start-line 10 --end-line 50 --name helper
moss refactor imports --file main.py

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

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MOSS v9.3.0                              │
├─────────────────────────────────────────────────────────────┤
│  VSCode / PyCharm / CLI / CI/CD                             │
├─────────────────────────────────────────────────────────────┤
│  LSP Server (JSON-RPC 2.0)                                  │
├─────────────────────────────────────────────────────────────┤
│  Performance Engine                                         │
│  ├─ Incremental Analyzer                                    │
│  ├─ Parallel Analyzer                                       │
│  └─ Multi-Level Cache (L1/L2/L3)                           │
├─────────────────────────────────────────────────────────────┤
│  ML Features                                                │
│  ├─ Refactoring Recommender                                 │
│  └─ Pattern Learning Engine                                 │
├─────────────────────────────────────────────────────────────┤
│  Cross-File Refactor Engine (v9.2)                          │
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
