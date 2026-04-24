# Quick Start

This guide will get you up and running with MOSS in 5 minutes.

## 1. Initialize Your Project

```bash
cd your-project
moss init
```

This creates a `.moss/config.json` file with default settings.

## 2. Analyze Your Code

```bash
moss analyze . --format text
```

Output:
```
============================================================
MOSS v9.3.0 分析报告
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

## 3. Get Refactoring Suggestions

```bash
moss analyze . --format json --output report.json
```

View the JSON report for detailed recommendations.

## 4. Apply Quick Fixes

### Organize Imports

```bash
moss refactor imports --file main.py
```

### Extract Function (Interactive)

Select code in your editor and use:

- **VSCode**: `Ctrl+Shift+R` → "Extract Function"
- **PyCharm**: Right-click → "MOSS" → "Extract Function"

## 5. Enable IDE Integration

### VSCode

The extension automatically connects to MOSS LSP server. Open any Python file to see diagnostics.

### PyCharm

The plugin adds a "MOSS" tool window on the right sidebar showing code quality metrics.

## 6. Set Up CI/CD

### GitHub Actions

Create `.github/workflows/moss.yml`:

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

## Next Steps

- Learn about [Performance Tuning](../guides/performance.md)
- Explore [Team Collaboration](../examples/team-collaboration.md)
- Read the [CLI Reference](../guides/cli.md)
