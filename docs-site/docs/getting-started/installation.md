# Installation

## Requirements

- Python 3.9 or higher
- pip or conda

## Install from PyPI

```bash
pip install moss-refactor
```

## Install from Source

```bash
git clone https://github.com/moss-devtools/moss.git
cd moss
pip install -e .
```

## Verify Installation

```bash
moss --version
# Output: MOSS v9.3.0
```

## IDE Extensions

### VSCode

1. Open VSCode
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "MOSS - Smart Code Refactoring"
4. Click Install

### PyCharm

1. Open PyCharm
2. Go to Settings → Plugins
3. Search for "MOSS"
4. Click Install

## Optional Dependencies

For enhanced ML features:

```bash
pip install moss-refactor[ml]
```

For local LLM support:

```bash
pip install moss-refactor[local-llm]
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configuration](configuration.md)
