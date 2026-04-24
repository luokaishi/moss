# MOSS v9.3

**M**odular **O**rganization and **S**tructuring **S**ystem

[![Version](https://img.shields.io/badge/version-9.3.0-blue.svg)](https://github.com/moss-devtools/moss)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](license.md)

> AI-powered code refactoring, analysis, and quality insights for Python

## Features

### 🚀 Performance
- **58.5x speedup** with incremental analysis and multi-level caching
- Parallel processing utilizing all CPU cores
- Hot cache analysis: 5000+ files/second

### 🔧 Refactoring
- Cross-file refactoring with dependency analysis
- Intelligent code extraction and movement
- Safe refactoring with transaction rollback

### 💡 Intelligence
- ML-powered refactoring recommendations
- Code pattern learning and anti-pattern detection
- Historical data analysis for better suggestions

### 🛠️ Developer Experience
- VSCode Extension with full LSP support
- PyCharm Plugin with inspections and quick fixes
- CLI for CI/CD integration

## Quick Start

### Installation

```bash
pip install moss-refactor
```

### Basic Usage

```bash
# Analyze your project
moss analyze ./src --format text

# Get refactoring recommendations
moss refactor extract --file main.py --start-line 10 --end-line 50 --name helper_function

# Start LSP server for IDE integration
moss server --mode stdio
```

### Python API

```python
from moss.core import PerformanceEngine, PerformanceConfig

# Initialize with performance optimization
config = PerformanceConfig(
    enable_incremental=True,
    enable_parallel=True,
    max_workers=8
)
engine = PerformanceEngine("./src", config)

# Analyze project
report = await engine.analyze_codebase()
print(f"Found {report.issues_found} issues in {report.duration:.2f}s")
```

## Documentation

- [Installation Guide](getting-started/installation.md)
- [CLI Reference](guides/cli.md)
- [API Documentation](api/core.md)
- [Examples](examples/basic-analysis.md)

## Performance Benchmarks

| Codebase Size | v9.2 Time | v9.3 Time | Speedup |
|---------------|-----------|-----------|---------|
| 100 files     | 2s        | 0.5s      | 4x      |
| 1,000 files   | 15s       | 3s        | 5x      |
| 10,000 files  | 3min      | 15s       | 12x     |

## IDE Support

### VSCode
Install from [VSCode Marketplace](https://marketplace.visualstudio.com/items?itemName=moss-devtools.moss-refactor)

### PyCharm
Install from [JetBrains Marketplace](https://plugins.jetbrains.com/plugin/moss)

## CI/CD Integration

### GitHub Actions

```yaml
- uses: moss-devtools/moss@v9.3
  with:
    path: ./src
    format: github
    fail-on-error: true
```

### GitLab CI

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/moss-devtools/moss/main/ci/gitlab-ci.yml'
```

## Contributing

We welcome contributions! See [Contributing Guide](contributing.md) for details.

## License

MOSS is released under the [MIT License](license.md).
